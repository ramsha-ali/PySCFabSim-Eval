import matplotlib.pyplot as plt
import pandas as pd

data_LVHM = {
    'Algorithm': ['FIFO (Dispatcher)', 'CR (Dispatcher)', 'RANDOM (Dispatcher)', 'GSACO-O (Dispatcher)', 'GSACO-O (Scheduler)'],
    1: [1419, 1416, 1403, 1442, 1422],
    2: [2249, 2328, 2275, 2409, 2368],
    3: [3284, 3372, 3314, 3427, 3234],
    4: [4018, 4083, 4039, 4272, 4015],
    5: [4901, 5023, 4972, 5174, 4722],
    6: [5665, 5799, 5767, 6014, 5306]
}
data_HVLM = {
    'Algorithm': ['FIFO (Dispatcher)', 'CR (Dispatcher)', 'RANDOM (Dispatcher)', 'GSACO-O (Dispatcher)', 'GSACO-O (Scheduler)'],
    1 : [1821, 1798, 1810, 1831, 1848],
    2 : [2831, 2811, 2852, 2957, 2960],
    3 : [4020, 4021, 4065, 4162, 4093],
    4 : [4914, 4934, 4975, 5118, 4970],
    5 : [5960, 6003, 6026, 6263, 5975],
    6 : [6841, 6946, 6973, 7162, 6716],
}
df = pd.DataFrame(data_HVLM)
fig, ax = plt.subplots(figsize=(10, 6))
colors = ['blue', 'green', 'red', 'purple', 'brown', 'orange']
for i in range(1, 7):
    if i == 1:
        line = ax.plot(df['Algorithm'], df[i], label=f'{i} hour', marker='o', linestyle='-', color=colors[i-1])
    else:
        line = ax.plot(df['Algorithm'], df[i], label=f'{i} hours', marker='o', linestyle='-', color=colors[i - 1])
    for x, y in zip(range(len(df['Algorithm'])), df[i]):
        ax.annotate(f'{y}', (x, y), textcoords="offset points", xytext=(0,10), ha='center')

ax.set_title('Operations dispatched over 6 planning horizons')
ax.set_xlabel('Algorithm')
ax.set_ylabel('Total Operations')
ax.set_ylim(1700, 7600)
ax.set_yticks(range(1700, 7600, 1000))
ax.set_xlim(-0.2, len(df['Algorithm']) - 0.7)

#ax.set_xticks(range(len(df['Algorithm'])))
ax.set_xticklabels(df['Algorithm'], rotation=45)

ax.legend(title='Horizon', bbox_to_anchor=(1, 1), loc='upper left')

plt.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust the right margin to fit the legend
plt.grid(True)
#plt.show()
output_filename = f'plots_SMT2020_HVLM/operations_HVLM.png'
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
