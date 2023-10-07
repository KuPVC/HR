import frappe
from craft_hr.events.get_leaves import get_earned_leave

def update_leave_allocations():
    get_earned_leave()