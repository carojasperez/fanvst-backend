from django.contrib.auth.models import User
from django.db import models
from work.models import Quote, ContractedWork
from adminsite.baseinfo.models import Bank

STATUS_INCOME = (
    ('0', 'Procesando pago'),
    ('1', 'Pagado')
)


class PaymentMP(models.Model):
    '''
    Estos datos se guardan tal como vienen de la pasarela
    en este caso MercadoPago
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    payment_id = models.CharField(max_length=300, null=True, blank=True)
    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, null=True)
    creation_date = models.DateTimeField(auto_now=True)
    date_of_expiration = models.DateTimeField(blank=True, null=True)
    money_release_date = models.DateTimeField(blank=True, null=True)
    operation_type = models.CharField(max_length=300, null=True, blank=True)
    issuer_id = models.IntegerField()
    payment_method_id = models.CharField(max_length=300, null=True, blank=True)
    payment_type_id = models.CharField(max_length=300, null=True, blank=True)
    status = models.CharField(max_length=300, null=True, blank=True)
    status_detail = models.CharField(max_length=300, null=True, blank=True)
    currency_id = models.CharField(max_length=300, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    live_mode = models.BooleanField()
    sponsor_id = models.CharField(max_length=300, null=True, blank=True)
    authorization_code = models.CharField(max_length=300, null=True, blank=True)
    money_release_schema = models.CharField(max_length=300, null=True, blank=True)
    taxes_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    counter_currency = models.CharField(max_length=300, null=True, blank=True)
    brand_id = models.CharField(max_length=300, null=True, blank=True)
    shipping_amount = models.CharField(max_length=300, null=True, blank=True)
    pos_id = models.CharField(max_length=300, null=True, blank=True)
    store_id = models.CharField(max_length=300, null=True, blank=True)
    collector_id = models.CharField(max_length=300, null=True, blank=True)
    # Payer
    first_name = models.CharField(max_length=300, null=True, blank=True)
    last_name = models.CharField(max_length=300, null=True, blank=True)
    email = models.CharField(max_length=300, null=True, blank=True)
    # Payer Identification
    number = models.CharField(max_length=300, null=True, blank=True)
    document_type = models.CharField(max_length=300, null=True, blank=True)
    phone = models.CharField(max_length=300, null=True, blank=True)
    payer_type = models.CharField(max_length=300, null=True, blank=True)
    # Transaction
    external_reference = models.CharField(max_length=300, null=True, blank=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    differential_pricing_id = models.CharField(max_length=300, null=True, blank=True)
    deduction_schema = models.CharField(max_length=300, null=True, blank=True)
    installments = models.IntegerField() # Cuotas
    # Transaction Details
    payment_method_reference_id = models.CharField(max_length=300, null=True, blank=True)
    net_received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overpaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    external_resource_url = models.CharField(max_length=300, null=True, blank=True)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    financial_institution = models.CharField(max_length=300, null=True, blank=True)
    payable_deferral_period = models.CharField(max_length=300, null=True, blank=True)
    acquirer_reference = models.CharField(max_length=300, null=True, blank=True)
    # Fee Details
    fee_type = models.CharField(max_length=300, null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_payer = models.CharField(max_length=300, null=True, blank=True)
    captured = models.BooleanField()
    binary_mode = models.BooleanField()
    call_for_authorize_id = models.CharField(max_length=300, null=True, blank=True)
    statement_descriptor = models.CharField(max_length=300, null=True, blank=True)
    # Card
    card_id = models.CharField(max_length=300, null=True, blank=True)
    first_six_digits = models.CharField(max_length=6)
    last_four_digits = models.CharField(max_length=4)
    expiration_month = models.CharField(max_length=4)
    expiration_year = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=300, null=True, blank=True)
    cardholder_identification_type = models.CharField(max_length=300, null=True, blank=True)
    cardholder_identification_number = models.CharField(max_length=300, null=True, blank=True)


class Payment(models.Model):
    '''
    Estos datos se guardan tal como vienen de la pasarela
    en este caso Culqi
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    payment_id = models.CharField(max_length=300)
    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, null=True)
    creation_date = models.DateTimeField(auto_now=True)
    amount = models.IntegerField()
    amount_refunded = models.IntegerField()
    installments = models.IntegerField() #Cuotas
    installments_amount = models.IntegerField()
    currency_code = models.CharField(max_length=10)
    email = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    # Card Detail
    card_email = models.CharField(max_length=200)
    card_number = models.CharField(max_length=100)
    last_four = models.CharField(max_length=4)
    card_active = models.CharField(max_length=200, null=True)
    # Iin
    iin_bin = models.CharField(max_length=200)
    iin_card_brand = models.CharField(max_length=200)
    iin_card_type = models.CharField(max_length=200)
    # Issuer
    iin_issuer_name = models.CharField(max_length=200)
    iin_issuer_country = models.CharField(max_length=200)
    # Client
    client_ip = models.CharField(max_length=200)
    client_ip_country = models.CharField(max_length=200)
    client_browser = models.CharField(max_length=200, null=True)
    client_device_fingerprint = models.CharField(max_length=500, null=True)
    client_device_type = models.CharField(max_length=300, null=True)
    # Outcome
    outcome_type = models.CharField(max_length=400)
    outcome_code = models.CharField(max_length=400)
    ourcome_merchant_message = models.TextField()
    ourcome_user_message = models.TextField()
    # Reference
    capture = models.BooleanField()
    reference_code = models.CharField(max_length=300)
    authorization_code = models.CharField(max_length=300)
    # Fee Culqi
    variable_fee = models.IntegerField()
    fixed_fee = models.IntegerField()
    total_fee = models.IntegerField()
    total_fee_taxes = models.IntegerField()
    # Monto recibido
    transfer_amount = models.IntegerField()

    class Meta:
        ordering = ['-id']


