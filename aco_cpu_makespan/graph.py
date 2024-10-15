import numpy as np
import torch

class Graph():

    pheromone_matrix = None
    def generate_graph(self, j, m, pheromone, mac_availability, mac_attime, current_time, device="cpu"):
        #print(len(j))
        #print(len(m))
        job = torch.tensor(j, device=device)
        #print(job)
        #valid_operations_mask = (job[:, :, 0] != -1) & (job[:, :, 1] != -1)  # operations not [-1, -1]: padded
        valid_operations_mask = (job != -1).all(dim=2) # operations not padded
        valid_flat_mask = valid_operations_mask.view(-1)

        valid_operations = job.view(-1, job.size(2))[valid_flat_mask]
        num_valid_operations = (valid_operations.shape[0] + 1)
        #print(num_valid_operations)
        adjacency_matrix = torch.zeros((num_valid_operations, num_valid_operations), device=device,
                                       dtype=torch.int)

        for job_index in range(job.size(0)):
            valid_ops_indices = valid_operations_mask[job_index].nonzero()
            if len(valid_ops_indices) > 0:

                first_op_global_index = valid_ops_indices[0, 0] + job_index * job.size(1)

                adjusted_index = (valid_flat_mask[:first_op_global_index].sum() + 1).item()
                adjacency_matrix[0, adjusted_index] = 1


        valid_job_indices = torch.repeat_interleave(torch.arange(job.size(0), device=device), job.size(1))[
            valid_flat_mask]

        # edges based on precedence within the same job
        # torch.roll to shift job indices for comparison
        shifted_job_indices = torch.roll(valid_job_indices, -1)
        valid_edge_mask = (valid_job_indices == shifted_job_indices)[:-1]

        source_indices = torch.arange(1, num_valid_operations - 1, device=device)
        target_indices = torch.arange(2, num_valid_operations, device=device)
        adjacency_matrix[source_indices, target_indices] = valid_edge_mask.int()
        # edges for operations on the same machine
        machine_ids = valid_operations[:, 0]
        machine_edges = (machine_ids[:, None] == machine_ids[None, :]) & (
                valid_job_indices[:, None] != valid_job_indices[None, :])
        adjacency_matrix[1:, 1:] += machine_edges.int()

        adjacency_matrix.clamp_(0, 1) # adjacency matrix to binary

        # no operation is a successor of itself
        adjacency_matrix.fill_diagonal_(0)

        self.pheromone_matrix = torch.zeros((num_valid_operations, num_valid_operations), device=device,
                                       dtype=torch.float16)
        self.pheromone_matrix[adjacency_matrix == 1] = pheromone



        machine = np.array([list(row)[1:] for row in m], dtype=np.int64)
        machine_tensor = torch.tensor(machine, device=device, dtype=torch.int64)
        num_machines = (torch.max(machine_tensor).item() + 1)

        machine_matrix = torch.zeros((num_valid_operations, num_machines), device=device)

        tool_for_operation = job[:, :, 3].flatten()
        #print(tool_for_operation)
        valid_tools = tool_for_operation != -1  # Remove padding
        tool_for_operation = tool_for_operation[valid_tools]

        for i, tool_id in enumerate(tool_for_operation):
            op_id = i + 1
            available_machines = machine_tensor[tool_id, :]
            mask = available_machines != -1
            machines = available_machines[mask].long()
            machine_matrix[op_id, machines] = 1
        #torch.set_printoptions(threshold=10_000)
        #for row in machine_matrix:
            #print(row.cpu().numpy())
        #print(len(adjacency_matrix))
        return m, job, adjacency_matrix, machine_matrix, mac_availability, mac_attime, current_time

    def update_pheromone(self, p_matrix, edges, contribution, rho, min_p_level):
        p_matrix *= (1-rho)
        start_nodes = edges[:, 0]
        end_nodes = edges[:, 1]
        p_matrix[start_nodes, end_nodes] += contribution
        torch.clamp(p_matrix, min=min_p_level, out=p_matrix)


