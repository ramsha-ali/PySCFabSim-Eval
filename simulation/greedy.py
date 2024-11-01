import sys
from datetime import datetime, timedelta

from simulation.dispatching.dispatcher import dispatcher_map
from simulation.file_instance import FileInstance
from simulation.plugins.cost_plugin import CostPlugin
from simulation.randomizer import Randomizer
from simulation.read import read_all
from simulation.stats import print_statistics, print_logs, get_process_time

import argparse

last_sort_time = -1

def dispatching_combined_permachine(ptuple_fcn, schedule, machine, time):
    for lot in machine.waiting_lots:
        lot.ptuple = ptuple_fcn(schedule, lot, time, machine)


def get_lots_to_dispatch_by_machine(instance, ptuple_fcn, schedule, machine=None):
    time = instance.current_time
    if machine is None:
        for machine in instance.usable_machines:
            break
    #print(machine, machine.waiting_lots)
    dispatching_combined_permachine(ptuple_fcn, schedule, machine, time)

    wl = sorted(machine.waiting_lots, key=lambda k: k.ptuple)
    #print(wl)
    # select lots to dispatch
    lots = [wl[0]] if wl else None
    return machine, lots


def run_greedy():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=str)
    p.add_argument('--days', type=int)
    p.add_argument('--dispatcher', type=str)
    p.add_argument('--seed', type=int)
    p.add_argument('--wandb', action='store_true', default=False)
    p.add_argument('--chart', action='store_true', default=False)
    p.add_argument('--alg', type=str, default='l4m', choices=['l4m', 'm4l'])
    a = p.parse_args()
    hours = int(round(a.days/3600, 2))

    if hours == 1:
        sys.stderr.write('Loading ' + a.dataset + ' for ' + str(a.days) + ' seconds ' + '(' + str(hours) + ' hour), using ' + a.dispatcher + '\n')
    else:
        sys.stderr.write('Loading ' + a.dataset + ' for ' + str(a.days) + ' seconds ' + '(' + str(
            hours) + ' hours), using ' + a.dispatcher + '\n')
    sys.stderr.flush()

    start_time = datetime.now()
    #print(start_time)
    #start_time = datetime.now() + timedelta(hours=1)
    #print(start_time)

    files = read_all('datasets/' + a.dataset)


    run_to = a.days


    Randomizer().random.seed(a.seed)
    l4m = a.alg == 'l4m'
    plugins = []
    if a.wandb:
        from simulation.plugins.wandb_plugin import WandBPlugin
        plugins.append(WandBPlugin())
    if a.chart:
        from simulation.plugins.chart_plugin import ChartPlugin
        plugins.append(ChartPlugin())
    plugins.append(CostPlugin())


    instance = FileInstance(files, run_to, l4m, plugins)
    #print(instance.schedule)
    #for machine in instance.machines:
        #print(machine, machine.waiting_lots)

    lot_id_to_position = {}
    for machine in instance.machines:
        scheduled_lot_ids = instance.schedule.get(machine.idx, [])
        if machine.idx not in lot_id_to_position:
            lot_id_to_position[machine.idx] = {}
        for idx, lot_id in enumerate(scheduled_lot_ids):
            lot_id_to_position[machine.idx][lot_id] = idx


    # for lot released by simulation
    lot_instance = []
    for lot in instance.active_lots:
        lot_tuple = (lot.idx, lot.part_name, lot.actual_step)
        lot_instance.append(lot_tuple)

    lot_instance_file = 'simulation_state/lot_instance_example.txt'
    with open(lot_instance_file, 'w') as file:
        print_head = f'Lot Product CurrentStep\n'
        file.write(print_head)
        for s in lot_instance:
            lot, product, actual_step = s
            message = f"{lot} {product} {actual_step}\n"
            file.write(message)

    dispatcher = dispatcher_map[a.dispatcher]

    sys.stderr.write('Starting simulation with dispatching rule\n\n')
    sys.stderr.flush()

    done_lots_by_dispatching = []
    while not instance.done:

        done = instance.next_decision_point()
        instance.print_progress_in_days()


        if done or instance.current_time > run_to:
            break
        if l4m:
            machine, lots = get_lots_to_dispatch_by_machine(instance, dispatcher, lot_id_to_position)

            if lots is None:
                instance.usable_machines.remove(machine)
            else:
                machine_done, lot_done = instance.dispatch(machine, lots)
                for lot in lots:
                    if lot_done <= run_to:
                        done_lots = (lot.idx, lot.part_name, lot.actual_step,
                                     machine.family, machine, instance.current_time, lot_done)
                        done_lots_by_dispatching.append(done_lots)


    sys.stderr.write(
        # f'\rDay {self.printed_days}===Throughput: {round(len(self.done_lots) / self.printed_days)}/day=')
        f'Throughput (lots): {round(len(instance.done_lots))} '
        f'Throughput (operations): {len(done_lots_by_dispatching)} '
        f'Makespan: {max(instance.mac_times.values())} ' #{max(instance.mac_times, key=lambda k: instance.mac_times[k])} '
        f'\n')


    lot_instance_file = f'dispatching_output/dispatching_seed{a.seed}_{a.dispatcher}_{a.days}s.txt'
    with open(lot_instance_file, 'w') as file:
        print_head = f'Lot Product Step Machine_id start end\n'
        file.write(print_head)
        for op in done_lots_by_dispatching:
            lot, product, actual_step, family, machine, start_lot, lot_time = op
            message = f"{lot} {product} {actual_step} {family} {machine} {start_lot} {lot_time}\n"
            file.write(message)


    instance.finalize()
    interval = datetime.now() - start_time


    #print(instance.current_time_days, ' hours simulated in ', interval)
    print(int(instance.run_to/3600), 'hour simulated in ', interval)

    print_statistics(instance, a.days, a.dataset, a.dispatcher, method='greedy_seed' + str(a.seed))
    print_logs(instance)
    get_process_time(instance)




