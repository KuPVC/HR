from craft_hr.events.get_leaves import get_earned_leave

def on_cancel(doc, method):
    print("**************************************")
    print("Attendance Cancelled")
    print("**************************************")
    get_earned_leave(doc.employee)