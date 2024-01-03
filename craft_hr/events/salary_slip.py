import frappe

def before_validate(doc, method):
    joining_date = frappe.db.get_value("Employee",doc.employee,"date_of_joining")
    doc.custom_working_days_from_joining = frappe.utils.date_diff(doc.end_date, joining_date)
    doc.custom_calendar_days = frappe.utils.date_diff(doc.end_date,doc.start_date)+1
    get_ot_from_overtime_sheet(doc)
    get_ot_from_attendance(doc)

def get_ot_from_overtime_sheet(doc):
    if doc.custom_ot == 0:
        ot_data = frappe.db.sql("""
        select sum(ot) ot, sum(hot) hot, sum(food_allowance) food_allowance
        from `tabOvertime Hours`
        where docstatus = 1
        and employee = %s
        and date between %s and %s
        """,(doc.employee,doc.start_date,doc.end_date),as_dict=True)[0]
        doc.custom_ot = ot_data.ot
        doc.custom_holiday_ot = ot_data.hot

def get_ot_from_attendance(doc,method=None):
    doc.ot,doc.hot,doc.late_hours = frappe.db.sql("""
                                      SELECT
                                        SUM(ot) ot, SUM(hot) hot, SUM(late_hours) late_hours
                                      FROM
                                        `tabAttendance`
                                      WHERE
                                        employee = %s
                                      AND
                                        docstatus = 1
                                      AND
                                        attendance_date BETWEEN %s AND %s
                                      """,(doc.employee,doc.start_date,doc.end_date))[0]