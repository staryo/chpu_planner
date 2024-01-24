class Operation:
    def __init__(self, identity, entity, nop, name, equipment_class,
                 machine_labor, human_labor, setup_time):
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

        #
        self.max_setups = ...
        # self.first_in_route_phase = True if str(self.nop).startswith("001_") else False

    def check_in_route_phase(self):
        print(f"{self.route_phase}_{self.route_letter}_{self.nop}")
        return f"{self.route_phase}_{self.route_letter}_{self.nop}"
