from django.db import models


DOC_TYPE = (
    ('06', 'RUC'),
    ('01', 'DNI'),
    ('04', 'CE'),
    ('07', 'Pasaporte'),
)

CLAIM_STATUS = (
    ('01', 'Abierto'),
    ('02', 'Respondido'),
    ('03', 'Resuelto')
)


class ComplaintBook(models.Model):
    '''
    Libro de reclamaciones exigido por la legislación Peruana
    '''
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    document_type = models.CharField(max_length=2, choices=DOC_TYPE)
    document = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    address = models.CharField(max_length=1000)
    attorney = models.CharField(max_length=500, blank=True, null=True) # representantes (menores de edad)
    is_service = models.BooleanField(default=True) # True: service, False: Product
    service_description = models.TextField()
    is_claim = models.BooleanField(default=True) # True: Reclamo, False: Queja
    claim_description = models.TextField()
    accept_terms = models.BooleanField(default=False)
    gtoken = models.BooleanField(default=False) # True: Ha sido validado el captcha
    status = models.CharField(max_length=2, choices=CLAIM_STATUS, default='01')

    def __str__(self):
        return self.name
