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
