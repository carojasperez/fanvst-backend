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
# ── Artist Payout Admin Views ─────────────────────────────────────────────────

class ArtistPayoutList(views.APIView):
    """
    GET /financial/data/API/artist-payouts/
    Lista solicitudes de payout de artistas.

    Query params:
        status      PENDING | APPROVED | COMPLETED | FAILED | CANCELLED
        artist      username del artista (filtro parcial)
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from wallet.models import PayoutRequest
        from wallet.serializers import PayoutRequestAdminSer

        qs = PayoutRequest.objects.select_related('artist', 'approved_by').all()

        payout_status = request.query_params.get('status')
        if payout_status:
            qs = qs.filter(status=payout_status)

        artist = request.query_params.get('artist')
        if artist:
            qs = qs.filter(artist__username__icontains=artist)

        return Response(PayoutRequestAdminSer(qs, many=True).data)


class ArtistPayoutApprove(views.APIView):
    """
    POST /financial/data/API/artist-payout-approve/
    Aprueba una solicitud de payout (PENDING → APPROVED).
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from wallet.models import PayoutRequest
        from wallet.serializers import PayoutApprovalSer, PayoutRequestAdminSer

        ser = PayoutApprovalSer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            payout = PayoutRequest.objects.get(pk=ser.validated_data['payout_id'])
        except PayoutRequest.DoesNotExist:
            return Response(
                {'payout_id': ['No encontrado.']},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payout.status != PayoutRequest.STATUS_PENDING:
            return Response(
                {'detail': f'No se puede aprobar un payout en estado {payout.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ser.validated_data.get('admin_notes'):
            payout.admin_notes = ser.validated_data['admin_notes']
            payout.save(update_fields=['admin_notes'])

        payout.approve(admin_user=request.user)
        return Response(PayoutRequestAdminSer(payout).data)


class ArtistPayoutComplete(views.APIView):
    """
    POST /financial/data/API/artist-payout-complete/
    Marca un payout como completado (APPROVED → COMPLETED).
    Requiere el reference ID del proveedor de pagos.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from wallet.models import PayoutRequest
        from wallet.serializers import PayoutCompleteSer, PayoutRequestAdminSer

        ser = PayoutCompleteSer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            payout = PayoutRequest.objects.get(pk=ser.validated_data['payout_id'])
        except PayoutRequest.DoesNotExist:
            return Response(
                {'payout_id': ['No encontrado.']},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payout.status != PayoutRequest.STATUS_APPROVED:
            return Response(
                {'detail': f'Solo se pueden completar payouts en estado APPROVED. Estado actual: {payout.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payout.complete(
            provider_reference=ser.validated_data.get('provider_reference', ''),
            transfer_fee=ser.validated_data.get('transfer_fee'),
        )
        return Response(PayoutRequestAdminSer(payout).data)


class ArtistPayoutCancel(views.APIView):
    """
    POST /financial/data/API/artist-payout-cancel/
    Cancela/rechaza un payout (PENDING o APPROVED → CANCELLED).
    Revierte los fondos al balance disponible del artista.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from wallet.models import PayoutRequest
        from wallet.serializers import PayoutCancelSer, PayoutRequestAdminSer

        ser = PayoutCancelSer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            payout = PayoutRequest.objects.get(pk=ser.validated_data['payout_id'])
        except PayoutRequest.DoesNotExist:
            return Response(
                {'payout_id': ['No encontrado.']},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payout.status not in [PayoutRequest.STATUS_PENDING, PayoutRequest.STATUS_APPROVED]:
            return Response(
                {'detail': f'No se puede cancelar un payout en estado {payout.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ser.validated_data.get('admin_notes'):
            payout.admin_notes = ser.validated_data['admin_notes']
            payout.save(update_fields=['admin_notes'])

        payout.cancel(reason=ser.validated_data.get('reason', ''))
        return Response(PayoutRequestAdminSer(payout).data)