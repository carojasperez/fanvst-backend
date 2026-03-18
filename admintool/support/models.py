'''
APP de herramientas para dar soporte a las clinicas
afiliadas a dentisplan
'''
from django.db import models
from adminsite.models import User, Clinic
from django.utils.translation import gettext as _
from adminsite.functions import clinic_path
from parler.models import TranslatableModel, TranslatedFields
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from PIL import Image


class TicketCategory(TranslatableModel):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    internal_name = models.CharField(max_length=250)

    translations = TranslatedFields(
        title=models.CharField(max_length=150),
        description=models.CharField(max_length=500),
    )

    def __str__(self):
        return self.internal_name

    class Meta:
        ordering = ['-id']
        default_permissions = ()


class Ticket(models.Model):
    '''
    Cada ticket es un requerimiento de soporte del
    cliente
    '''
    TICKET_PRIORITY = (
        (0, _('Low')),
        (1, _('Medium')),
        (2, _('High')),
        (3, _('Urgent'))
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_tickets")
    update_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                  null=True,  blank=True)
    subject = models.CharField(max_length=200)
    priority = models.CharField(max_length=1, choices=TICKET_PRIORITY, default=0)
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT)
    '''
    module = Lista de modulos deberia ser un modelo de adminsite.
    la idea es que nos pueda indicar en que modulo tiene el problema
    '''
    class Meta:
        ordering = ['-id']
        default_permissions = ()


class TicketMsg(models.Model):
    '''
    Lleva el registro de la conversación de cada ticket
    '''
    TICKET_MSG_TYPE = (
        (0, _('System')),  # Maybe this never be used
        (1, _('Clinic')),  # msg from clinic
        (2, _('Admin')),  # msg from admin reply
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    msg_type = models.CharField(max_length=1, choices=TICKET_MSG_TYPE, default=1)
    is_readed = models.BooleanField(default=False)  # To future notifications...
    message = models.TextField()

    class Meta:
        ordering = ['-id']
        default_permissions = ()


class TicketMsgImage(models.Model):
    '''
    Imágenes adjuntas al mensaje en un ticket
    '''
    created_at = models.DateTimeField(auto_now_add=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    ticketMsg = models.ForeignKey(TicketMsg, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(blank=True, null=True, upload_to=clinic_path)

    class Meta:
        ordering = ['-id']
        default_permissions = ()

    @staticmethod
    def remember_state(sender, instance, **kwargs):
        instance.previous_image = instance.image


post_init.connect(TicketMsgImage.remember_state, sender=TicketMsgImage)


@receiver(post_save, sender=TicketMsgImage)
def compress_img(sender, instance, created, **kwargs):
    if (created or instance.image != instance.previous_image):
        if instance.image:
            new_pic = Image.open(instance.image.path)
            new_pic.save(instance.image.path, quality=60, optimize=True)
