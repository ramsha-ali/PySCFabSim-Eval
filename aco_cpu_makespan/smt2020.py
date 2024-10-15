import os
import re
import pandas as pd
import numpy as np



class SMT2020:

    product_route = {}
    product_route_dynamic = {}
    wip_data = []
    tools_data = {}
    wip_data_batches = []

    machines = None
    jobs = None

    def read_files(self, instance, directory):
        route_pattern = re.compile(r"route_.*\.txt")
        route_file = "route.txt"
        tool_file = 'tool.txt.1l'
        wip_file = 'lot_instance.txt'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if route_pattern.match(filename):
                self.process_route_file(file_path)
            if filename == tool_file:
                self.process_tool_file(file_path)
            if filename == route_file:
                self.process_route_file_sim(file_path)
        for filename in os.listdir(instance):
            file_path_lots = os.path.join(instance, filename)
            if filename == wip_file:
                self.wip_instance(file_path_lots)
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

        #df['PROCESSING_TIME'] = (np.random.uniform(df['PTIME2'].fillna(0), df['PTIME'].fillna(0)) + 1).astype(int)
        #df['PROCESSING_TIME'] = df['PROCESSING_TIME'] * 60
        df['SETUP'] = df['SETUP'].fillna('0').str.lower()
        df['STIME'] = df['STIME'].fillna('0').astype(int)
        df['STNFAM'] = df['STNFAM'].str.lower()
        transformed = df.groupby('ROUTE_NUMBER').apply(
            lambda x: x[['ROUTE_NUMBER','STEP', 'STNFAM', 'PROCESSING_TIME_LOW', 'PROCESSING_TIME_HIGH']].to_records(index=False).tolist()
        )
        for route, routes in transformed.items():
            self.product_route_dynamic[route] = routes

        pass


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
        #print(self.product_route)
        pass

    def process_tool_file(self, file_path):
        df = pd.read_csv(file_path, sep='\t')
        df['STNQTY'] = df['STNQTY'].fillna('0').astype(int)
        df['STNFAM'] = df['STNFAM'].str.lower()
        tools_data = df.groupby('STNFAM')['STNQTY'].first().to_dict()
        self.tools_data = {tool: int(qty * 1) for tool, qty in tools_data.items()}

    """
    
    def process_wip_file(self, file_path):
        df = pd.read_csv(file_path, sep='\t',
                         usecols=['LOT', 'PART', 'PRIOR', 'PIECES', 'START', 'CURSTEP', 'DUE'])
        df[['Init', 'Lot', 'Product_name', 'Lot_number']] = df['LOT'].str.split('_', expand=True)
        df = df.drop(['Init', 'Lot', 'LOT'], axis=1)
        df['START'] = pd.to_datetime(df['START'], format='%m/%d/%y %H:%M:%S')
        df['DUE'] = pd.to_datetime(df['DUE'], format='%m/%d/%y %H:%M:%S')
        df['DUE_IN_DAYS'] = ((df['DUE'] - df['START']).dt.total_seconds() / (24 * 60 * 60)).round(2)

        df['Lot_ID'] = df.groupby('Product_name').cumcount() + 1

        self.wip_data = df[['Lot_ID', 'Product_name', 'CURSTEP']].astype({'Lot_ID': 'int', 'Product_name': 'int', 'CURSTEP': 'int'}).to_records(index=False).tolist()
        
        pass
    """

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

    def read_data(self, instance, directory):
        self.read_files(instance, directory)

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
                #remaining_steps = range(current_step, current_step + n)
                if n is None:
                    remaining_steps = steps_for_product  # All steps from current_step onward
                else:
                    remaining_steps = steps_for_product[:n]
                #step_id = 1
                info = []
                for steps in remaining_steps:
                    for route in self.product_route[product]:
                        #print(route)
                        product, step, tool, pro_time = route
                        if step == steps:
                            tool_indices = np.where(self.machines['tool_group_name'] == tool)[0]
                            if tool_indices.size > 0:
                                tool_number = tool_indices[0]
                                op_info = (lot, product, step, tool_number, pro_time)
                                info.append(op_info)
                            #step_id += 1
                job_info.append(info)
            max_operations = max(len(job) for job in job_info)
            padded_job_info = [job + [(-1, -1, -1, -1, -1)] * (max_operations - len(job)) for job in job_info]
            self.jobs = np.array(padded_job_info, dtype=int)
            #print(len(self.jobs))
            #np.set_printoptions(threshold=np.inf, linewidth=200)

        pass

    def get_remaining_operations_dynmaic(self, n):
        if not self.jobs:
            num_jobs = len(self.wip_data)
            attributes = 2 # tool, process time
            self.jobs = np.empty((num_jobs,n if n is not None else 0,attributes), dtype=int)
            job_info = []
            for item in self.wip_data:
                lot, product, current_step = item
                steps_for_product = [route[1] for route in self.product_route_dynamic[product] if route[1] >= current_step]
                #remaining_steps = range(current_step, current_step + n)
                if n is None:
                    remaining_steps = steps_for_product  # All steps from current_step onward
                else:
                    remaining_steps = steps_for_product[:n]
                #step_id = 1
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
                            #step_id += 1
                job_info.append(info)
            max_operations = max(len(job) for job in job_info)
            padded_job_info = [job + [(-1, -1, -1, -1, -1)] * (max_operations - len(job)) for job in job_info]
            self.jobs = np.array(padded_job_info, dtype=int)
            #print(len(self.jobs))
            #np.set_printoptions(threshold=np.inf, linewidth=200)
            #print(self.jobs)
        pass


    def transform_step(self, step_str):
        step_number = int(step_str.split()[-1])
        return step_number


    def smt_caller(self, i, d, n, state, seed):
        self.read_data(i, d)
        self.tool_mapping()
        if state == "deterministic":
            self.get_remaining_operations(n)
        if state == "dynamic":
            np.random.seed(seed)
            self.get_remaining_operations_dynmaic(n)
        pass

