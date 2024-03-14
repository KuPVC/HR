frappe.listview_settings["Document Request Form"] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		const status_color = {
			"Pending": "yellow",
			"Approved": "orange",
			"Returned": "green",
		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	},
}
