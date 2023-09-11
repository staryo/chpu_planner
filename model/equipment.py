class Equipment:
    def __init__(self, identity, humanized_identity, model, equipment_class,
                 equipment_group):
        self.identity = identity
        self.humanized_identity = humanized_identity
        self.model = model
        self.equipment_class = equipment_class
        self.equipment_group = equipment_group
        self.initial_setup = None
        self.schedule = []

    def __repr__(self):
        return self.humanized_identity

    @property
    def machine_labor(self):
        total = 0
        for task in self.schedule:
            total += task.machine_labor
        return total + self.setup_labor

    @property
    def setup_labor(self):
        total = 0
        unique_operations = set()
        for task in self.schedule:
            if task.operation == self.initial_setup:
                continue
            if task.operation not in unique_operations:
                total += task.operation.setup_time
            unique_operations.add(task.operation)
        return total

    @property
    def human_labor(self):
        total = 0
        for task in self.schedule:
            total += task.human_labor
        return total
