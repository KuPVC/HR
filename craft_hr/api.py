import frappe
from frappe.utils import add_days, add_to_date, cint, date_diff, flt, get_datetime, getdate, nowdate


@frappe.whitelist()
def get_doctype_fields(doctype: str) -> list[dict]:
    """
    Same as hrms.api.get_doctype_fields, but also includes HTML fields.
    hrms's SUPPORTED_FIELD_TYPES allow-list excludes fieldtype "HTML"
    entirely, which silently drops fields like Attendance Request's
    custom_limit_balance_html before the ESS form ever sees them - FormView
    renders those via a named slot (see FormView.vue's Table/HTML slot
    handling), but the slot has nothing to match against if the field isn't
    in the list at all.
    """
    from hrms.api import get_doctype_fields as get_hrms_doctype_fields

    fields = get_hrms_doctype_fields(doctype)
    existing = {field.fieldname for field in fields}

    html_fields = [
        field
        for field in frappe.get_meta(doctype).fields
        if field.fieldtype == "HTML" and field.fieldname not in existing
    ]
    if not html_fields:
        return fields

    by_name = {field.fieldname: field for field in fields + html_fields}
    return [
        by_name[meta_field.fieldname]
        for meta_field in frappe.get_meta(doctype).fields
        if meta_field.fieldname in by_name
    ]


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


LEAVE_AND_ATTENDANCE_CREATOR_TABLES = ("Department Leave Creator", "Department Attendance Request Creator")
OVERTIME_CREATOR_TABLES = ("Department Overtime Slip Creator",)


def _get_creator_department_employees(
    user: str, creator_tables: tuple[str, ...] = LEAVE_AND_ATTENDANCE_CREATOR_TABLES
) -> list[str]:
    """
    Active employees of every Department where ``user`` is listed in one of
    the given Creators tables (the "Creators" section added by sj_hr).
    Empty if sj_hr's tables aren't installed or the user isn't a creator
    anywhere.
    """
    departments: set[str] = set()
    for child in creator_tables:
        if not frappe.db.table_exists(child):
            continue
        departments.update(
            frappe.get_all(child, filters={"user": user, "parenttype": "Department"}, pluck="parent")
        )
    if not departments:
        return []
    return frappe.get_all(
        "Employee", filters={"department": ["in", list(departments)], "status": "Active"}, pluck="name"
    )


def _get_team_calendar_employees(user: str) -> list[str]:
    """Team Calendar scope: direct reports plus the employees of any
    department the user is a creator for (deduplicated, order preserved)."""
    return list(
        dict.fromkeys(_get_direct_report_employees(user) + _get_creator_department_employees(user))
    )


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


def _dates_between(start, end):
    date = getdate(start)
    end = getdate(end)
    while date_diff(end, date) >= 0:
        yield date
        date = add_days(date, 1)


def _requests_by_date(employee: str, from_date: str, to_date: str) -> dict:
    """Existing Attendance Request / Leave Application docs (any non-cancelled
    docstatus, so pending drafts show up too) overlapping [from_date, to_date],
    exploded per calendar date they cover - lets the calendar popup show and
    link to a request/application an employee already placed for a date,
    instead of only ever offering to raise a new one."""
    requests_by_date = {}

    attendance_requests = frappe.get_all(
        "Attendance Request",
        filters={
            "employee": employee,
            "docstatus": ["<", 2],
            "from_date": ["<=", to_date],
            "to_date": [">=", from_date],
        },
        fields=["name", "from_date", "to_date", "docstatus"],
    )
    for req in attendance_requests:
        status = "Approved" if req.docstatus == 1 else "Pending"
        overlap_start = max(getdate(from_date), getdate(req.from_date))
        overlap_end = min(getdate(to_date), getdate(req.to_date))
        for date in _dates_between(overlap_start, overlap_end):
            requests_by_date.setdefault(str(date), []).append(
                {"doctype": "Attendance Request", "name": req.name, "status": status}
            )

    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "docstatus": ["<", 2],
            "from_date": ["<=", to_date],
            "to_date": [">=", from_date],
        },
        fields=["name", "from_date", "to_date", "status"],
    )
    for leave in leave_applications:
        overlap_start = max(getdate(from_date), getdate(leave.from_date))
        overlap_end = min(getdate(to_date), getdate(leave.to_date))
        for date in _dates_between(overlap_start, overlap_end):
            requests_by_date.setdefault(str(date), []).append(
                {"doctype": "Leave Application", "name": leave.name, "status": leave.status}
            )

    return requests_by_date


