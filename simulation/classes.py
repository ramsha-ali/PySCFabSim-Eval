from typing import List, Dict

from simulation.events import BreakdownEvent
from simulation.randomizer import Randomizer
from simulation.tools import get_interval, get_distribution, date_time_parse, ConstantDistribution

r = Randomizer()

machine_classes = {}


def alt(d, a1, a2):
    return d[a1] if a1 in d else (d[a2] if a2 is not None else None)


def default(d, a1, de):
    return d[a1] if a1 in d else de


def none_is_0(v):
    return 0 if v is None else v


class Machine:

    def __init__(self, idx, d, speed):
        self.idx = idx
        self.name = f"Machine_{idx}"
        self.group = d['STNGRP']
        if self.group not in machine_classes:
            machine_classes[self.group] = len(machine_classes)
        self.machine_class = machine_classes[self.group]
        self.loc = d['STNFAMLOC']
        self.family = d['STNFAM']
        self.speed = speed
        self.will_be_free = 0
        self.available_from = None
        self.available_to = None
        self.waiting_lots: List[Lot] = []
        self.utilized_time = 0
        self.bred_time = 0
        self.events = []

    def __hash__(self):
        return self.idx

    def __repr__(self):
        return f'Machine {self.idx}'


class Product:
    def __init__(self, route, priority):
        self.route = route
        self.priority = priority


class Step:

    def __init__(self, idx, pieces_per_lot, d):
        self.idx = idx
        self.order = d['STEP']
        self.step_name = d['DESC']
        self.family = d['STNFAM']
        assert len(self.family) > 0

        self.processing_time = get_distribution(d['PDIST'], d['PTUNITS'], d['PTIME'], d['PTIME2'])
        self.family_location = ''


    def __repr__(self):
        return f'Step {self.idx}'

class Lot:
    def __init__(self, idx, route, priority, release, relative_deadline, d):
        #self.ptuple = None
        self.idx = idx
        self.remaining_steps = [step for step in route.steps]
        self.actual_step: Step = None
        self.processed_steps = []
        self.priority = priority
        self.position = None
        self.release_at = release
        self.deadline_at = self.release_at + relative_deadline
        self.name: str = d['LOT']
        self.part_name: str = d['PART']
        if 'Init_' in self.name:
            self.name = self.name[self.name.index('_') + 1:self.name.rindex('_')]

        if 'CURSTEP' in d:
            cs = d['CURSTEP']
            self.processed_steps, self.remaining_steps = self.remaining_steps[:cs - 1], self.remaining_steps[cs - 1:]

        self.pieces = d['PIECES']

        self.waiting_machines = []

        self.done_at = None
        self.free_since = None

        self.remaining_steps_last = -1
        self.remaining_time_last = 0

        self.waiting_time = 0
        self.processing_time = 0

        self.ft = None

    def __hash__(self):
        return self.idx

    def __repr__(self):
        return f'Lot {self.idx}'

    def cr(self, time):
        rt = self.remaining_time
        return (self.deadline_at - time) / rt if rt > 0 else 1

    @property
    def full_time(self):
        if self.ft is None:
            self.ft = sum(
                [s.processing_time.avg() for s in self.processed_steps +
                 ([self.actual_step] if self.actual_step is not None else []) + self.remaining_steps])
        return self.ft

    @property
    def remaining_time(self):
        if self.remaining_steps_last != len(self.remaining_steps):
            if self.remaining_steps_last - 1 == len(self.remaining_steps):
                self.remaining_time_last -= self.processed_steps[-1].processing_time.avg()
            else:
                self.remaining_time_last = sum(
                    [s.processing_time.avg() for s in self.remaining_steps]) + self.actual_step.processing_time.avg()
            self.remaining_steps_last = len(self.remaining_steps)
        return self.remaining_time_last


class Route:

    def __init__(self, idx, steps: List[Step]):
        self.idx = idx
        self.steps = steps


class FileRoute(Route):

    def __init__(self, idx, pieces_per_lot, steps: List[Dict]):
        steps = [Step(i, pieces_per_lot, d) for i, d in enumerate(steps)]
        super().__init__(idx, steps)
