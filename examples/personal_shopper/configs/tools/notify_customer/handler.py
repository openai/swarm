import database
import sqlite3

def notify_customer_assistants(tool_id, user_id, method):
    conn = database.get_connection()  # Use the global connection
    cursor = conn.cursor()
    print('Running notify customer function with for user_id:',user_id,'contacting via:',method)

    try:
        # Query to retrieve user's contact information
        #For now hard code 1 as user_id
        cursor.execute('''
            SELECT email, phone FROM Users
            WHERE user_id = ?
        ''', (user_id,))
        user = cursor.fetchone()

        if user:
            # Unpack user data
            email, phone = user

            # Determine the notification method
            if method == "email" and email:
                return {'id':tool_id, 'response':'Emailed customer a notification'}
            elif method == "phone" and phone:
                return {'id':tool_id, 'response':'Texted customer a notification'}
            else:
                return f"No {method} contact available for user."

        else:
            return {'id':tool_id, 'response':'User not found'}
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return "Error in notification process"

def notify_customer(user_id, method):
    conn = database.get_connection()  # Use the global connection
    cursor = conn.cursor()
    print('Running notify customer function with for user_id:',user_id,'contacting via:',method)

    try:
        # Query to retrieve user's contact information
        #For now hard code 1 as user_id
        cursor.execute('''
            SELECT email, phone FROM Users
            WHERE user_id = ?
        ''', (user_id,))
        user = cursor.fetchone()

        if user:
            # Unpack user data
            email, phone = user

            # Determine the notification method
            if method == "email" and email:
                return {'response':'Emailed customer a notification'}
            elif method == "phone" and phone:
                return {'response':'Texted customer a notification'}
            else:
                return f"No {method} contact available for user."

        else:
            return {'response':'User not found'}
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return "Error in notification process"