@frappe.whitelist()
def get_attendance_calendar_details(from_date: str, to_date: str) -> dict:
    """
    Attendance calendar events enriched with late entry / short hours / missed
    punch flags (mirrors the flags used by sj_hr's Monthly Attendance Sheet
    report) for the logged-in employee, for the given date range. Also
    attaches any existing Attendance Request / Leave Application already
    placed for each date, so the calendar popup can show and link to it
    instead of only ever offering to raise a new one.
    """
    from hrms.api import get_current_employee, get_holidays_for_calendar

    employee = get_current_employee()
    holidays = get_holidays_for_calendar(employee, from_date, to_date)
    requests_by_date = _requests_by_date(employee, from_date, to_date)

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
        elif date_str in requests_by_date:
            # No Attendance/Holiday for this date, but a request already
            # covers it (e.g. a pending Leave Application for a future or
            # not-yet-processed date) - still worth surfacing in the popup.
            events[date_str] = {
                "status": None,
                "late_entry": 0,
                "short_hours": 0,
                "missed_punch": 0,
                "hours_difference": 0,
                "in_time": None,
                "out_time": None,
            }
        date = add_days(date, 1)

    for date_str, event in events.items():
        event["requests"] = requests_by_date.get(date_str, [])

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
    Per-day attendance breakdown: issues (absent/late/short hours/missed punch)
    plus a "no_issues" list of everyone with attendance recorded and nothing
    flagged. Originally issues only; the old note below about days with no
    entry still holds for days with no attendance at all.
    for the logged-in manager's direct reports and the employees of any
    department they are a Leave Application / Attendance Request Creator for
    (see _get_team_calendar_employees), for the Team Calendar tab on
    the ESS Attendance dashboard. Unlike get_attendance_calendar_details
    (single employee, full day status incl. holidays), this only reports
    days/employees with an actual issue - a day with no entry here means
    nothing was flagged for anyone that day - so the frontend can render a
    green/red severity gradient per day without a separate "is everything
    okay" query. Manager-only, same reports_to gate as Team Requests /
    Overtime Slip (see can_approve_team_requests(), _get_direct_report_employees()).
    """
    checked_dates = [
        str(row)
        for row in frappe.get_all(
            "Team Calendar Check",
            filters={"user": frappe.session.user, "date": ["between", [from_date, to_date]]},
            pluck="date",
        )
    ]

    reports = _get_team_calendar_employees(frappe.session.user)
    if not reports:
        return {"total_employees": 0, "days": {}, "checked_dates": checked_dates}

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

    fields = ["name", "employee", "attendance_date", "status", "late_entry", "in_time", "out_time"]
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
            {
                "absent": [],
                "late": [],
                "short_hours": [],
                "missed_punch": [],
                "no_issues": [],
                "issue_employees": set(),
            },
        )
        entry = {
            "employee": row.employee,
            "employee_name": employee_names.get(row.employee, row.employee),
            "status": row.status,
            "attendance": row.name,
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

        # Attendance recorded and nothing flagged: goes in the "No Issues" list.
        if row.employee not in day["issue_employees"]:
            day["no_issues"].append(entry)

    for day in days.values():
        day["issue_count"] = len(day.pop("issue_employees"))

    return {"total_employees": len(reports), "days": days, "checked_dates": checked_dates}


@frappe.whitelist()
def set_team_calendar_date_checked(date: str, checked: int = 1) -> dict:
    """Tick / untick a date as "checked" in the current user's Team Calendar.
    A personal progress marker only - it changes nothing on any record."""
    if not can_view_team_calendar():
        frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

    date = str(getdate(date))
    name = f"{frappe.session.user}-{date}"
    exists = frappe.db.exists("Team Calendar Check", name)
    if cint(checked) and not exists:
        frappe.get_doc({"doctype": "Team Calendar Check", "user": frappe.session.user, "date": date}).insert(
            ignore_permissions=True
        )
    elif not cint(checked) and exists:
        frappe.delete_doc("Team Calendar Check", name, ignore_permissions=True, force=True)
    return {"date": date, "checked": cint(checked)}


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
def can_view_team_calendar() -> bool:
    """Whether the Team Calendar tab should show: anyone who can approve team
    requests, plus department Creators (who see their departments' staff)."""
    return bool(can_approve_team_requests() or _get_creator_department_employees(frappe.session.user))


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

    slips = frappe.get_list(
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
            "workflow_state",
            "creation",
        ],
        filters={"employee": ["in", reports]},
        order_by="creation desc",
        limit=limit,
        ignore_permissions=True,
    )
    styles = _workflow_state_styles(slip.workflow_state for slip in slips)
    for slip in slips:
        slip["state_style"] = styles.get(slip.workflow_state)
    return slips


