from django.shortcuts import render
from rest_framework import status, viewsets, views
from payment.serializers import PurchaseOrderSer, ChamberIncomeSer
from adminsite.functions import SmallPagination
from payment.models import PurchaseOrder, ChamberIncome
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class PurchaseOrderAPI(viewsets.ModelViewSet):
    '''
    API para gestionar las ordenes de compra
    '''
    serializer_class = PurchaseOrderSer
    pagination_class = SmallPagination
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Las ordenes de compra solo pueden ser vistas por su usuario vinculado
        '''
        user = self.request.user
        id = self.request.query_params.get('id', None)

        qs = PurchaseOrder.objects.filter(
            user=user
        )

        if id is not None:
            qs = qs.filter(id=id)

        return qs


class ChamberIncomeApi(viewsets.ModelViewSet):
    '''
    API de los ingresos 
    '''
    serializer_class = ChamberIncomeSer
    pagination_class = SmallPagination
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Se filtran los ingresos del Chamber logueado
        '''
        user = self.request.user

        qs = ChamberIncome.objects.filter(
            chamber=user
        )

        return qs


