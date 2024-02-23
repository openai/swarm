import database

def initiate_refund_assistants(tool_id,user_id,amount,reason="None given"):
    print('Running intiate refund for user_id:',user_id,'for: $',amount,"for reason:",reason)
    return {'id':tool_id, 'response':'refund given'}

def initiate_refund(user_id, item_id):
    conn = database.get_connection()  # Use the global connection
    cursor = conn.cursor()
    # Check if the user and item exist in the purchase history
    cursor.execute('''
        SELECT amount FROM PurchaseHistory
        WHERE user_id = ? AND item_id = ?
    ''', (user_id, item_id))
    result = cursor.fetchone()

    if result:
        amount = result[0]
        print(f"Refunding ${amount} to user ID {user_id} for item ID {item_id}.")
        # Here you can add logic to actually process the refund
    else:
        print(f"No purchase found for user ID {user_id} and item ID {item_id}.")
