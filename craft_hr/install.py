import frappe

def after_install():
    print("Creating UAE Annual Leave Distribution Template")
    document_details = {
        "title":"UAE Annual Leave Distribution",
        "maximum_leaves":0,
        "doctype":"Leave Distribution Template",
        "leave_distribution":[
        {"idx":1,"start":1,"end":5,"value_allocation":0},
        {"idx":2,"start":6,"end":6,"value_allocation":12},
        {"idx":3,"start":7,"end":11,"value_allocation":2},
        {"idx":4,"start":12,"end":12,"value_allocation":8},
        {"idx":5,"start":13,"end":0,"value_allocation":2.5}]
    }

    if not frappe.db.exists("Leave Distribution Template", document_details["title"]):
        doc=frappe.get_doc(document_details)
        doc.save()