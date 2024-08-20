import time

from get_input import get_user_input
from pyinstrument import Profiler
import torch.multiprocessing as mp
import torch
from colony import Colony
from heuristic import sequence
from get_schedule import get_schedule

device=torch.device('cpu')
global_best_makespan = float('inf')
global_best_edges = None
global_best_sequence = None
global_best_machines = None
global_best_start_time = None
global_best_end_time = None
job_matrix = None
parameters = get_user_input()
def worker(args):
    job_tensor, adjacency_matrix, pheromone_matrix, machine_matrix, device = args
    job_tensor = job_tensor.to(device)
    adjacency_matrix = adjacency_matrix.to(device)
    pheromone_matrix = pheromone_matrix.to(device)
    machine_matrix = machine_matrix.to(device)
    makespan, edges, seq, machine, start_time_op, end_time_op = sequence(job_tensor, adjacency_matrix, pheromone_matrix, machine_matrix, parameters['seed'])

    return makespan, edges.tolist(), seq.tolist(), machine.tolist(), start_time_op.tolist(), end_time_op.tolist()



def initialize_colony_parallel(num_ants, device):
    args_list = [(colony.job_tensor, colony.adjacency_matrix, colony.graph.pheromone_matrix, colony.machine_matrix, device) for _ in range(num_ants)]
    with mp.Pool(processes=num_ants) as pool:
        combined_results = pool.map(worker, args_list)



    f_makespan, f_edges, f_sequence, f_machine, f_start_time_op, f_end_time_op = zip(*combined_results)
    f_edges = [torch.tensor(edges, dtype=torch.long, device=device) for edges in
                 f_edges]
    return list(f_makespan), list(f_edges), list(f_sequence), list(f_machine), list(f_start_time_op), list(f_end_time_op)



if __name__ == '__main__':
    mp.set_start_method('spawn')
    profiler = Profiler()
    profiler.start()
    colony = Colony(parameters)
    start_time = time.time()
    n_cycles = 1
    while time.time() - start_time < parameters["time_limit"] or n_cycles <= parameters["cycle"]:
        #print(f'cycle {n_cycles}')
        m, e, s, mac, start, end = initialize_colony_parallel(parameters["num_ants"], device)
        makespans = torch.tensor(m)
        min_index = torch.argmin(makespans).item()
        current_best_makespan = makespans[min_index].item()
        current_best_edges = e[min_index]
        current_best_sequence = s[min_index]
        current_best_machines = mac[min_index]
        current_best_start_time = start[min_index]
        current_best_end_time = end[min_index]
        if current_best_makespan < global_best_makespan:
            global_best_makespan = current_best_makespan
            global_best_edges = current_best_edges
            global_best_sequence = current_best_sequence
            global_best_machines = current_best_machines
            global_best_start_time = current_best_start_time
            global_best_end_time = current_best_end_time
            print(f"New best makespan found: {global_best_makespan}")
        else:
            print(f"No improvement, best makespan remains: {global_best_makespan}")

        colony.graph.update_pheromone(colony.graph.pheromone_matrix, global_best_edges, parameters["contribution"],
                                      parameters["rho"], parameters["min_pheromone"])

        print(f'cycle {n_cycles} completed in {time.time() - start_time}')
        n_cycles+=1

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








