import io
import os
import subprocess
import threading
import time


threads = []


if not os.path.exists('greedy'):
    os.mkdir('greedy')
if not os.path.exists('simulation_state'):
    os.mkdir('simulation_state')
for seed in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
    for day in [3600, 7200, 10800, 14400, 18000, 21600]:
        for dataset, dispatcher in [('SMT2020_LVHM', 'fifo'), ('SMT2020_LVHM', 'cr'), ('SMT2020_LVHM', 'random'), ('SMT2020_LVHM', 'gsaco')]:
            def s(day_, dataset_, dispatcher_):
                name_ = f'greedy/greedy_seed{seed}_{day}days_{dataset}_{dispatcher}.txt'
                with io.open(name_, 'w') as f:
                    print(name_)
                    subprocess.call(['pypy3', 'main.py', '--days', str(day_),
                                     '--dataset', dataset_, '--dispatcher', dispatcher_, '--seed', str(seed),
                                     '--alg', 'l4m'], stdout=f)
            t = threading.Thread(target=s, args=(day, dataset, dispatcher))
            t.start()
            time.sleep(2)
            threads.append(t)

for t in threads:
    t.join()

print('Done')
print()

##### this is the project
