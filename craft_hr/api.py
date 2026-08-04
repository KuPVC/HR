import frappe
from frappe.utils import add_days, add_to_date, cint, date_diff, flt, get_datetime, getdate, nowdate


@frappe.whitelist()
def get_attendance_calendar_details(from_date: str, to_date: str) -> dict:
    """
    Attendance calendar events enriched with late entry / short hours / missed
    punch flags (mirrors the flags used by sj_hr's Monthly Attendance Sheet
    report) for the logged-in employee, for the given date range.
    """
    from hrms.api import get_current_employee, get_holidays_for_calendar

    employee = get_current_employee()
    holidays = get_holidays_for_calendar(employee, from_date, to_date)

    attendance_meta = frappe.get_meta("Attendance")
    has_short_hours = attendance_meta.has_field("custom_short_hours")
    has_missed_punch = attendance_meta.has_field("custom_missed_punch")
    has_hours_difference = attendance_meta.has_field("custom_hours_difference")

    fields = ["attendance_date", "status", "late_entry"]
    if has_short_hours:
        fields.append("custom_short_hours")
    if has_missed_punch:
        fields.append("custom_missed_punch")
    if has_hours_difference:
        fields.append("custom_hours_difference")

    records = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1,
        },
        fields=fields,
    )

    attendance_by_date = {
        str(row.attendance_date): {
            "status": row.status,
            "late_entry": cint(row.get("late_entry")),
            "short_hours": cint(row.get("custom_short_hours")),
            "missed_punch": cint(row.get("custom_missed_punch")),
            "hours_difference": row.get("custom_hours_difference") or 0,
        }
        for row in records
    }

    events = {}
    date = getdate(from_date)
    while date_diff(to_date, date) >= 0:
        date_str = date.strftime("%Y-%m-%d")
        if date_str in attendance_by_date:
            events[date_str] = attendance_by_date[date_str]
        elif date in holidays:
            events[date_str] = {
                "status": "Holiday",
                "late_entry": 0,
                "short_hours": 0,
                "missed_punch": 0,
                "hours_difference": 0,
            }
        date = add_days(date, 1)

    return events


@frappe.whitelist()
def get_attendance_request_type_hours_based(reason: str) -> int:
    """Whether the selected Attendance Request Type requires hours to be entered."""
    if not reason:
        return 0
    return cint(frappe.db.get_value("Attendance Request Type", reason, "hours_based"))


@frappe.whitelist()
def get_todays_checkins() -> list[dict]:
    """Today's Employee Checkin log times (IN/OUT) for the logged-in employee."""
    from hrms.api import get_current_employee

    employee = get_current_employee()
    today = nowdate()
    day_start = f"{today} 00:00:00"
    day_end = f"{today} 23:59:59"

    return frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [day_start, day_end]],
        },
        fields=["name", "log_type", "time"],
        order_by="time asc",
    )


@frappe.whitelist()
def get_next_holidays() -> list[dict]:
    """Next 3 upcoming holidays (>= today, excluding weekly offs) from the employee's assigned Holiday List."""
    from hrms.api import get_current_employee
    from hrms.utils.holiday_list import get_holiday_list_for_employee

    employee = get_current_employee()
    holiday_list = get_holiday_list_for_employee(employee, raise_exception=False)
    if not holiday_list:
        return []

    today = nowdate()
    return frappe.get_all(
        "Holiday",
        filters={
            "parent": holiday_list,
            "holiday_date": [">=", today],
            "weekly_off": 0,
        },
        fields=["holiday_date", "description"],
        order_by="holiday_date asc",
        limit=3,
    )