class PaymentPaypal(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    creation_date = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=300)
    intent = models.CharField(max_length=300)
    status = models.CharField(max_length=300)
    payer_email_address = models.CharField(max_length=300)
    payer_payer_id = models.CharField(max_length=300)
    payer_address = models.CharField(max_length=300)
    payer_name = models.CharField(max_length=300)
    payer_surname = models.CharField(max_length=300)
    purchase_description = models.CharField(max_length=300)
    purchase_reference_id = models.CharField(max_length=300)
    purchase_amount = models.CharField(max_length=300)
    purchase_currency = models.CharField(max_length=300)
    purchase_email_address = models.CharField(max_length=300)
    purchase_merchant_id = models.CharField(max_length=300)
  
    class Meta:
        ordering = ['-id']


class PurchaseOrder(models.Model):
    '''
    Modelo que guarda los pagos confirmados de los usuarios de QueChamba.
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    quote = models.OneToOneField(Quote, on_delete=models.PROTECT)
    payment = models.ForeignKey(PaymentMP, on_delete=models.PROTECT, null=True)
    paypal = models.ForeignKey(PaymentPaypal, on_delete=models.PROTECT, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-id']


class ChamberIncome(models.Model):
    '''
    Modelo que registra los Ingresos del Chamber, se crea un registro posterior
    a la finalización y conformidad de un trabajo. Este modelo debe guardar
    el registro del Status del pago
    '''
    cw = models.OneToOneField(ContractedWork, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=STATUS_INCOME, max_length=1, default='0')
    chamber = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name="chamber_income")
    payment_date = models.DateTimeField(null=True, blank=True)
    payed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                 related_name="admin_income")
    operation_number = models.CharField(null=True, blank=True, max_length=50)
    bank_from = models.ForeignKey(Bank, null=True, blank=True,
                                  on_delete=models.PROTECT,
                                  related_name="bank_from") # Banco Origen
    account_from = models.CharField(null=True, blank=True,  max_length=50)
    bank_to = models.ForeignKey(Bank, null=True, blank=True,
                                on_delete=models.PROTECT,
                                related_name="bank_to")  # Banco Destino
    acccount_to = models.CharField(null=True, blank=True,  max_length=50)
    paypal = models.CharField(null=True, blank=True,  max_length=50)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_igv = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-id']