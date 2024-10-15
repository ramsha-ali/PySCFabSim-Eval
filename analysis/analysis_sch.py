import matplotlib.pyplot as plt
import pandas as pd


def read_data_from_file(filename):
    df = pd.read_csv(filename, sep="\t", engine='python')
    if len(df.columns) == 1:
        df = df[df.columns[0]].str.split(expand=True)
        df.columns = ['lot', 'product', 'step', 'tool', 'machine', 'start_time', 'end_time']
        df['Start'] = pd.to_numeric(df['Start'])
        df['End'] = pd.to_numeric(df['End'])
    return df


def create_gantt_chart(df, filename='gantt_chart_sch.png'):
    #print(df)
    df['product'] = df['product'].fillna('0')
    df['step'] = df['step'].fillna('0')



    machine_to_y = {machine: idx for idx, machine in enumerate(sorted(df['machine'].unique()))}
    fig, ax = plt.subplots(figsize=(14, 10))

    unique_combinations = df['lot'].astype(str) + '_' + df['product'].astype(str)
    colors = {combo: f"C{i % 10}" for i, combo in enumerate(unique_combinations.unique())}
    df['Color'] = df.apply(lambda x: colors[f"{x['lot']}_{x['product']}"], axis=1)

    for _, row in df.iterrows():
        y_pos = machine_to_y[row['machine']]
        ax.broken_barh([(row['start_time'], row['end_time'] - row['start_time'])], (y_pos - 0.4, 0.8),
                       facecolors=row['Color'], edgecolor='black')
        # Add text label inside each bar
        mid_point = row['start_time'] + (row['end_time'] - row['start_time']) / 2
        #label_text = f"({row['lot']},{row['product']},{row['step']}) \n {row['start_time']}-{row['end_time']}"
        #ax.text(mid_point, y_pos, label_text, ha='center', va='center', color='black', fontsize=12, fontweight='bold')

        # Set y-ticks to machine IDs
    ax.set_yticks([machine_to_y[machine] for machine in sorted(df['machine'].unique())])
    ax.set_yticklabels(sorted(df['machine'].unique()))
    ax.set_xlabel("Time (units)")
    ax.set_ylabel("Machine ID")
    ax.set_title("Gantt Chart of Operations")
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)  # Save as PNG with high resolution
    plt.close(fig)




filename = "schedule_output.txt"
df = read_data_from_file(filename)
create_gantt_chart(df)
