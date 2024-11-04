import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def resource_utilization(schedule_file, tool_file):
    time = 3600
    df_schedule = pd.read_csv(schedule_file, delimiter='\t', usecols=['tool', 'start_time',	'end_time'])
    df_schedule['utilization_period'] = df_schedule['end_time'] - df_schedule['start_time']
    df_utilization = df_schedule.groupby('tool')['utilization_period'].sum().reset_index()
    df_utilization['utilization_percentage'] = (df_utilization['utilization_period'] / time) * 100
    df_tools = pd.read_csv(tool_file, sep='\t', usecols=['STNFAM', 'STNGRP'])
    df_tools['STNFAM'] = df_tools['STNFAM'].str.lower()

    df_merged = pd.merge(df_utilization, df_tools, left_on='tool', right_on='STNFAM', how='left')
    df_grouped = df_merged.groupby('STNGRP')[
        'utilization_percentage'].mean().reset_index()
    plt.figure(figsize=(12, 8))
    bars = plt.barh(df_grouped['STNGRP'], df_grouped['utilization_percentage'], color='blue')

    for bar in bars:
        plt.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f'{bar.get_width():.2f}%', va='center')  # Formatting as a percentage

    plt.xlabel('Utilization Percentage (%)')
    plt.ylabel('Station Group')
    plt.title('Utilization Percentage by Station Group for a 1-Hour Period')
    plt.tight_layout()
    plt.show()
#resource_utilization('schedule_output_HVLM/schedule_output_3600s.txt', '../datasets/SMT2020_HVLM/tool.txt.1l')

def read_schedule_and_visualize(schedule_file):
    df_schedule_lots = pd.read_csv(schedule_file, delimiter='\t', usecols=['lot', 'product', 'step', 'start_time'])
    #print(df_schedule_lots)
    df_schedule_lots_sorted = df_schedule_lots.sort_values(by='start_time')
    distinct_steps = df_schedule_lots_sorted.groupby(['lot', 'product'])['step'].nunique()
    lot_product_steps = distinct_steps.to_dict()
    counts = list(lot_product_steps.values())
    min_count = np.min(counts)
    max_count = np.max(counts)
    median_count = np.median(counts)

    algorithm_data = pd.DataFrame({
        'Algorithm': ['GSACO'] * len(counts),
        'Distinct Step Counts': counts
    })

    plt.figure(figsize=(8, 6))
    sns.boxplot(x='Algorithm', y='Distinct Step Counts', data=algorithm_data, width=0.3)
    plt.title('WIP flow across dispatching')
    plt.xlabel('Algorithm')
    plt.ylabel('WIP Range')
    plt.grid(True)
    plt.show()

read_schedule_and_visualize('schedule_output_HVLM_HVLM/schedule_output_3600s.txt')