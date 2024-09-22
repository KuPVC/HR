// Copyright (c) 2023, Craftinteractive and contributors
// For license information, please see license.txt

frappe.ui.form.on('NOC', {
	letter_template: function(frm){
		if (frm.doc.letter_template){
			frappe.call({
				method: 'craft_hr.craft_hr.doctype.letter_template.letter_template.get_letter_details',
				args : {
					template : frm.doc.letter_template
				},
				callback: function(r){
					if(r.message){
						let message_body = r.message;
						frm.set_value("subject", message_body[0].subject);
						frm.set_value("content", message_body[0].content);
						frm.refresh();
					}
				}

			});
		}
	},
});
