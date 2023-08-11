def tasks_left_report(all_tasks):
    return [{
        'OPERATION_ID': task.operation.identity,
        'ENTITY': task.operation.entity,
        'NOP': task.operation.nop,
        'EQUIPMENT_ID': task.operation.equipment_class.identity,
        'DATE': task.date,
        'QUANTITY': task.quantity,
        'SETUP_LABOR': task.operation.setup_time * 60,
        'HUMAN_LABOR': task.operation.human_labor * 60,
        'MACHINE_LABOR': task.operation.machine_labor * 60,
        'ORDER': task.order
    } for task in all_tasks]
