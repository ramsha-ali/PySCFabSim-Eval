import torch


def sequence(j, adjacency_matrix, pheromone_matrix, machine_matrix, device="cpu"):

    n = adjacency_matrix.size(0)
    valid_operations_mask = (j[:, :, 0] != -1) & (j[:, :, 1] != -1)
    valid_flat_mask = valid_operations_mask.view(-1)
    valid_operations = j.view(-1, j.size(2))[valid_flat_mask]
    processing_times = valid_operations[:, 1]

    start_times = torch.zeros(n-1, dtype=torch.float, device=device)
    end_times = torch.zeros(n-1, dtype=torch.float, device=device)
    num_machines = machine_matrix.size(1)
    machine_times = torch.zeros(num_machines, device=device, dtype=torch.float)

    valid_job_indices = torch.repeat_interleave(torch.arange(j.size(0), device=device), j.size(1))[
        valid_flat_mask]
    all_operation_indices = torch.tile(torch.arange(j.size(1), device=device), (j.size(0),))
    valid_operation_indices = all_operation_indices[valid_flat_mask]
    shifted_job_indices = torch.cat((torch.tensor([-1], device=device), valid_job_indices[:-1]))
    shifted_operation_indices = torch.cat((torch.tensor([-1], device=device), valid_operation_indices[:-1]))
    has_predecessor = (valid_job_indices == shifted_job_indices) \
                      & (valid_operation_indices == shifted_operation_indices + 1)
    predecessors = torch.full_like(valid_operation_indices, -1)
    predecessors[1:][has_predecessor[1:]] = torch.arange(len(valid_operation_indices),
                                                         device=device)[1:][has_predecessor[1:]] + 1
    op_has_predecessor = predecessors[predecessors != -1]

    pred = torch.full_like(valid_operation_indices, -1)
    pred[1:][has_predecessor[1:]] = torch.arange(len(valid_operation_indices),
                                                 device=device)[1:][has_predecessor[1:]]
    op_predecessor = pred[pred != -1]


    visited = torch.zeros(n, dtype=torch.bool, device=device)
    current_index = 0
    visited[current_index] = True
    schedule = torch.tensor([current_index], dtype=torch.long, device=device)
    estimated_size = 1000  # Adjust based on your typical scenario
    selected_edges = torch.empty((estimated_size, 2), dtype=torch.long, device=device)
    edge_count = 0
    selected_machine = torch.tensor([current_index], dtype=torch.long, device=device)


    while not visited.all():
        current_node = schedule[current_index].item()
        connected = adjacency_matrix[current_node].unsqueeze(0).any(dim=0) & ~visited

        if connected.any():
            candidates = torch.where(connected)[0]
            for i in range(len(candidates)):

                pheromone_levels = pheromone_matrix[current_node, candidates]
                total_pheromone = pheromone_levels.sum()
                probabilities = pheromone_levels / total_pheromone
                cdf = probabilities.cumsum(dim=0)
                random_value = torch.rand(1, device=pheromone_levels.device)
                #selected_index = (cdf >= random_value).nonzero().min().item()
                nonzero_indices = (cdf >= random_value).nonzero()
                if nonzero_indices.nelement() == 0:
                    continue
                else:
                    selected_index = nonzero_indices.min().item()
                s_node = candidates[selected_index].item()
                selected = torch.tensor([s_node], device=device)
                is_visited = visited[selected.item()]
                if not is_visited:
                    node_exists = (op_has_predecessor == selected.item()).any()
                    if node_exists:
                        indices = torch.nonzero(op_has_predecessor == selected.item(), as_tuple=False)
                        get_pred = op_predecessor[indices]
                        pred_is_visited = visited[get_pred.item()]
                        if pred_is_visited:
                            schedule = torch.cat((schedule, selected))
                            visited[selected] = True
                            if edge_count == selected_edges.size(0):

                                new_size = selected_edges.size(0) + estimated_size
                                new_edges = torch.empty((new_size, 2), dtype=torch.long, device=device)
                                new_edges[:edge_count] = selected_edges
                                selected_edges = new_edges
                            selected_edges[edge_count, 0] = current_node
                            selected_edges[edge_count, 1] = selected.item()
                            edge_count += 1
                            pred_index = (schedule[1:] == get_pred.item()).nonzero(as_tuple=True)[0]

                            predecessor_end_time = end_times[pred_index]
                            pro_time = processing_times[selected.item() - 1]
                            available_machines = machine_matrix[selected.item()]
                            available_machine_id = torch.where(available_machines == 1)[0]

                            mac = machine_times[available_machine_id]
                            min_time, min_index = torch.min(mac, 0)
                            earliest_available_machine = available_machine_id[min_index]
                            earliest_available_machine = earliest_available_machine.unsqueeze(0)
                            selected_machine = torch.cat((selected_machine, earliest_available_machine), dim=0)
                            start_time_machine = machine_times[earliest_available_machine]
                            start_time = torch.max(predecessor_end_time, start_time_machine)
                            end_time = start_time + pro_time

                            selected_indices = torch.where(schedule == selected)[0]
                            valid_i = selected_indices - 1
                            start_times[valid_i] = start_time
                            end_times[valid_i] = end_time
                            machine_times[earliest_available_machine] = end_time
                            mask = candidates != selected.view(-1, 1)
                            mask = mask.all(dim=0)
                            candidates = candidates[mask]

                        else:
                            mask = candidates != selected.view(-1, 1)
                            mask = mask.all(dim=0)
                            candidates = candidates[mask]
                    else:

                        schedule = torch.cat((schedule, selected))

                        visited[selected] = True
                        if edge_count == selected_edges.size(0):

                            new_size = selected_edges.size(0) + estimated_size
                            new_edges = torch.empty((new_size, 2), dtype=torch.long, device=device)
                            new_edges[:edge_count] = selected_edges
                            selected_edges = new_edges
                        selected_edges[edge_count, 0] = current_node
                        selected_edges[edge_count, 1] = selected.item()
                        edge_count += 1
                        pro_time_p = processing_times[selected.item() - 1]
                        available_machines = machine_matrix[selected.item()]
                        available_machine_id = torch.where(available_machines == 1)[0]

                        mac = machine_times[available_machine_id]
                        min_time, min_index = torch.min(mac, 0)
                        earliest_available_machine = available_machine_id[min_index]
                        earliest_available_machine = earliest_available_machine.unsqueeze(0)
                        selected_machine = torch.cat((selected_machine, earliest_available_machine), dim=0)

                        start_time_j = machine_times[earliest_available_machine]
                        end_time_j = start_time_j + pro_time_p

                        selected_indices = torch.where(schedule == selected)[0]
                        valid_i = selected_indices - 1
                        start_times[valid_i] = start_time_j
                        end_times[valid_i] = end_time_j
                        machine_times[earliest_available_machine] = end_time_j

                        mask = candidates != selected.view(-1, 1)
                        mask = mask.all(dim=0)
                        candidates = candidates[mask]

        current_index += 1

    selected_edges = selected_edges[:edge_count]
    makespan = torch.max(machine_times).item()
    #print(schedule)
    #print("start_time", start_times, "end_times",end_times, "machine_times", machine_times)
    #print("machine_times", machine_times)
    return makespan, selected_edges





