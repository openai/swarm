import sqlite3

#global connection
conn = None

def get_connection():
    global conn
    if conn is None:
        conn = sqlite3.connect('application.db')
    return conn

def create_database():
    # Connect to a single SQLite database
    conn = get_connection()
    cursor = conn.cursor()


    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            phone TEXT
        )
    ''')

    # Create PurchaseHistory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PurchaseHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date_of_purchase TEXT,
            item_id INTEGER,
            amount REAL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
    ''')

    # Save (commit) the changes
    conn.commit()


def add_user(user_id, first_name, last_name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if the user already exists
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        return

    try:
        cursor.execute('''
            INSERT INTO Users (user_id, first_name, last_name, email, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, first_name, last_name, email, phone))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")


def add_purchase(user_id, date_of_purchase, item_id, amount):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if the purchase already exists
    cursor.execute('''
        SELECT * FROM PurchaseHistory
        WHERE user_id = ? AND item_id = ? AND date_of_purchase = ?
    ''', (user_id, item_id, date_of_purchase))
    if cursor.fetchone():
       # print(f"Purchase already exists for user_id {user_id} on {date_of_purchase} for item_id {item_id}.")
        return

    try:
        cursor.execute('''
            INSERT INTO PurchaseHistory (user_id, date_of_purchase, item_id, amount)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date_of_purchase, item_id, amount))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")

def close_connection():
    global conn
    if conn:
        conn.close()
        conn = None

#Initialize and load database
def initialize_database():
    global conn

    # Initialize the database tables
    create_database()

    # Add some initial users
    initial_users = [
        (1,'Alice', 'Smith', 'alice@test.com', '123-456-7890'),
        (2, 'Bob', 'Johnson', 'bob@test.com', '234-567-8901'),
        # Add more initial users here
    ]

    for user in initial_users:
        add_user(*user)

    # Add some initial purchases
    initial_purchases = [
        (1, '2024-01-01', 101, 99.99),
        (1, '2023-12-25', 100, 39.99),
        (2, '2023-11-14', 307, 49.99),
    ]

    for purchase in initial_purchases:
        add_purchase(*purchase)
