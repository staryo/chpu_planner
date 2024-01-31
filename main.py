import csv
import math
from argparse import ArgumentParser
from os import getcwd
from os.path import join
from datetime import datetime

from tqdm import tqdm
import json

from config.config import read_config
from logic.calculate_tasks import calculate_tasks
from logic.daily_task_report import daily_task_report
from logic.final_setups_report import final_setups_report
from logic.read_counter import read_counter
from logic.read_equipment import read_equipment
from logic.read_setups import read_setups
from logic.read_tasks import read_tasks
from logic.tasks_left_report import tasks_left_report
from model.archive import Archive
from utils.excel import dict_to_excel
# from utils.listofdicts_to_csv import dict2csv


def chpu_planner():
    parser = ArgumentParser(
        description='Инструмент планирования станков ЧПУ.'
    )
    parser.add_argument('-c', '--config', required=False,
                        default=join(getcwd(), 'config.yml'))
    parser.add_argument('-d', '--days', required=False,
                        default=None)
    parser.add_argument('-hl', '--human', required=False,
                        default=None)
    parser.add_argument('-ml', '--machine', required=False,
                        default=None)
    parser.add_argument('-s', '--step', required=False,
                        default=None)
    parser.add_argument('-fd', '--first_date', required=False,
                        default=None)
    parser.add_argument('-ft', '--first_time', required=False,
                        default=None)
    parser.add_argument('-sc', '--setups_coef', required=False,
                        default=None)

    args = parser.parse_args()

    # basicConfig(level=args.debug and DEBUG or INFO)

    config = read_config(args.config)
    if args.days:
        config['rules']['days_number'] = int(args.days)
    if args.human:
        config['rules']['human_labor_limit'] = float(args.human)
    if args.machine:
        config['rules']['machine_labor_limit'] = float(args.machine)
    if args.step:
        config['rules']['step'] = int(args.step)
    if args.first_date:
        config['rules']['date_first_shift'] = str(args.first_date)
    if args.first_time:
        config['rules']['time_first_shift'] = int(args.first_time)
    if args.setups_coef:
        config['rules']['max_shifts_for_one_setup'] = int(args.setups_coef)

    cycle_data = {}
    try:
        with open(config['input']['cycle'], 'r',
                  encoding='utf-8') as input_file:
            for row in list(csv.DictReader(
                    input_file
            )):
                cycle_data[row['ROUTE_PHASE_previous']] = {
                    'NEXT_PHASE': row['ROUTE_PHASE_past'],
                    'CYCLE': math.ceil(
                        int(row['cycle_delta']) / config['rules']['step']
                    ) + 1
                }
    except BaseException:
        print('В конфигурационном файле нет ссылки на циклы, '
              'циклы по переходам не будут учтены.')

    with open(config['input']['phase'], 'r', encoding='utf-8') as input_file:
        phase_list = list(csv.DictReader(
            input_file
        ))
    phase_dict = {}
    for row in phase_list:
        phase_dict[row['operation_id']] = {
            'LABOR': float(row['human_labor']),
            'NEXT_PHASE': (cycle_data.get(row['phase']) or {}).get(
                'NEXT_PHASE'),
            'CYCLE': (cycle_data.get(row['phase']) or {}).get('CYCLE')
        }

    try:
        first_date = datetime.strptime(config['rules']['date_first_shift'],
                                       '%d-%m-%Y')
    except ValueError:
        first_date = datetime.now()

    try:
        shift = int(config['rules']['time_first_shift'])
    except (TypeError, KeyError, ValueError):
        print()
        print("ВНИМАНИЕ! Произошла ошибка чтения исходных параметров "
              "времени начала смены для формирования отчётов ЧПУ.")
        print()
        shift = 7

    archive = Archive(first_date=first_date, shift=shift, config=config)

    for day in tqdm(range(config['rules']['days_number'])):
        all_equipment_classes, all_equipment_groups = read_equipment(config)

        all_tasks, all_operations = read_tasks(
            tasks_path=config['input']['tasks'].format(day),
            all_equipment_classes=all_equipment_classes,
            dept_id=config['rules']['dept_id'],
            operations_total_labor_file_path=config['input']['operations_total_labor'],
            max_shifts_for_one_setup=config['rules']['max_shifts_for_one_setup']
        )

        counter = read_counter(
            counter_path=config['input']['counter'].format(day)
        )

        final_setup, all_equipment_setups = read_setups(
            config['input']['setups'].format(day),
            all_equipment_classes,
            all_operations
        )

        all_equipment_groups, counter = calculate_tasks(
            all_tasks,
            all_equipment_groups,
            all_equipment_setups,
            final_setup,
            config['rules']['human_labor_limit'],
            config['rules']['machine_labor_limit'],
            phase_dict,
            counter
        )

        all_equipment_groups = dict(
            sorted(all_equipment_groups.items(),
                   key=lambda x: x[1].identity)
        )

        counter_report = [{
            'PHASE_ID': None,
            'DAY': None,
            'QUANTITY': None
        }]
        for phase, phase_data in counter.items():
            for day_limit, quantity in phase_data.items():
                if quantity == 0:
                    continue
                counter_report.append({
                    'PHASE_ID': phase,
                    'DAY': max(0, day_limit - 1),
                    'QUANTITY': quantity
                })

        dict_to_excel(
            counter_report,
            config['input']['counter'].format(day + 1)
        )

        dict_to_excel(daily_task_report(all_equipment_groups),
                      config['output']['daily_tasks'].format(day + 1))

        dict_to_excel(final_setups_report(final_setup),
                      config['input']['setups'].format(day + 1))

        dict_to_excel(tasks_left_report(all_tasks),
                      config['input']['tasks'].format(day + 1))

        for equipment_group in all_equipment_groups.values():
            for equipment in equipment_group.equipment.values():
                archive.add_day(equipment, day)

    several_days_report, report_materials = archive.several_days_report(
        step=config['rules']['step'])

    dict_to_excel(several_days_report,
                  config['output']['daily_tasks'].format('all'))

    # формируем этот отчёт если были NOK-заказы
    # если в tasks_0 были только OK-заказы, то report_materials = []
    if len(report_materials) > 0:
        dict_to_excel(report_materials,
                      config['output']['daily_tasks'].format('materials'))
        archive.calculate_report_materials(
            step=config['rules']['step'],
            file_path=config['output']['daily_tasks'].format('materials')
        )

    dict_to_excel(
        archive.labor_report(
            config['rules']['step'],
            phase_dict
        ),
        config['output']['daily_tasks'].format('labor')
    )

    # dict2csv(archive.raport_report(
    #         config['rules']['step']
    #     ), config['output']['raport'])

    dict_to_excel(
        archive.raport_report(
            config['rules']['step']
        ),
        config['output']['daily_tasks'].format('raport')
    )

    with open(config['output']['raport'], 'w',
              encoding='utf-8') as output_file:
        json.dump(archive.raport_report_2(
            config['rules']['step']
        ),
            output_file
        )


if __name__ == '__main__':
    chpu_planner()
