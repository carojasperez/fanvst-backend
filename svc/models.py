from django.db import models
from django.contrib.auth.models import User
from adminsite.baseinfo.models import SubCategory
import uuid
from adminsite.functions import user_image_path
from django.dispatch import receiver
from django.db.models.signals import post_delete


SVC_LEVEL = (
    ('0', 'Basic'),
    ('1', 'Standard'),
    ('2', 'Pro')
)

class SvcInclude(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# class SvcAdd(models.Model):
#     '''
#     Elementos adicionales opcionales al servicio.
#     '''
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     sub_category = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
#     name = models.CharField(max_length=100)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name


class Svc(models.Model):
    '''
    Se refiere a los servicios que publican los chambers con una tarifa
    pre establecida para que el cliente pueda comprarlo sin que sea necesaria
    una negociación previa.
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.PROTECT,
                                     null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']


class SvcOpt(models.Model):
    '''
    Se refiere a las opciones del servicio, idealmente cada servicio
    debe contar con 3 opciones, cada una con una tarifa diferente. 
    '''
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    svc = models.ForeignKey(Svc, on_delete=models.CASCADE,
                            related_name='svcopt')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    level = models.CharField(choices=SVC_LEVEL, max_length=1, default='0')
    includes = models.ManyToManyField(SvcInclude, blank=True)
    required_days = models.PositiveSmallIntegerField()
    revision = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ['svc', 'level']
        ordering = ['svc', 'level']


class SvcImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    svc = models.ForeignKey(Svc, on_delete=models.CASCADE,
                            related_name='svcimage')
    picture = models.ImageField(upload_to=user_image_path,
                                null=True, blank=True)


@receiver(post_delete, sender=SvcImage)
def submission_delete(sender, instance, **kwargs):
    instance.picture.delete(False) 