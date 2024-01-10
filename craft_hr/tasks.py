import frappe
from craft_hr.events.get_leaves import get_earned_leave

def weekly():
    update_leave_allocations()

def daily():
    # Add script to reset leave allocations
    print("HERE DAILY")
    pass

def update_leave_allocations():
    get_earned_leave()