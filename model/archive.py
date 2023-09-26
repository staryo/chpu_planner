from collections import defaultdict
from datetime import datetime, timedelta


class Archive:
    def __init__(self):
        self.schedule = defaultdict(lambda: defaultdict(dict))

    def add_day(self, equipment, day):
        self.schedule[equipment.identity][
            day] = equipment

    def add_total_data(self, new_row, values, step):
        for total_day, total_value in values.items():
            new_row[self.get_humanized_data(total_day, step)] = total_value
        return new_row

    @staticmethod
    def get_humanized_data(period_number, step_value):
        return (
                datetime.now().replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(hours=period_number * step_value)
        ).strftime('%Y-%m-%d %H:%M')

    def several_days_report(self, step):
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
                        row[self.get_humanized_data(day, step)] = ''
                        continue
                    check = True
                    operation_id = f"{task.operation.entity} [{task.operation.identity.split('_')[1][1]} | {task.operation.nop}]"
                    if 'NOK' in task.order:
                        operation_id = f"!NOK! {operation_id}"
                    else:
                        operation_id = f"!OK! {operation_id}"
                    row[self.get_humanized_data(day,
                                                step)] = f"{operation_id}: {int(task.quantity)} шт"
                report.append(row)
                task_number += 1
        report.append(
            self.add_total_data(
                {
                    'ГРУППА': '',
                    'ИНВ. НОМЕР': '',
                    'МОДЕЛЬ ОБОРУДОВАНИЯ': 'НАЛАДКИ',
                },
                setup_labor,
                step)
        )
        report.append(
            self.add_total_data(
                {
                    'ГРУППА': '',
                    'ИНВ. НОМЕР': '',
                    'МОДЕЛЬ ОБОРУДОВАНИЯ': 'СТАНКОЧАСЫ',
                },
                machine_labor,
                step)
        )
        report.append(
            self.add_total_data(
                {
                    'ГРУППА': '',
                    'ИНВ. НОМЕР': '',
                    'МОДЕЛЬ ОБОРУДОВАНИЯ': 'НОРМОЧАСЫ',
                },
                human_labor,
                step)
        )
        return report

    def labor_report(self, step, labor_dict):
        report = []
        total_labor = defaultdict(float)
        daily_entities = defaultdict(lambda: defaultdict(float))
        total_entities = defaultdict(float)
        entity_labor = {}
        entity_identity = {}
        for equipment in self.schedule.values():
            for day, tasks in equipment.items():
                for task in tasks.schedule:
                    if task.operation.identity not in labor_dict:
                        continue
                    total_labor[day] += (
                            labor_dict[task.operation.identity] * task.quantity
                    )
                    entity_labor[task.operation.entity] = labor_dict[
                        task.operation.identity
                    ]
                    entity_identity[task.operation.entity] \
                        = task.operation.identity[:18]
                    daily_entities[task.operation.entity][day] += task.quantity
                    total_entities[task.operation.entity] += task.quantity
        for entity in sorted(total_entities):
            row = {
                'ДСЕ': entity,
                'КОД КСАУП': entity_identity[entity],
                'ТРУДОЕМКОСТЬ ЦЕХОЗАХОДА': entity_labor[entity],
            }
            for day in total_labor:
                row[
                    self.get_humanized_data(day, step)
                ] = daily_entities[entity][day] or ''
            row['ИТОГО'] = total_entities[entity]
            report.append(row)
        report.append(
            self.add_total_data(
                {
                    'ДСЕ': 'ОБЩАЯ ТРУДОЕМКОСТЬ',
                    'КОД КСАУП': '',
                    'ТРУДОЕМКОСТЬ ЦЕХОЗАХОДА': '',
                },
                total_labor,
                step
            )
        )
        return report
