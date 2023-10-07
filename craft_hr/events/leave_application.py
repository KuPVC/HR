from craft_hr.events.get_leaves import get_earned_leave

def on_submit(doc, method):
    print("**************************************")
    print("Leave Application submitted")
    print("**************************************")
    get_earned_leave(doc.employee)
