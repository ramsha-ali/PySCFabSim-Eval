import matplotlib.pyplot as plt
import glob
import pandas as pd
import seaborn as sns
from eval_sch_results import algorithm_data_sch

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
            algo_name = None
            if algo == 'gsaco':
                algo_name = "GSACO-O"
            elif algo in ['fifo', 'cr', 'random']:
                algo_name = algo.upper()

            dispatched_lots['Algorithm'] = algo_name
            df_wip_set = set(df_wip[['Lot', 'Product']].apply(tuple, axis=1))
            existing_set = set(dispatched_lots[['Lot', 'Product']].apply(tuple, axis=1))
            missing_pairs = df_wip_set - existing_set
            missing_data = [{'Lot': lot, 'Product': prod, 'Count': 0, 'Algorithm': algo_name} for lot, prod in missing_pairs]
            missing_lots = pd.DataFrame(missing_data)
            all_lots = pd.concat([dispatched_lots, missing_lots], ignore_index=True)
            #print(all_lots)

            algo_seed_data.append(all_lots)
        concatenated_df = pd.concat(algo_seed_data)
        average_counts = concatenated_df.groupby(['Lot', 'Product', 'Algorithm'])['Count'].mean().reset_index()
        average_counts['Count'] = average_counts['Count'].round().astype(int)  # Round and convert to integer
        all_data.extend(average_counts.to_dict('records'))
        #print(all_data)

    algorithm_data = pd.DataFrame(all_data)
    #print(algorithm_data)
    #print(algorithm_data_sch)
    algorithm_data_new = pd.concat([algorithm_data, algorithm_data_sch], ignore_index=True)

    # Plotting
    max_count = algorithm_data_new['Count'].max() + 1
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Algorithm', y='Count', data=algorithm_data_new, width=0.3)
    plt.title(f'WIP Flow in {hour} hours')
    plt.xlabel('Algorithm')
    plt.ylabel('WIP Range')
    plt.grid(True)
    plt.ylim(0, max_count)  # Set the y-axis to start at 0 and end at max_count
    plt.yticks(range(0, max_count, 1))
    #plt.xticks(rotation=45)
    plt.savefig(output_filename, dpi=300)

dataset = 'SMT2020_HVLM'
period = 21600
file_pattern = f'dispatching_output_{dataset}''/dispatching_seed*_{algo}_{period}s.txt'
#algos = ['FIFO (Dispatcher)', 'CR (Dispatcher)', 'RANDOM (Dispatcher)', 'GSACO-O (Dispatcher)']
algos = ['fifo', 'cr', 'random', 'gsaco']
wip = f'simulation_state/lot_instance_{dataset}.txt'
output_filename_wip = f'plots_{dataset}/new_period_{period}s.png'


read_and_visualize_wip(file_pattern, algos, output_filename_wip, period, wip)

