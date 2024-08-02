import os


class MachineDoneEvent:

    def __init__(self, timestamp, machines):
        self.timestamp = timestamp
        self.machines = machines
        self.lots = []

    def handle(self, instance):
        instance.free_up_machines(self.machines)


class LotDoneEvent:

    def __init__(self, timestamp, machines, lots):
        self.timestamp = timestamp
        self.machines = machines
        self.lots = lots

    def handle(self, instance):
        instance.free_up_lots(self.lots)


class ReleaseEvent:

    @staticmethod
    def handle(instance, to_time):
        if to_time is None or (
                len(instance.dispatchable_lots) > 0 and instance.dispatchable_lots[0].release_at <= to_time):
            instance.current_time = max(0, instance.dispatchable_lots[0].release_at, instance.current_time)
            lots_released = []
            while len(instance.dispatchable_lots) > 0 and max(0, instance.dispatchable_lots[
                0].release_at) <= instance.current_time:
                lots_released.append(instance.dispatchable_lots[0])
                instance.dispatchable_lots = instance.dispatchable_lots[1:]
            instance.active_lots += lots_released
            instance.free_up_lots(lots_released)
            for plugin in instance.plugins:
                plugin.on_lots_release(instance, lots_released)
            return True
        else:
            return False


class BreakdownEvent:

    def __init__(self, timestamp, length, repeat_interval, machine, is_breakdown):
        self.timestamp = timestamp
        self.machine = machine
        self.machines = []
        self.lots = []
        self.is_breakdown = is_breakdown
        self.repeat_interval = repeat_interval
        self.length = length
        if not is_breakdown:
            machine.next_preventive_maintenance = timestamp


    def handle(self, instance):
        length = self.length.sample()
        if self.is_breakdown:
            self.machine.bred_time += length
        else:
            self.machine.pmed_time += length
        instance.handle_breakdown(self.machine, length)
        #print(f'{self.machine} in {self.machine.family} breakdown at timestamp: {self.timestamp} for duration: {self.machine.bred_time}')




        file_path = 'simulation_state/breakdown_log.txt'
        header = 'Toolgroup Machineid at duration\n'


        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            write_mode = 'w'
        else:
            write_mode = 'a'
        with open(file_path, write_mode) as file:
            if write_mode == 'w':
                file.write(header)
            message = f"{self.machine.family} " \
                      f"{self.machine} " \
                      f"{int(self.timestamp)} " \
                      f"{int(self.machine.bred_time)}\n"
            file.write(message)



        for plugin in instance.plugins:
            if self.is_breakdown:
                plugin.on_breakdown(instance, self)
            else:
                plugin.on_preventive_maintenance(instance, self)
        instance.add_event(BreakdownEvent(
            self.timestamp + length + self.repeat_interval.sample(),
            self.length,
            self.repeat_interval,
            self.machine,
            self.is_breakdown,
        ))

