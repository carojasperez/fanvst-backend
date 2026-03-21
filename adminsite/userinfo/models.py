from django.db import models
from django.contrib.auth.models import User, Group
from adminsite.baseinfo.models import (Bank, Country, Department, District,
                                       Membership, MembershipPromoCode, Province,
                                       SubCategory)
from adminsite.functions import image_fix, user_image_path
from django.dispatch import receiver
from django.db.models.signals import post_save, post_init
import uuid


GENDER = (
    ('0', 'Femenino'),
    ('1', 'Masculino'),
    ('2', 'No especifica')
)

DOC_TYPE = (
    ('06', 'RUC'),
    ('01', 'DNI'),
    ('04', 'CE'),
    ('07', 'Pasaporte'),
)

ACCOUNT_TYPE = (
    ('0', 'Ahorros'),
    ('1', 'Corriente'),
)

SKILL_LEVEL = (
    ('0', 'Principiante'),
    ('1', 'Intermedio'),
    ('2', 'Maestro'),
)

ARTIST_TYPE = (
    ('musician', 'Músico'),
    ('band', 'Banda'),
    ('dj', 'DJ'),
    ('producer', 'Productor'),
    ('singer', 'Cantante'),
    ('composer', 'Compositor'),
    ('other', 'Otro'),
)


class Genre(models.Model):
    '''Géneros musicales disponibles en Fanvst.'''
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    '''
    Perfil general de usuarios.
    '''
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    email_confirmed = models.BooleanField(default=False)
    document_type = models.CharField(max_length=2, choices=DOC_TYPE,
                                     null=True, blank=True)
    document = models.CharField(max_length=100, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True,
                                blank=True, related_name='profcountry')
    nationality = models.ForeignKey(Country, on_delete=models.CASCADE,
                                    null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(choices=GENDER, max_length=1,
                              null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE,
                                 null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE,
                                 null=True, blank=True)
    city = models.CharField(max_length=80, blank=True, null=True)
    state = models.CharField(max_length=80, blank=True, null=True)
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=300, blank=True, null=True)
    address3 = models.CharField(max_length=300, blank=True, null=True)
    number = models.CharField(max_length=100, blank=True, null=True)
    floor = models.CharField(max_length=100, blank=True, null=True)
    dpto = models.CharField(max_length=100, blank=True, null=True)
    phone1 = models.CharField(max_length=100, blank=True, null=True) # Tlf Celular
    phone2 = models.CharField(max_length=100, blank=True, null=True) # Tlf Fijo
    picture = models.ImageField(upload_to=user_image_path,
                                null=True, blank=True)

    # ── Campos Fanvst ─────────────────────────────────────────────
    is_artist = models.BooleanField(default=False)
    stage_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    cover_picture = models.ImageField(upload_to=user_image_path,
                                      null=True, blank=True)
    artist_type = models.CharField(max_length=20, choices=ARTIST_TYPE,
                                   blank=True, null=True)
    location_display = models.CharField(max_length=120, blank=True, null=True,
                                        help_text='Ej: Lima, Perú')
    verified = models.BooleanField(default=False)
    genres = models.ManyToManyField('Genre', blank=True, related_name='artists')
    followers = models.ManyToManyField(User, blank=True,
                                       related_name='following_artists')

    class Meta:
        ordering = ['-id']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
   if created:
     Profile.objects.create(user=instance)
     # Se incluye al usuario en el grupo de permisos generales
     general = Group.objects.get(name='general') 
     general.user_set.add(instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class SocialAuth(models.Model):
    '''
    Almacena los datos relacionados al a autenticación por medio de redes
    sociales
    '''
    user = models.ForeignKey(User, models.CASCADE)
    provider_id = models.CharField(max_length=100)
    social_id = models.TextField()
    uid = models.TextField(null=True) # Firebase user ID
    id_token = models.TextField(null=True, blank=True)
    access_token = models.TextField()
    picture = models.URLField()


class EmailValidation(models.Model):
    # Almacena el token para verificar el correo
    user = models.ForeignKey(User, models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    uuid1 = models.UUIDField(default=uuid.uuid4, unique=True)
    uuid2 = models.UUIDField(default=uuid.uuid4, unique=True)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(auto_now=True)


class EmailPasswordReset(models.Model):
    # Almacena el token el reset de password, aca no usamos UUID sino
    # secrets.token_urlsafe()
    user = models.ForeignKey(User, models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    token1 = models.CharField(max_length=500)
    token2 = models.CharField(max_length=500)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(auto_now=True)


class Referral(models.Model):
    '''
    Codigo de referidos para promoción de difusión de la plataforma.
    '''
    user = models.ForeignKey(User, models.CASCADE)
    referred_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True,
                                    blank=True, related_name="user_referred_by")
    referred_at = models.DateTimeField(null=True, blank=True)
    refferral_code = models.UUIDField(default=uuid.uuid4, unique=True)


class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='user_device')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    device_token = models.CharField(unique=True, max_length=255)
    device_info = models.CharField(max_length=255)


class BankAccount(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE,
                             null=True, blank=True)
    account_type = models.CharField(choices=ACCOUNT_TYPE, max_length=1,
                                    null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    cci_number = models.CharField(max_length=100, null=True, blank=True)
    paypal = models.CharField(max_length=300, null=True, blank=True)


class Notification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='notification')


@receiver(post_save, sender=User)
def create_user_notification(sender, instance, created, **kwargs):
   if created:
     Notification.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_notification(sender, instance, created, **kwargs):
    if not created:
        Notification.objects.get_or_create(user=instance)
        instance.notification.save()
