import frappe
from craft_hr.events.leave_allocation import get_leaves

def get_earned_leave():
    for la in frappe.db.get_list('Leave Allocation',{'docstatus':1, 'custom_leave_distribution_template':['is','set']}):
        doc = frappe.get_doc('Leave Allocation', la.name)
        earned_leaves = get_leaves(doc.custom_date_of_joining,frappe.utils.today(), doc.custom_leave_distribution_template)
        new_used_leaves = frappe.db.count('Attendance',{'leave_type':doc.leave_type,'docstatus':1,'attendance_date':['between',[doc.from_date,doc.to_date]]})
        doc.new_leaves_allocated = earned_leaves - doc.custom_opening_used_leaves
        doc.custom_used_leaves = doc.custom_opening_used_leaves + new_used_leaves
        doc.custom_available_leaves = doc.new_leaves_allocated - new_used_leaves
        doc.save()