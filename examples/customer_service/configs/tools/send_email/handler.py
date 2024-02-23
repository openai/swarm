def send_email(email_address,message):
  response = f'email sent to: {email_address} with message: {message}'
  return {'response':response}
# def send_email_assistants(tool_id,address,message):
#   return {'response':f'email sent to {address} with message {message}'}
