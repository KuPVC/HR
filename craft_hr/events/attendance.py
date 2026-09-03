from craft_hr.events.get_leaves import get_earned_leave

def on_cancel(doc, method):
    #TODO: condition to check if the leave type is earned leave
    get_earned_leave(doc.employee)