import csv


def read_operations_total_labor():
    with open(r'C:\Users\user\PycharmProjects\chpu_planner\example/operations_total_labor.csv',
              'r', encoding='utf-8') as file:
        ops_total_labor_list = list(csv.DictReader(file))

    operations_total_labor_dict = {}
    for i in ops_total_labor_list:
        operations_total_labor_dict[i['OPERATION_ID']] = i['MACHINE_SUM, shifts']

    print(operations_total_labor_dict)
    return operations_total_labor_dict


# read_operations_total_labor()
