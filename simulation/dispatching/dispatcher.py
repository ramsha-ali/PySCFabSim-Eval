from simulation.classes import Lot, Machine
from simulation.randomizer import Randomizer

r = Randomizer()


class Dispatchers:


    @staticmethod
    def fifo_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        if machine is not None:
            lot.ptuple = (
                #0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                0 if lot.cqt_waiting is not None else 1,
                #Dispatchers.get_setup(lot.actual_step.setup_needed, machine, lot.actual_step.setup_time, setups),
                -lot.priority, lot.free_since, lot.deadline_at,
            )
            return lot.ptuple
        else:
            return -lot.priority, lot.free_since, lot.deadline_at,

    @staticmethod
    def cr_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        if machine is not None:
            lot.ptuple = (
                #0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                0 if lot.cqt_waiting is not None else 1,
                #Dispatchers.get_setup(lot.actual_step.setup_needed, machine, lot.actual_step.setup_time, setups),
                -lot.priority, lot.cr(time),
            )
            return lot.ptuple
        else:
            return -lot.priority, lot.cr(time),

    @staticmethod
    def random_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        print("----",machine)
        if machine is not None:
            return (
                #0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                0 if lot.cqt_waiting is not None else 1,
                r.random.uniform(0, 99999),
            )
        else:
            return r.random.uniform(0, 99999),


dispatcher_map = {
    'fifo': Dispatchers.fifo_ptuple_for_lot,
    'cr': Dispatchers.cr_ptuple_for_lot,
    'random': Dispatchers.random_ptuple_for_lot,
}
