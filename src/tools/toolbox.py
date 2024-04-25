from src.utils.vector_search import retrieve_results
import time

class Toolbox:

  def __init__(self, tool_name, params):
    self.tool_name = tool_name
    self.params = params
    self.tool_function = getattr(self, tool_name)

  def execute_tool(self):
    params_dict = {param.name: param.value for param in self.params}
    return self.tool_function(**params_dict)
  
  def return_order(self, **kwargs):
    orderId = kwargs.get('orderId')
    reason = kwargs.get('reason', '')
    time.sleep(0.5)
    return {'status': 'success', 'message': f'Return for order {orderId} has been successfully triggered.'}

  def refund_order(self, **kwargs):
    orderId = kwargs.get('orderId')
    amount = kwargs.get('amount')
    reason = kwargs.get('reason', '')
    time.sleep(0.5)
    return {'refundAmount': amount, 'message': f'Refunded order {orderId} for an amount of {amount}. Reason: {reason}'}

  def cancel_order(self, **kwargs):
    orderId = kwargs.get('orderId')
    reason = kwargs.get('reason', '')
    time.sleep(0.5)
    return {'status': 'success', 'message': f'Order {orderId} has been successfully cancelled.'}

  def check_delivery_status(self, **kwargs):
    orderId = kwargs.get('orderId')
    time.sleep(0.5)
    delivery_status = {
      'tracking_number': 'CNYDD9',
      'order_id': orderId,
      'status': 'in transit',
      'courier': 'UPS',
      'expected_date': '2024-05-14',
      'courier_message': 'Parcel arrived at local facility.'
    }
    return {'delivery_status': delivery_status}
  
  def find_order(self, **kwargs):
    accountId = kwargs.get('accountId')
    order_date = kwargs.get('orderDate', '')
    order_number = kwargs.get('orderNumber', '')
    last_order = kwargs.get('lastOrder', False)
    time.sleep(0.5)
    order = {
      'id': 'SFY12A' if order_number == '' else order_number,
      'accountId': accountId,
      'date': '2024-05-12' if order_date == '' else order_date,
      'amount': '600.25',
      'status': 'paid',
      'n_items': 4
      }
    return {'order': order}

  def find_customer_details(self, **kwargs):
    email = kwargs.get('email', '')
    birthday = kwargs.get('birthday', '')
    time.sleep(0.5)
    customer_details = {
      'id': 'usr_2896kOai',
      'name': email.split('@')[0].capitalize(),
      'email': email,
      'birthday': birthday,
      'phone': '+1234567890',
      'address': '123 Main St, New York, NY',
      'loyaltyPoints': '1250',
      'lastContacted': '2 days ago',
      'lastReservation': '1 month ago',
      'memberSince': '1 year 3 months'
    }
    return {'customer_details': customer_details}
  
  def query_kb(self, **kwargs):
    prompt = kwargs.get('prompt')
    results = retrieve_results(prompt, 'kb')
    return {'results': results}
  
  def query_faq(self, **kwargs):
    prompt = kwargs.get('prompt')
    results = retrieve_results(prompt, 'faq')
    return {'results': results}
  
  def submit_ticket(self, **kwargs):
    category = kwargs.get('category')
    summary = kwargs.get('summary')
    description = kwargs.get('description')
    ticket = {
      'category': category,
      'summary': summary,
      'description': description,
      'status': 'submitted'
    }
    time.sleep(0.5)
    return {'status': 'Successfully submitted ticket.', 'ticket': ticket}
  