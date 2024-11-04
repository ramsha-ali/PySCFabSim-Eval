import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

#file_path = '../schedule_output_HVLM/schedule_output_SMT2020_example_operations_900s.txt'
file_path = '../schedule_output_example/schedule_output_SMT2020_example_makespan.txt'


df = pd.read_csv(file_path, delimiter="\t")
df['start_time'] /= 60
df['end_time'] /= 60

df = df.sort_values(by='machine')
unique_combinations = df[['lot', 'product']].drop_duplicates()
color_map = plt.cm.get_cmap('tab20', len(unique_combinations))
color_labels = {tuple(row): color_map(i) for i, row in enumerate(unique_combinations.to_numpy())}
bar_height = 0.03
machine_positions = {machine: i * (bar_height + 0.08) for i, machine in enumerate(sorted(df['machine'].unique()))}

fig, ax = plt.subplots(figsize=(12, 4))
legend_handles = []
for _, row in df.iterrows():
    color = color_labels[(row['lot'], row['product'])]
    y_position = machine_positions[row['machine']]
    ax.broken_barh([(row['start_time'], row['end_time'] - row['start_time'])],
                   (y_position, bar_height),
                   facecolors=color)
    patch = mpatches.Patch(color=color, label=f"Lot {row['lot']}, Product {row['product']}")
    legend_handles.append(patch)

ax.spines['left'].set_position(('data', 0))
ax.set_xticks(range(0, 36))  # include every integer from 0 to 15
ax.set_xlim(0, 35)

ax.set_yticks([pos for pos in machine_positions.values()])
ax.set_yticklabels([f"{row['tool']}, M{row['machine']}" for index, row in df.drop_duplicates('machine').iterrows()])
ax.set_xlabel("Time (minutes)")
ax.set_ylabel("Tool Group, Machine No")
ax.set_title("Schedule - 15 minutes")
ax.set_title("Schedule - Makespan")

unique_legend_handles = {}
for handle in legend_handles:
    label = handle.get_label()
    if label not in unique_legend_handles:
        unique_legend_handles[label] = handle

ax.legend(unique_legend_handles.values(), unique_legend_handles.keys(),
          title="Job (Lot, Product)", bbox_to_anchor=(1, 1), loc='upper left')

plt.tight_layout()
#plt.savefig('../example_plots/schedule_example_operations.png', dpi=300)
plt.savefig('../example_plots/schedule_example_makespan.png', dpi=300)
plt.show()
