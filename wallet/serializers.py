from decimal import Decimal

from rest_framework import serializers

from .models import ArtistWallet, PayoutRequest, WalletConfig, WalletTransaction


class WalletBalanceSer(serializers.ModelSerializer):
    """Balance y configuración de la wallet del artista autenticado."""
    clearing_days_effective = serializers.SerializerMethodField()

    class Meta:
        model = ArtistWallet
        fields = [
            'currency',
            'balance_available',
            'balance_pending',
            'total_earned',
            'total_withdrawn',
            'auto_payout_enabled',
            'auto_payout_threshold',
            'clearing_days_effective',
        ]

    def get_clearing_days_effective(self, obj):
        return obj.get_clearing_days()


class WalletTransactionSer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'type',
            'category',
            'currency',
            'gross_amount',
            'fee_amount',
            'net_amount',
            'status',
            'available_at',
            'description',
            'created_at',
        ]


class PayoutRequestSer(serializers.ModelSerializer):
    """Lectura de una solicitud de payout (artista y admin)."""

    class Meta:
        model = PayoutRequest
        fields = [
            'id',
            'currency',
            'amount_requested',
            'transfer_fee',
            'amount_to_transfer',
            'provider',
            'provider_account_ref',
            'status',
            'is_automatic',
            'requested_at',
            'approved_at',
            'completed_at',
            'provider_reference',
            'failure_reason',
            'admin_notes',
        ]
        read_only_fields = fields


class PayoutRequestCreateSer(serializers.Serializer):
    """Input para que el artista solicite un payout."""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    provider = serializers.ChoiceField(choices=PayoutRequest.PROVIDER_CHOICES)
    provider_account_ref = serializers.CharField(
        max_length=300, required=False, default='',
        help_text='Email PayPal, cuenta MercadoPago, etc.',
    )
    bank_account_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text='ID de la cuenta bancaria (solo para Bank Transfer).',
    )

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('El monto debe ser mayor a cero.')

        config = WalletConfig.get()
        if value < config.min_payout_usd:
            raise serializers.ValidationError(
                f'El monto mínimo para retiro es ${config.min_payout_usd} USD.'
            )
        return value

    def validate(self, data):
        artist = self.context['request'].user

        try:
            wallet = artist.wallet
        except ArtistWallet.DoesNotExist:
            raise serializers.ValidationError('No tienes una wallet activa.')

        if wallet.balance_available < data['amount']:
            raise serializers.ValidationError(
                f'Balance insuficiente. '
                f'Disponible: {wallet.balance_available} {wallet.currency}'
            )

        # Solo un payout pendiente a la vez
        has_pending = PayoutRequest.objects.filter(
            artist=artist,
            status__in=[PayoutRequest.STATUS_PENDING, PayoutRequest.STATUS_APPROVED],
        ).exists()
        if has_pending:
            raise serializers.ValidationError(
                'Ya tienes una solicitud de payout en proceso. '
                'Espera a que sea procesada antes de crear una nueva.'
            )

        if data['provider'] == PayoutRequest.PROVIDER_BANK and not data.get('bank_account_id'):
            raise serializers.ValidationError(
                'Debes indicar una cuenta bancaria para transferencia bancaria.'
            )

        return data


# ── Admin serializers ─────────────────────────────────────────────────────────

class PayoutRequestAdminSer(serializers.ModelSerializer):
    """Vista completa para admin, incluye datos del artista."""
    artist_username = serializers.CharField(source='artist.username', read_only=True)
    artist_email = serializers.CharField(source='artist.email', read_only=True)

    class Meta:
        model = PayoutRequest
        fields = [
            'id',
            'artist_username',
            'artist_email',
            'currency',
            'amount_requested',
            'transfer_fee',
            'amount_to_transfer',
            'provider',
            'provider_account_ref',
            'status',
            'is_automatic',
            'requested_at',
            'approved_at',
            'approved_by_id',
            'completed_at',
            'provider_reference',
            'failure_reason',
            'admin_notes',
        ]


class PayoutApprovalSer(serializers.Serializer):
    """Input para que admin apruebe un payout."""
    payout_id = serializers.IntegerField()
    admin_notes = serializers.CharField(required=False, default='', allow_blank=True)


class PayoutCompleteSer(serializers.Serializer):
    """Input para que admin marque un payout como completado."""
    payout_id = serializers.IntegerField()
    provider_reference = serializers.CharField(
        max_length=300, required=False, default='',
        help_text='ID de la transferencia en el proveedor.',
    )
    transfer_fee = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=Decimal('0.00'),
    )


class PayoutCancelSer(serializers.Serializer):
    """Input para que admin rechace/cancele un payout."""
    payout_id = serializers.IntegerField()
    reason = serializers.CharField(
        max_length=500, required=False, default='', allow_blank=True,
    )
    admin_notes = serializers.CharField(required=False, default='', allow_blank=True)