def _workflow_state_styles(states) -> dict:
    """{workflow_state: style} (Success/Danger/Warning/Primary/Info/Inverse)
    for the given Workflow State names."""
    states = [state for state in set(states) if state]
    if not states:
        return {}
    return {
        row.name: row.style
        for row in frappe.get_all("Workflow State", filters={"name": ["in", states]}, fields=["name", "style"])
    }


def _get_payroll_period(offset: int = 0) -> tuple:
    """Salary period (start, end) containing today, shifted by ``offset``
    periods. Uses Attendance Notification Settings' Payroll Start/End Day
    (25 -> 24 by default), the same convention as the notification digests."""
    from datetime import date

    from frappe.utils import add_months, get_last_day

    start_day, end_day = 25, 24
    if frappe.db.exists("DocType", "Attendance Notification Settings"):
        start_day = cint(frappe.db.get_single_value("Attendance Notification Settings", "payroll_start_day")) or 25
        end_day = cint(frappe.db.get_single_value("Attendance Notification Settings", "payroll_end_day")) or 24

    today = getdate(nowdate())
    month_anchor = date(today.year, today.month, 1)
    if today.day < start_day:
        month_anchor = add_months(month_anchor, -1)
    month_anchor = add_months(month_anchor, cint(offset))

    start = date(month_anchor.year, month_anchor.month, min(start_day, get_last_day(month_anchor).day))
    end_month = add_months(month_anchor, 1) if end_day < start_day else month_anchor
    end = date(end_month.year, end_month.month, min(end_day, get_last_day(end_month).day))
    return start, end


def _get_overtime_team_employees(user: str) -> list[str]:
    """Employees whose Overtime Slips the user sees as 'team': direct reports
    plus the employees of departments where the user is an Overtime Slip
    Creator (never the user's own employee)."""
    own = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    team = _get_direct_report_employees(user) + _get_creator_department_employees(user, OVERTIME_CREATOR_TABLES)
    return [emp for emp in dict.fromkeys(team) if emp != own]


