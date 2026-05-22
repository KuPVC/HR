import math
import frappe
from hrms.hr.doctype.leave_allocation.leave_allocation import get_carry_forwarded_leaves
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry

def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None):
    if not leave_distribution_template:
        return 0

    days_since_joining = frappe.utils.date_diff(allocation_start_date, date_of_joining)
    opening_years = math.ceil(days_since_joining / 365)
    opening_months = round(frappe.utils.date_diff(allocation_start_date, date_of_joining) / 365 * 12)

    if opening_years < 0 or opening_months < 0:
        frappe.throw(_("Leave Period from date should be after employee joining date"))

    month_array = {}
    cumulative_allocation = {}    
    template = frappe.get_doc('Leave Distribution Template', leave_distribution_template)

    # Check if leave allocation is 'Annually' or 'Monthly'
    if template.leave_allocation_type == "Annually":
        # Use the new leave_distribution_annual field for annual allocation
        annual_leaves = template.leave_distribution_annual
        
        # Calculate leaves based on the rounded-up number of years
        # This will assign full year's leave even for partial years
        leaves = annual_leaves * opening_years

    else:  # Monthly logic (existing behavior)
        for row in template.leave_distribution:
            if row.end != 0:  # Limited duration
                for i in range(row.start, row.end + 1):
                    month_array[i] = row.value_allocation
            else:  # Unlimited duration (Forever)
                month_array[row.start] = row.value_allocation
                month_array[row.end] = row.value_allocation

        # Calculate cumulative allocation for each month
        allocation = 0
        for i in range(1, max(list(month_array.keys())) + 1):
            allocation += month_array[i]
            cumulative_allocation[i] = allocation

        cumulative_allocation[0] = month_array[0]  # Monthly forever allocation
        max_months = max(list(cumulative_allocation.keys()))

        # Calculate the leaves for the employee based on the joining date and the current month
        leaves = 0
        if opening_months <= max_months:
            leaves = cumulative_allocation[opening_months]
        else:
            leaves = cumulative_allocation[max_months] + cumulative_allocation[0] * (opening_months - max_months)

    return leaves


def get_earned_leave(employee=None):
    filters = {
        'docstatus': 1,
        'custom_leave_distribution_template': ['is', 'set'],
        'custom_status': "Ongoing"
    }
    if employee:
        filters['employee'] = employee

    fields = [
        "name", "employee", "leave_type", "from_date", "to_date",
        "custom_date_of_joining", "custom_leave_distribution_template",
        "custom_opening_used_leaves"
    ]
    for la in frappe.db.get_all('Leave Allocation', filters, fields):
        if not la.custom_leave_distribution_template:
            continue

        earned_leaves = get_leaves(
            la.custom_date_of_joining, frappe.utils.today(), la.custom_leave_distribution_template
        )

        new_used_leaves = frappe.db.sql("""
            SELECT SUM(CASE
                        WHEN status = 'Half Day' THEN 0.5
                        WHEN status = 'On Leave' THEN 1
                        ELSE 0
                      END)
            FROM `tabAttendance`
            WHERE employee = %s
            AND leave_type = %s
            AND docstatus = 1
            AND attendance_date BETWEEN %s AND %s
        """, (la.employee, la.leave_type, la.from_date, la.to_date))[0][0] or 0

        frappe.db.set_value('Leave Allocation', la.name, {
            'new_leaves_allocated': earned_leaves - la.custom_opening_used_leaves,
            'total_leaves_allocated': earned_leaves,
            'custom_used_leaves': la.custom_opening_used_leaves + new_used_leaves,
            'custom_available_leaves': earned_leaves - la.custom_opening_used_leaves - new_used_leaves
        }, update_modified=False)

        frappe.db.sql("""
            DELETE FROM `tabLeave Ledger Entry`
            WHERE transaction_type = 'Leave Allocation'
              AND transaction_name = %s
              AND is_carry_forward = 0
              AND is_expired = 0
              AND docstatus = 1
        """, la.name)

        args = dict(
            leaves=earned_leaves - la.custom_opening_used_leaves,
            from_date=la.from_date,
            to_date=la.to_date,
            is_carry_forward=0
        )
        doc = frappe.get_doc('Leave Allocation', la.name)
        create_leave_ledger_entry(doc, args, submit=True)



@frappe.whitelist()
def get_carry_forwarded_leave(employee: str, leave_type: str, date: str, carry_forward: float | None = None) -> float:
    return get_carry_forwarded_leaves(employee, leave_type, date, carry_forward) or 0.0