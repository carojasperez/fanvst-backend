
from .models import Payment, PaymentMP, PurchaseOrder
from work.models import ContractedWork, Quote
from adminsite.tasks import contracted_notification, payment_notification
from datetime import date, datetime, timedelta
import pytz
from payment.models import PaymentPaypal
from work.functions import create_quote_svc


def save_payment_info_mp(user, data, quote):
    '''
    Guarda la info proveniente de la pasarela "Mercado Pago"
    '''
    payment = PaymentMP.objects.create(
        user=user,
        quote=quote,
        payment_id=data['id'],
        operation_type=data['operation_type'],
        issuer_id=data['issuer_id'],
        payment_method_id=data['payment_method_id'],
        payment_type_id=data['payment_type_id'],
        status=data['status'],
        status_detail=data['status_detail'],
        currency_id=data['currency_id'],
        description=data['description'],
        live_mode=data['live_mode'],
        # sponsor_id=data['sponsor_id'],
        authorization_code=data['authorization_code'],
        money_release_schema=data['money_release_schema'],
        taxes_amount=data['taxes_amount'],
        counter_currency=data['counter_currency'],
        brand_id=data['brand_id'],
        shipping_amount=data['shipping_amount'],
        pos_id=data['pos_id'],
        store_id=data['store_id'],
        collector_id=data['collector_id'],
        # Payer
        first_name=data['payer']['first_name'],
        last_name=data['payer']['last_name'],
        email=data['payer']['email'],
        # Payer Identification
        number=data['payer']['identification']['number'],
        document_type=data['payer']['identification']['type'],
        phone=data['payer']['phone']['number'],
        payer_type=data['payer']['type'],
        # Transaction
        external_reference=data['external_reference'],
        transaction_amount=data['transaction_amount'],
        transaction_amount_refunded=data['transaction_amount_refunded'],
        coupon_amount=data['coupon_amount'],
        differential_pricing_id=data['differential_pricing_id'],
        deduction_schema=data['deduction_schema'],
        installments=data['installments'],
        # Transaction Details
        payment_method_reference_id=data['transaction_details']['payment_method_reference_id'],
        net_received_amount=data['transaction_details']['net_received_amount'],
        total_paid_amount=data['transaction_details']['total_paid_amount'],
        overpaid_amount=data['transaction_details']['overpaid_amount'],
        external_resource_url=data['transaction_details']['external_resource_url'],
        installment_amount=data['transaction_details']['installment_amount'],
        financial_institution=data['transaction_details']['financial_institution'],
        payable_deferral_period=data['transaction_details']['payable_deferral_period'],
        acquirer_reference=data['transaction_details']['acquirer_reference'],
        # Fee Details
        fee_type=data['fee_details'][0]['type'],
        fee_amount=data['fee_details'][0]['amount'],
        fee_payer=data['fee_details'][0]['fee_payer'],
        captured=data['captured'],
        binary_mode=data['binary_mode'],
        call_for_authorize_id=data['call_for_authorize_id'],
        statement_descriptor=data['statement_descriptor'],
        # Card
        card_id=data['card']['id'],
        first_six_digits=data['card']['first_six_digits'],
        last_four_digits=data['card']['last_four_digits'],
        expiration_month=data['card']['expiration_month'],
        expiration_year=data['card']['expiration_year'],
        cardholder_name=data['card']['cardholder']['name'],
        cardholder_identification_type=data['card']['cardholder']['identification']['type'],
        cardholder_identification_number=data['card']['cardholder']['identification']['number'],

    )
    Quote.objects.filter(id=quote.id).update(
        status='3',
        accepted_date=datetime.now(pytz.utc)
        )
    return create_purchase_order(payment, None, user, quote)


def save_payment_info(user, data, quote):
    '''
    Guarda la info proveniente de la pasarela "Culqi"
    '''
    try:
        fixed_fee = data['fee_details']['fixed_fee']['total']
    except KeyError:
        fixed_fee = 0

    payment = Payment.objects.create(
        user=user,
        quote=quote,
        payment_id=data['id'],
        amount=data['amount'],
        amount_refunded=data['amount_refunded'],
        installments=data['installments'],
        installments_amount=data['installments_amount'],
        currency_code=data['currency_code'],
        email=data['email'],
        description=data['description'],
        card_email=data['source']['email'],
        card_number=data['source']['card_number'],
        last_four=data['source']['last_four'],
        card_active=data['source']['active'],

        iin_bin=data['source']['iin']['bin'],
        iin_card_brand=data['source']['iin']['card_brand'],
        iin_card_type=data['source']['iin']['card_type'],

        iin_issuer_name=data['source']['iin']['issuer']['name'],
        iin_issuer_country=data['source']['iin']['issuer']['country'],

        client_ip=data['source']['client']['ip'],
        client_ip_country=data['source']['client']['ip_country'],
        client_browser=data['source']['client']['browser'],
        client_device_fingerprint=data['source']['client']['device_fingerprint'],
        client_device_type=data['source']['client']['device_type'],
        # Outcome
        outcome_type=data['outcome']['type'],
        outcome_code=data['outcome']['code'],
        ourcome_merchant_message=data['outcome']['merchant_message'],
        ourcome_user_message=data['outcome']['user_message'],
        # Reference
        capture=data['capture'],
        reference_code=data['reference_code'],
        authorization_code=data['authorization_code'],
        # Fee Culqi
        variable_fee=data['fee_details']['variable_fee']['total'],
        fixed_fee=fixed_fee,
        total_fee=data.get('total_fee', 0),
        total_fee_taxes=data.get('total_fee_taxes', 0),
        transfer_amount=data.get('transfer_amount', 0),
    )
    Quote.objects.filter(id=quote.id).update(
        status='3',
        accepted_date=datetime.now(pytz.utc)
        )
    return create_purchase_order(payment, None, user, quote)


