from simulation.greedy import run_greedy
import sys
import argparse

sys.path.insert(0, '.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='SMT2020_HVLM')
    parser.add_argument('--days', type=int, default=1)
    parser.add_argument('--dispatcher', type=str, default='fifo')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--wandb', action='store_true', default=False)
    parser.add_argument('--chart', action='store_true', default=False)
    parser.add_argument('--alg', type=str, default='l4m', choices=['l4m', 'm4l'])
    args = parser.parse_args()

    profile = False
    if profile:
        from pyinstrument import Profiler
        p = Profiler()
        p.start()

    run_greedy(args.dataset, args.days, args.dispatcher, args.seed, args.wandb, args.chart, args.alg)
    print()
    print()

    if profile:
        p.stop()
        p.open_in_browser()

if __name__ == '__main__':
    main()
