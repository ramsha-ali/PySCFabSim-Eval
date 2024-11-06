import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

file_path = '../schedule_output_example/schedule_output_SMT2020_example_operations_900s.txt'
#file_path = '../schedule_output_example/schedule_output_SMT2020_example_makespan.txt'


df = pd.read_csv(file_path, delimiter="\t")
df['start_time'] /= 60
df['end_time'] /= 60
df['lot'] += 1
df['machine'] += 1
df = df.sort_values(by='machine')
unique_combinations = df[['lot', 'product']].drop_duplicates()

lot_colors = {
    1: 'red', 2: 'blue', 3: 'green', 4: 'yellow', 5: 'purple',
    6: 'orange', 7: 'pink', 8: 'brown', 9: 'grey', 10: 'cyan'
}
# Map each lot-product combination to a color
color_labels = {tuple(row): lot_colors[row[0]] for row in unique_combinations.to_numpy()}

#color_map = plt.cm.get_cmap('tab20', len(unique_combinations))
#color_labels = {tuple(row): color_map(i) for i, row in enumerate(unique_combinations.to_numpy())}
bar_height = 0.03
machine_positions = {machine: i * (bar_height + 0.08) for i, machine in enumerate(sorted(df['machine'].unique()))}

legend_handles = {}
for index, row in df.iterrows():
    lot_prod_tuple = (row['lot'], row['product'])  # Create a tuple for sorting
    color = color_labels[lot_prod_tuple]
    label = f"Lot {row['lot']}, Product {row['product']}"
    if label not in legend_handles:
        legend_handles[lot_prod_tuple] = mpatches.Patch(color=color, label=label)


sorted_legend_handles = sorted(legend_handles.items(), key=lambda x: (x[0][0], x[0][1]))
sorted_legend_patches = [item[1] for item in sorted_legend_handles]  # Extract sorted patches


fig, ax = plt.subplots(figsize=(12, 4))

for _, row in df.iterrows():
    color = color_labels[(row['lot'], row['product'])]
    y_position = machine_positions[row['machine']]
    ax.broken_barh([(row['start_time'], row['end_time'] - row['start_time'])],
                   (y_position, bar_height),
                   facecolors=color)


ax.spines['left'].set_position(('data', 0))
ax.set_xticks(range(0, 16))  # include every integer from 0 to 15
ax.set_xlim(0, 15)

ax.set_yticks([pos for pos in machine_positions.values()])
ax.set_yticklabels([f"{row['tool']}, M{row['machine']}" for index, row in df.drop_duplicates('machine').iterrows()])
ax.set_xlabel("Time (minutes)")
ax.set_ylabel("Tool Group, Machine No")
ax.set_title("Schedule - 15 minutes")
#ax.set_title("Schedule - Makespan")

ax.legend(handles=sorted_legend_patches,
          title="Job (Lot, Product)", bbox_to_anchor=(1, 1), loc='upper left')

plt.tight_layout()
plt.savefig('../example_plots/schedule_example_operations.png', dpi=300)
#plt.savefig('../example_plots/schedule_example_makespan.png', dpi=300)
plt.show()
