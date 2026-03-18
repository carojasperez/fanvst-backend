from django.shortcuts import render
from rest_framework import permissions, status, views, viewsets
from .serializers import PedingPaymentSer
from payment.models import ChamberIncome
from work.models import ContractedWork, Quote, WorkOffer
from django.db.models import Case, Count, F, Q, Sum, Value, When
from requests.models import Response
from admintool.financial.serializers import CountChamberSer, CountContractedWorkSer, OpenQuotesSer, OpenWorksSer, SalesPerMonthSer
from django.db.models.fields import CharField
from adminsite.userinfo.models import Profile
from adminsite.tasks import deposit_notification
from datetime import date, datetime, timedelta
import pytz


class OpenQuotes(viewsets.ModelViewSet):
    serializer_class = OpenQuotesSer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve cantidad de cotizaciones abiertas.
        '''
        qs = Quote.objects.filter(
            status='0'
            #  | Q(status='2') | Q(status='6')
        )

        qs = qs.values('status').annotate(
            total=Count('id', distinct=True)
        ).order_by('status')

        return qs


class OpenWorks(viewsets.ModelViewSet):
    serializer_class = OpenWorksSer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve cantidad de ofertas de trabajo abiertas.
        '''
        qs = WorkOffer.objects.filter(
            status='0' 
        )

        qs = qs.values('status').annotate(
            total=Count('id', distinct=True)
        ).order_by('status')

        return qs


class CountChambers(viewsets.ModelViewSet):
    serializer_class = CountChamberSer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve cantidad de Chambers registrados.
        '''
        qs = Profile.objects.filter(
            is_chamber=True 
        )

        qs = qs.values('is_chamber').annotate(
            total=Count('id', distinct=True)
        ).order_by('is_chamber')

        return qs


class CountContractedWork(viewsets.ModelViewSet):
    serializer_class = CountContractedWorkSer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve cantidad de trabajos contratados.
        '''
        qs = ContractedWork.objects.filter(
            status='0' 
        )

        qs = qs.values('status').annotate(
            total=Count('id', distinct=True)
        ).order_by('status')

        return qs


class SalesPerMonth(viewsets.ModelViewSet):
    serializer_class = SalesPerMonthSer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve las ventas mensuales
        '''
        qs = ChamberIncome.objects.all()

        qs = qs.values('created_at__month').annotate(
            total=Sum(F('fee')-F('fee_igv')-F('cw__po__payment__fee_amount'))
        ).order_by('created_at__month')

        return qs


class PendingPayment(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PedingPaymentSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuele las transferencias pendientes por realizar a los
        Chambers, ademas de la info necesaria para los pagos.
        '''
        status = self.request.query_params.get('status', None)

        qs = ChamberIncome.objects.all()

        if status is not None:
            qs = qs.filter(
                status=status
            )

        return qs 


class PendingPaymentBank(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PedingPaymentSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuele las transferencias pendientes por realizar a los
        Chambers, ademas de la info necesaria para los pagos.
        '''
        qs = ChamberIncome.objects.filter(
            status='0'
        )

        return qs


class RegisterPayment(views.APIView):
    '''
    Permite registrar el pago efectuado al Chamber.
    A su vez genera la notificación al Chamber
    '''
    permission_classes = [permissions.IsAdminUser]
    http_method_names= ['post']

    def post(self, serializer):

        inId = self.request.data.get('income', None)
        code = self.request.data.get('code', None)
        date = self.request.data.get('date', None)
        user = self.request.user

        # TODO: Agregar validador campos mandatorios..
        try:
            income = ChamberIncome.objects.get(id=inId)

            income.operation_number=code
            # income.payment_date=date
            income.payment_date=datetime.now(pytz.utc)
            income.payed_by = user
            income.paypal=income.chamber.bankaccount.paypal

            income.status='1'

            income.save()
            # Datos para el correo al chamber
            dp = {
                'paypal': income.paypal,
                'openumber': code,
                'date': date,
                'amount': income.cost
            }
            deposit_notification.delay(
                income.chamber.username,
                income.chamber.first_name,
                dp,
                income.cw.id
            )

            return Response({"corrrecto": ["Registro guardado"]}, 
                    status=status.HTTP_200_OK)

        except ChamberIncome.DoesNotExist:
            return Response({"id_invalid": ["El id suministrado no es valido."]}, 
                            status=status.HTTP_400_BAD_REQUEST)
# class PayToChamber(views.APIView):
#     # permission_classes 
#     http_method_names = ['post']

#     def post(self, request, *args, **kwargs):
#         pass