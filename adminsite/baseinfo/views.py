from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import views
from rest_framework import permissions
from .serializers import (DistrictSer, CountrySer, ProvinceSer, BankSer,
                          CategorySer, SubCategorySer)
from .models import (District, Country, Province, Department, Bank, Category,
                     SubCategory)


class DistrictAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = DistrictSer
    http_method_names = ['get']

    def get_queryset(self):
        province = self.request.query_params.get('province', None)
        '''
        Devuelve todos los distritos de la provincia seleccionada
        '''
        query_set = District.objects.filter(province=province)
        return query_set


class ProvinceAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = ProvinceSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve todos los distritos de la provincia seleccionada
        '''
        department = self.request.query_params.get('department', None)

        query_set = Province.objects.filter(department=department)
        return query_set


class DepartmentAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = ProvinceSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve todos los distritos de la provincia seleccionada
        '''
        query_set = Department.objects.all()
        return query_set


class BankAPI(viewsets.ModelViewSet):
    serializer_class = BankSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve el listado de Bancos
        '''
        query_set = Bank.objects.all()
        return query_set


class CategoryAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = CategorySer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve el listado de Bancos
        '''
        query_set = Category.objects.filter(
            is_active=True)

        return query_set


class SubCategoryAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = SubCategorySer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve el listado de Sub categorias
        '''
        category = self.request.query_params.get('category', None)
        if category is not None:
            query_set = SubCategory.objects.filter(
                category=category,
                category__is_active=True,
                is_active=True
                )
        else:
            query_set = SubCategory.objects.filter(
                is_active=True,
                category__is_active=True,
            )
        return query_set


class CountryAPI(viewsets.ModelViewSet):
    serializer_class = CountrySer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve el listado de paises.
        '''
        query_set = Country.objects.all()
        return query_set
