def respond_to_user(message):
  print(message)
  return {'response':message}
def respond_to_user_assistants(tool_id,message):
  return {'id':tool_id, 'response':message}
