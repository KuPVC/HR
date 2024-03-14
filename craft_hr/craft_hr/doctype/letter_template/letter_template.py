# Copyright (c) 2024, Craftinteractive and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LetterTemplate(Document):
	pass

@frappe.whitelist()
def get_letter_details(template):
	body = []
	intro = frappe.get_list(
		"Letter Template",
		fields=["subject", "content"],
		filters={"name": template},
	)[0]
	body.append(intro)
	return body