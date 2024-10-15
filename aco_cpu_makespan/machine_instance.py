import os

import pandas as pd
import numpy as np
import torch


class Machine_Instance:

    current_time = 0
    tools_data = {}
    machine_availability = {}
    unavail_macid = []
    machines = None
    availability_matrix = None
    availability_time_matrix = None
    machine_attime = None

    def get_machine_instance(self, directory):
        breakdown_log_file = 'breakdown_log.txt'
        breakdown_stats_file = 'breakdown_stats.txt'
        tool_file = 'tool.txt.1l'
        #time_instance = 'at_time.txt'

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            #if filename == time_instance:
                #self.get_time(file_path)
            if filename == tool_file:
                self.process_tool_file(file_path)
                self.tool_mapping()
            #if filename == breakdown_log_file:
                #self.process_breakdown_log(file_path)
            #if filename == breakdown_stats_file:
                #self.breakdown_stats(file_path)
        #self.avail()

    def get_time(self, file_path):
        with open(file_path, 'r') as file:
            first_line = file.readline().strip()
            self.current_time = float(first_line.split()[1])

    def process_breakdown_log(self, file_path):
        df = pd.read_csv(file_path, sep=' ', usecols=['Toolgroup', 'Machineid', 'at', 'duration'])
        df['Toolgroup'] = df['Toolgroup'].str.lower()
        df['available_at'] = df['at'] + df['duration']
        df['not_available'] = df['available_at'] > int(self.current_time)

        unavailable_machines = df[df['not_available']]
        machine_details = [(row['Toolgroup'], row['Machineid']) for index, row in unavailable_machines.iterrows()]
        machine_array = np.array(machine_details, dtype=[('Toolgroup', 'U20'), ('Machineid', 'i4')])

        unavail_macid_dict = {}
        for tool_group, machine_id in machine_array:
            if tool_group not in unavail_macid_dict:
                unavail_macid_dict[tool_group] = []
            unavail_macid_dict[tool_group].append(machine_id)
        unavail_macid = []
        for tool_group, machine_ids in unavail_macid_dict.items():
            entry = (tool_group, *machine_ids)
            unavail_macid.append(entry)
        self.unavail_macid = np.array(unavail_macid, dtype=object)

        machine_attime = [(row['Toolgroup'], row['Machineid'], row['available_at']) for index, row in
                          unavailable_machines.iterrows()]
        self.machine_attime = sorted(machine_attime, key=lambda x: x[1])


        pass


    def process_tool_file(self, file_path):
        df = pd.read_csv(file_path, sep='\t')
        df['STNQTY'] = df['STNQTY'].fillna('0').astype(int)
        df['STNFAM'] = df['STNFAM'].str.lower()
        tools_data = df.groupby('STNFAM')['STNQTY'].first().to_dict()
        self.tools_data = {tool: int(qty * 1) for tool, qty in tools_data.items()}
        #print(self.tools_data)
        pass

    def tool_mapping(self):
        if self.machines is None:
            max_machines = max(self.tools_data.values())
            dtype = [('tool_group_name', 'U20')] + [(f'machine_{i}', 'i4') for i in range(1, max_machines + 1)]
            self.machines = np.zeros(len(self.tools_data), dtype=dtype)
            id = 0
            for idx, (tool_name, num_machines) in enumerate(self.tools_data.items()):
                row_data = tuple([tool_name] + list(range(id, id + num_machines)) + [-1] * (max_machines - num_machines))
                id += num_machines
                self.machines[idx] = row_data
        pass


    """
    def breakdown_stats(self, file_path):
        with open(file_path, 'r') as file:
            #first_line = file.readline().strip()
            #self.current_time = float(first_line.split()[1])
            df = pd.read_csv(file_path, sep=' ', skiprows=1, usecols=['Machine', 'Cnt', 'avail', 'br'])
            for index, row in df.iterrows():
                available_machines = int(row['Cnt'] * (row['avail'] / 100.0))
                if row['Cnt'] == 1:
                    self.machine_availability[row['Machine'].lower()] = int(row['Cnt'])
                elif available_machines == row['Cnt']:
                    available_machines = int(available_machines)
                    self.machine_availability[row['Machine'].lower()] = available_machines
                else:
                    self.machine_availability[row['Machine'].lower()] = available_machines

        #######
        unavailable_count = {}
        for tool_group, *machines in self.unavail_macid:
            if tool_group not in unavailable_count:
                unavailable_count[tool_group] = len(machines)
            else:
                unavailable_count[tool_group] += len(machines)

        for tool_group, count in unavailable_count.items():
            if tool_group in self.machine_availability:
                self.machine_availability[tool_group] -= count
        #########

        #print(self.unavail_macid)
        #print(self.machine_availability)
        pass
        """




    def avail(self, device="cpu"):
        machine = np.array([list(row)[1:] for row in self.machines], dtype=np.int64)
        machine_tensor = torch.tensor(machine, device=device, dtype=torch.int64)

        num_machines = (torch.max(machine_tensor[machine_tensor != -1]).item() + 1)
        num_tools = len(machine)
        self.availability_matrix = torch.zeros((num_tools, num_machines), device=device)
        time_dict = {id: time for _, id, time in self.machine_attime}
        self.availability_time_matrix = torch.zeros((num_tools, num_machines), device=device)
        unavailable_ids = set()
        for _, *ids in self.unavail_macid:
            unavailable_ids.update(ids)
        unavailable_ids = sorted(unavailable_ids)
        for tool_index, tool_machines in enumerate(machine_tensor):
            for machine_index, machine_id in enumerate(tool_machines):
                if machine_id != -1:
                    if machine_id not in unavailable_ids:
                        self.availability_matrix[tool_index, machine_id] = 1
                    int_id = machine_id.item()
                    if int_id in time_dict:
                        time_value = time_dict[int_id]
                        self.availability_time_matrix[tool_index, machine_id] = time_value

        #print(self.availability_time_matrix)
        pass







"""
mi = Machine_Instance()
script_dir = Path(__file__).resolve().parent.parent
folder = "simulation_state"
path = script_dir / folder
directory = path
mi.get_machine_instance(directory)
print("done")
#torch.set_printoptions(threshold=np.inf, linewidth=200)
"""

# use machine_availability
#     availability_matrix
#     availability_time_matrix
