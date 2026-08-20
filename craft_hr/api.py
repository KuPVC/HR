import frappe
from frappe.utils import add_days, add_to_date, cint, date_diff, flt, get_datetime, getdate, nowdate


def _get_reports_to_workflow_states(doctype: str) -> list[str]:
    """
    States of doctype's active Workflow whose incoming transition is gated by
    sj_hr's reports_to approver mechanism (the `approved_by_reports_to`
    checkbox on Workflow Transition - see sj_hr.workflow_reports_to), rather
    than a role. hrms's own get_allowed_states_for_workflow only matches the
    role-based `allowed` field, so it never returns these states for anyone.
    """
    workflow_name = frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1})
    if not workflow_name:
        return []

    workflow = frappe.get_cached_doc("Workflow", workflow_name)
    return [t.state for t in workflow.transitions if t.get("approved_by_reports_to")]


def _get_direct_report_employees(user: str) -> list[str]:
    employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    if not employee:
        return []
    return frappe.get_all("Employee", filters={"reports_to": employee}, pluck="name")


def _get_pending_reports_to_documents(doctype: str, fields: list[str], limit: int | None = None) -> list[dict]:
    """
    Documents of doctype currently awaiting approval from the logged-in
    user in their capacity as the reports_to manager of the document's
    employee, additive to whatever hrms's own role-based "for approval"
    filtering already returns for this doctype.
    """
    from hrms.api import get_workflow_state_field

    states = _get_reports_to_workflow_states(doctype)
    if not states:
        return []

    reports = _get_direct_report_employees(frappe.session.user)
    if not reports:
        return []

    workflow_state_field = get_workflow_state_field(doctype)
    if not workflow_state_field:
        return []

    return frappe.get_list(
        doctype,
        fields=fields,
        filters={
            "employee": ["in", reports],
            "docstatus": 0,
            workflow_state_field: ["in", states],
        },
        order_by="creation desc",
        limit=limit,
    )


def _merge_reports_to_documents(
    results: list[dict], doctype: str, fields: list[str], workflow_state_field: str | None, limit: int | None
) -> list[dict]:
    extra = _get_pending_reports_to_documents(doctype, fields, limit)
    if workflow_state_field:
        for doc in extra:
            doc["workflow_state_field"] = workflow_state_field

    existing_names = {doc["name"] for doc in results}
    results.extend(doc for doc in extra if doc["name"] not in existing_names)
    if limit:
        results = results[:limit]
    return results


@frappe.whitelist()
def get_attendance_requests(
    employee: str, for_approval: bool = False, limit: int | None = None
) -> list[dict]:
    from hrms.api import get_attendance_requests as get_hrms_attendance_requests, get_workflow_state_field

    results = get_hrms_attendance_requests(employee=employee, for_approval=for_approval, limit=limit)
    if not for_approval:
        return results

    fields = [
        "name",
        "reason",
        "employee",
        "employee_name",
        "from_date",
        "to_date",
        "include_holidays",
        "shift",
        "docstatus",
        "creation",
    ]
    workflow_state_field = get_workflow_state_field("Attendance Request")
    if workflow_state_field:
        fields.append(workflow_state_field)

    return _merge_reports_to_documents(results, "Attendance Request", fields, workflow_state_field, limit)


@frappe.whitelist()
def get_leave_applications(
    employee: str, approver_id: str | None = None, for_approval: bool = False, limit: int | None = None
) -> list[dict]:
    from hrms.api import get_leave_applications as get_hrms_leave_applications, get_workflow_state_field

    results = get_hrms_leave_applications(
        employee=employee, approver_id=approver_id, for_approval=for_approval, limit=limit
    )
    if not for_approval:
        return results

    fields = [
        "name",
        "posting_date",
        "employee",
        "employee_name",
        "leave_type",
        "status",
        "from_date",
        "to_date",
        "half_day",
        "half_day_date",
        "description",
        "total_leave_days",
        "leave_balance",
        "leave_approver",
        "creation",
    ]
    workflow_state_field = get_workflow_state_field("Leave Application")
    if workflow_state_field:
        fields.append(workflow_state_field)

    return _merge_reports_to_documents(results, "Leave Application", fields, workflow_state_field, limit)


@frappe.whitelist()
def get_shift_requests(
    employee: str, approver_id: str | None = None, for_approval: bool = False, limit: int | None = None
) -> list[dict]:
    from hrms.api import get_shift_requests as get_hrms_shift_requests, get_workflow_state_field

    results = get_hrms_shift_requests(
        employee=employee, approver_id=approver_id, for_approval=for_approval, limit=limit
    )
    if not for_approval:
        return results

    fields = [
        "name",
        "employee",
        "employee_name",
        "shift_type",
        "from_date",
        "to_date",
        "status",
        "approver",
        "docstatus",
        "creation",
    ]
    workflow_state_field = get_workflow_state_field("Shift Request")
    if workflow_state_field:
        fields.append(workflow_state_field)

    return _merge_reports_to_documents(results, "Shift Request", fields, workflow_state_field, limit)


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

    fields = ["attendance_date", "status", "late_entry", "in_time", "out_time"]
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
            "in_time": row.get("in_time"),
            "out_time": row.get("out_time"),
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
                "in_time": None,
                "out_time": None,
            }
        date = add_days(date, 1)

    return events


@frappe.whitelist()
def get_checkins_for_period(from_date: str, to_date: str) -> list[dict]:
    """
    Employee Checkin logs (IN/OUT) for the logged-in employee within the
    given date range, for the "Check-in Logs" box on the My Attendance tab.
    Each log's `attendance` field is set by hrms's auto attendance marking
    once it's consumed into a submitted Attendance record - the frontend
    uses that to highlight which logs were actually used.
    """
    from hrms.api import get_current_employee

    employee = get_current_employee()
    return frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]],
        },
        fields=["name", "log_type", "time", "attendance"],
        order_by="time asc",
    )


