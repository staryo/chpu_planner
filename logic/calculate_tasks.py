import sys

from logic.tasks_limit import get_task_limit, get_task_limit_cache
from model.task import Task


def calculate_tasks(
        all_tasks,
        all_equipment_groups,
        all_equipment_setups,
        final_setup,
        human_labor_limit,
        machine_labor_limit
):
    setups = {}
    cache = get_task_limit_cache(all_tasks)
    for task in all_tasks:
        # print(task.operation.identity,
        #       get_task_limit(all_tasks, task.operation.identity))
        if task.quantity == 0:
            continue
        for equipment_group in all_equipment_groups.values():
            if equipment_group.human_labor > human_labor_limit:
                continue
            quantity = (
                               human_labor_limit - equipment_group.human_labor
                       ) // max(
                task.operation.human_labor,
                0.0001
            ) + 1
            if quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                if all_equipment_setups.get(equipment) != task.operation:
                    continue
                if equipment.machine_labor > machine_labor_limit:
                    continue
                # if task.operation in setups:
                #     if setups[task.operation] != equipment:
                #         continue
                if equipment.identity not in task.operation.equipment_class.equipment:
                    continue
                quantity = min(
                    quantity,
                    (machine_labor_limit - equipment.machine_labor) // max(
                        task.operation.machine_labor,
                        0.0001
                    ) + 1,
                    get_task_limit(task.operation.identity, cache)
                )
                if quantity <= 0:
                    continue
                new_task = Task(
                    task.operation,
                    min(quantity, task.quantity),
                    task.date,
                    task.order
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
            if equipment_group.human_labor > human_labor_limit:
                continue
            quantity = (
                (
                        human_labor_limit - equipment_group.human_labor
                ) // max(
                    task.operation.human_labor,
                    0.0001
                ) + 1,
                get_task_limit(task.operation.identity, cache)
            )
            if quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                quantity = (
                        (
                                human_labor_limit - equipment_group.human_labor
                        ) // max(task.operation.human_labor, 0.0001)
                ) + 1
                if equipment.machine_labor > machine_labor_limit:
                    continue
                if task.operation in setups:
                    if setups[task.operation] != equipment:
                        continue
                if equipment.identity not in \
                        task.operation.equipment_class.equipment:
                    continue
                if setups.get(task.operation) != equipment:
                    if equipment.machine_labor + task.setup_labor <= \
                            machine_labor_limit:
                        quantity = min(
                            quantity,
                            (machine_labor_limit - (
                                    equipment.machine_labor + task.setup_labor
                            )) // max(task.operation.machine_labor, 0.001),
                            get_task_limit(
                                task.operation.identity, cache
                            ) + 1
                        )
                    else:
                        quantity = 0
                    # if task.setup_labor > task.operation.machine_labor and quantity / task.quantity < 0.1:
                    #     continue
                else:
                    quantity = min(
                        quantity,
                        (machine_labor_limit - equipment.machine_labor) // max(
                            task.operation.machine_labor,
                            0.0001
                        ) + 1,
                        get_task_limit(
                            task.operation.identity, cache
                        )
                    )
                if quantity <= 0:
                    continue
                new_task = Task(
                    task.operation,
                    min(quantity, task.quantity),
                    task.date,
                    task.order
                )
                task.quantity = task.quantity - new_task.quantity
                if task.quantity > 0:
                    final_setup[equipment] = new_task.operation
                equipment.schedule.append(new_task)
                setups[new_task.operation] = equipment
                break
    return all_equipment_groups
