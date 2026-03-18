import datetime
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import serializers
from django.utils import timezone
from PIL import Image, ExifTags
from io import BytesIO
from django.core.files import File
import requests


def user_image_path(instance, filename):
    '''
    Obtiene la ruta para cada usuario, de esa forma se mantienen separados
    los media de cada cliente.
    '''
    model_name = instance._meta.model.__name__
    return '{model_name}/{path}/{Y}/{M}/{filename}'.format(
        model_name=model_name, path=instance.user.id,
        filename=filename, Y=datetime.datetime.now().year,
        M=datetime.datetime.now().month)


def user_file_path(instance, filename):
    '''
    Obtiene la ruta para cada usuario, de esa forma se mantienen separados
    los media de cada cliente.
    '''
    model_name = instance._meta.model.__name__
    return '{model_name}/{path}/{Y}/files/{filename}'.format(
        model_name=model_name, path=instance.user.id,
        filename=filename, Y=datetime.datetime.now().year)


class HeaderPagination(PageNumberPagination):

    def get_paginated_response(self, data):
        return Response(dict([
            ('x-page', self.page.number),
            ('x-total', self.page.paginator.count),
            ('x-per-page', self.page_size),
            ('x-total-pages', self.page.paginator.num_pages),
            ('data', data),
        ]))


class StandardPagination(HeaderPagination):
    page_size = 50
    max_page_size = 500


class MediumPagination(HeaderPagination):
    page_size = 20
    max_page_size = 50


class SmallPagination(HeaderPagination):
    page_size = 5
    max_page_size = 50


class DateTimeLocalTimeZone(serializers.DateTimeField):
    '''Solución al bug de timezone de django rest'''
    def to_representation(self, value):
        value = timezone.localtime(value)
        return super(DateTimeLocalTimeZone, self).to_representation(value)


def validate_recaptcha(gtoken):
    '''
    Valida la respuesta de google 
    https://www.google.com/recaptcha/api/siteverify?secret=D&response=uNdE
    '''
    secret = '6LfBEaMZAAAAAM3T0GeTsdThc8HjMCVMF8EtagtD'
    response = gtoken # request.GET['response']
    params = {
        'secret': secret,
        'response': response
    }
    r = requests.post(
        'https://www.google.com/recaptcha/api/siteverify', data=params)

    json = r.json()
    resp = json['success']

    return resp


def image_fix(self):
    '''
    Para las imagenes que provienen desde telefonos se encarga de
    girarlas según su orientación, de esta forma no aparecen volteadas
    en el frontend. Ademas hace una reducción considerable del tamaño y peso
    '''
    if self.picture:
        pilImage = Image.open(BytesIO(self.picture.read()))
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        try:
            exif = dict(pilImage.getexif())
            if exif[orientation] == 3:
                pilImage = pilImage.rotate(180, expand=True)
            elif exif[orientation] == 6:
                pilImage = pilImage.rotate(270, expand=True)
            elif exif[orientation] == 8:
                pilImage = pilImage.rotate(90, expand=True)
        except KeyError:
            pass
        if pilImage.mode != "RGB":
            pilImage = pilImage.convert("RGB")
        output = BytesIO()
        pilImage.save(output, format='JPEG', quality=75, dpi=(400,400))
        output.seek(0)
        self.picture = File(output, self.picture.name)


def get_paypal_token(url, client, secret):
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US'
    }
    d = {"grant_type" : "client_credentials"}

    url = url + 'v1/oauth2/token'
    r = requests.post(url, auth=(client, secret), headers=headers, data=d)

    json = r.json()
    print("Respuesta De token paypal")
    print(json['access_token'])
    return json['access_token']