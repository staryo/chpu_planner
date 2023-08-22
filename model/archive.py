from collections import defaultdict


class Archive:
    def __init__(self):
        self.schedule = defaultdict(lambda: defaultdict(dict))

    def add_day(self, equipment, day):
        self.schedule[equipment.identity][
            day] = equipment

    def several_days_report(self):
        report = []
        for equipment in self.schedule.values():
            check = True
            task_number = 0
            while check:
                check = False
                row = None
                for day, tasks in equipment.items():
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
                        row[day] = ''
                        continue
                    check = True
                    operation_id = f"{task.operation.entity} [{task.operation.identity.split('_')[1][1]} | {task.operation.nop}]"
                    if 'NOK' in task.order:
                        operation_id = f"!NOK! {operation_id}"
                    else:
                        operation_id = f"!OK! {operation_id}"
                    row[day] = f"{operation_id}: {task.quantity} шт"
                report.append(row)
                task_number += 1
        return report