def create_purchase_order(mp, paypal, user, quote):
    '''
    Orden de Servicio
    Se genera una orden de compra vinculada al pago
    y a la cotización. Para el cliente le denominamos Orden de Servicio
    '''

    # Se genera una Orden de servicio
    po = PurchaseOrder.objects.create(
        payment=mp,
        paypal=paypal,
        user=user,
        quote=quote,
        price=quote.sale
    )

    # Se genera un servicio contratado
    cw = ContractedWork.objects.create(
        user=user,
        chamber=quote.chamber,
        po=po
    )

    # Se envia la orden de servicio generada al cliente.
    payment_notification.delay(
        po.user.username,
        po.user.first_name,
        po.price,
        cw.id
    )

    # Se envia una notificación al Chamber sobre la chamba contratada
    contracted_notification.delay(
        po.quote.chamber.username, # To
        po.quote.chamber.first_name, # Chamber name
        po.user.first_name, # Customer name
        cw.id
    )
    return cw.id


def get_rejected_reason(status):
    '''
    Función que devuelve el mensaje apropiado para el usuario dependiendo
    del tipo de rechazo que ha recibido en su Pago con Mercado Pago
    '''
    if status == 'cc_rejected_bad_filled_card_number':
            content = {'msg': 'Revisa el número de tarjeta.'}

    if status == 'cc_rejected_bad_filled_date':
            content = {'msg': 'Revisa la fecha de vencimiento.'}

    if status == 'cc_rejected_bad_filled_other':
            content = {'msg': 'Revisa los datos ingresados.'}

    if status == 'cc_rejected_bad_filled_security_code':
            content = {'msg': 'Revisa el código de seguridad de la tarjeta.'}

    if status == 'cc_rejected_blacklist	':
            content = {'msg': 'No pudimos procesar tu pago.'}

    if status == 'cc_rejected_call_for_authorize':
            content = {'msg': 'Debes autorizar ante tu banco el pago.'}

    if status == 'cc_rejected_card_disabled':
            content = {'msg': 'Llama a tu banco para activar tu tarjeta o usa otro medio de pago.\nEl teléfono está al dorso de tu tarjeta.'}

    if status == 'cc_rejected_card_error':
            content = {'msg': 'No pudimos procesar tu pago.'}

    if status == 'cc_rejected_card_error':
            content = {'msg': 'No pudimos procesar tu pago.'}

    if status == 'cc_rejected_duplicated_payment':
            content = {'msg': 'Ya hiciste un pago por ese valor.\nSi necesitas volver a pagar usa otra tarjeta.'}

    if status == 'cc_rejected_high_risk':
            content = {'msg': 'Tu pago fue rechazado. \nElige otro de los medios de pago.'}

    if status == 'cc_rejected_insufficient_amount':
            content = {'msg': 'Tu metodo de pago no tiene fondos suficientes.'}

    if status == 'cc_rejected_insufficient_amount':
            content = {'msg': 'Tu metodo de pago no tiene fondos suficientes.'}

    if status == 'cc_rejected_invalid_installments':
            content = {'msg': 'Tu metodo de pago no acepta pago en cuotas.'}

    if status == 'cc_rejected_max_attempts':
            content = {'msg': 'Llegaste al límite de intentos permitidos.\nElige otra tarjeta u otro medio de pago.'}

    if status == 'cc_rejected_other_reason':
            content = {'msg': 'Tu banco no procesó el pago.'}
    
    return content


def save_paypal_info(data, user, uuid, opt, quote=None):
    '''
    Guarda la información del pago de paypal
    '''

    # Se registra la información del pago de Paypal
    paypal = PaymentPaypal.objects.create(
        user=user,
        payment_id=data['id'],
        intent=data['intent'],
        status=data['status'],
        payer_email_address=data['payer']['email_address'],
        payer_payer_id=data['payer']['payer_id'],
        payer_address=data['payer']['address'],
        payer_name=data['payer']['name']['given_name'],
        payer_surname=data['payer']['name']['surname'],
        purchase_description=data['purchase_units'][0]['description'],
        purchase_reference_id=data['purchase_units'][0]['reference_id'],
        purchase_amount=data['purchase_units'][0]['amount']['value'],
        purchase_currency=data['purchase_units'][0]['amount']['currency_code'],
        purchase_email_address=data['purchase_units'][0]['payee']['email_address'],
        purchase_merchant_id=data['purchase_units'][0]['payee']['merchant_id']
        )
    if quote is None:
        quote = create_quote_svc(uuid, opt, user)

    else:
        quote = Quote.objects.get(id=quote)
        today = datetime.now(pytz.utc)
        dlvdate = today + timedelta(days=quote.required_days)

        quote.status='3'
        quote.accepted_date=today
        quote.delivery_date=dlvdate
        quote.save()
        # Quote.objects.filter(id=quote).update(
        # status='3',
        # accepted_date=datetime.now(pytz.utc)
        # )
    cw = create_purchase_order(None, paypal, user, quote)


    return cw

