import requests
import hmac
import hashlib
import re
from decouple import config

# Credenciales desde settings o .env
DLOCAL_API_URL = config('DLOCAL_API_URL', default='https://api-sbx.dlocalgo.com/v1')
DLOCAL_X_LOGIN = config('DLOCAL_X_LOGIN', default='')
DLOCAL_SECRET_KEY = config('DLOCAL_SECRET_KEY', default='')

def get_dlocal_headers():
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DLOCAL_X_LOGIN}:{DLOCAL_SECRET_KEY}',
    }

def create_dlocal_payment(amount, currency, description, success_url=None, back_url=None, notification_url=None, allow_transparent=False):
    """
    Llama a la API de dLocal Go para crear un Payment Link (Checkout) o un merchant_checkout_token.
    """
    url = f"{DLOCAL_API_URL}/payments"
    
    payload = {
        "amount": str(amount),
        "currency": currency,
        "country": "PE", # Adaptable
        "description": description,
    }

    if allow_transparent:
        payload["allow_transparent"] = True
    else:
        # Modo Smart Checkout
        if success_url: payload["success_url"] = success_url
        if back_url: payload["back_url"] = back_url
        
    if notification_url:
        payload["notification_url"] = notification_url

    try:
        response = requests.post(url, json=payload, headers=get_dlocal_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'payment_id': data.get('id', ''),
            'checkout_token': data.get('merchant_checkout_token', ''),
            'checkout_url': data.get('redirect_url', ''),
            'raw_data': data
        }
    except requests.exceptions.RequestException as e:
        # Registrar error
        print(f"Error creating dLocal payment: {e}")
        if e.response is not None:
             print(e.response.text)
        api_error = None
        if e.response is not None:
            api_error = e.response.text
        return {
            'success': False,
            'error': str(e),
            'api_error': api_error,
        }

def confirm_dlocal_payment(checkout_token, card_token, client_data=None, country='PE'):
    """
    Llama a dLocal Go para confirmar un Transparent Checkout pasándole el token de la tarjeta.
    Importante: Se usa el checkoutToken en la URL.
    """
    url = f"{DLOCAL_API_URL}/payments/confirm/{checkout_token}"
    
    payload = {"cardToken": card_token, "country": country}
    if client_data:
        payload.update(client_data)
        
    try:
        response = requests.post(url, json=payload, headers=get_dlocal_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'raw_data': data
        }
    except requests.exceptions.RequestException as e:
        print(f"Error confirmando pago dLocal: {e}")
        if e.response is not None:
             print(e.response.text)
        api_error = None
        if e.response is not None:
            api_error = e.response.text
        return {
            'success': False,
            'error': str(e),
            'api_error': api_error,
        }

def retrieve_dlocal_payment(payment_id):
    """
    Recupera el estado de un pago en dLocal Go.
    """
    url = f"{DLOCAL_API_URL}/payments/{payment_id}"
    try:
        response = requests.get(url, headers=get_dlocal_headers(), timeout=30)
        response.raise_for_status()
        return {
            'success': True,
            'raw_data': response.json()
        }
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo pago dLocal {payment_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'api_error': e.response.text if e.response is not None else None,
        }

def _extract_signature(signature_header):
    """
    Extrae el valor hexadecimal de firma desde:
    Authorization: V2-HMAC-SHA256, Signature: <hex>
    """
    if not signature_header:
        return ''
    match = re.search(r'Signature:\s*([a-fA-F0-9]+)', signature_header)
    return match.group(1).lower() if match else signature_header.strip().lower()

def verify_webhook_signature(payload_body, signature_header):
    """
    Verifica que la petición de webhook provenga realmente de dLocal
    según docs: HMAC_SHA256(secret, api_key + payload_json)
    """
    if not DLOCAL_X_LOGIN or not DLOCAL_SECRET_KEY:
        return False

    received_signature = _extract_signature(signature_header)
    if not received_signature:
        return False

    payload_text = payload_body.decode('utf-8')
    message = f"{DLOCAL_X_LOGIN}{payload_text}".encode('utf-8')

    expected_signature = hmac.new(
        DLOCAL_SECRET_KEY.encode('utf-8'),
        msg=message,
        digestmod=hashlib.sha256
    ).hexdigest().lower()
    
    return hmac.compare_digest(expected_signature, received_signature)
