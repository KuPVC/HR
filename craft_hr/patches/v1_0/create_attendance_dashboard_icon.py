import frappe


def execute():
    """
    Add the HR Attendance Dashboard (/attendance-dashboard) as a Desktop
    Icon nested under the "Frappe HR" app tile, alongside its other
    sub-icons like "Shift & Attendance" - same pattern as
    fix_employee_self_service_icon.py used for the top-level ESS tile.
    Visibility is restricted to HR Manager / IT Admin via the icon's
    roles table, matching craft_hr.api.ATTENDANCE_DASHBOARD_ROLES.

    frappe.desk.doctype.desktop_icon.desktop_icon.get_desktop_icons()
    only shows a non-Folder/non-App Desktop Icon when a Workspace Sidebar
    of the *same name* exists with at least one item that
    WorkspaceSidebar.is_item_allowed() permits - this is the single
    source of truth it uses for "does this tile have anything behind it",
    regardless of the icon's own link_type. Employee Self Service's tile
    only renders because a matching "Employee Self Service" Workspace
    Sidebar exists; without a same-named sidebar here, this icon is
    silently dropped from frappe.boot.desktop_icons every time. A "URL"
    link_type item is always allowed (is_item_allowed hard-codes True for
    "url"/"help"), so it satisfies that check without duplicating the
    role gate - that's still enforced by the Desktop Icon's own roles
    table below.
    """
    icon_name = "HR Attendance Dashboard"

    if not frappe.db.exists("Workspace Sidebar", icon_name):
        frappe.get_doc(
            {
                "doctype": "Workspace Sidebar",
                "title": icon_name,
                "items": [
                    {
                        "label": "Attendance Dashboard",
                        "type": "Link",
                        "link_type": "URL",
                        "url": "/attendance-dashboard",
                    }
                ],
            }
        ).insert(ignore_permissions=True)

    if frappe.db.exists("Desktop Icon", icon_name):
        doc = frappe.get_doc("Desktop Icon", icon_name)
    else:
        doc = frappe.new_doc("Desktop Icon")
        doc.label = icon_name
        doc.icon_type = "Link"
        doc.link_type = "External"
        doc.link = "/attendance-dashboard"
        doc.parent_icon = "Frappe HR"
        doc.standard = 0
        doc.hidden = 0
        doc.icon = "bar-chart-2"

    doc.link_type = "External"
    doc.link = "/attendance-dashboard"
    doc.link_to = None
    doc.parent_icon = "Frappe HR"

    existing_roles = {row.role for row in doc.roles}
    for role in ("HR Manager", "IT Admin"):
        if role not in existing_roles and frappe.db.exists("Role", role):
            doc.append("roles", {"role": role})

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    frappe.db.commit()
