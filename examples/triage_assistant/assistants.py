from swarm import Assistant


def process_refund(item_id, reason="NOT SPECIFIED"):
    """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""
    print(f"[mock] Refunding item {item_id} because {reason}...")
    return "Success!"


def apply_discount():
    """Apply a discount to the user's cart."""
    print("[mock] Applying discount...")
    return "Applied discount of 11%"


triage_assistant = Assistant(
    name="Triage Assistant",
    instructions="Determine which assistant is best suited to handle the user's request, and transfer the conversation to that assistant.",
)
sales_assistant = Assistant(
    name="Sales Assistant",
    instructions="Be super enthusiastic about selling bees.",
)
refunds_assistant = Assistant(
    name="Refunds Assistant",
    instructions="Help the user with a refund. If the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund.",
    functions=[process_refund, apply_discount],
)


def transfer_back_to_triage():
    """Call this function if a user is asking about a topic that is not handled by the current assistant."""
    return triage_assistant


def transfer_to_sales():
    return sales_assistant


def transfer_to_refunds():
    return refunds_assistant


triage_assistant.functions = [transfer_to_sales, transfer_to_refunds]
sales_assistant.functions.append(transfer_back_to_triage)
refunds_assistant.functions.append(transfer_back_to_triage)
