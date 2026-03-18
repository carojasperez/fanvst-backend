from django.contrib.auth.models import User
from django.db import models
from adminsite.baseinfo.models import Department, District, Province, SubCategory
import uuid
from svc.models import Svc
from adminsite.functions import user_file_path


STATUS_QUOTE = (
    ('0', 'Pendiente'),
    ('1', 'Visto'),
    ('2', 'Cotizado'),
    ('3', 'Aceptado'),
    ('4', 'Cancelado por Chamber'),
    ('5', 'Cancelado por Cliente'),
    ('6', 'Requiere mas Info.')
)

STATUS_WORK = (
    ('0', 'Por realizar'),
    ('1', 'Finalizado'),
    ('2', 'Conforme'),
    ('3', 'Cancelado')
)

STATUS_CONTRACT = (
    ('0', 'En proceso'),
    ('1', 'Finalizado'),
    ('2', 'Finalizado por Chamber'),
    ('4', 'Cancelado por Chamber'),
    ('5', 'Cancelado por Cliente'),
)


STATUS_DISPUTE = (
    ('0', 'En proceso'),
    ('1', 'Respuesta del Chamber'),
    ('2', 'Respuesta del Cliente'),
    ('4', 'Resuelto'),
    ('5', 'Cancelada por Cliente'),
)

# Solo para uso referencial, esto se guarda en el modelo CancelReason.
REASON = (
    # Quote Cliente
    ('A00', 'Precio muy elevado'),
    ('A01', 'He conseguido otro chamber'),
    ('A02', 'He conseguido mejor oferta en otra web'),
    ('A03', 'Ya no necesito el servicio'),
    ('A04', 'No tengo presupuesto para el trabajo'),
    ('A05', 'El Chamber me hizo sentir incomodo'),
    ('A06', 'El Chamber no respondió a tiempo'),
    # Quote Chamber
    ('B01', 'Ubicación del trabajo'),
    ('B02', 'El trabajo no corresponde a mi perfil'),
    ('B03', 'No tengo disponibilidad'),
    ('B04', 'El cliente me pide un precio no razonable'),
    ('B05', 'El cliente me exige condiciones no razonables'),

    # Contracted Customer Work
    ('C01', 'Ya no necesito el trabajo'),
    ('C02', 'El Chamber no se presentó al trabajo'),
    ('C03', 'El Chamber no respondió mis mensajes'),
    ('C04', 'Quiero presentar una disputa'),

    # Contracted Chamber Work
    ('D01', 'Ya no tengo disponibilidad'),
    ('D02', 'El cliente me exige condiciones no razonables'),

    # Work Cliente
    ('Z01', 'Precio muy elevado'),
    ('Z02', 'No He conseguido un chamber'),
    ('Z03', 'He conseguido mejor oferta en otra web'),
    ('Z04', 'Ya no necesito el servicio'),
    ('Z05', 'No tengo presupuesto para el trabajo'),
    ('Z06', 'No obtuve una oferta a tiempo'), 
)


class CancelReason(models.Model):
    '''
    Modelo que guarda los motivos de cancelación de una cotización,
    esto sirve para analisis estadisticos
    '''
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True,
                                   blank=True, related_name="cancelu_user")
    updated_at = models.DateTimeField(auto_now=True, null=True)
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)


class ComplainReason(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True,
                                   blank=True, related_name="creasonu_user")
    updated_at = models.DateTimeField(auto_now=True, null=True)
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)


class WorkOffer(models.Model):
    '''
    Registra la ofertas de trabajo publicadas por los clientes
    '''
    uuid1 = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=200, blank=True)
    job_description = models.TextField(default='')
    expire_date = models.DateField()
    flexible_time = models.BooleanField(default=False)
    time = models.TimeField(null=True, blank=True)
    say_price = models.BooleanField(default=True)
    tarif_from = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarif_to = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    req_hours = models.BooleanField(default=False)
    hours = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(choices=STATUS_WORK, max_length=1, default='0')
    accepted = models.BooleanField(default=False)
    accepted_date = models.DateTimeField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.ForeignKey(CancelReason, null=True, blank=True,
                                      on_delete=models.CASCADE)
    category = models.ManyToManyField(SubCategory, blank=True)
    remote_work = models.BooleanField(default=False)
    # Dirección en donde se necesita hacer el trabajo.
    department = models.ForeignKey(Department, on_delete=models.PROTECT, 
                                   null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, null=True,
                                 blank=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, null=True,
                                 blank=True)
    address = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']


