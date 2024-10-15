import sys

from simulation.classes import Lot, Machine
from simulation.randomizer import Randomizer

r = Randomizer()


class Dispatchers:

    @staticmethod
    def fifo_ptuple_for_lot(schedule, lot: Lot, time, machine: Machine = None):
        #print(lot, machine)
        if machine is not None:
            lot.ptuple = (1, -lot.priority, lot.free_since, lot.deadline_at,)
            return lot.ptuple
        else:
            return -lot.priority, lot.free_since, lot.deadline_at,

    @staticmethod
    def cr_ptuple_for_lot(schedule, lot: Lot, time, machine: Machine = None):
        if machine is not None:
            lot.ptuple = (1, -lot.priority, lot.cr(time),)
            return lot.ptuple
        else:
            return -lot.priority, lot.cr(time),


    @staticmethod
    def random_ptuple_for_lot(schedule, lot: Lot, time, machine: Machine = None):
        if machine is not None:
            return (1, r.random.uniform(0, 99999),)
        else:
            return r.random.uniform(0, 99999),

    @staticmethod
    def gsaco_ptuple_for_lot(schedule, lot: Lot, time, machine: Machine = None):
        if machine is not None:
            machine_schedule = schedule.get(machine.idx, {})
            if lot.idx in machine_schedule:
                lot.position = machine_schedule[lot.idx]
                #print(machine, machine.waiting_lots)
            else:
                lot.position = float('inf')
            lot.ptuple = (1, lot.position)
            #print(machine, lot, lot.ptuple)
            return lot.ptuple
        else:
            return lot.position,

dispatcher_map = {
    'fifo': Dispatchers.fifo_ptuple_for_lot,
    'cr': Dispatchers.cr_ptuple_for_lot,
    'random': Dispatchers.random_ptuple_for_lot,
    'gsaco': Dispatchers.gsaco_ptuple_for_lot,
}
