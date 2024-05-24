import datetime
import random

import database
from swarm import Assistant
from swarm.assistants import create_triage_assistant
from swarm.repl import run_demo_loop


def refund_item(user_id, item_id):
    """Initiate a refund based on the user ID and item ID.
    Takes as input arguments in the format '{"user_id":"1","item_id":"3"}'
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT amount FROM PurchaseHistory
        WHERE user_id = ? AND item_id = ?
    """,
        (user_id, item_id),
    )
    result = cursor.fetchone()
    if result:
        amount = result[0]
        print(f"Refunding ${amount} to user ID {user_id} for item ID {item_id}.")
    else:
        print(f"No purchase found for user ID {user_id} and item ID {item_id}.")
    print("Refund initiated")


def notify_customer(user_id, method):
    """Notify a customer by their preferred method of either phone or email.
    Takes as input arguments in the format '{"user_id":"1","method":"email"}'"""

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT email, phone FROM Users
        WHERE user_id = ?
    """,
        (user_id,),
    )
    user = cursor.fetchone()
    if user:
        email, phone = user
        if method == "email" and email:
            print(f"Emailed customer {email} a notification.")
        elif method == "phone" and phone:
            print(f"Texted customer {phone} a notification.")
        else:
            print(f"No {method} contact available for user ID {user_id}.")
    else:
        print(f"User ID {user_id} not found.")


def order_item(user_id, product_id):
    """Place an order for a product based on the user ID and product ID.
    Takes as input arguments in the format '{"user_id":"1","product_id":"2"}'"""
    date_of_purchase = datetime.datetime.now()
    item_id = random.randint(1, 300)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT product_id, product_name, price FROM Products
        WHERE product_id = ?
    """,
        (product_id,),
    )
    result = cursor.fetchone()
    if result:
        product_id, product_name, price = result
        print(
            f"Ordering product {product_name} for user ID {user_id}. The price is {price}."
        )
        # Add the purchase to the database
        database.add_purchase(user_id, date_of_purchase, item_id, price)
    else:
        print(f"Product {product_id} not found.")


# Initialize the database
database.initialize_database()

# Preview tables
database.preview_table("Users")
database.preview_table("PurchaseHistory")
database.preview_table("Products")

# Define the assistants

refunds_assistant = Assistant(
    name="Refunds Assistant",
    description=f"""You are a refund assistant that handles all actions related to refunds after a return has been processed.
    You must ask for both the user ID and item ID to initiate a refund. Ask for both user_id and item_id in one message.
    If the user asks you to notify them, you must ask them what their preferred method of notification is. For notifications, you must
    ask them for user_id and method in one message.""",
    functions=[refund_item, notify_customer],
)

sales_assistant = Assistant(
    name="Sales Assistant",
    description=f"""You are a sales assistant that handles all actions related to placing an order to purchase an item.
    Regardless of what the user wants to purchase, must ask for BOTH the user ID and product ID to place an order.
    An order cannot be placed without these two pieces of inforamation. Ask for both user_id and product_id in one message.
    If the user asks you to notify them, you must ask them what their preferred method is. For notifications, you must
    ask them for user_id and method in one message.
    """,
    functions=[order_item, notify_customer],
)

triage_assistant = create_triage_assistant(
    name="Triage Assistant",
    instructions=f"""You are to triage a users request, and call a tool to transfer to the right intent.
    Once you are ready to transfer to the right intent, call the tool to transfer to the right intent.
    You dont need to know specifics, just the topic of the request.
    If the user request is about making an order or purchasing an item, transfer to the Sales Assistant.
    If the user request is about getting a refund on an item or returning a product, transfer to the Refunds Assistant.
    When you need more information to triage the request to an assistant, ask a direct question without explaining why you're asking it.
    Do not share your thought process with the user! Do not make unreasonable assumptions on behalf of user.""",
    assistants=[sales_assistant, refunds_assistant],
    add_backlinks=True,
)

for f in triage_assistant.functions:
    print(f.__name__)

if __name__ == "__main__":
    # Run the demo loop
    run_demo_loop(triage_assistant, debug=False)
