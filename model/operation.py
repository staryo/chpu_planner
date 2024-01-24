import math

class Operation:
    def __init__(self, identity, entity, nop, name, equipment_class,
                 machine_labor, human_labor, setup_time, external_func, max_shifts_for_one_setup):
        self.identity = identity
        self.entity = entity
        self.nop = nop
        self.name = name
        self.equipment_class = equipment_class
        self.machine_labor = machine_labor
        self.human_labor = human_labor
        self.setup_time = setup_time
        self.route_phase = self.identity[:18]
        self.route_letter = self.identity[-8]
        # добавляем функцию для подсчёта максимального кол-ва наладок
        self.external_func = external_func
        self.max_shifts_for_one_setup = max_shifts_for_one_setup

    def max_setups(self):
        machine_sum_shifts = int(self.external_func()[self.identity])
        return math.ceil(machine_sum_shifts / self.max_shifts_for_one_setup)

    def check_in_route_phase(self):
        print(f"{self.route_phase}_{self.route_letter}_{self.nop}")
        return f"{self.route_phase}_{self.route_letter}_{self.nop}"
