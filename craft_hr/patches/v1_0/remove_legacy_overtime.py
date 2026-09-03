import frappe


def execute():
    """
    Overtime is now handled end-to-end by sj_hr's Overtime Slip -> Salary
    Slip pipeline. This removes craft_hr's older, now-unused overtime
    mechanism from the site: the Attendance-level OT/HOT/late-hours custom
    fields and their "Overtime Details" section, the Monthly Overtime Sheet
    and Overtime Hours doctypes (and any data in them), the Salary Slip/
    Salary Structure Assignment custom fields that fed off them, the
    Shift Type OT/HOT config fields, and the "Overtime Summary" report.

    Removing entries from custom_field.json alone only stops them being
    re-created on the next fixture sync - it does not delete records that
    already exist on a site, so this patch does the actual deletion.
    """
    custom_fields_to_delete = [
        "Attendance-section_break_jnm0g",
        "Attendance-shift_hours",
        "Attendance-break_hours",
        "Attendance-ot",
        "Attendance-hot",
        "Attendance-late_hours",
        "Attendance-column_break_d82hb",
        "Salary Slip-overtime_details",
        "Salary Slip-custom_overtime_from_attendance",
        "Salary Slip-ot",
        "Salary Slip-hot",
        "Salary Slip-column_break_nglxj",
        "Salary Slip-late_hours",
        "Salary Slip-custom_calendar_days",
        "Salary Slip-custom_working_days_from_joining",
        "Salary Slip-custom_overtime_sheet_data",
        "Salary Slip-custom_ot",
        "Salary Slip-custom_holiday_ot",
        "Salary Slip-custom_section_break_739fm",
        "Salary Slip-custom_column_break_jkyrt",
        "Salary Slip-custom_manual_ot",
        "Salary Slip-custom_manual_hot",
        "Salary Structure Assignment-custom_holiday_overtime_rate",
        "Salary Structure Assignment-ot_rate",
        "Shift Type-enable_ot",
        "Shift Type-enable_hot",
        "Shift Type-break_hours",
        "Shift Type-shift_threshold",
    ]
    for name in custom_fields_to_delete:
        if frappe.db.exists("Custom Field", name):
            frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)

    if frappe.db.exists("Report", "Overtime Summary"):
        frappe.delete_doc("Report", "Overtime Summary", force=True, ignore_permissions=True)

    for doctype in ("Monthly Overtime Sheet", "Overtime Hours"):
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc(
                "DocType", doctype, force=True, ignore_permissions=True, ignore_missing=True
            )

    # The now-deleted craft_hr/ot_mgmt module folder is no longer in
    # modules.txt; drop its stale Module Def too, or frappe.get_module()
    # fails to resolve it on the next schema sync.
    if frappe.db.exists("Module Def", "OT Mgmt"):
        frappe.delete_doc("Module Def", "OT Mgmt", force=True, ignore_permissions=True)

    frappe.db.commit()
