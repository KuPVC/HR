# Copyright (c) 2023, Craftinteractive and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class MonthlyOvertimeSheet(Document):
	def before_validate(self):
		for row in self.ot_table:
			row.date = self.date
