import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import List

from simulation.classes import Lot, Machine
from simulation.dispatching.dispatcher import dispatcher_map
from simulation.file_instance import FileInstance
from simulation.plugins.cost_plugin import CostPlugin
from simulation.randomizer import Randomizer
from simulation.read import read_all
from simulation.stats import print_statistics, print_logs, get_process_time

last_sort_time = -1

def dispatching_combined_permachine(ptuple_fcn, machine, time):
    for lot in machine.waiting_lots:
        lot.ptuple = ptuple_fcn(lot, time, machine)

def get_lots_to_dispatch_by_machine(instance, ptuple_fcn, machine=None):
    time = instance.current_time
    if machine is None:
        for machine in instance.usable_machines:
            break

    dispatching_combined_permachine(ptuple_fcn, machine, time)

    wl = sorted(machine.waiting_lots, key=lambda k: k.ptuple)
    # select lots to dispatch
    lots = [wl[0]] if wl else None
    return machine, lots

def read_schedule(file_path):
    schedule = []
    with open(file_path, 'r') as f:
        next(f)  # Skip header
        for line in f:
            lot, _, _, _, machine, start_time, _ = line.strip().split('\t')
            schedule.append((int(lot), machine, float(start_time)))
    return sorted(schedule, key=lambda x: x[2])  # Sort by start_time

def run_greedy(dataset, days, dispatcher, seed, wandb=False, chart=False, alg='l4m'):
    sys.stderr.write(f'Loading {dataset} for {days} days, using {dispatcher}\n')
    sys.stderr.flush()

    start_time = datetime.now()

    files = read_all('datasets/' + dataset)

    run_to = 3600 * 24 * days
    Randomizer().random.seed(seed)
    l4m = alg == 'l4m'
    plugins = []
    if wandb:
        from simulation.plugins.wandb_plugin import WandBPlugin
        plugins.append(WandBPlugin())
    if chart:
        from simulation.plugins.chart_plugin import ChartPlugin
        plugins.append(ChartPlugin())
    plugins.append(CostPlugin())
    instance = FileInstance(files, run_to, l4m, plugins)

    schedule = read_schedule('aco_cpu/schedule_output.txt')
    schedule_index = 0

    sys.stderr.write('Starting simulation with strict schedule-based dispatching\n\n')
    sys.stderr.flush()

    iteration_count = 0
    last_progress_update = datetime.now()
    events_processed = 0

    while not instance.done:
        iteration_count += 1
        done = instance.next_decision_point()
        instance.print_progress_in_days()
        if done or instance.current_time > run_to:
            break

        # Add progress update every 1000 iterations or every 60 seconds
        current_time = datetime.now()
        if iteration_count % 1000 == 0 or (current_time - last_progress_update).total_seconds() > 60:
            elapsed_time = current_time - start_time
            progress_percentage = (instance.current_time / run_to) * 100
            events_processed = len(instance.done_lots)  # Approximating events processed with completed lots
            sys.stderr.write(f"Iteration: {iteration_count}, Time: {instance.current_time:.2f} seconds ({instance.current_time_days:.4f} days), "
                             f"Progress: {progress_percentage:.2f}%, Events processed: {events_processed}, "
                             f"Elapsed time: {elapsed_time}\n")
            sys.stderr.flush()
            last_progress_update = current_time

        if schedule_index < len(schedule):
            lot_id, machine_name, scheduled_time = schedule[schedule_index]

            if instance.current_time >= scheduled_time:
                lot = next((l for l in instance.active_lots if l.idx == lot_id), None)
                machine = next((m for m in instance.usable_machines if m.name == machine_name), None)

                if lot and machine:
                    instance.dispatch(machine, [lot])
                    schedule_index += 1
                else:
                    # If the scheduled lot or machine is not available, move to the next schedule entry
                    schedule_index += 1
                    continue
            else:
                # If it's not time for the next scheduled operation, do nothing and wait
                pass
        else:
            # If we've gone through all scheduled operations, use the original dispatching method
            machine, lots = get_lots_to_dispatch_by_machine(instance, dispatcher_map[dispatcher])
            if lots is None:
                instance.usable_machines.remove(machine)
            else:
                instance.dispatch(machine, lots)

    instance.finalize()
    interval = datetime.now() - start_time
    print(f"{instance.current_time_days} days simulated in {interval}")
    print_statistics(instance, days, dataset, dispatcher, method=f'strict_schedule_based_seed{seed}')
    print_logs(instance)
    get_process_time(instance)
