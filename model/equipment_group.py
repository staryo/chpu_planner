class EquipmentGroup:
    def __init__(self, identity):
        self.identity = identity
        self.equipment = {}

    @property
    def human_labor(self):
        total = 0
        for equipment in self.equipment.values():
            total += equipment.human_labor
        return total

