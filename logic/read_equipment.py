from model.equipment import Equipment
from model.equipment_class import EquipmentClass
from model.equipment_group import EquipmentGroup
from utils.excel import excel_to_dict


def read_equipment(config):
    all_equipment_groups = {}
    all_equipment_classes = {}

    for row in excel_to_dict(config['input']['equipment']):
        if not (row['GROUP']):
            continue
        if row['GROUP'] not in all_equipment_groups:
            all_equipment_groups[row['GROUP']] = EquipmentGroup(
                identity=row['GROUP']
            )
        if str(row['EQUIPMENT_ID']) not in all_equipment_classes:
            all_equipment_classes[str(row['EQUIPMENT_ID'])] = EquipmentClass(
                identity=str(row['EQUIPMENT_ID']),
                name=row['NAME']
            )
        all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[row['ID']] = Equipment(
            identity=row['ID'],
            model=row['MODEL'],
            equipment_class=all_equipment_classes[
                str(row['EQUIPMENT_ID'])
            ]
        )
        all_equipment_groups[
            row['GROUP']
        ].equipment[row['ID']] = all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[row['ID']]

    return all_equipment_classes, all_equipment_groups