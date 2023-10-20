def final_setups_report(final_setup):
    return [{
        'EQUIPMENT_ID': equipment.identity,
        'EQUIPMENT_CLASS_ID': equipment.equipment_class.identity,
        'SETUP_OPERATION': operation.identity
    } for equipment, operation in final_setup.items()]