@frappe.whitelist()
def get_overtime_overview(offset: int = 0) -> dict:
    """
    Overtime Slips for one salary period, for the Overtime section of the ESS
    Attendance dashboard: the user's own slips, and (if they have a team) the
    slips of their team grouped by employee, each with its in-period overtime
    rows, plus a per-day roll-up (who has overtime on which day).

    "Team" = direct reports plus employees of departments the user is an
    Overtime Slip Creator for. Scoped here rather than by the caller's read
    permissions, like get_team_overtime_slips (Overtime Slip has no
    reports_to concept of its own).
    """
    user = frappe.session.user
    start, end = _get_payroll_period(offset)
    own = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    team_ids = _get_overtime_team_employees(user)

    result = {
        "period_start": str(start),
        "period_end": str(end),
        "offset": cint(offset),
        "employee": own,
        "has_team": bool(team_ids),
        "self": {"slips": [], "total_hours": 0, "daily": {}},
        "team": {"employees": [], "total_hours": 0, "daily": {}},
    }

    scope = ([own] if own else []) + team_ids
    if not scope:
        return result

    slips = frappe.get_all(
        "Overtime Slip",
        filters={
            "employee": ["in", scope],
            "docstatus": ["<", 2],
            "start_date": ["<=", end],
            "end_date": [">=", start],
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "start_date",
            "end_date",
            "total_overtime_duration",
            "docstatus",
            "workflow_state",
            "creation",
        ],
        order_by="start_date asc, creation asc",
        ignore_permissions=True,
    )
    details_by_slip: dict[str, list[dict]] = {}
    if slips:
        for row in frappe.get_all(
            "Overtime Details",
            filters={
                "parent": ["in", [slip.name for slip in slips]],
                "parenttype": "Overtime Slip",
                "date": ["between", [start, end]],
            },
            fields=["parent", "date", "overtime_type", "overtime_duration"],
            order_by="date asc",
            ignore_permissions=True,
        ):
            details_by_slip.setdefault(row.parent, []).append(
                {
                    "date": str(row.date),
                    "overtime_type": row.overtime_type,
                    "hours": flt(row.overtime_duration, 2),
                }
            )

    state_styles = _workflow_state_styles(slip.workflow_state for slip in slips)
    team_groups: dict[str, dict] = {}
    for slip in slips:
        details = details_by_slip.get(slip.name, [])
        hours = flt(sum(d["hours"] for d in details), 2)
        item = {
            "name": slip.name,
            "employee": slip.employee,
            "employee_name": slip.employee_name,
            "start_date": str(slip.start_date),
            "end_date": str(slip.end_date),
            "docstatus": slip.docstatus,
            "workflow_state": slip.workflow_state,
            "state_style": state_styles.get(slip.workflow_state),
            "total_hours": flt(slip.total_overtime_duration, 2),
            "period_hours": hours,
            "details": details,
        }
        bucket = result["self"] if slip.employee == own else result["team"]
        if slip.employee == own:
            bucket["slips"].append(item)
        else:
            group = team_groups.setdefault(
                slip.employee,
                {"employee": slip.employee, "employee_name": slip.employee_name, "total_hours": 0, "slips": []},
            )
            group["slips"].append(item)
            group["total_hours"] = flt(group["total_hours"] + hours, 2)
        bucket["total_hours"] = flt(bucket["total_hours"] + hours, 2)

        for detail in details:
            day = bucket["daily"].setdefault(detail["date"], {})
            entry = day.setdefault(
                slip.employee, {"employee": slip.employee, "employee_name": slip.employee_name, "hours": 0}
            )
            entry["hours"] = flt(entry["hours"] + detail["hours"], 2)

    # daily: {date: [{employee, employee_name, hours}, ...]}
    for bucket in (result["self"], result["team"]):
        bucket["daily"] = {
            day: sorted(entries.values(), key=lambda e: e["employee_name"] or e["employee"])
            for day, entries in sorted(bucket["daily"].items())
        }
    result["team"]["employees"] = sorted(team_groups.values(), key=lambda g: g["employee_name"] or g["employee"])
    return result


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


ATTENDANCE_DASHBOARD_ROLES = ["HR Manager", "IT Admin", "System Manager"]


def has_attendance_dashboard_access() -> bool:
    """Used as add_to_apps_screen's has_permission hook for the dashboard tile."""
    return bool(set(frappe.get_roles()) & set(ATTENDANCE_DASHBOARD_ROLES))


