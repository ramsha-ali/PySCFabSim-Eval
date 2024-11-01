import sys
from typing import Dict, List

from simulation.classes import Machine, FileRoute, Lot
from simulation.events import BreakdownEvent
from simulation.instance import Instance
from simulation.randomizer import Randomizer
from simulation.tools import get_interval, get_distribution, UniformDistribution, date_time_parse


class FileInstance(Instance):

    def __init__(self, files: Dict[str, List[Dict]], run_to, lot_for_machine, plugins):
        machines = []
        machine_id = 0
        r = Randomizer()
        family_locations = {}
        for d_m in files['tool.txt.1l']:
            for i in range(int(d_m['STNQTY'])):
                speed = 1
                m = Machine(idx=machine_id, d=d_m, speed=speed)
                family_locations[m.family] = m.loc
                machines.append(m)
                machine_id += 1

        pieces = max([a['PIECES'] for a in files['order.txt'] + files['WIP.txt']])
        routes = {}
        route_keys = [key for key in files.keys() if 'route' in key]
        for rk in route_keys:
            route = FileRoute(rk, pieces, files[rk])
            for s in route.steps:
                s.family_location = family_locations[s.family]
            routes[rk] = route

        parts = {p['PART']: p['ROUTEFILE'] for p in files['part.txt']}

        # for gsaco dispatch
        file_path = f'schedule_output/schedule_output_{run_to}s.txt'
        schedule = []
        with open(file_path, 'r') as f:
            next(f)
            for line in f:
                lot, product, step, tool, machine, start_time, end_time = line.strip().split('\t')
                schedule.append((int(lot), int(product), int(step), int(machine), float(start_time)))
        sorted(schedule, key=lambda x: x[4])
        scheduled_lots = [(lot, machine) for lot, product, step, machine, _ in schedule]
        gsaco_schedule = {}
        for i in scheduled_lots:
            l, m = i
            if m not in gsaco_schedule:
                gsaco_schedule[m] = []
            gsaco_schedule[m].append(l)
        min_steps = {}
        for lot, part, curstep, _, _ in schedule:
            key = (lot, part)
            if key not in min_steps or curstep < min_steps[key][0]:
                min_steps[key] = (curstep, f"Init_Lot_{part}_{lot}")

        ## ------------------------------------------------  ##

        lots = []
        idx = 0
        lot_pre = {}
        for wip in files['WIP.txt']:
            assert pieces == wip['PIECES']
            first_release = 0
            relative_deadline = (date_time_parse(wip['DUE']) - date_time_parse(wip['START'])).total_seconds()
            if wip['CURSTEP'] < len(routes[parts[wip['PART']]].steps) - 1:
                #idx = wip['LOT'].split('_')[-1]
                lot = Lot(idx, routes[parts[wip['PART']]], wip['PRIOR'], first_release, relative_deadline, wip)
                lots.append(lot)
                lot_pre[lot.name] = relative_deadline
                lot.release_at = lot.deadline_at - lot_pre[lot.name]
            idx += 1

        sys.stderr.write(
            f'lots: {len(lots)} '
            f'machines: {len(machines)}'
            f'\n')

        downcals = {}
        for dc in files['downcal.txt']:
            downcals[dc['DOWNCALNAME']] = (get_distribution(dc['MTTFDIST'], dc['MTTFUNITS'], dc['MTTF']),
                                           get_distribution(dc['MTTRDIST'], dc['MTTRUNITS'], dc['MTTR']))
        pmcals = {}
        for dc in files['pmcal.txt']:
            pmcals[dc['PMCALNAME']] = (get_distribution('constant', dc['MTBPMUNITS'], dc['MTBPM']),
                                       get_distribution(dc['MTTRDIST'], dc['MTTRUNITS'], dc['MTTR'], dc['MTTR2']))

        breakdowns = []
        for a in files['attach.txt']:
            if a['RESTYPE'] == 'stngrp':
                m_break = [m for m in machines if m.group == a['RESNAME']]
            else:
                m_break = [m for m in machines if m.family == a['RESNAME']]
            distribution = get_distribution(a['FOADIST'], a['FOAUNITS'], a['FOA'])
            if a['CALTYPE'] == 'down':
                is_breakdown = True
                ne, le = downcals[a['CALNAME']]
            else:
                is_breakdown = False
                ne, le = pmcals[a['CALNAME']]
            if distribution is None:
                distribution = ne

            for m in m_break:
                br = BreakdownEvent(distribution.sample(), le, ne, m, is_breakdown)
                breakdowns.append(br)

        #super().__init__(machines, routes, lots, breakdowns, lot_for_machine, plugins)

        super().__init__(machines, routes, lots, breakdowns, lot_for_machine, gsaco_schedule, run_to, plugins)

