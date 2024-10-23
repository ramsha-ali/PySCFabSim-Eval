import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def resource_util(file_path, tool_file):
    df_util = pd.read_csv(file_path, delim_whitespace=True, header=1,
                          usecols=['Machine', 'Cnt', 'avail', 'util', 'br'])
    df_util = df_util[df_util['util'] > 0]  # Filter out zero utilization
    df_tools = pd.read_csv(tool_file, sep='\t', usecols=['STNFAM', 'STNGRP'])
    #print(df_util)
    #print(df_tools)
    df_merged = pd.merge(df_util, df_tools, left_on='Machine', right_on='STNFAM', how='left')
    df_grouped = df_merged.groupby('STNGRP')[
        'util'].mean().reset_index()

    plt.figure(figsize=(12, 8))
    bars = plt.barh(df_grouped['STNGRP'], df_grouped['util'], color='blue')
    for bar in bars:
        plt.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f'{bar.get_width():.2f}%',
                 va='center')

    plt.xlabel('Average Utilization (%)')
    plt.ylabel('Station Group')
    plt.title('Average Machine Utilization Over 1 Hour by Station Group')
    plt.tight_layout()
    plt.show()
#resource_util('greedy/greedy_seed0_3600days_SMT2020_HVLM_fifo.txt', 'datasets/SMT2020_HVLM/tool.txt.1l')

def read_and_visualize_operations_line_graph(files, algos, output_filename, period):
    period = int(period / 3600)
    operations_data = []
    for file, algo in zip(files, algos):
        data = pd.read_csv(file, delimiter="\t", skiprows=1)
        parsed_rows = []
        for index, row in data.iterrows():
            parts = row[0].split()
            product_number = parts[1].split('_')[1]
            parsed_rows.append({
                'Lot': parts[0],
                'Product': int(product_number),
                'Step': parts[3],
                'tool': parts[4],
                'Machine_id': parts[6],
                'Start': parts[-2],
                'End': parts[-1]
            })
        df = pd.DataFrame(parsed_rows)
        operations_data.append({
            'Algorithm': algo,
            'Total Operations': len(df)
        })
    operations_df = pd.DataFrame(operations_data)

    plt.figure(figsize=(10, 6))
    sns.lineplot(x='Algorithm', y='Total Operations', data=operations_df, marker='o')  # Using markers for points
    plt.title(f'Operations dispatched in {period} hour')
    plt.xlabel('Dispatcher')
    plt.ylabel('Total Operations')
    plt.grid(True)

    plt.savefig(output_filename)
    #plt.show()
    # compare
    baseline = operations_df.loc[operations_df['Algorithm'] == 'FIFO', 'Total Operations'].values[0]
    operations_df['% Difference from FIFO'] = ((operations_df['Total Operations'] - baseline) / baseline) * 100


def read_and_visualize_wip(files, algos, output_filename, period):
    period = int(period/3600)
    all_data = []
    for file, algo in zip(files, algos):
        data = pd.read_csv(file, delimiter="\t", skiprows=1)
        parsed_rows = []
        for index, row in data.iterrows():
            parts = row[0].split()
            product_number = parts[1].split('_')[1]
            parsed_rows.append({
                'Lot': parts[0],
                'Product': int(product_number),
                'Step': parts[3],
                'tool': parts[4],
                'Machine_id': parts[6],
                'Start': parts[-2],
                'End': parts[-1]
            })
        df = pd.DataFrame(parsed_rows)
        distinct_steps = df.groupby(['Lot', 'Product'])['Step'].nunique()
        #print(distinct_steps)

        lot_product_steps = distinct_steps.to_dict()
        counts = list(lot_product_steps.values())

        for count in counts:
            all_data.append({'Algorithm': algo, 'Distinct Step Counts': count})

    algorithm_data = pd.DataFrame(all_data)
    #print(algorithm_data)

    # Plotting
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Algorithm', y='Distinct Step Counts', data=algorithm_data, width=0.3)
    plt.title(f'WIP Flow in {period} hour')
    plt.xlabel('Dispatcher')
    plt.ylabel('WIP Range')
    plt.grid(True)
    #plt.show()
    plt.savefig(output_filename)

period = 3600

files = [
    f'dispatching_output/dispatching_fifo_{period}s.txt',
    f'dispatching_output/dispatching_cr_{period}s.txt',
    f'dispatching_output/dispatching_random_{period}s.txt',
    f'dispatching_output/dispatching_gsaco_{period}s.txt'
]
algos = ['FIFO', 'CR', 'Random', 'GSACO']

output_filename_wip = f'plots/period_{period}s.png'
output_filename_op = f'plots/total_operations_{period}s.png'

read_and_visualize_wip(files, algos, output_filename_wip, period)
read_and_visualize_operations_line_graph(files, algos, output_filename_op, period)