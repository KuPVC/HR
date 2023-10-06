import frappe

def before_save(doc,method):
    print("Before Save")
    print("****************************")
    total_opening_leaves = get_leaves(doc.custom_date_of_joining,doc.from_date, doc.custom_leave_distribution_template)
    doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
    doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
    doc.new_leaves_allocated = doc.custom_opening_leaves
    doc.custom_available_leaves = doc.custom_opening_leaves

def before_submit(doc,method):
    print("Before Submit")
    print("****************************")
    total_opening_leaves = get_leaves(doc.custom_date_of_joining,doc.from_date, doc.custom_leave_distribution_template)
    doc.custom_used_leaves   = total_opening_leaves - doc.custom_opening_leaves
    doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
    doc.new_leaves_allocated = doc.custom_opening_leaves
    doc.custom_available_leaves = doc.custom_opening_leaves


def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None):
    opening_months = round(frappe.utils.date_diff(allocation_start_date, date_of_joining)/365 * 12)
    month_array = {}
    cumulative_allocation = {}    
    template = frappe.get_doc('Leave Distribution Template',leave_distribution_template)
    for row in template.leave_distribution:
        if row.end != 0:
            n = 0
            for i in range(row.start,row.end+1,1):
                month_array[i] = row.monthly_allocation
        else:
            month_array[row.start] = row.monthly_allocation
            month_array[row.end] =  row.monthly_allocation
    
    allocation = 0
    for i in range(1,max(list(month_array.keys()))+1,1):
        allocation = allocation + month_array[i]
        cumulative_allocation[i] = allocation
    cumulative_allocation[0] = month_array[0]
    
    max_months = max(list(cumulative_allocation.keys()))
    leaves = 0
    if opening_months <= max(list(month_array.keys())):
        leaves = cumulative_allocation[opening_months]
    
    else:
        leaves = cumulative_allocation[max_months] + cumulative_allocation[0] * (opening_months - max_months)
    return leaves