@frappe.whitelist()
def get_todays_estimated_checkout() -> dict | None:
    """
    Estimated check-out time for today, derived from today's shift's
    `custom_required_working_hours` (Shift Type custom field) and the
    employee's first IN checkin of the day.
    """
    from hrms.api import get_current_employee

    employee = get_current_employee()
    today = nowdate()

    # Prefer an active Shift Assignment covering today, else fall back to
    # Employee.default_shift.
    shift_type = frappe.db.get_value(
        "Shift Assignment",
        {
            "employee": employee,
            "status": "Active",
            "docstatus": 1,
            "start_date": ["<=", today],
        },
        "shift_type",
        order_by="start_date desc",
    )
    if shift_type:
        # ensure it hasn't ended before today
        end_date = frappe.db.get_value(
            "Shift Assignment",
            {"employee": employee, "shift_type": shift_type, "start_date": ["<=", today]},
            "end_date",
            order_by="start_date desc",
        )
        if end_date and getdate(end_date) < getdate(today):
            shift_type = None

    if not shift_type:
        shift_type = frappe.db.get_value("Employee", employee, "default_shift")

    if not shift_type:
        return None

    if not frappe.get_meta("Shift Type").has_field("custom_required_working_hours"):
        return None

    required_hours = flt(
        frappe.db.get_value("Shift Type", shift_type, "custom_required_working_hours")
    )
    if not required_hours:
        return None

    day_start = f"{today} 00:00:00"
    day_end = f"{today} 23:59:59"
    first_checkin_time = frappe.db.get_value(
        "Employee Checkin",
        {
            "employee": employee,
            "log_type": "IN",
            "time": ["between", [day_start, day_end]],
        },
        "time",
        order_by="time asc",
    )
    if not first_checkin_time:
        return None

    estimated_checkout = add_to_date(get_datetime(first_checkin_time), hours=required_hours)

    return {
        "shift_type": shift_type,
        "required_hours": required_hours,
        "first_checkin_time": first_checkin_time,
        "estimated_checkout": estimated_checkout,
    }


@frappe.whitelist()
def can_approve_team_requests() -> bool:
    """
    Whether the current user is eligible to approve at least one other
    employee's Leave Application, Shift Request, or Attendance Request.

    Eligibility (mirrors hrms's own approver/permission logic; not based on
    whether anything is currently pending):
      - Attendance Request has no per-employee approver field in hrms;
        access is role-gated (System Manager / HR Manager / HR User per
        attendance_request.json permissions), so any of those roles qualify.
      - Leave Application: user is set as `leave_approver` on any Employee,
        or is listed as an approver in a Department Approver row for the
        `leave_approver` parentfield.
      - Shift Request: user is set as `shift_request_approver` on any
        Employee, or is listed as an approver in a Department Approver row
        for the `shift_request_approver` parentfield.
    """
    user = frappe.session.user

    if frappe.db.exists(
        "Has Role",
        {"parent": user, "role": ["in", ["System Manager", "HR Manager", "HR User"]]},
    ):
        return True

    if frappe.db.exists("Employee", {"leave_approver": user}):
        return True
    if frappe.db.exists("Employee", {"shift_request_approver": user}):
        return True

    if frappe.db.exists(
        "Department Approver",
        {"parentfield": "leave_approver", "approver": user},
    ):
        return True
    if frappe.db.exists(
        "Department Approver",
        {"parentfield": "shift_request_approver", "approver": user},
    ):
        return True

    return False


@frappe.whitelist()
def get_my_assets() -> list[dict]:
    """
    Company assets currently held by the logged-in employee, sourced from
    Asset.custodian (kept in sync automatically by Asset Movement on
    submit/cancel — the authoritative "who has it right now" field, no need
    to query Asset Movement directly).
    """
    from hrms.api import get_current_employee

    employee = get_current_employee()

    return frappe.get_all(
        "Asset",
        filters={
            "custodian": employee,
            "docstatus": 1,
            "status": ["not in", ["Scrapped", "Sold", "Cancelled", "Draft"]],
        },
        fields=["name", "asset_name", "asset_category", "location", "status"],
        order_by="asset_name asc",
        ignore_permissions=True,
    )