class WorkOfferCandidate(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    work_offer = models.ForeignKey(WorkOffer, on_delete=models.CASCADE)
    chamber = models.ForeignKey(User, on_delete=models.PROTECT)
    info_required = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    message = models.TextField(blank=True)
    how_message = models.TextField(blank=True)
    customer_accepted = models.BooleanField(default=False)
    accepted_date = models.DateTimeField(null=True, blank=True)
    canceled = models.BooleanField(default=False)
    canceled_date = models.DateTimeField(null=True, blank=True)
    required_days = models.PositiveSmallIntegerField(default=0)
    revision = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ['work_offer', 'chamber']
        ordering = ['-id']


class Quote(models.Model):
    '''
    Solicitudes de cotización
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Solicitante
    chamber = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name="quote_chamber")
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, blank=True)
    job_description = models.TextField(default='')
    how_message = models.TextField(blank=True)
    expire_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    flexible_time = models.BooleanField(default=True)
    time = models.TimeField(null=True, blank=True)
    req_hours = models.BooleanField(default=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    work_offer = models.ForeignKey(WorkOffer, on_delete=models.PROTECT,
                                   blank=True, null=True)
    status = models.CharField(choices=STATUS_QUOTE, max_length=1, default='0')
    hours = models.PositiveSmallIntegerField(default=0)
    accepted = models.BooleanField(default=False)
    accepted_date = models.DateTimeField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.ForeignKey(CancelReason, null=True, blank=True,
                                      on_delete=models.CASCADE)
    is_svc = models.BooleanField(default=False)
    svc = models.ForeignKey(Svc, null=True, blank=True, on_delete=models.CASCADE)
    remote_work = models.BooleanField(default=True)
    required_days = models.PositiveSmallIntegerField(default=0)
    revision = models.PositiveSmallIntegerField(default=0)
    # Dirección en donde se necesita hacer el trabajo. DEPRECATED
    department = models.ForeignKey(Department, on_delete=models.PROTECT, 
                                   null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, null=True,
                                 blank=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, null=True,
                                 blank=True)

    class Meta:
        ordering = ['-id']


class QuoteReply(models.Model):
    '''
    Registra cada interacción de la cotización. 
    '''
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='qreply_user')
    is_client = models.BooleanField(default=False)
    message = models.TextField()
    how_message = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    required_days = models.PositiveSmallIntegerField(default=1)
    revision = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-id']


class QuoteFile(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    created_at = models.DateTimeField(auto_now_add=True)
    is_client = models.BooleanField(default=False)
    file = models.FileField(upload_to=user_file_path)
    filename = models.CharField(max_length=300, null=True, blank=True)


class ContractedWork(models.Model):
    '''
    Este modelo gestiona las Chambas contratadas, estas se generan de forma
    automatica posterior al pago Confirmado del cliente.
    Abreviado como: CW
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    created_at = models.DateTimeField(auto_now_add=True)
    chamber = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name="cwork_chamber")
    po = models.ForeignKey(to="payment.PurchaseOrder", on_delete=models.PROTECT)
    finished_date = models.DateTimeField(null=True, blank=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.ForeignKey(CancelReason, null=True, blank=True,
                                      on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CONTRACT,
                              max_length=1, default='0')

    class Meta:
        ordering = ['-id']


class CWMessage(models.Model):
    cw = models.ForeignKey(ContractedWork, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    created_at = models.DateTimeField(auto_now_add=True)
    is_client = models.BooleanField(default=False)
    message = models.TextField()

    class Meta:
        ordering = ['-id']


class CWComplain(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    cw = models.ForeignKey(ContractedWork, on_delete=models.CASCADE)
    reason = models.ForeignKey(ComplainReason, null=True, blank=True,
                               on_delete=models.PROTECT)
    message = models.TextField()


class CWReview(models.Model):
    '''
    Review del servicio, esto marca la conformidad del trabajo
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    chamber = models.ForeignKey(User, on_delete=models.PROTECT, null=True,
                                related_name="chamber_review")
    created_at = models.DateTimeField(auto_now_add=True)
    cw = models.OneToOneField(ContractedWork, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['-id']


class Dispute(models.Model):
    '''
    Disputas entre Cliente y Chamber respecto a un servicio
    '''
    cw = models.ForeignKey(ContractedWork, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT) # Cliente
    chamber = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name="dispute_chamber", null=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_customer = models.BooleanField(default=False)
    customer_prop = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_prop_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    chamber_prop = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    chamber_prop_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=2, choices=STATUS_DISPUTE, default=0)
 
    class Meta:
        ordering = ['-id']


class DisputeReply(models.Model):
    '''
    Registra cada interacción de la cotización. 
    '''
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='dispute_user')
    is_client = models.BooleanField(default=False)
    message = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-id']
