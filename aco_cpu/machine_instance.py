import os

import pandas as pd
import numpy as np
from pathlib import Path

current_time = 0
script_dir = Path(__file__).resolve().parent.parent
folder = "simulation_state"
path = script_dir / folder
directory = path
def get_machine_instance(directory):
    breakdown_log_file = 'breakdown_log.txt'
    breakdown_stats_file = 'breakdown_stats.txt'
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename == breakdown_stats_file:
            breakdown_stats(file_path)
        if filename == breakdown_log_file:
            process_breakdown_log(file_path)
    pass

def breakdown_stats(file_path):
    global current_time
    with open(file_path, 'r') as file:
        first_line = file.readline().strip()
        current_time = float(first_line.split()[1])
        df = pd.read_csv(file_path, sep=' ', skiprows=1, usecols=['Machine', 'Cnt', 'avail', 'br'])
        machine_availability = {}
        for index, row in df.iterrows():
            available_machines = round(row['Cnt'] * (row['avail'] / 100.0))
            if row['Cnt'] == 1:
                available_machines = int(available_machines)
                machine_availability[row['Machine']] = available_machines
            if available_machines == row['Cnt']:
                available_machines = int(available_machines-1)
                machine_availability[row['Machine']] = available_machines
        print(machine_availability)



    pass

def process_breakdown_log(file_path):
    df = pd.read_csv(file_path, sep=' ', usecols=['Toolgroup', 'Machineid', 'at', 'duration'])
    df['Toolgroup'] = df['Toolgroup'].str.lower()
    df['available_at'] = df['at'] + df['duration']
    df['not_available'] = df['available_at'] > current_time
    unavailable_machines = df[df['not_available']]
    machine_details = [(row['Toolgroup'], row['Machineid']) for index, row in unavailable_machines.iterrows()]
    machine_array = np.array(machine_details, dtype=[('Toolgroup', 'U20'), ('Machineid', 'i4')])

    grouped = {}
    for tool_group, machine_id in machine_array:
        if tool_group not in grouped:
            grouped[tool_group] = []
        grouped[tool_group].append(machine_id)

    formatted_output = []
    for tool_group, machine_ids in grouped.items():
        entry = (tool_group, *machine_ids)
        formatted_output.append(entry)

    unavail_macid = np.array(formatted_output, dtype=object)

    pass






get_machine_instance(directory)
print("done")