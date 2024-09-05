from simulation.classes import Lot, Machine
from simulation.randomizer import Randomizer

r = Randomizer()


class Dispatchers:

    @staticmethod
    def fifo_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        if machine is not None:
            lot.ptuple = (
                0 if lot.cqt_waiting is not None else 1,
                10,  # Set the same priority (10) for all lots
                lot.free_since,
                lot.deadline_at,
            )
            return lot.ptuple
        else:
            return 10, lot.free_since, lot.deadline_at,  # Priority is always 10

    @staticmethod
    def cr_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        if machine is not None:
            lot.ptuple = (
                0 if lot.cqt_waiting is not None else 1,
                10,  # Set the same priority (10) for all lots
                lot.cr(time),
            )
            return lot.ptuple
        else:
            return 10, lot.cr(time),  # Priority is always 10

    @staticmethod
    def random_ptuple_for_lot(lot: Lot, time, machine: Machine = None):
        if machine is not None:
            return (
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
