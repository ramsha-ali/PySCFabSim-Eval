import random
import time

import numpy as np

from get_input import get_user_input
from pyinstrument import Profiler
import torch.multiprocessing as mp
import torch
from colony import Colony
from heuristic import sequence
from get_schedule import get_schedule

device=torch.device('cpu')

global_best_makespan = float('inf')
global_best_operations = 0
global_best_edges = None
global_best_sequence = None
global_best_machines = None
global_best_start_time = None
global_best_end_time = None
parameters = get_user_input()

def worker(args):
    machine_map, job_tensor, adjacency_matrix, pheromone_matrix, machine_matrix, availability_matrix, availability_time_matrix, current_time, num_day, device, seed = args
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    job_tensor = job_tensor.to(device)
    adjacency_matrix = adjacency_matrix.to(device)
    pheromone_matrix = pheromone_matrix.to(device)
    machine_matrix = machine_matrix.to(device)
    if availability_matrix is not None and availability_time_matrix is not None:
        availability_matrix = availability_matrix.to(device)
        availability_time_matrix = availability_time_matrix.to(device)

    operations, makespan, edges, seq, machine, start_time_op, end_time_op = sequence(machine_map, job_tensor, adjacency_matrix, pheromone_matrix,
                                                                         machine_matrix, availability_matrix, availability_time_matrix, current_time, num_day)

    return operations, makespan, edges.tolist(), seq.tolist(), machine.tolist(), start_time_op.tolist(), end_time_op.tolist()


def initialize_colony_parallel(num_ants, seed_base, device):
    print("initializing")
    args_list = []

    for ant in range(num_ants):
        args_tuple = (
            colony.machine_map,
            colony.job_tensor,
            colony.adjacency_matrix,
            colony.graph.pheromone_matrix,
            colony.machine_matrix,
            colony.availability_matrix,
            colony.availability_time_matrix,
            colony.current_time,
            parameters['days'],
            device
        )
        #print("Memory address of job_tensor:", id(colony.job_tensor))
        args_list.append(args_tuple)
    with mp.Pool(processes=num_ants) as pool:
        worker_seeds = [seed_base + i for i in range(num_ants)]
        seeds_and_args = [(args + (worker_seeds[i],)) for i, args in enumerate(args_list)]
        combined_results = pool.map(worker, seeds_and_args)

    f_operations, f_makespan, f_edges, f_sequence, f_machine, f_start_time_op, f_end_time_op = zip(*combined_results)
    f_edges = [torch.tensor(edges, dtype=torch.long, device=device) for edges in
                 f_edges]
    return list(f_operations), list(f_makespan), list(f_edges), list(f_sequence), list(f_machine), list(f_start_time_op), list(f_end_time_op)


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    colony = Colony(parameters)
    print("done step 1")
    for seed in parameters['seed']:
        profiler = Profiler()
        profiler.start()
        start_time = time.time()
        n_cycles = 1
        cycle_best_makespan = []
        cycle_best_operations = []
        print(f'State: processing time: {parameters["state"]}, breakdown: {parameters["breakdown"]}')
        while time.time() - start_time < parameters["time_limit"] or n_cycles <= parameters["cycle"]:
            cycle_seed = seed + n_cycles
            #np.random.seed(cycle_seed)
            #random.seed(cycle_seed)
            #torch.manual_seed(cycle_seed)
            op, m, e, s, mac, start, end = initialize_colony_parallel(parameters["num_ants"], cycle_seed, device)
            ops = torch.tensor(op)
            makespans = torch.tensor(m)

            min_index = torch.argmin(makespans).item()
            max_index_op = torch.argmax(ops).item()
            current_best_makespan = makespans[min_index].item()
            current_best_ops = ops[min_index].item()
            current_best_edges = e[min_index]
            current_best_sequence = s[min_index]
            current_best_machines = mac[min_index]
            current_best_start_time = start[min_index]
            current_best_end_time = end[min_index]
            if current_best_makespan < global_best_makespan:
                global_best_makespan = current_best_makespan
                global_best_operations = current_best_ops
                global_best_edges = current_best_edges
                global_best_sequence = current_best_sequence
                global_best_machines = current_best_machines
                global_best_start_time = current_best_start_time
                global_best_end_time = current_best_end_time
                cycle_best_makespan.append(global_best_makespan)
                print(f"New best makespan found: {global_best_makespan}")
            else:
                global_best_operations = global_best_operations
                global_best_makespan = global_best_makespan
                print(f"No improvement, best makespan remains: {global_best_makespan}")


            colony.graph.update_pheromone(colony.graph.pheromone_matrix, global_best_edges, parameters["contribution"],
                                          parameters["rho"], parameters["min_pheromone"])

            #print(f'cycle {n_cycles} completed in {time.time() - start_time}')
            print(f'cycle {n_cycles}/{parameters["cycle"]} completed')
            n_cycles+=1

        average_makespan = sum(cycle_best_makespan) / len(cycle_best_makespan)
        #print(f'average makespan: {average_makespan}')
        print(f'operations: {global_best_operations}')


        profiler.stop()
        #profiler.open_in_browser()
        #print(profiler.output_text(unicode=True, color=True))
        job_matrix = colony.job_tensor
        machine_map = colony.machine_map
        sequence = global_best_sequence
        machine_asigned = global_best_machines
        start_job = global_best_start_time
        end_job = global_best_end_time

        get_schedule(job_matrix, machine_map, sequence, machine_asigned, start_job, end_job)








