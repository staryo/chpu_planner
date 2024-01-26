# import sys
from collections import defaultdict

from logic.tasks_limit import (get_task_limit, get_task_limit_cache,
                               have_to_minus)
from model.task import Task


def calculate_tasks(
        all_tasks,
        all_equipment_groups,
        all_equipment_setups,
        final_setup,
        human_labor_limit,
        machine_labor_limit,
        phase_data,
        counter=None
):
    """
    Составляем расписание работы оборудования
    @param all_tasks: все задания
    @param all_equipment_groups: сгруппированное оборудование
    @param all_equipment_setups: наладки исходные.
    Кажется, что нет никаких ограничений, чтоб одна и та же наладка была на нескольких станках
    @param final_setup: типа текущая наладка, но как будто в логике вообще
    не используется, мы его просто здесь внутри переопределяем, чтоб сохранить в ксв и
    передать в качестве исходных данных в расчет следующего дня
    @param human_labor_limit: лимит по трудоемкости персонала
    @param machine_labor_limit: лимит по трудоемкости оборудования
    @param phase_data: информация по циклам цехозаходов
    @param counter: счетчик сколько обеспеченных деталей у нас есть
    @return:
    """
    # Вот эта логика является ограничением.
    # setups_0 = {}

    # в каждую операцию в список собираю оборудование,
    # которое налаживается на неё при переборе заданий
    setups = defaultdict(list)

    # Типа у каждого задания тут есть один станок
    # надо переделать, чтоб было списком.
    # И добавлять в список / убирать из списка при каждой переналадке.

    cache = get_task_limit_cache(all_tasks)
    counter = counter or defaultdict(lambda: defaultdict(int))
    all_depended_phases = set(
        [row['NEXT_PHASE'] for row in phase_data.values()]
    )

    # Первая фаза набора заданий --
    # ставим только те, что соответствуют исходной наладке
    for task in all_tasks:
        if task.quantity == 0:
            continue
        for equipment_group in all_equipment_groups.values():
            if equipment_group.human_labor > human_labor_limit:
                continue
            quantity = (
                               human_labor_limit - equipment_group.human_labor
                       ) // max(task.operation.human_labor, 0.0001)
            if quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                # проверка на текущую наладку единицы оборудования
                if all_equipment_setups.get(equipment) != task.operation:
                    continue
                if equipment.machine_labor > machine_labor_limit:
                    continue
                # проверка на технологию
                if equipment.identity not in task.operation.equipment_class.equipment:
                    continue
                quantity = min(quantity + 1,
                               (machine_labor_limit - equipment.machine_labor) //
                               max(task.operation.machine_labor, 0.0001) + 1,
                               # получает сколько можно сделать по операции
                               get_task_limit(
                                   task.operation.identity,
                                   cache,
                                   counter,
                                   ('_OK' in task.order) or ("_".join(
                                       task.operation.identity.split('_')[:2]
                                   ) not in all_depended_phases)
                               )
                               )
                if quantity <= 0 or task.quantity <= 0:
                    continue
                # новый экземпляр класса Task
                new_task = Task(
                    task.operation,
                    min(quantity, task.quantity),
                    task.date,
                    task.order
                )
                # в исходном задании оставляем за вычетом того, что уже взяли
                task.quantity = task.quantity - new_task.quantity
                final_setup[equipment] = new_task.operation
                equipment.schedule.append(new_task)
                # в операцию добавляем станок, на который наладка
                setups[new_task.operation.identity].append(equipment)
                if have_to_minus(
                        task.operation.identity,
                        cache,
                        ('_OK' in task.order) or ("_".join(
                            task.operation.identity.split('_')[:2]
                        ) not in all_depended_phases)
                ):
                    # для передачи в следующую смену нового количества
                    counter[
                        "_".join(task.operation.identity.split('_')[:2])
                    ][0] -= new_task.quantity
                # счётчик цехозаходов по последней его операции
                if task.operation.identity in phase_data:
                    next_phase_data = phase_data[task.operation.identity]
                    if next_phase_data['NEXT_PHASE'] is not None:
                        counter[
                            next_phase_data['NEXT_PHASE']
                        ][next_phase_data['CYCLE']] += new_task.quantity

    # Вторая фаза набора заданий --
    # ставим только те, что не соответствуют исходной наладке
    for task in all_tasks:
        # сортируем группы оборудования по загрузке - самая незагруженная вверху
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
            labor_quantity = (human_labor_limit - equipment_group.human_labor
                              ) // max(task.operation.human_labor, 0.0001)
            if labor_quantity == 0:
                continue
            for equipment in equipment_group.equipment.values():
                if equipment.machine_labor > machine_labor_limit:
                    continue
                # if task.operation in setups:
                #     if setups[task.operation] != equipment:
                #         continue
                # здесь пытаюсь менять логику
                if task.operation.identity in setups.keys():
                    if len(setups[task.operation.identity]) >= task.operation.max_setups:
                        continue
                if equipment.identity not in \
                        task.operation.equipment_class.equipment:
                    continue
                if setups.get(task.operation) != equipment:
                    if equipment.machine_labor + task.setup_labor <= \
                            machine_labor_limit:
                        quantity = min(
                            labor_quantity + 1,
                            (machine_labor_limit - (
                                    equipment.machine_labor + task.setup_labor
                            )) // max(task.operation.machine_labor, 0.001) + 1,
                            get_task_limit(
                                task.operation.identity,
                                cache,
                                counter,
                                ('_OK' in task.order) or ("_".join(
                                    task.operation.identity.split('_')[:2]
                                ) not in all_depended_phases)
                            )
                        )
                    else:
                        quantity = 0
                else:
                    quantity = min(
                        labor_quantity + 1,
                        (machine_labor_limit - equipment.machine_labor) // max(
                            task.operation.machine_labor,
                            0.0001
                        ) + 1,
                        get_task_limit(
                            task.operation.identity,
                            cache,
                            counter,
                            ('_OK' in task.order) or ("_".join(
                                task.operation.identity.split('_')[:2]
                            ) not in all_depended_phases)
                        )
                    )
                if quantity <= 0 or task.quantity <= 0:
                    continue
                new_task = Task(
                    task.operation,
                    min(quantity, task.quantity),
                    task.date,
                    task.order
                )
                task.quantity -= new_task.quantity
                final_setup[equipment] = new_task.operation
                equipment.schedule.append(new_task)
                if have_to_minus(
                        task.operation.identity,
                        cache,
                        ('_OK' in task.order) or ("_".join(
                            task.operation.identity.split('_')[:2]
                        ) not in all_depended_phases)
                ):
                    counter[
                        "_".join(task.operation.identity.split('_')[:2])
                    ][0] -= new_task.quantity
                if task.operation.identity in phase_data:
                    next_phase_data = phase_data[task.operation.identity]
                    if next_phase_data['NEXT_PHASE'] is not None:
                        counter[
                            next_phase_data['NEXT_PHASE']
                        ][next_phase_data['CYCLE']] += new_task.quantity
                setups[new_task.operation] = equipment
                labor_quantity -= new_task.quantity
                if quantity == 0:
                    continue
                for similar_task in all_tasks:
                    if similar_task.operation != new_task.operation:
                        continue
                    quantity_to_take = min(
                        labor_quantity,
                        similar_task.quantity,
                        get_task_limit(
                            task.operation.identity,
                            cache,
                            counter,
                            ('_OK' in task.order) or ("_".join(
                                task.operation.identity.split('_')[:2]
                            ) not in all_depended_phases)
                        ),
                        (machine_labor_limit - equipment.machine_labor
                         ) // max(
                            task.operation.machine_labor,
                            0.0001
                        ) + 1,
                    )
                    if quantity_to_take <= 0:
                        continue
                    new_task = Task(
                        similar_task.operation,
                        quantity_to_take,
                        similar_task.date,
                        similar_task.order
                    )
                    similar_task.quantity -= new_task.quantity
                    equipment.schedule.append(new_task)
                    if have_to_minus(
                            task.operation.identity,
                            cache,
                            ('_OK' in task.order) or ("_".join(
                                task.operation.identity.split('_')[:2]
                            ) not in all_depended_phases)
                    ):
                        counter[
                            "_".join(task.operation.identity.split('_')[:2])
                        ][0] -= new_task.quantity
                    if task.operation.identity in phase_data:
                        next_phase_data = phase_data[task.operation.identity]
                        if next_phase_data['NEXT_PHASE'] is not None:
                            counter[
                                next_phase_data['NEXT_PHASE']
                            ][next_phase_data['CYCLE']] += new_task.quantity
                    final_setup[equipment] = new_task.operation

    all_tasks.sort(key=lambda x: x.operation.max_setups_float, reverse=True)


    # Здесь нужно пробежаться по оборудованию, проверить есть ли незагруженные
    # и снова повторить первую фазу -- берем все задания, которые подходят под наладку
    # На что обратить внимание:
    # 1. Если станок недогружен на ... 5 минут -- то может просто ему не
    # хватило время на переналадку. Там есть такая логика, что он берет задание,
    # только если ему хватает время переналадиться и сделать хотя бы одну деталь.
    # 2. Сами приоритеты на что налаживаться входными данными в метод наверное надо затащить.
    # обернуть all_tasks через lambda условие ...
    # Плюс не забыть считать текущее количество наладок, чтоб приоритет исходный делить на это число.
    return all_equipment_groups, counter
