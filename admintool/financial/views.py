from django.shortcuts import render
from rest_framework import permissions, status, views, viewsets
from django.db.models import Case, Count, F, Q, Sum, Value, When
from datetime import date, datetime, timedelta
import pytz


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