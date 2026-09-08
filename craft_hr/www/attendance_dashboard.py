import frappe

from craft_hr.api import ATTENDANCE_DASHBOARD_ROLES

no_cache = 1


def get_context(context):
	if not set(frappe.get_roles()) & set(ATTENDANCE_DASHBOARD_ROLES):
		frappe.throw(
			frappe._("Not permitted to view the attendance dashboard"),
			frappe.PermissionError,
		)

	context = frappe._dict()
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.site_name = frappe.local.site
	return context
