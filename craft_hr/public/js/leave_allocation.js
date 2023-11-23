
frappe.ui.form.on("Leave Allocation",{
    onload: function(frm){
        if(frm.doc.custom_status=="Ongoing" && frm.doc.docstatus){
            frm.add_custom_button(__('Close'), function(){
                if(frm.doc.from_date<frappe.datetime.get_today()){
                    frappe.confirm(__("Are you sure you want to close this allocation?"), function(){
                        frappe.call({
                            method:"craft_hr.events.leave_allocation.close_allocation",
                            args:{
                                docname : frm.doc.name
                            },
                            callback: function(r){
                                console.log("Success")
                            }
                        })
                    })
                }
                else {
                    frappe.msgprint(__("This leave allocation period has not started yet."))
                }
            })
        }
    },
    custom_carry_forward: function(frm){
        if (frm.doc.custom_carry_forward && frm.doc.custom_is_earned_leave){
            frm.trigger("calculate_leaves_allocated")
        }
    },
    calculate_leaves_allocated: function(frm){
        if (cint(frm.doc.custom_carry_forward) == 1 && frm.doc.leave_type && frm.doc.employee) {
			return frappe.call({
				method: "craft_hr.events.get_leaves.get_carry_forwarded_leave",
				args:{
                    employee: frm.doc.employee,
                    leave_type: frm.doc.leave_type, 
                    date:frm.doc.from_date, 
                    carry_forward:frm.doc.carry_forward
                },
				callback: function(r) {
                    if (r.message != frm.doc.custom_opening_leaves){
                        frm.set_value("custom_opening_leaves", r.message)
                        frm.refresh()
                    }
				}
			});
		} 
    }

})