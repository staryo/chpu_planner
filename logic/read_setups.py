from utils.excel import excel_to_dict


def read_setups(setups_path, all_equipment_classes, all_operations):
    final_setup = {}
    all_equipment_setups = {}
    for row in excel_to_dict(setups_path):
        row['EQUIPMENT_ID'] = str(row['EQUIPMENT_ID'])
        row['EQUIPMENT_CLASS_ID'] = str(row['EQUIPMENT_CLASS_ID'])
        try:
            all_equipment_classes[
                row['EQUIPMENT_CLASS_ID']
            ].equipment[
                row['EQUIPMENT_ID']
            ].initial_setup = all_operations[row['SETUP_OPERATION']]
            final_setup[all_equipment_classes[
                row['EQUIPMENT_CLASS_ID']
            ].equipment[
                row['EQUIPMENT_ID']
            ]] = all_operations[row['SETUP_OPERATION']]
            all_equipment_setups[
                all_equipment_classes[
                    row['EQUIPMENT_CLASS_ID']
                ].equipment[row['EQUIPMENT_ID']]
            ] = all_operations[row['SETUP_OPERATION']]
        except KeyError:
            print(f"Строка наладки проигнорирована: {row}")

    return final_setup, all_equipment_setups
