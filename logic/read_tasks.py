from model.operation import Operation
from model.task import Task
from utils.excel import excel_to_dict


def read_tasks(tasks_path, all_equipment_classes, dept_id):
    all_tasks = []
    all_operations = {}
    # tasks = sorted(
    #     excel_to_dict(tasks_path),
    #     key=lambda k: (k['ORDER'][:9], 1 if '_NOK' in k['ORDER'] else 0)
    # )
    for row in excel_to_dict(tasks_path):
        if dept_id != (row.get('DEPT_ID') or dept_id):
            continue
        if row['OPERATION_ID'] not in all_operations:
            all_operations[row['OPERATION_ID']] = Operation(
                identity=row['OPERATION_ID'],
                entity=row.get('ENTITY'),
                nop=row.get('NOP'),
                name='',
                equipment_class=all_equipment_classes[row['EQUIPMENT_CLASS_ID']],
                machine_labor=row['MACHINE_LABOR'] / 60,
                human_labor=row['HUMAN_LABOR'] / 60,
                setup_time=row['SETUP_LABOR'] / 60
            )
        all_tasks.append(Task(
            operation=all_operations[row['OPERATION_ID']],
            quantity=row['QUANTITY'],
            date=row['DATE'],
            order=row['ORDER']
        ))

    return all_tasks, all_operations