def assert_attendance_dashboard_access():
    if not set(frappe.get_roles()) & set(ATTENDANCE_DASHBOARD_ROLES):
        frappe.throw(
            frappe._("Not permitted to view the attendance dashboard"),
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_attendance_dashboard_companies() -> list[str]:
    assert_attendance_dashboard_access()
    return frappe.get_all("Company", pluck="name", order_by="name asc")


@frappe.whitelist()
def get_attendance_dashboard_data(
    period: str = "Daily",
    date: str | None = None,
    company: str | None = None,
    status: str | None = None,
) -> dict:
    """
    Company-wide attendance report for the HR attendance dashboard: one row
    per employee for the selected period, with status, short hours and leave
    type (approved/pending), matching the "UAE Group HR Attendance
    Dashboard" artifact this page was built to replicate inside the app.
    """
    assert_attendance_dashboard_access()

    date = getdate(date) if date else getdate(nowdate())
    if period == "Weekly":
        from_date = add_days(date, -date.weekday())
        to_date = add_days(from_date, 6)
    elif period == "Monthly":
        from_date = date.replace(day=1)
        to_date = add_days(add_to_date(from_date, months=1), -1)
    else:
        from_date = to_date = date

    employee_filters = {"status": "Active"}
    if company:
        employee_filters["company"] = company

    employees = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=["name", "employee_name", "designation", "company"],
        order_by="employee_name asc",
    )
    if not employees:
        return {"from_date": from_date, "to_date": to_date, "rows": []}

    employee_names = [e.name for e in employees]

    attendance_meta = frappe.get_meta("Attendance")
    has_short_hours = attendance_meta.has_field("custom_short_hours")

    attendance_fields = ["employee", "attendance_date", "status"]
    if has_short_hours:
        attendance_fields.append("custom_short_hours")

    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "employee": ["in", employee_names],
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1,
        },
        fields=attendance_fields,
    )

    leave_records = frappe.get_all(
        "Leave Application",
        filters={
            "employee": ["in", employee_names],
            "from_date": ["<=", to_date],
            "to_date": [">=", from_date],
            "docstatus": ["in", [0, 1]],
            "status": ["in", ["Open", "Approved"]],
        },
        fields=["employee", "leave_type", "status"],
    )
    leave_by_employee = {}
    for row in leave_records:
        leave_by_employee.setdefault(row.employee, []).append(row)

    by_employee = {}
    for row in attendance_records:
        bucket = by_employee.setdefault(
            row.employee,
            {"statuses": set(), "short_hours": 0},
        )
        bucket["statuses"].add(row.status)
        if has_short_hours and cint(row.get("custom_short_hours")):
            bucket["short_hours"] += 1

    rows = []
    for employee in employees:
        bucket = by_employee.get(employee.name, {"statuses": set(), "short_hours": 0})
        leaves = leave_by_employee.get(employee.name, [])

        if leaves:
            emp_status = "On Leave"
        elif "Absent" in bucket["statuses"]:
            emp_status = "Absent"
        elif bucket["short_hours"]:
            emp_status = "Short Hours"
        elif bucket["statuses"]:
            emp_status = "Present"
        else:
            emp_status = "No Record"

        if status and status != "All" and emp_status != status:
            continue

        rows.append(
            {
                "employee": employee.name,
                "employee_name": employee.employee_name,
                "designation": employee.designation,
                "company": employee.company,
                "status": emp_status,
                "short_hours": bucket["short_hours"],
                "leave_type": leaves[0].leave_type if leaves else None,
                "leave_status": leaves[0].status if leaves else None,
            }
        )

    return {"from_date": from_date, "to_date": to_date, "rows": rows}


import re

STATUS_KEY = {
    "Present": "present",
    "Work From Home": "wfh",
    "Half Day": "half_day",
    "On Leave": "on_leave",
    "Absent": "absent",
    "Missed Punch": "missed_punch",
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _get_roster_and_companies():
    """Shared by get_attendance_dashboard_bundle and get_sick_leave_year_data."""
    companies = frappe.get_all(
        "Company",
        fields=["name", "default_holiday_list"],
        order_by="name asc",
    )

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "company", "holiday_list"],
    )
    employee_by_id = {e.name: e for e in employees}

    active_by_company = {}
    for e in employees:
        active_by_company[e.company] = active_by_company.get(e.company, 0) + 1

    company_slugs = {c.name: _slugify(c.name) for c in companies}
    company_list_out = [
        {
            "company": c.name,
            "slug": company_slugs[c.name],
            "display_name": c.name,
            "active_employees": active_by_company.get(c.name, 0),
        }
        for c in companies
    ]

    return companies, employee_by_id, company_slugs, company_list_out


