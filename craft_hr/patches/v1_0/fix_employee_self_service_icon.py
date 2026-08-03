import frappe


def execute():
    """
    The Employee Self Service Workspace has been superseded by the standalone
    /ess frontend. Remove the old workspace (if it still exists from a
    previous install), point the Desktop Icon tile at /ess directly with a
    distinct accent color, remove duplicate desktop icon tiles left over
    from earlier setup, and normalize Financial Audit's tile color.
    """
    if frappe.db.exists("Workspace", "Employee Self Service"):
        frappe.delete_doc(
            "Workspace",
            "Employee Self Service",
            force=True,
            ignore_permissions=True,
        )

    if frappe.db.exists("Desktop Icon", "Employee Self Service"):
        frappe.db.set_value(
            "Desktop Icon",
            "Employee Self Service",
            {
                "link_type": "External",
                "link": "/ess",
                "link_to": None,
                "bg_color": "purple",
            },
            update_modified=False,
        )
    else:
        frappe.get_doc(
            {
                "doctype": "Desktop Icon",
                "label": "Employee Self Service",
                "icon_type": "Link",
                "link_type": "External",
                "link": "/ess",
                "standard": 0,
                "hidden": 0,
                "icon": "share-people",
                "bg_color": "purple",
            }
        ).insert(ignore_permissions=True)

    # duplicate low-fidelity tiles created alongside the real "Home" and
    # "Smart Importer" standard icons
    for duplicate_icon in ("fa-home", "smart-importer"):
        if frappe.db.exists("Desktop Icon", duplicate_icon):
            frappe.delete_doc(
                "Desktop Icon",
                duplicate_icon,
                force=True,
                ignore_permissions=True,
            )

    if frappe.db.exists("Desktop Icon", "Financial Audit"):
        frappe.db.set_value(
            "Desktop Icon", "Financial Audit", "bg_color", "blue", update_modified=False
        )

    frappe.db.commit()
