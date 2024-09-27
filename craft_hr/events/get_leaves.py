import math
import frappe
from hrms.hr.doctype.leave_allocation.leave_allocation import get_carry_forwarded_leaves

def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None):
    # Calculate the number of months or years since joining
    days_since_joining = frappe.utils.date_diff(allocation_start_date, date_of_joining)
    opening_years = math.ceil(days_since_joining / 365)  # Always round up for years
    opening_months = round(frappe.utils.date_diff(allocation_start_date, date_of_joining) / 365 * 12)

    if opening_years < 0 or opening_months < 0:
        frappe.throw("Leave Period from date should be after employee joining date")

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

    for la in frappe.db.get_list('Leave Allocation', filters):
        doc = frappe.get_doc('Leave Allocation', la.name)
        earned_leaves = get_leaves(doc.custom_date_of_joining, frappe.utils.today(), doc.custom_leave_distribution_template)
        new_used_leaves = frappe.db.count('Attendance', {
            'employee': doc.employee,
            'leave_type': doc.leave_type,
            'docstatus': 1,
            'attendance_date': ['between', [doc.from_date, doc.to_date]]
        })
        doc.new_leaves_allocated = earned_leaves - doc.custom_opening_used_leaves
        doc.custom_used_leaves = doc.custom_opening_used_leaves + new_used_leaves
        doc.custom_available_leaves = doc.new_leaves_allocated - new_used_leaves
        doc.save()


@frappe.whitelist()
def get_carry_forwarded_leave(employee, leave_type, date, carry_forward=None):
    # return get_carry_forwarded_leaves(employee, leave_type, date, carry_forward)
    pass