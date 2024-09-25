// Copyright (c) 2023, Craftinteractive and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Distribution Template', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Leave Distribution Template', {
    // Trigger when the form is refreshed or loaded
    refresh: function(frm) {
        update_labels_based_on_allocation_type(frm);
    },

    // Trigger when leave_allocation_type is changed
    leave_allocation_type: function(frm) {
        update_labels_based_on_allocation_type(frm);
    },

    // Ensure the labels are updated once the form is fully loaded
    onload_post_render: function(frm) {
        update_labels_based_on_allocation_type(frm);
    }
});

// Function to update labels based on leave_allocation_type
function update_labels_based_on_allocation_type(frm) {
    if (frm.doc.leave_allocation_type === 'Annually') {
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('start', 'label', 'From Year');
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('end', 'label', 'To Year (Choose 0 Forever)');
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('value_allocation', 'label', 'Yearly Allocation');
    } else if (frm.doc.leave_allocation_type === 'Monthly') {
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('start', 'label', 'From Month');
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('end', 'label', 'To Month (Choose 0 Forever)');
        frm.fields_dict['leave_distribution'].grid.update_docfield_property('value_allocation', 'label', 'Monthly Allocation');
    }
}
