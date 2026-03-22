"""
Views del artista para el sistema de wallets.

Endpoints montados bajo /wallet/ — requieren autenticación y perfil is_artist=True.
"""
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from decimal import Decimal

from .models import ArtistWallet, PayoutRequest, WalletTransaction, DlocalPayment
from .serializers import (
    PayoutRequestCreateSer,
    PayoutRequestSer,
    WalletBalanceSer,
    WalletTransactionSer,
)
from .services import debit_artist_wallet, credit_artist_wallet
from .dlocal_service import (
    create_dlocal_payment,
    confirm_dlocal_payment,
    verify_webhook_signature,
    retrieve_dlocal_payment,
)
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


class IsArtist(permissions.BasePermission):
    """El usuario autenticado debe tener Profile.is_artist = True."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.is_artist
        )


# ── Balance ───────────────────────────────────────────────────────────────────

class WalletBalanceView(views.APIView):
    """
    GET /wallet/balance/
    Retorna el balance actual de la wallet del artista autenticado.
    """
    permission_classes = [permissions.IsAuthenticated, IsArtist]

    def get(self, request):
        try:
            wallet = request.user.wallet
        except ArtistWallet.DoesNotExist:
            return Response(
                {'detail': 'Wallet no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(WalletBalanceSer(wallet).data)


# ── Transacciones ─────────────────────────────────────────────────────────────

class WalletTransactionListView(generics.ListAPIView):
    """
    GET /wallet/transactions/
    Historial de transacciones del artista.

    Query params:
        type        CREDIT | DEBIT
        category    MEMBERSHIP_INCOME | FAN_FUNDING | CONTENT_SALE | PAYOUT | ...
        status      PENDING | CLEARED | COMPLETED | REVERSED
    """
    serializer_class = WalletTransactionSer
    permission_classes = [permissions.IsAuthenticated, IsArtist]

    def get_queryset(self):
        try:
            wallet = self.request.user.wallet
        except ArtistWallet.DoesNotExist:
            return WalletTransaction.objects.none()

        qs = wallet.transactions.all()

        tx_type = self.request.query_params.get('type')
        if tx_type:
            qs = qs.filter(type=tx_type)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        tx_status = self.request.query_params.get('status')
        if tx_status:
            qs = qs.filter(status=tx_status)

        return qs


# ── Payout ────────────────────────────────────────────────────────────────────

class PayoutRequestView(views.APIView):
    """
    GET  /wallet/payout/         → lista las solicitudes del artista
    POST /wallet/payout/request/ → crea una nueva solicitud
    """
    permission_classes = [permissions.IsAuthenticated, IsArtist]

    def get(self, request):
        qs = PayoutRequest.objects.filter(artist=request.user)
        return Response(PayoutRequestSer(qs, many=True).data)

    def post(self, request):
        ser = PayoutRequestCreateSer(data=request.data, context={'request': request})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        artist = request.user
        wallet = artist.wallet

        # Obtener cuenta bancaria si aplica
        bank_account = None
        if data['provider'] == PayoutRequest.PROVIDER_BANK and data.get('bank_account_id'):
            from adminsite.userinfo.models import BankAccount
            try:
                bank_account = BankAccount.objects.get(
                    id=data['bank_account_id'], user=artist,
                )
            except BankAccount.DoesNotExist:
                return Response(
                    {'bank_account_id': ['Cuenta bancaria no encontrada.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Reservar fondos: crea WalletTransaction DEBIT
        tx = debit_artist_wallet(
            artist=artist,
            amount=data['amount'],
            currency=wallet.currency,
            category=WalletTransaction.CAT_PAYOUT,
            description=f'Payout request — {data["provider"]}',
        )

        payout = PayoutRequest.objects.create(
            artist=artist,
            wallet_transaction=tx,
            currency=wallet.currency,
            amount_requested=data['amount'],
            transfer_fee=0,
            amount_to_transfer=data['amount'],
            provider=data['provider'],
            provider_account_ref=data.get('provider_account_ref', ''),
            bank_account=bank_account,
        )

        return Response(
            PayoutRequestSer(payout).data,
            status=status.HTTP_201_CREATED,
        )


class PayoutRequestDetailView(views.APIView):
    """
    GET /wallet/payout/<pk>/
    Detalle de una solicitud de payout del artista autenticado.
    """
    permission_classes = [permissions.IsAuthenticated, IsArtist]

    def get(self, request, pk):
        try:
            payout = PayoutRequest.objects.get(pk=pk, artist=request.user)
        except PayoutRequest.DoesNotExist:
            return Response(
                {'detail': 'No encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PayoutRequestSer(payout).data)

# ── dLocal Go Integración ─────────────────────────────────────────────────────

class CreatePaymentView(views.APIView):
    """
    POST /wallet/payment/create/
    Endpoint para crear una intención de pago en dLocal Go.
    Se espera: amount, currency, description, reference_id, reference_model, is_transparent
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'USD')
        description = request.data.get('description', 'FanVST Payment')
        is_transparent = request.data.get('is_transparent', True)
        
        # Integración con el modelo de Referencia
        target_model = request.data.get('reference_model', 'directtip')
        target_id = request.data.get('reference_id')

        try:
            # Importación dinámica del modelo
            from django.apps import apps
            ModelKlass = apps.get_model('fanvst', target_model)
            if target_model.lower() == 'campaign':
                obj = ModelKlass.objects.get(uuid=target_id)
            else:
                obj = ModelKlass.objects.get(pk=target_id)
            ct = ContentType.objects.get_for_model(obj)
        except Exception:
            return Response({'error': 'Invalid reference'}, status=status.HTTP_400_BAD_REQUEST)

        # URLs de redirección para fallback o 3DS
        origin = request.headers.get('Origin', 'http://localhost:4900').rstrip('/')
        success_url = f"{origin}/campaigns"
        back_url = f"{origin}/campaigns"
        notification_url = request.build_absolute_uri('/wallet/payment/webhook/')

        dlocal_res = create_dlocal_payment(
            amount=amount, 
            currency=currency, 
            description=description,
            success_url=success_url,
            back_url=back_url,
            notification_url=notification_url,
            allow_transparent=is_transparent
        )

        if not dlocal_res.get('success'):
            return Response(
                {
                    'error': dlocal_res.get('error'),
                    'api_error': dlocal_res.get('api_error'),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Crear DlocalPayment en BD para tracking interno
        dp = DlocalPayment.objects.create(
            dlocal_payment_id=dlocal_res['payment_id'],
            amount=amount,
            currency=currency,
            reference_ct=ct,
            reference_id=obj.pk,
            checkout_url=dlocal_res.get('checkout_url', ''),
            status=DlocalPayment.STATUS_PENDING
        )

        return Response({
            'checkout_url': dlocal_res.get('checkout_url'),
            'payment_id': dlocal_res['payment_id'],
            'checkout_token': dlocal_res.get('checkout_token'),
            'status': 'PENDING'
        })


class ConfirmPaymentView(views.APIView):
    """
    POST /wallet/payment/confirm/
    Endpoint para confirmar un pago Transparent Checkout de dLocal Go.
    Se espera: payment_id (DB id), checkout_token (merchant_checkout_token) y card_token
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        checkout_token = request.data.get('checkout_token')
        card_token = request.data.get('card_token')
        
        if not payment_id or not checkout_token or not card_token:
            return Response({'error': 'Missing payment parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            dp = DlocalPayment.objects.get(dlocal_payment_id=payment_id)
        except DlocalPayment.DoesNotExist:
            return Response({'error': 'Payment intent not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if dp.status == DlocalPayment.STATUS_PAID:
            return Response({'status': 'PAID', 'message': 'Payment already processed'})
            
        # Llamar a dLocal Go
        profile = getattr(request.user, 'profile', None)
        req_first_name = (request.data.get('client_first_name') or '').strip()
        req_last_name = (request.data.get('client_last_name') or '').strip()
        req_document_type = (request.data.get('client_document_type') or '').strip().upper()
        req_document = (request.data.get('client_document') or '').strip()
        req_email = (request.data.get('client_email') or '').strip()
        req_phone = (request.data.get('client_phone') or '').strip()

        client_data = {
            "clientFirstName": req_first_name or request.user.first_name or "Guest",
            "clientLastName": req_last_name or request.user.last_name or "User",
            "clientEmail": req_email or request.user.email,
            "clientPhone": req_phone or getattr(profile, 'phone1', None) or "",
        }

        document_type_map = {
            '01': 'DNI',
            '04': 'CE',
            '06': 'RUC',
            '07': 'PASSPORT',
        }
        document_type = req_document_type or getattr(profile, 'document_type', None)
        document = req_document or getattr(profile, 'document', None)
        if document_type and document:
            client_data["clientDocumentType"] = document_type_map.get(document_type, document_type)
            client_data["clientDocument"] = document
        else:
            return Response(
                {
                    'error': 'Missing required payer fields',
                    'missing': ['client_document_type', 'client_document'],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        country_iso = "PE"
        if getattr(profile, 'country', None):
            iso = getattr(profile.country, 'iso3166', '') or ''
            country_iso = (iso[:2] or "PE").upper()

        res = confirm_dlocal_payment(checkout_token, card_token, client_data, country=country_iso)
        
        if not res.get('success'):
            return Response(
                {
                    'error': res.get('error'),
                    'api_error': res.get('api_error'),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
        raw_status = res.get('raw_data', {}).get('status', 'PENDING')
        
        # El endpoint /confirm puede retornar success=True en el JSON
        if raw_status == 'PAID' or res.get('raw_data', {}).get('success') is True:
            dp.status = DlocalPayment.STATUS_PAID
            dp.save()
            
            # Acreditar
            obj = dp.reference_object
            
            # Buscar el artista (dueño de la billetera)
            artist_profile = None
            if hasattr(obj, 'campaign') and hasattr(obj.campaign, 'artist'):
                # Caso CampaignContribution
                artist_profile = obj.campaign.artist
            elif hasattr(obj, 'artist'):
                # Caso DirectTip o similar
                artist_profile = obj.artist

            artist_user = getattr(artist_profile, 'user', None) if artist_profile else None
                
            if artist_user:
                fee = dp.amount * Decimal('0.10')
                credit_artist_wallet(
                    artist=artist_user,
                    gross_amount=dp.amount,
                    fee_amount=fee,
                    currency=dp.currency,
                    category=WalletTransaction.CAT_FAN_FUNDING,
                    reference_obj=obj,
                    description=f"dLocal Payment: {dp.dlocal_payment_id}"
                )
                if hasattr(obj, 'confirmed'):
                    obj.confirmed = True
                    obj.save()
                    
            return Response({'status': 'PAID'})
            
        # Si requiere 3DS auth
        if res.get('raw_data', {}).get('redirect_url'):
             return Response({'status': 'ACTION_REQUIRED', 'redirect_url': res.get('raw_data', {}).get('redirect_url')})
             
        if raw_status in ['PENDING', 'AUTHORIZED']:
            return Response({'status': raw_status, 'message': 'Payment is being processed'})
            
        dp.status = DlocalPayment.STATUS_REJECTED
        dp.save()
        return Response({'status': raw_status, 'error': f'Payment status: {raw_status}'})


class DlocalWebhookView(views.APIView):
    """
    POST /wallet/payment/webhook/
    Recibe la confirmación asíncrona de un pago desde dLocal Go.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 1. Validar la firma
        signature = request.headers.get('Authorization', '') or request.headers.get('X-Signature', '')
        if not verify_webhook_signature(request.body, signature):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        payment_id = data.get('payment_id') or data.get('id')
        payment_status = data.get('status')

        if not payment_id:
            return Response({'error': 'Missing payment id in webhook'}, status=status.HTTP_400_BAD_REQUEST)

        if not payment_status:
            payment_lookup = retrieve_dlocal_payment(payment_id)
            if not payment_lookup.get('success'):
                return Response(
                    {
                        'error': 'Could not retrieve payment status',
                        'details': payment_lookup.get('error'),
                        'api_error': payment_lookup.get('api_error'),
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            payment_status = payment_lookup.get('raw_data', {}).get('status')

        try:
            dlocal_payment = DlocalPayment.objects.get(dlocal_payment_id=payment_id)
        except DlocalPayment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        if payment_status == 'PAID' and dlocal_payment.status != DlocalPayment.STATUS_PAID:
            dlocal_payment.status = DlocalPayment.STATUS_PAID
            dlocal_payment.save()
            
            # 2. Acreditar la Wallet del Artista
            order = dlocal_payment.reference_object
            
            # Buscar el artista (dueño de la billetera)
            artist_profile = None
            if hasattr(order, 'campaign') and hasattr(order.campaign, 'artist'):
                artist_profile = order.campaign.artist
            elif hasattr(order, 'artist'):
                artist_profile = order.artist

            artist_user = getattr(artist_profile, 'user', None) if artist_profile else None
                
            if artist_user:
                # Calcular fees (ejemplo 10%)
                fee = dlocal_payment.amount * Decimal('0.10')
                
                credit_artist_wallet(
                    artist=artist_user,
                    gross_amount=dlocal_payment.amount,
                    fee_amount=fee,
                    currency=dlocal_payment.currency,
                    category=WalletTransaction.CAT_FAN_FUNDING,
                    reference_obj=order,
                    description=f"dLocal Payment: {payment_id}"
                )
                
                # Opcionalmente marcar la orden (obj) como confirmada
                if hasattr(order, 'confirmed'):
                    order.confirmed = True
                    order.save()

        elif payment_status in ['REJECTED', 'CANCELLED']:
            dlocal_payment.status = DlocalPayment.STATUS_REJECTED
            dlocal_payment.save()

        return Response({'status': 'ok'})
