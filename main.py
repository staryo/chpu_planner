from argparse import ArgumentParser
from os import getcwd
from os.path import join

from config.config import read_config
from model.equipment import Equipment
from model.equipment_class import EquipmentClass
from model.equipment_group import EquipmentGroup
from model.operation import Operation
from model.task import Task
from utils.excel import excel_to_dict, dict_to_excel


def main():

    parser = ArgumentParser(
        description='Инструмент планирования станков ЧПУ.'
    )
    parser.add_argument('-c', '--config', required=False,
                        default=join(getcwd(), 'config.yml'))

    args = parser.parse_args()

    # basicConfig(level=args.debug and DEBUG or INFO)

    config = read_config(args.config)

    all_equipment_groups = {}
    all_equipment_classes = {}

    for row in excel_to_dict(config['input']['equipment']):
        if not(row['GROUP']):
            continue
        if row['GROUP'] not in all_equipment_groups:
            all_equipment_groups[row['GROUP']] = EquipmentGroup(
                identity=row['GROUP']
            )
        if row['EQUIPMENT_ID'] not in all_equipment_classes:
            all_equipment_classes[str(row['EQUIPMENT_ID'])] = EquipmentClass(
                identity=str(row['EQUIPMENT_ID']),
                name=row['NAME']
            )
        all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[row['ID']] = Equipment(
            identity=row['ID'],
            model=row['MODEL'],
            equipment_class=all_equipment_classes[
                str(row['EQUIPMENT_ID'])
            ]
        )
        all_equipment_groups[
            row['GROUP']
        ].equipment[row['ID']] = all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[row['ID']]

    all_tasks = []
    all_operations = {}
    for row in excel_to_dict(config['input']['tasks']):
        if row['OPERATION_ID'] not in all_operations:
            all_operations[row['OPERATION_ID']] = Operation(
                identity=row['OPERATION_ID'],
                entity=row.get('ENTITY'),
                nop=row.get('NOP'),
                name='',
                equipment_class=all_equipment_classes[row['EQUIPMENT_ID']],
                machine_labor=row['MACHINE_LABOR'] / 60,
                human_labor=row['HUMAN_LABOR'] / 60,
                setup_time=row['SETUP_LABOR'] / 60
            )
        all_tasks.append(Task(
            operation=all_operations[row['OPERATION_ID']],
            quantity=row['QUANTITY'],
            date=row['DATE']
        ))

    final_setup = {}
    all_equipment_setups = {}
    if 'setups' in config['input']:
        for row in excel_to_dict(config['input']['setups']):
            try:
                all_equipment_classes[
                    row['EQUIPMENT_CLASS_ID']
                ].equipment[
                    row['EQUIPMENT_ID']
                ].initial_setup = all_operations[row['SETUP_OPERATION']]
                final_setup[all_equipment_classes[
                    row['EQUIPMENT_CLASS_ID']
                ].equipment[
                    row['EQUIPMENT_ID']
                ]] = all_operations[row['SETUP_OPERATION']]
                all_equipment_setups[
                    all_equipment_classes[
                        row['EQUIPMENT_CLASS_ID']
                    ].equipment[row['EQUIPMENT_ID']]
                ] = all_operations[row['SETUP_OPERATION']]
            except KeyError:
                print(f"Строка наладки проигнорирована: {row}")
                # print(row)
    else:
        all_equipment_setups = {}

    setups = {}
    for task in all_tasks:
        if task.quantity == 0:
            continue
        for equipment_group in all_equipment_groups.values():
            if equipment_group.human_labor > config['rules']['human_labor_limit']:
                continue
            try:
                quantity = (config['rules']['human_labor_limit'] - equipment_group.human_labor) // task.operation.human_labor
            except ZeroDivisionError:
                quantity = task.quantity
            if quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                if all_equipment_setups.get(equipment) != task.operation:
                    continue
                if equipment.machine_labor > config['rules']['machine_labor_limit']:
                    continue
                # if task.operation in setups:
                #     if setups[task.operation] != equipment:
                #         continue
                if equipment.identity not in task.operation.equipment_class.equipment:
                    continue
                try:
                    quantity = min(
                        quantity,
                        (config['rules']['machine_labor_limit'] - equipment.machine_labor) // task.operation.machine_labor
                    )
                except ZeroDivisionError:
                    quantity = task.quantity
                if quantity <= 0:
                    continue
                new_task = Task(
                    task.operation,
                    min(quantity + 1, task.quantity),
                    task.date
                )
                task.quantity = task.quantity - new_task.quantity
                if task.quantity > 0:
                    final_setup[equipment] = new_task.operation
                equipment.schedule.append(new_task)
                setups[new_task.operation] = equipment
                break

    for task in all_tasks:
        all_equipment_groups = dict(
            sorted(
                all_equipment_groups.items(), key=lambda x: x[1].human_labor
            )
        )
        if task.quantity == 0:
            continue
        for equipment_group in all_equipment_groups.values():
            if equipment_group.human_labor > config['rules']['human_labor_limit']:
                continue
            try:
                quantity = (config['rules']['human_labor_limit'] - equipment_group.human_labor) // task.operation.human_labor
            except ZeroDivisionError:
                quantity = task.quantity
            if quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                if equipment.machine_labor > config['rules']['machine_labor_limit']:
                    continue
                if task.operation in setups:
                    if setups[task.operation] != equipment:
                        continue
                if equipment.identity not in \
                        task.operation.equipment_class.equipment:
                    continue
                if setups.get(task.operation) != equipment:
                    if equipment.machine_labor + task.setup_labor <= \
                            config['rules']['machine_labor_limit']:
                        try:
                            quantity = min(
                                quantity,
                                (config['rules']['machine_labor_limit'] - (
                                        equipment.machine_labor + task.setup_labor
                                )) // task.operation.machine_labor
                            )
                        except ZeroDivisionError:
                            pass
                    # if task.setup_labor > task.operation.machine_labor and quantity / task.quantity < 0.1:
                    #     continue
                else:
                    try:
                        quantity = min(
                            quantity,
                            (config['rules']['machine_labor_limit'] - equipment.machine_labor) // task.operation.machine_labor
                        )
                    except ZeroDivisionError:
                        pass
                if quantity <= 0:
                    continue
                new_task = Task(
                    task.operation,
                    min(quantity + 1, task.quantity),
                    task.date
                )
                task.quantity = task.quantity - new_task.quantity
                if task.quantity > 0:
                    final_setup[equipment] = new_task.operation
                equipment.schedule.append(new_task)
                setups[new_task.operation] = equipment
                break

    report = []
    all_equipment_groups = dict(
        sorted(
            all_equipment_groups.items(), key=lambda x: x[1].identity
        )
    )

    for equipment_group in all_equipment_groups.values():
        # print(equipment_group.identity, equipment_group.human_labor)
        report.append({
            'ГРУППА': equipment_group.identity,
            'ИНВ. НОМЕР': '',
            'МОДЕЛЬ ОБОРУДОВАНИЯ': '',
            'МАРШРУТ': '',
            'ДСЕ,ОПЕРАЦИЯ': '',
            'КОЛИЧЕСТВО': '',
            'ВРЕМЯ НАЛАДКИ': '',
            'СТАНКОЧАСЫ': '',
            'НОРМОЧАСЫ': equipment_group.human_labor
        })
        equipment_group.equipment = dict(
            sorted(
                equipment_group.equipment.items(), key=lambda x: x[1].identity
            )
        )
        for equipment in equipment_group.equipment.values():
            # print(equipment.identity, equipment.machine_labor)
            if equipment.initial_setup:
                operation_id = f"НАЛАДКА: {equipment.initial_setup.entity} [{equipment.initial_setup.nop}]"
                route_id = equipment.initial_setup.identity.split('_')[1][1]
            else:
                operation_id = 'НАЛАДКИ НЕТ'
                route_id = '-'
            report.append({
                'ГРУППА': '',
                'ИНВ. НОМЕР': equipment.identity,
                'МОДЕЛЬ ОБОРУДОВАНИЯ': f"{equipment.equipment_class.name} "
                                       f"[{equipment.equipment_class.identity}]",
                'МАРШРУТ': route_id,
                'ДСЕ,ОПЕРАЦИЯ': operation_id,
                'КОЛИЧЕСТВО': '',
                'ВРЕМЯ НАЛАДКИ': '',
                'СТАНКОЧАСЫ': equipment.machine_labor,
                'НОРМОЧАСЫ': ''
            })
            task_sum = {}
            for task in equipment.schedule:
                if task.operation not in task_sum:
                    if equipment.initial_setup == task.operation:
                        setup_time = 0
                    else:
                        setup_time = task.setup_labor
                    task_sum[task.operation] = {
                        'QUANTITY': task.quantity,
                        'SETUP_TIME': setup_time
                    }
                else:
                    task_sum[task.operation]['QUANTITY'] += task.quantity
            for each in task_sum:
                report.append({
                    'ГРУППА': '',
                    'ИНВ. НОМЕР': equipment.identity,
                    'МОДЕЛЬ ОБОРУДОВАНИЯ': '',
                    'МАРШРУТ': f"{each.identity.split('_')[1][1]}",
                    'ДСЕ,ОПЕРАЦИЯ': f"{each.entity} [{each.nop}]",
                    'КОЛИЧЕСТВО': task_sum[each]['QUANTITY'],
                    'ВРЕМЯ НАЛАДКИ': task_sum[each]['SETUP_TIME'],
                    'СТАНКОЧАСЫ': task_sum[each]['QUANTITY'] * each.machine_labor,
                    'НОРМОЧАСЫ': task_sum[each]['QUANTITY'] * each.human_labor
                })
    dict_to_excel(report, config['output']['daily_tasks'])
    report = [{
        'EQUIPMENT_ID': equipment.identity,
        'EQUIPMENT_CLASS_ID': equipment.equipment_class.identity,
        'SETUP_OPERATION': operation.identity
    } for equipment, operation in final_setup.items()]
    print(report[0])

    dict_to_excel(report, config['output']['final_setups'])

    report = [{
        'OPERATION_ID': task.operation.identity,
        'ENTITY': task.operation.entity,
        'NOP': task.operation.nop,
        'EQUIPMENT_ID': task.operation.equipment_class.identity,
        'DATE': task.date,
        'QUANTITY': task.quantity,
        'SETUP_LABOR': task.operation.setup_time * 60,
        'HUMAN_LABOR': task.operation.human_labor * 60,
        'MACHINE_LABOR': task.operation.machine_labor * 60
    } for task in all_tasks]
    print(report[0])
    dict_to_excel(report, config['output']['tasks_left'])


if __name__ == '__main__':
    main()
