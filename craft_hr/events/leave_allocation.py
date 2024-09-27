import frappe
from craft_hr.events.get_leaves import get_leaves, get_earned_leave

def before_save(doc, method):
    # TODO: use is_earned_leave from inside leave type for this logic
    if doc.custom_is_earned_leave:
        # Get the total leaves for both 'Monthly' and 'Annually' leave allocation types
        total_opening_leaves = get_leaves(doc.custom_date_of_joining, doc.from_date, doc.custom_leave_distribution_template) or 0

        # Update custom leave fields based on total earned leaves
        doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.new_leaves_allocated = doc.custom_opening_leaves
        doc.custom_available_leaves = doc.custom_opening_leaves

def before_submit(doc, method):
    if doc.custom_is_earned_leave:
        # Get the total leaves for both 'Monthly' and 'Annually' leave allocation types
        total_opening_leaves = get_leaves(doc.custom_date_of_joining, doc.from_date, doc.custom_leave_distribution_template) or 0

        # Update custom leave fields based on total earned leaves
        doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.new_leaves_allocated = doc.custom_opening_leaves
        doc.custom_available_leaves = doc.custom_opening_leaves

        # Fetch the earned leave balance for the employee
        get_earned_leave(doc.employee)

# This seems like a duplicate function, so we can merge the logic with the one above or keep it if it’s needed separately.
# But removing the extra before_submit definition.
# def before_submit(doc, method):
#     if doc.custom_is_earned_leave:
#         get_earned_leave(doc.employee)

# TODO: Make sure there is no leave application across the leave allocation after today's date before closing

@frappe.whitelist()
def close_allocation(docname):
    # Fetch the Leave Allocation document by name
    doc = frappe.get_doc("Leave Allocation", docname)

    # Ensure correct calculation of balance leave before closing the allocation
    get_earned_leave(doc.employee)

    # Update the status and set the 'to_date' as today's date
    doc.db_set("custom_status", "Closed")
    doc.db_set("to_date", frappe.utils.nowdate())