@frappe.whitelist()
def get_sick_leave_year_data(
    year: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    """
    Sick leave pattern data for either a single calendar year or an
    explicit custom date range, independent of the attendance dashboard's
    rolling ~200-day window - the pattern view needs a fixed period the
    user can flip between years on (or pick exactly), not a moving
    lookback window.

    Pass either `year`, or both `from_date`/`to_date` - explicit dates take
    precedence when given.
    """
    assert_attendance_dashboard_access()

    today = getdate(nowdate())
    if from_date and to_date:
        from_date = str(getdate(from_date))
        to_date = str(min(getdate(to_date), today))
        year = None
    else:
        year = cint(year) or today.year
        from_date = f"{year}-01-01"
        to_date = f"{year}-12-31" if year < today.year else str(today)

    _companies, employee_by_id, company_slugs, company_list_out = _get_roster_and_companies()
    employee_ids = list(employee_by_id.keys())

    leave_applications = (
        frappe.get_all(
            "Leave Application",
            filters={
                "employee": ["in", employee_ids],
                "to_date": [">=", from_date],
                "from_date": ["<=", to_date],
                "docstatus": ["in", [0, 1]],
                "status": ["in", ["Open", "Approved"]],
            },
            fields=["employee", "from_date", "to_date", "leave_type", "status", "half_day"],
        )
        if employee_ids
        else []
    )

    roster = [
        {
            "employee": e.name,
            "name": e.employee_name,
            "designation": e.designation,
            "company_slug": company_slugs.get(e.company, _slugify(e.company or "")),
        }
        for e in employee_by_id.values()
    ]

    return {
        "year": year,
        "from_date": from_date,
        "to_date": to_date,
        "companies": company_list_out,
        "employees": roster,
        "leave_applications": [
            {
                "employee": row.employee,
                "from_date": str(row.from_date),
                "to_date": str(row.to_date),
                "leave_type": row.leave_type,
                "status": row.status,
                "half_day": bool(row.half_day),
            }
            for row in leave_applications
        ],
    }


@frappe.whitelist()
def get_attendance_dashboard_bundle(days: int = 200) -> dict:
    """
    Everything the HR attendance dashboard needs in one call: per-day
    per-employee attendance (bucketed like the reference dashboard),
    company roster/headcounts, leave applications, and holiday/weekly-off
    context - mirrors the shape of the "UAE Group HR Attendance Dashboard"
    artifact (attendance_days / meta/companies / meta/holidays /
    meta/leave_applications), but pulled live from ERPNext instead of a
    separately-synced database.
    """
    assert_attendance_dashboard_access()

    days = cint(days) or 200
    # Attendance for "today" isn't marked until end of day, so cap the
    # window at yesterday to avoid showing a misleadingly empty/incomplete
    # current day as if it were real data.
    to_date = add_days(getdate(nowdate()), -1)
    from_date = add_days(to_date, -days)

    companies, employee_by_id, company_slugs, company_list_out = _get_roster_and_companies()
    employee_ids = list(employee_by_id.keys())

    attendance = (
        frappe.get_all(
            "Attendance",
            filters={
                "employee": ["in", employee_ids],
                "attendance_date": ["between", [from_date, to_date]],
                "docstatus": 1,
            },
            fields=[
                "employee", "attendance_date", "status",
                "late_entry", "custom_missed_punch", "custom_short_hours", "custom_hours_difference",
            ],
        )
        if employee_ids
        else []
    )
    attendance_meta = frappe.get_meta("Attendance")
    has_hours_field = attendance_meta.has_field("custom_hours_difference")
    has_missed_punch_field = attendance_meta.has_field("custom_missed_punch")
    has_short_hours_field = attendance_meta.has_field("custom_short_hours")
    has_late_entry_field = attendance_meta.has_field("late_entry")

    by_date = {}
    for row in attendance:
        emp = employee_by_id.get(row.employee)
        if not emp:
            continue

        # An Attendance record only has a single check-in log (no check-out)
        # gets auto-marked "Absent" by the checkin->attendance sync, same as
        # a genuine no-show. custom_missed_punch distinguishes the two, so
        # surface it as its own status instead of inflating the Absent count.
        is_missed_punch = bool(has_missed_punch_field and row.get("custom_missed_punch"))
        effective_status = "Missed Punch" if row.status == "Absent" and is_missed_punch else row.status

        sk = STATUS_KEY.get(effective_status)
        if not sk:
            continue

        date_key = str(row.attendance_date)
        hours_short = flt(row.custom_hours_difference) if has_hours_field else 0
        is_short_hours = bool(has_short_hours_field and row.get("custom_short_hours"))
        by_date.setdefault(date_key, []).append(
            {
                "employee": row.employee,
                "name": emp.employee_name,
                "designation": emp.designation,
                "company_slug": company_slugs.get(emp.company, _slugify(emp.company or "")),
                "status": effective_status,
                "late_entry": bool(has_late_entry_field and row.get("late_entry")),
                "short_hours": is_short_hours,
                "hours_short": abs(hours_short) if is_short_hours and hours_short else None,
            }
        )
    attendance_days = [{"date": d, "employees": rows} for d, rows in sorted(by_date.items())]

    leave_applications = (
        frappe.get_all(
            "Leave Application",
            filters={
                "employee": ["in", employee_ids],
                "to_date": [">=", from_date],
                "from_date": ["<=", to_date],
                "docstatus": ["in", [0, 1]],
                "status": ["in", ["Open", "Approved"]],
            },
            fields=["employee", "from_date", "to_date", "leave_type", "status", "half_day"],
        )
        if employee_ids
        else []
    )

    holiday_lists = {c.default_holiday_list for c in companies if c.default_holiday_list}
    holiday_lists |= {e.holiday_list for e in employee_by_id.values() if e.holiday_list}
    weekly_off_by_list = {}
    named_holidays = []
    if holiday_lists:
        holiday_rows = frappe.get_all(
            "Holiday",
            filters={"parent": ["in", list(holiday_lists)]},
            fields=["parent", "holiday_date", "weekly_off", "description"],
        )
        weekday_counts_by_list = {}
        for row in holiday_rows:
            if row.weekly_off:
                dow = getdate(row.holiday_date).strftime("%A")
                counts = weekday_counts_by_list.setdefault(row.parent, {})
                counts[dow] = counts.get(dow, 0) + 1
            elif from_date <= getdate(row.holiday_date) <= to_date:
                named_holidays.append({"date": str(row.holiday_date), "name": row.description or "Holiday"})
        for list_name, counts in weekday_counts_by_list.items():
            weekly_off_by_list[list_name] = max(counts, key=counts.get)

    company_holiday_list = {
        company_slugs[c.name]: c.default_holiday_list for c in companies if c.default_holiday_list
    }

    roster = [
        {
            "employee": e.name,
            "name": e.employee_name,
            "designation": e.designation,
            "company_slug": company_slugs.get(e.company, _slugify(e.company or "")),
        }
        for e in employee_by_id.values()
    ]

    return {
        "companies": company_list_out,
        "employees": roster,
        "attendance_days": attendance_days,
        "leave_applications": [
            {
                "employee": row.employee,
                "from_date": str(row.from_date),
                "to_date": str(row.to_date),
                "leave_type": row.leave_type,
                "status": row.status,
                "half_day": bool(row.half_day),
            }
            for row in leave_applications
        ],
        "holidays": {
            "weekly_off_by_list": weekly_off_by_list,
            "company_list": company_holiday_list,
            "named": named_holidays,
        },
        "last_pull_at": frappe.utils.now_datetime().isoformat(),
    }


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
