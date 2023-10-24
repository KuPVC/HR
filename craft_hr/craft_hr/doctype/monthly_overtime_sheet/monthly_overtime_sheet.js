// Copyright (c) 2023, Craftinteractive and contributors
// For license information, please see license.txt



frappe.ui.form.on('Monthly Overtime Sheet', {
    get_employees(frm){
        if (frm.is_new()){
            frappe.db.get_list('Employee', {
                fields: ['name','employee_name','department'],
                filters: {
                    status: 'Active',
                    company: frm.doc.company
                },
                limit:0,
                order_by:'name asc'
            }).then(records => {
                records.forEach(emp=>{
                    frm.add_child('ot_table',{
                        employee:emp.name,
                        employee_name:emp.employee_name,
                        department:emp.department,
                        date:frm.doc.date
                        
                    });
                    frm.refresh_fields('ot_table');
            });
		});
        }
    },
});