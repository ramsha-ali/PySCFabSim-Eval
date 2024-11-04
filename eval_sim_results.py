import matplotlib.pyplot as plt
import glob
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

def read_and_visualize_operations_line_graph(file_pattern, algos, output_filename, period):
    last_step = {'part_1': 520, 'part_2': 528, 'part_3': 582, 'part_4': 342, 'part_5': 241, 'part_6':292, 'part_7':352, 'part_8':374, 'part_9':383, 'part_10':389}
    hour = int(period / 3600)
    avg_operations = []
    for algo in algos:
        algo_files = glob.glob(file_pattern.format(algo=algo, period=period))
        total_operations_per_seed = []
        lots_done_per_seed = []
        for file in algo_files:
            data = pd.read_csv(file, delimiter="\t")
            parsed_rows = []
            for index, row in data.iterrows():
                parts = row[0].split()
                parsed_rows.append({
                    'Lot': parts[0],
                    'Product': parts[1],
                    'Step': int(parts[3])
                })
            df = pd.DataFrame(parsed_rows)
            last_steps_reached = df[df.apply(lambda row: row['Step'] == last_step[row['Product']], axis=1)]
            #print(last_steps_reached)
            #unique_lots_products_count = last_steps_reached.groupby('Product')['Lot'].nunique()
            lots_done = len(last_steps_reached)
            lots_done_per_seed.append(lots_done)
            total_operations = len(df)
            total_operations_per_seed.append(total_operations)
            #print(algo, lots_done)

        average_operations = sum(total_operations_per_seed) / len(total_operations_per_seed)
        average_lots = sum(lots_done_per_seed) / len(lots_done_per_seed)
        avg_operations.append({
            'Algorithm': algo,
            'Total Operations': int(average_operations),
            'Total_lots': int(average_lots),
        })
    operations_df = pd.DataFrame(avg_operations)
    plt.figure(figsize=(10, 6))
    ax = sns.lineplot(x='Algorithm', y='Total Operations', data=operations_df, marker='o')
    for index, row in operations_df.iterrows():
        ax.text(row['Algorithm'], row['Total Operations'], f'{row["Total Operations"]}',
                color='black', ha="right", va="bottom")
    plt.title(f'Operations dispatched in {hour} hour')
    plt.xlabel('Dispatcher')
    plt.ylabel('Total Operations')
    plt.grid(True)
    plt.savefig(output_filename, dpi=300)
    #plt.show()

    baseline = operations_df.loc[operations_df['Algorithm'] == 'fifo', 'Total Operations'].values[0]
    operations_df['% Difference from fifo'] = ((operations_df['Total Operations'] - baseline) / baseline) * 100
    print(operations_df)



def read_and_visualize_wip(file_pattern, algos, output_filename, period, wip):
    data_wip = pd.read_csv(wip, delimiter="\t")
    parsed_rows_wip = []
    for index, row in data_wip.iterrows():
        parts = row[0].split()
        product_number = parts[1].split('_')[1]
        parsed_rows_wip.append({
            'Lot': int(parts[0]),
            'Product': int(product_number),
            'Step': int(parts[3])
        })
    df_wip = pd.DataFrame(parsed_rows_wip)
    hour = int(period / 3600)
    all_data = []

    for algo in algos:
        algo_files = glob.glob(file_pattern.format(algo=algo, period=period))
        algo_seed_data = []
        for file in algo_files:
            data = pd.read_csv(file, delimiter="\t")
            parsed_rows = []
            for index, row in data.iterrows():
                parts = row[0].split()
                product_number = parts[1].split('_')[1]
                parsed_rows.append({
                    'Lot': int(parts[0]),
                    'Product': int(product_number),
                    'Step': int(parts[3])
                })
            df = pd.DataFrame(parsed_rows)
            dispatched_lots = df.groupby(['Lot', 'Product'])['Step'].nunique().reset_index()
            dispatched_lots.rename(columns={'Step': 'Count'}, inplace=True)
            dispatched_lots['Algorithm'] = algo
            df_wip_set = set(df_wip[['Lot', 'Product']].apply(tuple, axis=1))
            existing_set = set(dispatched_lots[['Lot', 'Product']].apply(tuple, axis=1))
            missing_pairs = df_wip_set - existing_set
            missing_data = [{'Lot': lot, 'Product': prod, 'Count': 0, 'Algorithm': algo} for lot, prod in missing_pairs]
            missing_lots = pd.DataFrame(missing_data)
            all_lots = pd.concat([dispatched_lots, missing_lots], ignore_index=True)
            algo_seed_data.append(all_lots)
        concatenated_df = pd.concat(algo_seed_data)
        average_counts = concatenated_df.groupby(['Lot', 'Product', 'Algorithm'])['Count'].mean().reset_index()
        average_counts['Count'] = average_counts['Count'].round().astype(int)  # Round and convert to integer
        all_data.extend(average_counts.to_dict('records'))
    algorithm_data = pd.DataFrame(all_data)
    # Plotting
    max_count = algorithm_data['Count'].max() + 1
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Algorithm', y='Count', data=algorithm_data, width=0.3)
    plt.title(f'WIP Flow in {hour} hour')
    plt.xlabel('Dispatcher')
    plt.ylabel('WIP Range')
    plt.grid(True)
    plt.ylim(0, max_count)  # Set the y-axis to start at 0 and end at max_count
    plt.yticks(range(0, max_count, 1))
    #plt.show()
    plt.savefig(output_filename, dpi=300)

period = 21600
file_pattern = 'dispatching_output_LVHM/dispatching_seed*_{algo}_{period}s.txt'
algos = ['fifo', 'cr', 'random', 'gsaco']
wip = 'simulation_state/lot_instance_LVHM.txt'
output_filename_wip = f'plots_LVHM/period_{period}s.png'
output_filename = f'plots_LVHM/total_operations_{period}s.png'

read_and_visualize_wip(file_pattern, algos, output_filename_wip, period, wip)
read_and_visualize_operations_line_graph(file_pattern, algos, output_filename, period)