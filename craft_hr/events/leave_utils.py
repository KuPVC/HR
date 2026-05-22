import frappe
from frappe import _
from dateutil.relativedelta import relativedelta

def update_leave_entitlement_on_save(doc, method):
    """
    Hook function to be called when Leave Application is saved
    Add this to hooks.py:
    
    doc_events = {
        "Leave Application": {
            "before_save": "craft_hr.craft_hr.utils.leave_utils.update_leave_entitlement_on_save"
        }
    }
    """
    if doc.employee and doc.from_date:
        entitlement = calculate_leave_entitlement(doc.employee, doc.from_date, doc.leave_type)
        doc.custom_leave_entitlement_as_of_leave_start_date = entitlement

@frappe.whitelist()
def calculate_leave_entitlement(employee, from_date, leave_type=None):
    """
    Calculate leave entitlement for an employee as of a specific date
    
    Args:
        employee (str): Employee ID
        from_date (str): Date to calculate entitlement as of
        leave_type (str): Leave type to consider for used leaves
    
    Returns:
        float: Final leave entitlement after deducting used leaves
    """
    try:
        # Get employee's date of joining
        employee_doc = frappe.get_doc("Employee", employee)
        if not employee_doc.date_of_joining:
            frappe.throw(_("Date of Joining not found for employee {0}").format(employee))
        
        date_of_joining = employee_doc.date_of_joining
        from_date = frappe.utils.getdate(from_date)
        
        # Calculate months of service
        months = calculate_months_of_service(date_of_joining, from_date)
        
        # Calculate total entitlement based on months of service
        if months < 12:
            total_entitlement = months * 2
        else:
            total_entitlement = months * 2.5
        
        # Get custom used leaves from Leave Allocation
        custom_used_leaves = 0
        if leave_type:
            custom_used_leaves = get_custom_used_leaves(employee, leave_type)
        
        # Calculate final entitlement
        final_entitlement = total_entitlement - custom_used_leaves
        
        frappe.logger().info(f"Leave entitlement calculation for {employee}: "
                           f"Months: {months}, Total: {total_entitlement}, "
                           f"Used: {custom_used_leaves}, Final: {final_entitlement}")
        
        return final_entitlement
        
    except Exception as e:
        frappe.logger().error(f"Error calculating leave entitlement: {str(e)}")
        frappe.throw(_("Error calculating leave entitlement: {0}").format(str(e)))

def calculate_months_of_service(date_of_joining, from_date):
    """
    Calculate months of service between two dates
    
    Args:
        date_of_joining (date): Employee's joining date
        from_date (date): Date to calculate months until
    
    Returns:
        int: Number of complete months
    """
    if isinstance(date_of_joining, str):
        date_of_joining = frappe.utils.getdate(date_of_joining)
    if isinstance(from_date, str):
        from_date = frappe.utils.getdate(from_date)
    
    # Calculate the difference
    rd = relativedelta(from_date, date_of_joining)
    months = rd.years * 12 + rd.months
    
    return months

def get_custom_used_leaves(employee, leave_type):
    """
    Get custom used leaves from Leave Allocation
    
    Args:
        employee (str): Employee ID
        leave_type (str): Leave type
    
    Returns:
        float: Custom used leaves
    """
    try:
        leave_allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": leave_type,
                "docstatus": 1  # Only consider submitted allocations
            },
            fields=["custom_used_leaves"],
            order_by="creation desc",
            limit=1
        )
        
        if leave_allocations:
            return leave_allocations[0].get("custom_used_leaves", 0) or 0
        
        return 0
        
    except Exception:
        frappe.logger().error("Error fetching custom used leaves", exc_info=True)
        return 0

# Alternative approach using property setter or custom field update
@frappe.whitelist()
def update_leave_entitlement_field(employee, from_date, leave_type=None):
    """
    Standalone method to update leave entitlement field
    Can be called via frappe.call from client side if needed
    """
    entitlement = calculate_leave_entitlement(employee, from_date, leave_type)
    return {
        "custom_leave_entitlement_as_of_leave_start_date": entitlement,
        "months_of_service": calculate_months_of_service(
            frappe.get_value("Employee", employee, "date_of_joining"),
            frappe.utils.getdate(from_date)
        )
    }