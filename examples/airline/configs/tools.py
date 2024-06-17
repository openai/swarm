def escalate_to_agent(reason=None):
    return f"Escalating to agent: {reason}" if reason else "Escalating to agent"


def valid_to_change_flight():
    return "Customer is eligible to change flight"


def change_flight():
    return "Flight was successfully changed!"


def initiate_refund():
    status = "Refund initiated"
    return status


def initiate_flight_credits():
    status = "Successfully initiated flight credits"
    return status


def case_resolved():
    return "Case resolved. No further questions."


def initiate_baggage_search():
    return "Baggage was found!"
