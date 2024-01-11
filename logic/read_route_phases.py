import csv
from utils.excel import dict_to_excel


def read_route_phases(file_path, output_file):
    # file_path = r'C:\Users\user\PycharmProjects\chpu_planner\example/spec.csv'
    with open(file_path, 'r', encoding='utf-8') as spec_file:
        route_phase_list = list(csv.DictReader(spec_file))

    for i in route_phase_list:
        for k in ('PARENT_IDENTITY', 'IDENTITY', 'AMOUNT'):
            del i[k]

    route_phase_list.sort(key=lambda x: x['PARENT_CODE'])

    route_phase_dict = {}
    for i in route_phase_list:
        route_phase_dict[i['PARENT_CODE']] = (i['NAME'], i['CODE'])
        # route_phase_dict[i['PARENT_NAME']] = i['NAME']

    dict_to_excel(route_phase_list,
                  output_file)

    return route_phase_dict
