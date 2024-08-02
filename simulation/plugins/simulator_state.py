
from simulation.plugins.interface import IPlugin



class SimulatorStateGeneratorPlugin(IPlugin):

    def on_sim_init(self, instance):
        super().on_sim_init(instance)
        for machine in instance.machines:
            machine.will_be_free = instance.current_time

    def on_dispatch(self, instance, machine, lots, machine_end_time, lot_end_time):
        super().on_dispatch(instance, machine, lots, machine_end_time, lot_end_time)
        machine.will_be_free = machine_end_time

    def on_next_day(self, instance, day_number: int):
        super().on_next_day(instance, day_number)
