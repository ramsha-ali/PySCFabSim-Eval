import io
import json
import statistics
import sys
from collections import defaultdict
from simulation.classes import Lot



def print_statistics(instance, days, dataset, disp, method='greedy', dir='greedy'):
    from simulation.instance import Instance

    instance: Instance
    lot: Lot
    lots = defaultdict(lambda: {'ACT': [], 'throughput': 0, 'on_time': 0, 'tardiness': 0, 'waiting_time': 0,
                                'processing_time': 0, 'transport_time': 0, 'waiting_time_batching': 0})

    #for machine in instance.machines:
        #for e in machine.events:
            #print(e)

    utilized_times = defaultdict(lambda: [])
    br_times = defaultdict(lambda: [])
    for machine in instance.machines:
        utilized_times[machine.family].append(machine.utilized_time)
        br_times[machine.family].append(machine.bred_time)
    #print(utilized_times)
    print('Machine', 'Cnt', 'avail', 'util', 'br')
    machines = defaultdict(lambda: {})
    for machine_name in sorted(list(utilized_times.keys())):
        av = (instance.current_time - statistics.mean(br_times[machine_name]))
        machines[machine_name]['avail'] = av / instance.current_time
        machines[machine_name]['util'] = statistics.mean(utilized_times[machine_name]) / av
        machines[machine_name]['br'] = statistics.mean(br_times[machine_name]) / instance.current_time
        r = instance.lot_waiting_at_machine[machine_name]
        print(machine_name, len(utilized_times[machine_name]),
              round(machines[machine_name]['avail'] * 100, 2),
              round(machines[machine_name]['util'] * 100, 2),
              round(machines[machine_name]['br'] * 100, 2),
              )



    plugins = {}

    for plugin in instance.plugins:
        if plugin.get_output_name() is not None:
            plugins[plugin.get_output_name()] = plugin.get_output_value()

    with io.open(f'{dir}/{method}_{days}days_{dataset}_{disp}.json', 'w') as f:
        json.dump({
            'lots': lots,
            'machines': machines,
            'plugins': plugins,
        }, f)

    return


def print_logs(instance):
    file_path_lots = 'simulation_state/wip_lots.txt'
    with open(file_path_lots, 'w') as file:
        print_head = f'Lot Product CurrentStep\n'
        file.write(print_head)
        for wip in instance.active_lots:
            current_step = wip.remaining_steps[0] if wip.remaining_steps else 'None'
            message = f"{wip.idx} " \
                      f"{wip.part_name} " \
                      f"{current_step}\n"
            file.write(message)

    file_path = 'simulation_state/tools.txt'
    with open(file_path, 'w') as file:
        print_head = f'Toolgroup Machineid\n'
        file.write(print_head)
        for machine in instance.machines:
            message = f"{machine.family} " \
                      f"{machine.idx}\n"
            file.write(message)

    file_path_stats = 'simulation_state/breakdown_stats.txt'
    with open(file_path_stats, 'w') as file:
        print_time = f'current_time {instance.current_time}\n'
        file.write(print_time)
        utilized_times = defaultdict(lambda: [])
        br_times = defaultdict(lambda: [])
        for machine in instance.machines:
            utilized_times[machine.family].append(machine.utilized_time)
            br_times[machine.family].append(machine.bred_time)

        print_head = f'Machine Cnt avail util br\n'
        file.write(print_head)
        machines = defaultdict(lambda: {})
        for machine_name in sorted(list(utilized_times.keys())):
            av = (instance.current_time - statistics.mean(br_times[machine_name]))
            machines[machine_name]['avail'] = av / instance.current_time
            machines[machine_name]['util'] = statistics.mean(utilized_times[machine_name]) / av
            machines[machine_name]['br'] = statistics.mean(br_times[machine_name]) / instance.current_time
            r = instance.lot_waiting_at_machine[machine_name]
            machine_info = f"{machine_name} {len(utilized_times[machine_name])} " \
                           f"{round(machines[machine_name]['avail'] * 100, 2)} " \
                           f"{round(machines[machine_name]['util'] * 100, 2)} " \
                           f"{round(machines[machine_name]['br'] * 100, 2)}\n"
            file.write(machine_info)

    file_path_stats = 'simulation_state/at_time.txt'
    with open(file_path_stats, 'w') as file:
        print_time = f'current_time {instance.current_time}\n'
        file.write(print_time)


def get_process_time(instance):
    file_path_lots = 'datasets/SMT2020_example_sch/route.txt'
    with open(file_path_lots, 'w') as file:
        print_head = f'Product Step Tool Processtime\n'
        file.write(print_head)
        for name, route in instance.routes.items():
            name = name.replace('route', 'part').replace('.txt', '')
            for step in route.steps:
                message = f"{name} " \
                          f"{step.idx} " \
                          f"{step.family} " \
                          f"{int(step.processing_time.avg())}\n"
                file.write(message)



