import frappe
from craft_hr.events.get_leaves import get_earned_leave

def reset_leave_allocation():
    filters = {
        "reset_allocation_on_expiry":1,
        "to_date": frappe.utils.today(),
        "docstatus":"1",
    }
    allocations = frappe.db.get_all("Leave Allocation", filters=filters, pluck="name")
    for allocation_name in allocations:
        allocation = frappe.get_doc("Leave Allocation", allocation_name)
        new_allocation = frappe.copy_doc(allocation)
        new_allocation.from_date = frappe.utils.add_days(new_allocation.to_date, 1)
        new_allocation.to_date = frappe.utils.add_years(new_allocation.to_date, 1)
        new_allocation.new_leaves_allocated = new_allocation.reset_to
        new_allocation.insert(ignore_permissions=True)
        new_allocation.submit()

def update_leave_allocations():
    get_earned_leave()