import frappe
from frappe.model.document import Document


class TeamCalendarCheck(Document):
    """One row = this user ticked this date as "checked" in the ESS Team Calendar.
    Purely a personal progress marker; managed through craft_hr.api only."""

    pass
