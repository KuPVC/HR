import frappe

def before_validate(doc, method):
    joining_date = frappe.db.get_value("Employee",doc.employee,"date_of_joining")
    doc.custom_working_days_from_joining = frappe.utils.date_diff(doc.end_date, joining_date)
    doc.custom_calendar_days = frappe.utils.date_diff(doc.end_date,doc.start_date)+1