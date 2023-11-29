import sys
from collections import defaultdict


def get_task_limit(operation_id, cache, counter, allow_max):
    report = defaultdict(float)
    for task in cache["_".join(operation_id.split('_')[:2])]:
        if task.operation.identity.split('_')[:2] != operation_id.split('_')[
                                                     :2]:
            continue
        if task.operation.nop.split('_')[-1] > operation_id.split('_')[-1]:
            continue
        report[task.operation.nop.split('_')[-1]] += task.quantity

    try:
        return report[sorted(report)[-1]] - report[sorted(report)[-2]]
    except (KeyError, IndexError):
        if allow_max:
            return sys.maxsize
        return counter["_".join(operation_id.split('_')[:2])][0]


def get_task_limit_cache(all_tasks):
    cache = defaultdict(list)
    for task in all_tasks:
        cache["_".join(task.operation.identity.split('_')[:2])].append(task)
    return cache


def have_to_minus(operation_id, cache, allow_max):
    if '5505D0000007-G0531_ZG01' in operation_id:
        a = 1
    if allow_max:
        return False
    report = defaultdict(float)
    for task in cache["_".join(operation_id.split('_')[:2])]:
        if task.operation.identity.split('_')[:2] != operation_id.split('_')[
                                                     :2]:
            continue
        if task.operation.nop.split('_')[-1] > operation_id.split('_')[-1]:
            continue
        report[task.operation.nop.split('_')[-1]] += task.quantity

    if len(report) > 1:
        return False
    return True
