def daily_task_report(all_equipment_groups):
    report = []
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
                    if '_NOK' in task.order:
                        task_sum[task.operation] = {
                            'QUANTITY': 0,
                            'QUANTITY_NOK': task.quantity,
                            'SETUP_TIME': setup_time
                        }
                    else:
                        task_sum[task.operation] = {
                            'QUANTITY': task.quantity,
                            'QUANTITY_NOK': 0,
                            'SETUP_TIME': setup_time
                        }
                else:
                    if '_NOK' in task.order:
                        task_sum[task.operation]['QUANTITY_NOK'] += task.quantity
                    else:
                        task_sum[task.operation]['QUANTITY'] += task.quantity
            for each in task_sum:
                if task_sum[each]['QUANTITY'] > 0:
                    report.append({
                        'ГРУППА': '',
                        'ИНВ. НОМЕР': equipment.identity,
                        'МОДЕЛЬ ОБОРУДОВАНИЯ': '',
                        'МАРШРУТ': f"{each.identity.split('_')[1][1]}",
                        'ДСЕ,ОПЕРАЦИЯ': f"{each.entity} [{each.nop}]",
                        'КОЛИЧЕСТВО': task_sum[each]['QUANTITY'],
                        'ВРЕМЯ НАЛАДКИ': task_sum[each]['SETUP_TIME'],
                        'СТАНКОЧАСЫ': task_sum[each][
                                          'QUANTITY'] * each.machine_labor,
                        'НОРМОЧАСЫ': task_sum[each]['QUANTITY'] * each.human_labor
                    })
                if task_sum[each]['QUANTITY_NOK'] > 0:
                    if task_sum[each]['QUANTITY'] > 0:
                        setup_time = 0
                    else:
                        setup_time = task_sum[each]['QUANTITY_NOK']
                    report.append({
                        'ГРУППА': '',
                        'ИНВ. НОМЕР': equipment.identity,
                        'МОДЕЛЬ ОБОРУДОВАНИЯ': '',
                        'МАРШРУТ': f"{each.identity.split('_')[1][1]}",
                        'ДСЕ,ОПЕРАЦИЯ': f"{each.entity} [{each.nop}] !NOK!",
                        'КОЛИЧЕСТВО': task_sum[each]['QUANTITY_NOK'],
                        'ВРЕМЯ НАЛАДКИ': setup_time,
                        'СТАНКОЧАСЫ': task_sum[each][
                                          'QUANTITY_NOK'] * each.machine_labor,
                        'НОРМОЧАСЫ': task_sum[each][
                                         'QUANTITY_NOK'] * each.human_labor
                    })

    return report
