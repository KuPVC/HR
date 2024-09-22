# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from frappe import _


def get_dashboard_for_employee(data):
	return {
		"heatmap": True,
		"heatmap_message": _("This is based on the attendance of this Employee"),
		"fieldname": "employee",
		"non_standard_fieldnames": {"Bank Account": "party", "Employee Grievance": "raised_by"},
		"method": "hrms.overrides.employee_master.get_timeline_data",
		"transactions": [
			{"label": _("Attendance"), "items": ["Attendance", "Attendance Request", "Employee Checkin"]},
			{
				"label": _("Leave"),
				"items": ["Leave Application", "Leave Allocation", "Leave Policy Assignment"],
			},
			{
				"label": _("Lifecycle"),
				"items": [
					"Employee Onboarding",
					"Employee Transfer",
					"Employee Promotion",
					"Employee Grievance",
					# TODO: Employment Contract is currently linked with job applicant
					# "Employment Contract"
				],
			},
			{
				"label": _("Exit"),
				"items": ["Employee Separation", "Exit Interview", "Full and Final Statement", "Termination Letter"],
			},
			{"label": _("Shift"), "items": ["Shift Request", "Shift Assignment"]},
			{"label": _("Expense"), "items": ["Expense Claim", "Travel Request", "Employee Advance"]},
			{"label": _("Benefit"), "items": ["Employee Benefit Application", "Employee Benefit Claim"]},
			{
				"label": _("Payroll"),
				"items": [
					"Salary Structure Assignment",
					"Salary Slip",
					"Additional Salary",
					"Timesheet",
					"Employee Incentive",
					"Retention Bonus",
					"Bank Account",
				],
			},
			{
				"label": _("Training"),
				"items": ["Training Event", "Training Result", "Training Feedback", "Employee Skill Map"],
			},
			{"label": _("Evaluation"), "items": ["Appraisal"]},
			{"label": _("Documents"), "items": ["Certificate of Employment","NOC","Work Experience Certificate","Warning Letter"]}
		],
	}