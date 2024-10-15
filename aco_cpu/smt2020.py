import os
import re
import pandas as pd
import numpy as np
import torch


class SMT2020:
    current_time = 0
    product_route = {}
    product_route_dynamic = {}
    wip_data = []
    tools_data = {}
    wip_data_batches = []

    machines = None
    jobs = None

    unavail_macid = []

    machine_attime = None
    availability_matrix = None
    availability_time_matrix = None

    def read_files(self, instance, directory, breakdown):
        route_pattern = re.compile(r"route_.*\.txt")
        route_file = "route.txt"
        tool_file = 'tool.txt.1l'
        wip_file = 'lot_instance.txt'
        breakdown_log_file = 'breakdown_log.txt'
        time_instance = 'at_time.txt'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if route_pattern.match(filename):
                self.process_route_file(file_path)
            if filename == tool_file:
                self.process_tool_file(file_path)
            if filename == route_file:
                self.process_route_file_sim(file_path)

        for filename in os.listdir(instance):
            file_path = os.path.join(instance, filename)
            if filename == time_instance:
                self.get_time(file_path)
            if filename == wip_file:
                self.wip_instance(file_path)
            if breakdown == "yes":
                if filename == breakdown_log_file:
                    self.process_breakdown_log(file_path)
        pass

    def process_route_file(self, file_path):
        df = pd.read_csv(file_path, sep='\t',
                         usecols=['ROUTE', 'STEP', 'STNFAM', 'PDIST', 'PTIME', 'PTIME2', 'PTUNITS', 'SETUP', 'STIME'])
        df['ROUTE_NUMBER'] = df['ROUTE'].str.extract('(\d+)').astype(float).fillna(0).astype(int)
        df['STEP'] = df['STEP'].astype(float).fillna(0).astype(int)

        df['PTIME'] = df['PTIME'].fillna(0)
        df['PTIME2'] = df['PTIME2'].fillna(0)
        df['PROCESSING_TIME_LOW'] = (np.minimum(df['PTIME'], df['PTIME2'])*60)
        df['PROCESSING_TIME_HIGH'] = (np.maximum(df['PTIME'], df['PTIME2'])*60)

        transformed = df.groupby('ROUTE_NUMBER').apply(
            lambda x: x[['ROUTE_NUMBER','STEP', 'STNFAM', 'PROCESSING_TIME_LOW', 'PROCESSING_TIME_HIGH']].to_records(index=False).tolist()
        )
        for route, routes in transformed.items():
            self.product_route_dynamic[route] = routes
        pass

    # for deterministic processing time
    def process_route_file_sim(self, file_path):
        df = pd.read_csv(file_path, sep=' ',
                         usecols=['Product', 'Step', 'Tool', 'Processtime'])
        df['Product'] = df['Product'].str.extract('(\d+)').astype(float).fillna(0).astype(int)
        df['Step'] = df['Step'].astype(float).fillna(0).astype(int)
        df['Processtime'] = df['Processtime'].astype(int)
        df['Tool'] = df['Tool'].str.lower()
        transformed = df.groupby('Product').apply(
            lambda x: x[['Product','Step', 'Tool', 'Processtime']].to_records(index=False).tolist()
        )
        for route, routes in transformed.items():
            self.product_route[route] = routes
        pass

    def process_tool_file(self, file_path):
        df = pd.read_csv(file_path, sep='\t')
        df['STNQTY'] = df['STNQTY'].fillna('0').astype(int)
        df['STNFAM'] = df['STNFAM'].str.lower()
        tools_data = df.groupby('STNFAM')['STNQTY'].first().to_dict()
        self.tools_data = {tool: int(qty * 1) for tool, qty in tools_data.items()}

    def wip_instance(self, file_path):
        df = pd.read_csv(file_path, header=None, names=['Data'])
        df[['Lot', 'Product', 'CurrentStep']] = df['Data'].str.extract(r'(\d+)\s+(\w+)\s+Step\s+(\d+)')
        df.dropna(inplace=True)

        df['Lot'] = df['Lot'].astype(int)
        df['Product'] = df['Product'].str.extract(r'(\d+)').astype(int)
        df['CurrentStep'] = df['CurrentStep'].astype(int)
        wtuple = [(lot, prod, step) for lot, prod, step in zip(df['Lot'], df['Product'], df['CurrentStep'])]
        self.wip_data = wtuple
        pass


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

    def read_data(self, instance, directory, breakdown):
        self.read_files(instance, directory, breakdown)

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

    def get_remaining_operations(self, n):
        if not self.jobs:
            num_jobs = len(self.wip_data)
            attributes = 2 # tool, process time
            self.jobs = np.empty((num_jobs,n if n is not None else 0,attributes), dtype=int)
            job_info = []
            for item in self.wip_data:
                lot, product, current_step = item
                steps_for_product = [route[1] for route in self.product_route[product] if route[1] >= current_step]
                if n is None:
                    remaining_steps = steps_for_product
                else:
                    remaining_steps = steps_for_product[:n]
                info = []
                for steps in remaining_steps:
                    for route in self.product_route[product]:
                        product, step, tool, pro_time = route
                        if step == steps:
                            tool_indices = np.where(self.machines['tool_group_name'] == tool)[0]
                            if tool_indices.size > 0:
                                tool_number = tool_indices[0]
                                op_info = (lot, product, step, tool_number, pro_time)
                                info.append(op_info)
                job_info.append(info)
            max_operations = max(len(job) for job in job_info)
            padded_job_info = [job + [(-1, -1, -1, -1, -1)] * (max_operations - len(job)) for job in job_info]
            self.jobs = np.array(padded_job_info, dtype=int)
        pass

    # for stochastic processing times
    def get_remaining_operations_dynmaic(self, n):
        if not self.jobs:
            num_jobs = len(self.wip_data)
            attributes = 2 # tool, process time
            self.jobs = np.empty((num_jobs,n if n is not None else 0,attributes), dtype=int)
            job_info = []
            for item in self.wip_data:
                lot, product, current_step = item
                steps_for_product = [route[1] for route in self.product_route_dynamic[product] if route[1] >= current_step]
                if n is None:
                    remaining_steps = steps_for_product
                else:
                    remaining_steps = steps_for_product[:n]
                info = []
                for steps in remaining_steps:
                    for route in self.product_route_dynamic[product]:
                        product, step, tool, pro_time1, pro_time2 = route
                        if step == steps:
                            tool_indices = np.where(self.machines['tool_group_name'] == tool)[0]
                            if tool_indices.size > 0:
                                tool_number = tool_indices[0]
                                op_info = (lot, product, step, tool_number, np.random.uniform(pro_time1, pro_time2))
                                info.append(op_info)
                job_info.append(info)
            max_operations = max(len(job) for job in job_info)
            padded_job_info = [job + [(-1, -1, -1, -1, -1)] * (max_operations - len(job)) for job in job_info]
            self.jobs = np.array(padded_job_info, dtype=int)
        pass


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

        pass


    def smt_caller(self, i, d, n, state, breakdown, seed):
        self.read_data(i, d, breakdown)
        self.tool_mapping()
        if state == "deterministic":
            self.get_remaining_operations(n)
        if state == "dynamic":
            np.random.seed(seed)
            self.get_remaining_operations_dynmaic(n)
        if state ==  "deterministic" and breakdown == "yes":
            self.avail()
        if breakdown == 'no':
            self.current_time = 0
        pass

