import pandas as pd
from collections import defaultdict
from datetime import timedelta
from logic.read_route_phases import read_route_phases
from logic.read_route_phase_first_operation import read_route_phase_first_operation


class Archive:
    def __init__(self, first_date, shift, config):
        self.schedule = defaultdict(lambda: defaultdict(dict))
        self.first_date = first_date
        self.shift = shift
        self.config = config

    def add_day(self, equipment, day):
        self.schedule[equipment.identity][day] = equipment

    def add_total_data(self, new_row, values, step):
        for total_day, total_value in values.items():
            new_row[self.get_humanized_data(total_day, step)] = total_value
        return new_row

#    @staticmethod
    def get_humanized_data(self, period_number, step_value):
        return (
                self.first_date.replace(
                    hour=self.shift,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(hours=period_number * step_value)
        ).strftime('%Y-%m-%d %H:%M')

    def several_days_report(self, step):
        report = []
        route_phase_dict = read_route_phases(self.config['input']['spec'],
                                             self.config['output']['route_phases'])
        route_phase_first_operation_set = read_route_phase_first_operation(
            self.config['input']['route_phase_first_operation'])
        report_materials = []

        machine_labor = defaultdict(float)
        human_labor = defaultdict(float)
        setup_labor = defaultdict(float)
        prof_labor = defaultdict(lambda: defaultdict(float))

        for equipment in self.schedule.values():
            check = True
            task_number = 0
            while check:
                check = False
                row = None
                for day, tasks in equipment.items():

                    if task_number == 0:
                        prof_labor[tasks.equipment_group.profession][day] += tasks.human_labor
                        machine_labor[day] += tasks.machine_labor
                        setup_labor[day] += tasks.setup_labor
                        human_labor[day] += tasks.human_labor
                    if row is None:
                        if task_number == 0:
                            row = {
                                'ГРУППА': tasks.equipment_group.identity,
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
                    operation_id = f"{task.operation.entity} [{task.operation.route_letter} | {task.operation.nop}]"
                    if task.order_provided:
                        operation_id = f"!OK! {operation_id}"
                    else:
                        operation_id = f"!NOK! {operation_id}"
                        if task.operation.check_in_route_phase() in route_phase_first_operation_set:
                            # формируем запись для "Участок-отправитель" в row1
                            dept_name = ""
                            if "-" in route_phase_dict[task.operation.route_phase][1]:
                                # подставляем первую цифру под участок, 316 или 1ХХ
                                dept_code_raw = route_phase_dict[task.operation.route_phase][1]
                                first_dept_digit = "3" if dept_code_raw[-4:-2] == "16" else "1"
                                dept_name = f"{first_dept_digit}{dept_code_raw[-4:-2]}-0{dept_code_raw[-2]}"
                            row1 = {
                                "Заказ": task.order,
                                "Дата потребности": self.get_humanized_data(day, step),
                                "Наименование NOK_ДСЕ": task.operation.entity,
                                "Буква маршрута": task.operation.route_letter,
                                "Артикул NOK_ДСЕ с цехозаходом": task.operation.route_phase,
                                "Количество_шт": int(task.quantity),
                                "Участок-отправитель": dept_name,
                                "Наименование ДСЕ_комплектующей": route_phase_dict[task.operation.route_phase][0],
                                "Артикул ДСЕ_комплектующей с цехозаходом": route_phase_dict[
                                    task.operation.route_phase][1]
                            }
                            report_materials.append(row1)
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
        for profession, labor in prof_labor.items():
            report.append(
                self.add_total_data(
                    {'ГРУППА': '',
                        'ИНВ. НОМЕР': '',
                        'МОДЕЛЬ ОБОРУДОВАНИЯ': profession,
                    },
                    labor,
                    step)
            )

        try:
            report_materials.sort(key=lambda x: (x["Дата потребности"], -x["Количество_шт"]))
        except Exception as error:
            print()
            print(f"ВНИМАНИЕ! Произошла ошибка {error}, отчёт по МИК не отсортирован.")
            print()
        return report, report_materials

    def calculate_report_materials(self, step, file_path):
        initial_report = self.several_days_report(step)[1]
        df = pd.DataFrame(initial_report)
        # датафрейм для сменного отчёта
        df["Дата потребности"] = df["Дата потребности"].astype('datetime64[ns]')
        df = df.groupby(["Дата потребности", "Заказ", "Наименование NOK_ДСЕ", "Буква маршрута",
                         "Артикул NOK_ДСЕ с цехозаходом", "Участок-отправитель",
                         "Наименование ДСЕ_комплектующей", "Артикул ДСЕ_комплектующей с цехозаходом"]
                        ).Количество_шт.sum().reset_index()
        df = df.sort_values(["Дата потребности", "Количество_шт"],
                            ascending=(True, False))
        # датафрейм для суточного отчёта
        df2 = df.copy()
        df2["Дата потребности"] = pd.to_datetime(df2["Дата потребности"]).dt.date
        df2 = df2.groupby(["Дата потребности", "Заказ", "Наименование NOK_ДСЕ", "Буква маршрута",
                           "Артикул NOK_ДСЕ с цехозаходом", "Участок-отправитель",
                           "Наименование ДСЕ_комплектующей", "Артикул ДСЕ_комплектующей с цехозаходом"]
                          ).Количество_шт.sum().reset_index()
        df2 = df2.sort_values(["Дата потребности", "Количество_шт"],
                              ascending=(True, False))
        # выстраиваем в обеих таблицах нужный порядок столбцов
        df = df[["Дата потребности", "Заказ", "Количество_шт", "Наименование NOK_ДСЕ",
                 "Артикул NOK_ДСЕ с цехозаходом", "Буква маршрута",
                 "Участок-отправитель", "Наименование ДСЕ_комплектующей",
                 "Артикул ДСЕ_комплектующей с цехозаходом"]]
        df2 = df2[["Дата потребности", "Заказ", "Количество_шт", "Наименование NOK_ДСЕ",
                   "Артикул NOK_ДСЕ с цехозаходом", "Буква маршрута",
                   "Участок-отправитель", "Наименование ДСЕ_комплектующей",
                   "Артикул ДСЕ_комплектующей с цехозаходом"]]
        # запись датафреймов в тот же файл отчёта МИК
        excel_sheets = {"Сменный_отчёт": df, "Суточный отчёт": df2}
        with pd.ExcelWriter(file_path, mode='a',
                            engine='openpyxl',
                            if_sheet_exists='replace') as writer:
            for sheet, data in excel_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)

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
                            labor_dict[task.operation.identity]['LABOR']
                            * task.quantity
                    )
                    entity_labor[task.operation.identity[:18]] = labor_dict[
                        task.operation.identity
                    ]['LABOR']
                    entity_identity[task.operation.identity[:18]] \
                        = task.operation.entity
                    daily_entities[task.operation.identity[:18]][
                        day] += task.quantity
                    total_entities[
                        task.operation.identity[:18]] += task.quantity
        for entity in sorted(total_entities):
            row = {
                'ДСЕ': entity_identity[entity],
                'КОД КСАУП': entity,
                'ТРУДОЕМКОСТЬ ЦЕХОЗАХОДА': entity_labor[entity],
            }
            for day in sorted(total_labor):
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

    def raport_report(self, step):
        daily_operation = defaultdict(lambda: defaultdict(float))
        for equipment in self.schedule.values():
            for day, tasks in equipment.items():
                for task in tasks.schedule:
                    daily_operation[task.operation.identity][
                        day] += task.quantity
        return [{
            'operationIdentity': operation,
            'assemblyElementIdentity': (
                operation.split('-')[0].zfill(
                    18) if '-' in operation else operation[:18]
            ),
            'dateBegin': (self.get_humanized_data(day, step)).split(' ')[0],
            'timeBegin': f"{(self.get_humanized_data(day, step)).split(' ')[1]}:00",
            'quantityPlan': daily_operation[operation][day],
        } for operation in daily_operation for day in
            daily_operation[operation]]

    def raport_report_2(self, step):
        daily_operation = defaultdict(lambda: defaultdict(float))
        for equipment in self.schedule.values():
            for day, tasks in equipment.items():
                for task in tasks.schedule:
                    daily_operation[task.operation.identity][
                        day] += task.quantity
        return {
            f'{(self.get_humanized_data(day, step)).split(" ")[0]}_{(self.get_humanized_data(day, step)).split(" ")[1]}:00_{operation}':
                {
                    'identity': f'{(self.get_humanized_data(day, step)).split(" ")[0]}_{(self.get_humanized_data(day, step)).split(" ")[1]}:00_{operation}',
                    'operationIdentity': operation,
                    'assemblyElementIdentity': (
                        operation.split('-')[0].zfill(
                            18) if '-' in operation else operation[:18]
                    ),
                    'dateBegin':
                        (self.get_humanized_data(day, step)).split(' ')[0],
                    'timeBegin': f"{(self.get_humanized_data(day, step)).split(' ')[1]}:00",
                    'quantityPlan': daily_operation[operation][day],
                } for operation in daily_operation for day in
            daily_operation[operation]
        }
