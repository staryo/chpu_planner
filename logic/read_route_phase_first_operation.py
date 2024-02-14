from utils.excel import excel_to_dict


def read_route_phase_first_operation(file_path):
    lst = excel_to_dict(file_path)
    route_phase_first_operation_set = set()
    for i in lst:
        route_phase_first_operation_set.add(
            f"{i['ROUTE_PHASE']}_{i['ROUTE_LETTER']}_{i['NOP']}")
    # print(route_phase_first_operation_set)
    # x = '377002002001-V0521_V_001_0100'
    # print("YES" if x in route_phase_first_operation else "NO")
    return route_phase_first_operation_set
