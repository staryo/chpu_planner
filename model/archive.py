from collections import defaultdict
from datetime import datetime, timedelta


class Archive:
    def __init__(self):
        self.schedule = defaultdict(lambda: defaultdict(dict))

    def add_day(self, equipment, day):
        self.schedule[equipment.identity][
            day] = equipment

    def several_days_report(self, step):
        def add_total_data(values, name):
            new_row = {
                'ГРУППА': '',
                'ИНВ. НОМЕР': '',
                'МОДЕЛЬ ОБОРУДОВАНИЯ': name,
            }
            for total_day, total_value in values.items():
                new_row[get_humanized_data(total_day, step)] = total_value
            return new_row

        def get_humanized_data(period_number, step_value):
            return (
                    datetime.now().replace(
                        hour=8,
                        minute=0,
                        second=0,
                        microsecond=0
                    ) + timedelta(hours=period_number * step_value)
            ).strftime('%Y-%m-%d %H:%M')

        report = []
        machine_labor = defaultdict(float)
        human_labor = defaultdict(float)
        setup_labor = defaultdict(float)
        for equipment in self.schedule.values():
            check = True
            task_number = 0
            while check:
                check = False
                row = None
                for day, tasks in equipment.items():
                    if task_number == 0:
                        machine_labor[day] += tasks.machine_labor
                        setup_labor[day] += tasks.setup_labor
                        human_labor[day] += tasks.human_labor
                    if row is None:
                        if task_number == 0:
                            row = {
                                'ГРУППА': tasks.equipment_group,
                                'ИНВ. НОМЕР': tasks.humanized_identity,
                                'МОДЕЛЬ ОБОРУДОВАНИЯ': f"{tasks.equipment_class.name} "
                                                       f"[{tasks.equipment_class.identity}]",
                            }
                        else:
                            row = {
                                'ГРУППА': '',
                                'ИНВ. НОМЕР': '',
                                'МОДЕЛЬ ОБОРУДОВАНИЯ': '',
                            }
                    try:
                        task = tasks.schedule[task_number]
                    except IndexError:
                        row[get_humanized_data(day, step)] = ''
                        continue
                    check = True
                    operation_id = f"{task.operation.entity} [{task.operation.identity.split('_')[1][1]} | {task.operation.nop}]"
                    if 'NOK' in task.order:
                        operation_id = f"!NOK! {operation_id}"
                    else:
                        operation_id = f"!OK! {operation_id}"
                    row[get_humanized_data(day, step)] = f"{operation_id}: {int(task.quantity)} шт"
                report.append(row)
                task_number += 1
        report.append(add_total_data(setup_labor, 'НАЛАДКИ'))
        report.append(add_total_data(machine_labor, 'СТАНКОЧАСЫ'))
        report.append(add_total_data(human_labor, 'НОРМОЧАСЫ'))
        return report
