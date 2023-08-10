from argparse import ArgumentParser
from os import getcwd
from os.path import join

from tqdm import tqdm

from config.config import read_config
from logic.calculate_tasks import calculate_tasks
from logic.daily_task_report import daily_task_report
from logic.final_setups_report import final_setups_report
from logic.read_equipment import read_equipment
from logic.read_setups import read_setups
from logic.read_tasks import read_tasks
from logic.tasks_left_report import tasks_left_report
from utils.excel import dict_to_excel


def main():
    parser = ArgumentParser(
        description='Инструмент планирования станков ЧПУ.'
    )
    parser.add_argument('-c', '--config', required=False,
                        default=join(getcwd(), 'config.yml'))
    parser.add_argument('-d', '--days', required=False,
                        default=None)

    args = parser.parse_args()

    # basicConfig(level=args.debug and DEBUG or INFO)

    config = read_config(args.config)
    if args.days:
        config['rules']['days_number'] = int(args.days)

    for day in tqdm(range(config['rules']['days_number'])):
        all_equipment_classes, all_equipment_groups = read_equipment(config)

        all_tasks, all_operations = read_tasks(
            config['input']['tasks'].format(day),
            all_equipment_classes,
            config['rules']['dept_id']
        )

        final_setup, all_equipment_setups = read_setups(
            config['input']['setups'].format(day), all_equipment_classes,
            all_operations
        )

        all_equipment_groups = calculate_tasks(
            all_tasks,
            all_equipment_groups,
            all_equipment_setups,
            final_setup,
            config['rules']['human_labor_limit'],
            config['rules']['machine_labor_limit']
        )

        all_equipment_groups = dict(
            sorted(
                all_equipment_groups.items(), key=lambda x: x[1].identity
            )
        )

        dict_to_excel(daily_task_report(all_equipment_groups),
                      config['output']['daily_tasks'].format(day + 1))

        dict_to_excel(final_setups_report(final_setup),
                      config['input']['setups'].format(day + 1))

        dict_to_excel(tasks_left_report(all_tasks),
                      config['input']['tasks'].format(day + 1))


if __name__ == '__main__':
    main()
