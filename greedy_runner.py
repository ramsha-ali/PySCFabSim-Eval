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
for seed in [0, 1]:
    for day in [3600]:
        for dataset, dispatcher in [('SMT2020_HVLM', 'fifo')]:
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
