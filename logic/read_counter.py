from collections import defaultdict

from model.operation import Operation
from model.task import Task
from utils.excel import excel_to_dict


def read_counter(counter_path):
    report = defaultdict(lambda: defaultdict(float))
    for row in excel_to_dict(counter_path):
        report[row['PHASE_ID']][row['DAY']] += row['QUANTITY']

    return report
