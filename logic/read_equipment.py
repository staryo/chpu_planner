from model.equipment import Equipment
from model.equipment_class import EquipmentClass
from model.equipment_group import EquipmentGroup
from utils.excel import excel_to_dict


def read_equipment(config):
    all_equipment_groups = {}
    all_equipment_classes = {}
    dept_id = config['rules']['dept_id']

    for row in excel_to_dict(config['input']['equipment']):
        if dept_id != (row.get('DEPT_ID') or dept_id):
            continue
        if not (row['GROUP']):
            continue
        if str(row['GROUP']) not in all_equipment_groups:
            all_equipment_groups[str(row['GROUP'])] = EquipmentGroup(
                identity=str(row['GROUP']), profession=row['PROFESSION']
            )
        if str(row['EQUIPMENT_ID']) not in all_equipment_classes:
            all_equipment_classes[str(row['EQUIPMENT_ID'])] = EquipmentClass(
                identity=str(row['EQUIPMENT_ID']),
                name=row['NAME']
            )
        machine_id = f"{row['ID']}"
        if row['Порядковый номер']:
            machine_id += f" / {row['Порядковый номер']}"
        all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[str(row['ID'])] = Equipment(
            identity=str(row['ID']),
            humanized_identity=machine_id,
            model=row['MODEL'],
            equipment_class=all_equipment_classes[
                str(row['EQUIPMENT_ID'])
            ],
            equipment_group=None
        )
        all_equipment_groups[str(row['GROUP'])].equipment[str(row['ID'])] = \
            all_equipment_classes[str(row['EQUIPMENT_ID'])].equipment[
                str(row['ID'])]

        all_equipment_classes[
            str(row['EQUIPMENT_ID'])
        ].equipment[str(row['ID'])].equipment_group = all_equipment_groups[str(row['GROUP'])]

    return all_equipment_classes, all_equipment_groups
