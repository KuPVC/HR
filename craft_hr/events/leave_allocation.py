import frappe
from craft_hr.events.get_leaves import get_leaves

def before_save(doc,method):
    # TODO: use is_earned_leave from inside leave type for this logic
    if doc.custom_is_earned_leave:
        total_opening_leaves = get_leaves(doc.custom_date_of_joining,doc.from_date, doc.custom_leave_distribution_template)
        doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.new_leaves_allocated = doc.custom_opening_leaves
        doc.custom_available_leaves = doc.custom_opening_leaves

def before_submit(doc,method):
    if doc.custom_is_earned_leave:
        total_opening_leaves = get_leaves(doc.custom_date_of_joining,doc.from_date, doc.custom_leave_distribution_template)
        doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.new_leaves_allocated = doc.custom_opening_leaves
        doc.custom_available_leaves = doc.custom_opening_leaves