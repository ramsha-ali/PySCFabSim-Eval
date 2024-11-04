import os
import pandas as pd
import numpy as np

seed = 42
np.random.seed(seed)

def read_data(d):
    products_data = {}
    wip_data = {}
    tools_data = {}

    if not products_data:
        for filename in os.listdir(d):

            if filename.startswith("route_") and filename.endswith(".txt"):
                with open(os.path.join(d, filename), 'r', encoding="utf-16") as file:
                    data = file.read()

                    lines = data.split('\n')
                    columns = lines[0].split('\t')
                    data = []
                    for line in lines[1:]:
                        if line:
                            data.append(line.split('\t'))
                df = pd.DataFrame(data, columns=columns)
                df = df[['ROUTE', 'STEP', 'STNFAM', 'PDIST', 'PTIME', 'PTIME2', 'PTUNITS', 'SETUP', 'STIME']]

                df['ROUTE_NUMBER'] = df['ROUTE'].str.extract('(\d+)').astype(int)
                df['STEP'] = df['STEP'].astype('int')
                df['PROCESSING_TIME'] = (np.random.uniform(df.PTIME2, df.PTIME) + 1).astype(int)
                df['SETUP'] = df['SETUP'].replace('', '0')
                df['STIME'] = df['STIME'].replace('', '0').astype('int')

                for route in df['ROUTE_NUMBER'].unique():

                    route_df = df[df['ROUTE_NUMBER'] == route]
                    route_list = []
                    for i, row in route_df.iterrows():
                        step = row['STEP']
                        tool_group = row['STNFAM'].lower()
                        pro_time = row['PROCESSING_TIME']
                        setup = row['SETUP'].lower()
                        setuptime = row['STIME']
                        route_list.append((route, step, tool_group, pro_time, setup, setuptime))

                    products_data[route] = route_list
                    #products_data[route].append(route_list)

                    """
                    products_data.append({
                        'name': route,
                        'route': route_list
                    })
                    """
            if not tools_data:
                if filename == 'tool.txt':
                    columns = ["STNFAM", "STN", "RULE", "FWLRANK", "WAKERESRANK", "BATCHCRITF", "BATCHPER", "LTIME",
                               "LTUNITS", "ULTIME", "ULTUNITS", "STNCAP", "STNQTY", "STNGRP", "STNFAMSTEP_ACTLIST",
                               "STNFAMLOC", "PRERULERWL", "SETUPGRP"]
                    data_dict = {col: [] for col in columns}

                    with open(os.path.join(d, filename), 'r', encoding="utf-16") as file:
                        lines = file.readlines()
                    last_seen_values = {col: '' for col in columns}

                    for line in lines[1:]:
                        values = line.split('\t')
                        for i, value in enumerate(values):
                            value = value.strip()
                            if value:
                                last_seen_values[columns[i]] = value
                            data_dict[columns[i]].append(last_seen_values[columns[i]])

                    df = pd.DataFrame(data_dict)
                    df = df[['STNFAM', 'STNQTY']]
                    df['STNFAM'] = df['STNFAM'].str.lower()
                    df['STNQTY'] = df['STNQTY'].astype('int')
                    tools_data = df.groupby('STNFAM')['STNQTY'].first().to_dict()
                    tools_data = {tool: int(qty * 1) for tool, qty in tools_data.items()}

            if not wip_data:
                if filename == 'WIP.txt':
                    columns = ["LOT", "PART", "PRIOR", "PIECES", "START", "CURSTEP", "DUE", "ORDER", "HOTLOT", "TRACE"]
                    data_dict = {col: [] for col in columns}
                    with open(os.path.join(d, filename), 'r', encoding="utf-16") as file:
                        lines = file.readlines()
                        last_seen_values = {col: '' for col in columns}

                        for line in lines[1:]:
                            values = line.split('\t')
                            for i, value in enumerate(values):
                                value = value.strip()
                                if value:
                                    last_seen_values[columns[i]] = value
                                data_dict[columns[i]].append(last_seen_values[columns[i]])
                        df = pd.DataFrame(data_dict)
                        df = df[["LOT", "PRIOR", "PIECES", "START", "CURSTEP", "DUE"]]
                        df[['Init', 'Lot', 'Product_name', 'Lot_number']] = df['LOT'].str.split('_', expand=True)
                        df = df.drop(['Init', 'Lot', 'LOT'], axis=1)
                        df['START'] = pd.to_datetime(df['START'], format='%m/%d/%y %H:%M:%S')
                        df['DUE'] = pd.to_datetime(df['DUE'], format='%m/%d/%y %H:%M:%S')
                        df['DUE_IN_DAYS'] = ((df['DUE'] - df['START']).dt.total_seconds() / (24 * 60 * 60)).round(2)

                        df['Lot_ID'] = df.groupby('Product_name').cumcount() + 1

                        wip_data = df[['Lot_ID', 'Product_name', 'CURSTEP']].astype(
                            {'Lot_ID': 'int', 'Product_name': 'int', 'CURSTEP': 'int'}).to_records(index=False).tolist()

        return products_data, wip_data, tools_data

def get_remaining_operations(r, w, n):
    remaining_operations = []
    #print("product_routes",product_routes)
    for item in w:
        lot, product, current_step = item
        remaining_steps = range(current_step, current_step + n)
        for step in remaining_steps:
            for route in r[product]:
                if route[1] == step:
                    tool = route[2]
                    pro_time = route[3]
                    remaining_operations.append((lot, product, step, tool, pro_time))
    return remaining_operations






