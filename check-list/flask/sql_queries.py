SYSTEM_CHECKLIST = (
    "SELECT item.id, item.seq_order, item.name, role.short_name, "
    "subsystem.name "
    "FROM item "
    "INNER JOIN role ON role_id=role.id "
    "INNER JOIN subsystem ON subsystem_id=subsystem.id "
    "WHERE day_phase_id=%s AND subsystem_id=%s "
    "ORDER BY seq_order ASC"
)

# Reverse Order
LAST_CHECKLINES = (
    "SELECT sub.* FROM ("
    "SELECT item_id, item.seq_order, "
    "time_date, "
    "role.short_name AS Resp, complete_status.status, "
    "item.name "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.report_id = %s AND "
    # "CheckItemSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = %s "
    "ORDER BY time_date DESC LIMIT 5"
    ") sub ORDER BY time_date ASC"
)

LAST_CHECKED = (
    "SELECT item_id, item.seq_order "
    "FROM complete "
    "INNER JOIN item ON complete.item_id = item.id "
    "WHERE complete.report_id = %s AND "
    "item.subsystem_id = %s AND "
    "item.role_id= %s "
    "ORDER BY time_date DESC LIMIT 1"
)

NEXT_CHECKLINES = (
    "SELECT id, seq_order, name "
    "FROM item "
    "WHERE day_phase_id = %s AND subsystem_id = %s AND "
    "role_id = %s AND seq_order > %s "
    "ORDER BY seq_order ASC LIMIT 3"
)

PRECENDENCE = (
    "SELECT item_id, after_item_id "
    "FROM precedence "
    "INNER JOIN item ON item_id = item.id "
    "WHERE item_id = %s "
    "ORDER BY item_id ASC"
)

MISSING_ITEM = (
    "SELECT role.short_name, item.id, seq_order, item.name, "
    "subsystem.name AS System, day_phase.short_name AS Phase "
    "FROM item "
    "INNER JOIN subsystem ON subsystem_id = subsystem.id "
    "INNER JOIN day_phase ON day_phase_id = day_phase.id "
    "INNER JOIN role ON role_id = role.id "
    "WHERE item.id = %s"
)

PARAMETERS = "SELECT cc_pressure_sp, he_sp, h2_sp, o2_sp FROM reports WHERE id=%s"

# Reverse Order
REPORT_LIST = (
    "SELECT sub.* FROM ("
    "SELECT id, series_name, shot, chief_engineer_id, researcher_id, "
    "cc_pressure_sp, he_sp, h2_sp, o2_sp FROM reports "
    "ORDER BY id DESC LIMIT %s"
    ") sub ORDER BY id ASC"
)

REPORT_FULL = (
    "SELECT item_id, item.seq_order, "
    "time_date, item.name, "
    "role.short_name AS Resp, complete_status.short_status "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.report_id=%s "
    "ORDER BY time_date ASC"
)

OPERATOR_ROLES = (
    "SELECT operator_roles.role_id, role.name FROM operator_roles "
    "INNER JOIN role ON role_id = role.id "
    "WHERE operator_id=%s"
)