@frappe.whitelist()
def get_team_attendance_calendar_details(from_date: str, to_date: str) -> dict:
    """
    Per-day attendance issue breakdown (absent/late/short hours/missed punch)
    for the logged-in manager's direct reports, for the Team Calendar tab on
    the ESS Attendance dashboard. Unlike get_attendance_calendar_details
    (single employee, full day status incl. holidays), this only reports
    days/employees with an actual issue - a day with no entry here means
    nothing was flagged for anyone that day - so the frontend can render a
    green/red severity gradient per day without a separate "is everything
    okay" query. Manager-only, same reports_to gate as Team Requests /
    Overtime Slip (see can_approve_team_requests(), _get_direct_report_employees()).
    """
    reports = _get_direct_report_employees(frappe.session.user)
    if not reports:
        return {"total_employees": 0, "days": {}}

    employee_names = {
        row.name: row.employee_name
        for row in frappe.get_all(
            "Employee", filters={"name": ["in", reports]}, fields=["name", "employee_name"]
        )
    }

    attendance_meta = frappe.get_meta("Attendance")
    has_short_hours = attendance_meta.has_field("custom_short_hours")
    has_missed_punch = attendance_meta.has_field("custom_missed_punch")
    has_hours_difference = attendance_meta.has_field("custom_hours_difference")

    fields = ["employee", "attendance_date", "status", "late_entry", "in_time", "out_time"]
    if has_short_hours:
        fields.append("custom_short_hours")
    if has_missed_punch:
        fields.append("custom_missed_punch")
    if has_hours_difference:
        fields.append("custom_hours_difference")

    records = frappe.get_all(
        "Attendance",
        filters={
            "employee": ["in", reports],
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1,
        },
        fields=fields,
        ignore_permissions=True,
    )

    days = {}
    for row in records:
        date_str = str(row.attendance_date)
        day = days.setdefault(
            date_str,
            {"absent": [], "late": [], "short_hours": [], "missed_punch": [], "issue_employees": set()},
        )
        entry = {
            "employee": row.employee,
            "employee_name": employee_names.get(row.employee, row.employee),
            "in_time": row.get("in_time"),
            "out_time": row.get("out_time"),
            "hours_difference": row.get("custom_hours_difference") or 0,
        }

        # missed_punch is itself only ever set when status == Absent (see
        # sj_hr's _calculate_attendance_flags), so an absent-with-missed-punch
        # employee would otherwise land in both buckets - missed_punch is the
        # more specific/actionable category, so it takes priority and absent
        # only gets employees who are absent for some other reason.
        if has_missed_punch and cint(row.get("custom_missed_punch")):
            day["missed_punch"].append(entry)
            day["issue_employees"].add(row.employee)
        elif row.status == "Absent":
            day["absent"].append(entry)
            day["issue_employees"].add(row.employee)

        if cint(row.get("late_entry")):
            day["late"].append(entry)
            day["issue_employees"].add(row.employee)
        if has_short_hours and cint(row.get("custom_short_hours")):
            day["short_hours"].append(entry)
            day["issue_employees"].add(row.employee)

    for day in days.values():
        day["issue_count"] = len(day.pop("issue_employees"))

    return {"total_employees": len(reports), "days": days}


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
        Line Manager also qualifies here since sj_hr's reports_to workflow
        mechanism (workflow_reports_to.py) uses this role for the "Awaiting
        Line Manager Approval" transition on Attendance Request.
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
        {
            "parent": user,
            "role": ["in", ["System Manager", "HR Manager", "HR User", "Line Manager"]],
        },
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
def get_team_overtime_slips(limit: int | None = None) -> list[dict]:
    """
    Overtime Slips for the logged-in manager's direct reports, for the
    Overtime Slip tab on the ESS home screen. That tab is only shown to
    users who pass can_approve_team_requests() (same manager-only gate as
    Team Requests), and this is scoped to direct reports regardless of the
    caller's own read permissions on Overtime Slip - mirrors get_comments's
    ignore_permissions approach, since Overtime Slip's own permission model
    (System Manager/HR User/Leave Approver/Employee) has no reports_to
    concept to check against.
    """
    reports = _get_direct_report_employees(frappe.session.user)
    if not reports:
        return []

    return frappe.get_list(
        "Overtime Slip",
        fields=[
            "name",
            "employee",
            "employee_name",
            "posting_date",
            "start_date",
            "end_date",
            "total_overtime_duration",
            "docstatus",
            "creation",
        ],
        filters={"employee": ["in", reports]},
        order_by="creation desc",
        limit=limit,
        ignore_permissions=True,
    )


@frappe.whitelist()
def get_comments(reference_doctype: str, reference_name: str) -> list[dict]:
    """
    Comments on any document the logged-in user can read - e.g. HR asking for
    clarification on a submitted Attendance Request/Leave Application. The
    Comment doctype's own permissions only grant read access to System
    Manager/Website Manager (see comment.json), so a plain frappe.client
    list call returns nothing for a regular ESS user even though they can
    see the same comments in the desk timeline. This checks read access on
    the referenced document instead and fetches with ignore_permissions,
    mirroring how frappe.desk.form.load.get_docinfo (the desk timeline's own
    source) does it.
    """
    frappe.get_lazy_doc(reference_doctype, reference_name, check_permission=True)

    return frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "comment_type": "Comment",
        },
        fields=["name", "content", "comment_by", "comment_email", "creation"],
        order_by="creation asc",
        ignore_permissions=True,
    )


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
