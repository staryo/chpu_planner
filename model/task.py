class Task:
    def __init__(self, operation, quantity, date):
        self.operation = operation
        self.quantity = quantity
        self.date = date

    @property
    def human_labor(self):
        return self.operation.human_labor * self.quantity

    @property
    def machine_labor(self):
        return self.operation.machine_labor * self.quantity

    @property
    def setup_labor(self):
        return self.operation.setup_time
