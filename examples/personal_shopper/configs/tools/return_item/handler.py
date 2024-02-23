import database
import sqlite3

def return_item(item_id):
    print('Running item return function for item_id:',item_id)
    return {'response':'return completed'}

def return_item_assistants(tool_id,item_id):
    print('Running item return function for item_id:',item_id)
    return {'id':tool_id, 'response':'return completed'}

