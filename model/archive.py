from collections import defaultdict
from datetime import datetime, timedelta


class Archive:
    def __init__(self):
        self.schedule = defaultdict(lambda: defaultdict(dict))

    def add_day(self, equipment, day):
        self.schedule[equipment.identity][
            day] = equipment

    def several_days_report(self, step, shift_hours):
        def add_total_data(values, name):
            new_row = {
                'ГРУППА': '',
                'ИНВ. НОМЕР': '',
                'МОДЕЛЬ ОБОРУДОВАНИЯ': name,
            }
            for total_day, total_value in values.items():
                new_row[get_humanized_data(total_day, step,
                                           shift_hours)] = total_value
            return new_row

        def get_humanized_data(period_number, step_value, shift_start):
            now_hour = (datetime.now().hour - shift_start) % 24
            cur_hour = (now_hour // step_value) * step_value + shift_start

            return (
                    datetime.now().replace(
                        hour=cur_hour % 24,
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
                        row[get_humanized_data(day, step, shift_hours)] = ''
                        continue
                    check = True
                    if ',' in task.operation.entity:
                        operation_id = (
                            f"{task.operation.entity.split('(')[0]}"
                            f"{')'.join(task.operation.entity.split(')')[1:])}"
                            f"[{task.operation.identity.split('_')[1][1]}-"
                            f"{task.operation.entity.split(',')[1][0]}-"
                            f"{task.operation.nop.split('_')[1]}]")
                    else:
                        operation_id = (f"{task.operation.entity}"
                                        f"[{task.operation.identity.split('_')[1][1]}-"
                                        f"?-"
                                        f"{task.operation.nop.split('_')[1]}]")

                    if 'NOK_D' in task.order:
                        ok_nok = 'NOK_D'
                    elif 'NOK' in task.order:
                        ok_nok = 'NOK'
                    elif 'OK_D' in task.order:
                        ok_nok = 'OK_D'
                    elif 'OK' in task.order:
                        ok_nok = 'OK'
                    row[
                        get_humanized_data(day, step, shift_hours)
                    ] = f"{operation_id} {int(task.quantity)} {ok_nok}"
                report.append(row)
                task_number += 1
        report.append(add_total_data(setup_labor, 'НАЛАДКИ'))
        report.append(add_total_data(machine_labor, 'СТАНКОЧАСЫ'))
        report.append(add_total_data(human_labor, 'НОРМОЧАСЫ'))
        return report
