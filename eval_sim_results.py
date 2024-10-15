import matplotlib.pyplot as plt
import pandas as pd


def read_and_visualize(file_path, tool_file):
    df_util = pd.read_csv(file_path, delim_whitespace=True, header=1,
                          usecols=['Machine', 'Cnt', 'avail', 'util', 'br'])
    df_util = df_util[df_util['util'] > 0]  # Filter out zero utilization

    # Read tool file
    df_tools = pd.read_csv(tool_file, sep='\t', usecols=['STNFAM', 'STNGRP'])
    print(df_util)
    print(df_tools)
    # Merge data on machine name
    df_merged = pd.merge(df_util, df_tools, left_on='Machine', right_on='STNFAM', how='left')

    # Group data by station group and sum or average the utilizations
    df_grouped = df_merged.groupby('STNGRP')[
        'util'].mean().reset_index()  # Use mean, sum, or another method as fits your need

    # Creating the horizontal bar chart
    plt.figure(figsize=(12, 8))  # Adjusted figure size for clarity
    bars = plt.barh(df_grouped['STNGRP'], df_grouped['util'], color='blue')

    for bar in bars:
        plt.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f'{bar.get_width():.2f}%',  # Format the number to two decimal places
                 va='center')  # Vertical alignment

    plt.xlabel('Average Utilization (%)')
    plt.ylabel('Station Group')
    plt.title('Average Machine Utilization Over 1 Hour by Station Group')
    plt.tight_layout()
    plt.show()

# Replace 'path_to_your_file.txt' with the actual path of your file
read_and_visualize('greedy/greedy_seed0_3600days_SMT2020_HVLM_fifo.txt', 'datasets/SMT2020_HVLM/tool.txt.1l')
