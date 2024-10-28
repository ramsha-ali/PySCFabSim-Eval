from collections import defaultdict
from typing import Dict, List, Set, Tuple

from simulation.classes import Machine, Route, Lot
from simulation.dispatching.dm_lot_for_machine import LotForMachineDispatchManager
from simulation.dispatching.dm_machine_for_lot import MachineForLotDispatchManager
from simulation.event_queue import EventQueue
from simulation.events import MachineDoneEvent, LotDoneEvent, BreakdownEvent, ReleaseEvent
from simulation.plugins.interface import IPlugin


class Instance:

    def __init__(self, machines: List[Machine], routes: Dict[str, Route], lots: List[Lot],
                 breakdowns: List[BreakdownEvent],
                 lot_for_machine,
                 schedule, run_to, plugins):

        self.run_to = run_to
        self.plugins: List[IPlugin] = plugins
        self.lot_waiting_at_machine = defaultdict(lambda: (0, 0))

        self.free_machines: List[bool] = []
        self.usable_machines: Set[Machine] = set()
        self.usable_lots: List[Lot] = list()

        self.machines: List[Machine] = [m for m in machines]
        self.family_machines = defaultdict(lambda: [])
        for m in self.machines:
            self.family_machines[m.family].append(m)
        self.routes: Dict[str, Route] = routes

        self.dm = LotForMachineDispatchManager() if lot_for_machine else MachineForLotDispatchManager()
        self.dm.init(self)

        self.schedule = schedule

        self.dispatchable_lots: List[Lot] = lots
        self.dispatchable_lots.sort(key=lambda k: k.release_at)
        self.active_lots: List[Lot] = []
        self.done_lots: List[Lot] = []
        self.events = EventQueue()

        self.current_time = 0

        for plugin in self.plugins:
            plugin.on_sim_init(self)

        self.next_step()
        self.free_up_machines(self.machines)

        #for br in breakdowns:
            #self.add_event(br)

        self.printed_days = -1

        self.mac_times = {}

    @property
    def current_time_days(self):
        return self.current_time / 3600 / 24

    def next_step(self):
        process_until = []
        if len(self.events.arr) > 0:
            process_until.append(max(0, self.events.first.timestamp))
        if len(self.dispatchable_lots) > 0:
            process_until.append(max(0, self.dispatchable_lots[0].release_at))
        process_until = min(process_until)
        while len(self.events.arr) > 0 and self.events.first.timestamp <= process_until:
            ev = self.events.pop_first()
            self.current_time = max(0, ev.timestamp, self.current_time)
            ev.handle(self)
        ReleaseEvent.handle(self, process_until, self.schedule)

    def free_up_machines(self, machines):
        for machine in machines:
            machine.events.clear()
            self.dm.free_up_machine(self, machine)
            for plugin in self.plugins:
                plugin.on_machine_free(self, machine)

    def free_up_lots(self, lots: List[Lot], schedule):
        for lot in lots:
            lot.free_since = self.current_time
            step_found = False
            while len(lot.remaining_steps) > 0:
                old_step = None
                if lot.actual_step is not None:
                    lot.processed_steps.append(lot.actual_step)
                    old_step = lot.actual_step
                lot.actual_step, lot.remaining_steps = lot.remaining_steps[0], lot.remaining_steps[1:]
                if lot.actual_step:
                    self.dm.free_up_lots(self, lot, schedule)
                    step_found = True
                    for plugin in self.plugins:
                        plugin.on_step_done(self, lot, old_step)
                    break

            if not step_found:
                assert len(lot.remaining_steps) == 0
                lot.actual_step = None
                lot.done_at = self.current_time

                self.active_lots.remove(lot)
                self.done_lots.append(lot)
                for plugin in self.plugins:
                    plugin.on_lot_done(self, lot)

            for plugin in self.plugins:
                plugin.on_lot_free(self, lot)


    def dispatch(self, machine: Machine, lots: List[Lot]):
        # remove machine and lot from active sets
        #print(machine, lots)
        if machine not in self.mac_times:
            self.mac_times[machine] = 0
        self.reserve_machine_lot(lots, machine, self.schedule)
        lwam = self.lot_waiting_at_machine[machine.family]
        self.lot_waiting_at_machine[machine.family] = (lwam[0] + len(lots),
                                                       lwam[1] + sum([self.current_time - l.free_since for l in lots]))

        for lot in lots:
            lot.waiting_time += self.current_time - lot.free_since

        # compute times for lot and machine
        lot_time, machine_time = self.get_times(lots, machine)
        # add events
        machine_done = self.current_time + machine_time

        if machine_done <= self.run_to:
            self.mac_times[machine] = machine_done


        machine.will_be_free = machine_done
        lot_done = self.current_time + lot_time
        ev1 = MachineDoneEvent(machine_done, [machine])
        ev2 = LotDoneEvent(lot_done, [machine], lots, self.schedule)
        self.add_event(ev1)
        self.add_event(ev2)
        machine.events += [ev1, ev2]

        for plugin in self.plugins:
            plugin.on_dispatch(self, machine, lots, machine_done, lot_done)
        return machine_done, lot_done


    def get_times(self, lots, machine):
        # for stochastic pro time
        proc_t_samp = lots[0].actual_step.processing_time.sample()

        # for deterministic pro time
        #proc_t_samp = lots[0].actual_step.processing_time.avg()
        lot_time = int(proc_t_samp)
        for lot in lots:
            lot.processing_time = lot_time

        machine_time = lot_time
        if machine_time <= self.run_to:
            if (machine.utilized_time + machine_time) <= self.run_to:
                machine.utilized_time += machine_time
        #print(machine.family, machine.idx, machine.utilized_time)
        return lot_time, machine_time

    def reserve_machine_lot(self, lots, machine, schedule):
        self.dm.reserve(self, lots, machine, schedule)

    def add_event(self, to_insert):
        # insert event to the correct place in the array
        self.events.ordered_insert(to_insert)

    def next_decision_point(self):
        return self.dm.next_decision_point(self)

    def handle_breakdown(self, machine, delay):
        ta = []
        for ev in machine.events:
            if ev in self.events.arr:
                ta.append(ev)
                self.events.remove(ev)
        for ev in ta:
            ev.timestamp += delay
            self.add_event(ev)

    @property
    def done(self):
        # for constant lot release
        #return len(self.dispatchable_lots) == 0 and len(self.active_lots) == 0
        return len(self.active_lots) == 0


    def finalize(self):
        for plugin in self.plugins:
            plugin.on_sim_done(self)


    def print_progress_in_days(self):
        import sys
        if int(self.current_time_days) > self.printed_days:
            self.printed_days = int(self.current_time_days)
            if self.printed_days > 0:
                sys.stderr.write(
                    f'\rDay {self.printed_days}===Throughput: {round(len(self.done_lots) / self.printed_days)}'
                    f'===Makespan: {max(self.mac_times.values())} {max(self.mac_times, key=lambda k: self.mac_times[k])}/day=')

                sys.stderr.flush()




