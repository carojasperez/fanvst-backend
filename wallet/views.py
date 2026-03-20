"""
Views del artista para el sistema de wallets.

Endpoints montados bajo /wallet/ — requieren autenticación y perfil is_artist=True.
"""
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from .models import ArtistWallet, PayoutRequest, WalletTransaction
from .serializers import (
    PayoutRequestCreateSer,
    PayoutRequestSer,
    WalletBalanceSer,
    WalletTransactionSer,
)
from .services import debit_artist_wallet


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
