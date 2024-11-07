import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def read_schedule_and_visualize(schedule_file, wip, period):
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
    all_data =[]

    algo= 'GSACO-O (Scheduler)'
    data = pd.read_csv(schedule_file, delimiter='\t', usecols=['lot', 'product', 'step'])

    parsed_rows = []
    for index, row in data.iterrows():
        parsed_rows.append({
            'Lot': int(row[0]),
            'Product': int(row[1]),
            'Step': int(row[2])
        })

    df = pd.DataFrame(parsed_rows)
    dispatched_lots = df.groupby(['Lot', 'Product'])['Step'].nunique().reset_index()
    dispatched_lots['Algorithm'] = algo
    dispatched_lots.rename(columns={'Step': 'Count'}, inplace=True)
    df_wip_set = set(df_wip[['Lot', 'Product']].apply(tuple, axis=1))
    existing_set = set(dispatched_lots[['Lot', 'Product']].apply(tuple, axis=1))
    missing_pairs = df_wip_set - existing_set
    missing_data = [{'Lot': lot, 'Product': prod, 'Count': 0, 'Algorithm': algo} for lot, prod in missing_pairs]
    missing_lots = pd.DataFrame(missing_data)
    all_lots = pd.concat([dispatched_lots, missing_lots], ignore_index=True)

    algorithm_data = pd.DataFrame(all_lots)

    new_order = ['Lot', 'Product', 'Algorithm', 'Count']
    algorithm_data = algorithm_data[new_order]
    max_count = algorithm_data['Count'].max() + 1
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Algorithm', y='Count', data=algorithm_data, width=0.3)
    plt.title(f'WIP Flow in {hour} hours')
    plt.xlabel('Dispatcher')
    plt.ylabel('WIP Range')
    plt.grid(True)
    plt.ylim(0, max_count)  # Set the y-axis to start at 0 and end at max_count
    plt.yticks(range(0, max_count, 1))
    plt.show()
    #plt.savefig(output_filename, dpi=300)
    return algorithm_data

dataset = 'SMT2020_HVLM'
period = 21600
wip = f'simulation_state/lot_instance_{dataset}.txt'
algorithm_data_sch = read_schedule_and_visualize(f'schedule_output_HVLM/schedule_output_{period}s.txt', wip, period)