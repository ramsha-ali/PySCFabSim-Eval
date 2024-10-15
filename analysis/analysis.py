import matplotlib.pyplot as plt
import pandas as pd


def read_data_from_file(filename):
    df = pd.read_csv(filename, sep="\t", engine='python')
    if len(df.columns) == 1:
        df = df[df.columns[0]].str.split(expand=True)
        df.columns = ['Lot', 'Product', 'Step', 'Step_id', 'Machine', 'Machine_id', 'Start', 'End']
        df['Start'] = pd.to_numeric(df['Start'])
        df['End'] = pd.to_numeric(df['End'])

    return df


def create_gantt_chart(df, filename='gantt_chart_dispatch.png'):
    df['Product'] = df['Product'].str.extract('(\d+)').fillna('0').astype(int)
    df['Step'] = df['Step'].str.extract('(\d+)').fillna('0').astype(int)
    #print(df)


    machine_to_y = {machine: idx for idx, machine in enumerate(sorted(df['Machine_id'].unique()))}
    fig, ax = plt.subplots(figsize=(14, 10))

    unique_combinations = df['Lot'].astype(str) + '_' + df['Product'].astype(str)
    colors = {combo: f"C{i % 10}" for i, combo in enumerate(unique_combinations.unique())}
    df['Color'] = df.apply(lambda x: colors[f"{x['Lot']}_{x['Product']}"], axis=1)

    for _, row in df.iterrows():
        y_pos = machine_to_y[row['Machine_id']]
        ax.broken_barh([(row['Start'], row['End'] - row['Start'])], (y_pos - 0.4, 0.8),
                       facecolors=row['Color'], edgecolor='black')
        # Add text label inside each bar
        mid_point = row['Start'] + (row['End'] - row['Start']) / 2
        #label_text = f"({row['Lot']},{row['Product']},{row['Step_id']}) \n {row['Start']}-{row['End']}"
        #ax.text(mid_point, y_pos, label_text, ha='center', va='center', color='black', fontsize=12, fontweight='bold')

        # Set y-ticks to machine IDs
    ax.set_yticks([machine_to_y[machine] for machine in sorted(df['Machine_id'].unique())])
    ax.set_yticklabels(sorted(df['Machine_id'].unique()))
    ax.set_xlabel("Time (units)")
    ax.set_ylabel("Machine ID")
    ax.set_title("Gantt Chart of Operations")
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)  # Save as PNG with high resolution
    plt.close(fig)




filename = "done_lots_by_dispatching.txt"
df = read_data_from_file(filename)
create_gantt_chart(df)
