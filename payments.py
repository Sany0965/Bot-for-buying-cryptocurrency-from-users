import requests
import config

YOOMONEY_REQUEST_PAYMENT_URL = 'https://yoomoney.ru/api/request-payment'
YOOMONEY_PROCESS_PAYMENT_URL = 'https://yoomoney.ru/api/process-payment'
COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price'
CRYPTBOT_CREATE_URL = 'https://pay.crypt.bot/api/createInvoice'
CRYPTBOT_INVOICES_URL = 'https://pay.crypt.bot/api/getInvoices'


def get_usdt_to_rub_rate():
    resp = requests.get(
        COINGECKO_URL,
        params={'ids': 'tether', 'vs_currencies': 'rub'}
    )
    resp.raise_for_status()
    return resp.json()['tether']['rub']


def create_invoice(amount):
    headers = {'Crypto-Pay-API-Token': config.CRYPTOBOT_API_TOKEN}
    data = {'asset': 'USDT', 'amount': amount}
    resp = requests.post(
        CRYPTBOT_CREATE_URL,
        headers=headers,
        json=data
    )
    resp.raise_for_status()
    result = resp.json().get('result', {})
    return result.get('pay_url'), result.get('invoice_id')



def check_invoice_paid(invoice_id):
    headers = {'Crypto-Pay-API-Token': config.CRYPTOBOT_API_TOKEN}
    params = {'invoice_ids': str(invoice_id)}  
    
    print(f"[DEBUG] Checking invoice: {invoice_id}")
    
    try:
        response = requests.get(
            CRYPTBOT_INVOICES_URL,
            headers=headers,
            params=params
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Request failed: {str(e)}")
        return None
    
    print(f"[DEBUG] Response: {response.text}")  
    
    try:
        result = response.json()
    except ValueError:
        print("[ERROR] Invalid JSON response")
        return None
    
    if result.get('result') and result['result'].get('items'):
        for inv in result['result']['items']:
            if str(inv.get('invoice_id')) == str(invoice_id):
                return inv.get('status')
    else:
        print(f"[ERROR] API error: {result.get('error', 'Unknown error')}")
    
    return None
    
def create_crypto_check(user_id, amount_usdt):
    headers = {'Crypto-Pay-API-Token': config.CRYPTOBOT_API_TOKEN}
    payload = {
        'asset': 'USDT',
        'amount': f"{amount_usdt:.2f}",
        'user_id': user_id
    }
    
    try:
        response = requests.post(
            'https://pay.crypt.bot/api/createCheck',
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка создания чека: {str(e)}")
        return None

def send_yoomoney_payment(to, amount_rub, message, label='cryptobot', sandbox=False, money_source='wallet'):
    headers = {
        'Authorization': f"Bearer {config.YOUMONEY_OAUTH_TOKEN}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    req_data = {
        'pattern_id': 'p2p',
        'to': to,
        'amount': f"{amount_rub:.2f}",
        'message': message,
        'label': label
    }

    if sandbox:
        req_data['test_payment'] = 'true'
        req_data['test_result'] = 'success'

    resp = requests.post(
        YOOMONEY_REQUEST_PAYMENT_URL,
        headers=headers,
        data=req_data
    )
    resp.raise_for_status()
    request_resp = resp.json()

    if request_resp.get('status') != 'success':
        raise ValueError(request_resp.get('error_description', request_resp))

    request_id = request_resp.get('request_id')
    if not request_id:
        raise ValueError("no request_id")

    proc_data = {
        'request_id': request_id,
        'money_source': money_source
    }

    resp2 = requests.post(
        YOOMONEY_PROCESS_PAYMENT_URL,
        headers=headers,
        data=proc_data
    )
    resp2.raise_for_status()
    process_resp = resp2.json()

    if process_resp.get('status') != 'success':
        raise ValueError(process_resp.get('error_description', process_resp))

    return process_resp