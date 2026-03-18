from django.db import models
from django.contrib.auth.models import User
from adminsite.functions import user_image_path


class Country(models.Model):
    '''
    Modelo gestionable solo por administradores
    Permite especificar el País.
    '''
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    iso3166 = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Department(models.Model):
    """
    Modelo que almacena los Departamento de Perú
    ISO 3166-2:PE
    """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='departments')
    iso3166_2 = models.CharField(max_length=3)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
        # return '%d: %s' % (self.id, self.name)

    class Meta:
        ordering = ['name']


class Province(models.Model):
    """
    Modelo que almacena las Provincias de Perú
    """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True, related_name='provinces')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class District(models.Model):
    """
    Modelo que almacena los distritos de Perú
    """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Bank(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Category(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SubCategory(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    keywords = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Membership(models.Model):
    '''
    Lleva el control de las membresías disponibles en Qué Chamba
    '''
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MembershipPromoCode(models.Model):
    '''
    Modelo que guarda las promociones de Que Chamba
    '''
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    for_chamber = models.BooleanField(default=True)
    membership = models.ForeignKey(Membership, models.CASCADE, null=True)
    months = models.PositiveSmallIntegerField(default=1)
