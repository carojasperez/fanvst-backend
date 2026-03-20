from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('PEN', 'Peruvian Sol'),
    ('MXN', 'Mexican Peso'),
    ('COP', 'Colombian Peso'),
    ('ARS', 'Argentine Peso'),
    ('BRL', 'Brazilian Real'),
    ('CLP', 'Chilean Peso'),
]


class WalletConfig(models.Model):
    """
    Configuración global del sistema de wallets (singleton).
    Solo puede existir un registro (pk=1).
    """
    clearing_days_default = models.PositiveIntegerField(
        default=14,
        help_text='Días antes de que los fondos estén disponibles para retirar (default global).',
    )
    min_payout_usd = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('10.00'),
        help_text='Monto mínimo en USD para solicitar un payout.',
    )
    auto_payout_day = models.PositiveIntegerField(
        default=1,
        help_text='Día del mes en que se ejecutan los auto-payouts (1–28).',
    )

    class Meta:
        verbose_name = 'Wallet Configuration'
        verbose_name_plural = 'Wallet Configuration'

    def __str__(self):
        return (
            f'Wallet Config — clearing={self.clearing_days_default}d  '
            f'min_payout=${self.min_payout_usd}'
        )

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ArtistWallet(models.Model):
    """
    Cartera virtual del artista. Registra balances en tiempo real.
    Se crea automáticamente cuando Profile.is_artist = True.
    """
    artist = models.OneToOneField(User, on_delete=models.PROTECT, related_name='wallet')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    # Balances
    balance_available = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Fondos disponibles para retirar ahora.',
    )
    balance_pending = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Fondos en período de clearing, aún no retirables.',
    )
    total_earned = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Total acumulado histórico (neto después de fees).',
    )
    total_withdrawn = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Total retirado históricamente.',
    )

    # Clearing override por artista
    clearing_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Override del período de clearing para este artista. '
                  'Dejar vacío para usar el valor global.',
    )

    # Auto-payout
    auto_payout_enabled = models.BooleanField(default=False)
    auto_payout_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('10.00'),
        help_text='Balance mínimo requerido para disparar el auto-payout mensual.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Artist Wallet'
        verbose_name_plural = 'Artist Wallets'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Wallet({self.artist.username})  '
            f'{self.currency}  '
            f'available={self.balance_available}  '
            f'pending={self.balance_pending}'
        )

    def get_clearing_days(self):
        """Retorna el clearing_days efectivo: override propio o el valor global."""
        if self.clearing_days is not None:
            return self.clearing_days
        return WalletConfig.get().clearing_days_default


class WalletTransaction(models.Model):
    """
    Ledger completo de la cartera del artista.
    Cada centavo que entra o sale queda registrado aquí.
    El balance de ArtistWallet es siempre derivable de estas transacciones.
    """

    # ── Tipos ────────────────────────────────────────────────────────────────
    TYPE_CREDIT = 'CREDIT'
    TYPE_DEBIT = 'DEBIT'
    TYPE_CHOICES = [
        (TYPE_CREDIT, 'Credit'),
        (TYPE_DEBIT, 'Debit'),
    ]

    # ── Categorías ───────────────────────────────────────────────────────────
    CAT_MEMBERSHIP_INCOME = 'MEMBERSHIP_INCOME'
    CAT_FAN_FUNDING = 'FAN_FUNDING'
    CAT_CONTENT_SALE = 'CONTENT_SALE'
    CAT_PLATFORM_FEE = 'PLATFORM_FEE'
    CAT_PAYOUT = 'PAYOUT'
    CAT_REFUND = 'REFUND'
    CAT_CHARGEBACK = 'CHARGEBACK'
    CAT_ADJUSTMENT = 'ADJUSTMENT'
    CATEGORY_CHOICES = [
        (CAT_MEMBERSHIP_INCOME, 'Membership Income'),
        (CAT_FAN_FUNDING, 'Fan Funding'),
        (CAT_CONTENT_SALE, 'Content Sale'),
        (CAT_PLATFORM_FEE, 'Platform Fee'),
        (CAT_PAYOUT, 'Payout'),
        (CAT_REFUND, 'Refund'),
        (CAT_CHARGEBACK, 'Chargeback'),
        (CAT_ADJUSTMENT, 'Manual Adjustment'),
    ]

    # ── Estados ──────────────────────────────────────────────────────────────
    STATUS_PENDING = 'PENDING'
    STATUS_CLEARED = 'CLEARED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_REVERSED = 'REVERSED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending (in clearing)'),
        (STATUS_CLEARED, 'Cleared (available)'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REVERSED, 'Reversed'),
    ]

    # ── Campos ───────────────────────────────────────────────────────────────
    wallet = models.ForeignKey(
        ArtistWallet, on_delete=models.PROTECT, related_name='transactions',
    )
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    gross_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto bruto (lo que pagó el fan).',
    )
    fee_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Fee de la plataforma descontado al ingreso.',
    )
    net_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto neto acreditado al artista (gross - fee).',
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    available_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha/hora en que los fondos estarán disponibles para retirar.',
    )

    # Generic FK: referencia al objeto origen (PurchaseOrder, FanFunding, etc.)
    reference_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL,
    )
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    reference_object = GenericForeignKey('reference_ct', 'reference_id')

    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wallet Transaction'
        verbose_name_plural = 'Wallet Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'status']),
            models.Index(fields=['status', 'available_at']),
        ]

    def __str__(self):
        return (
            f'{self.type} {self.net_amount} {self.currency} '
            f'[{self.status}] — {self.wallet.artist.username}'
        )


class PayoutRequest(models.Model):
    """
    Solicitud de retiro del artista.

    Ciclo de vida:
        PENDING → APPROVED → COMPLETED
        PENDING → CANCELLED  (rechazado por admin o cancelado por artista)
        APPROVED → CANCELLED (rechazado antes de ejecutar)
        APPROVED → FAILED    (error en la transferencia)

    Al crearse se genera un WalletTransaction DEBIT que reserva los fondos.
    Si se cancela/falla, esa transacción se revierte y los fondos regresan.
    """

    PROVIDER_MERCADOPAGO = 'MERCADOPAGO'
    PROVIDER_PAYPAL = 'PAYPAL'
    PROVIDER_BANK = 'BANK_TRANSFER'
    PROVIDER_CHOICES = [
        (PROVIDER_MERCADOPAGO, 'MercadoPago'),
        (PROVIDER_PAYPAL, 'PayPal'),
        (PROVIDER_BANK, 'Bank Transfer'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending (awaiting admin approval)'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    artist = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='payout_requests',
    )
    wallet_transaction = models.OneToOneField(
        WalletTransaction, on_delete=models.PROTECT,
        related_name='payout_request',
        help_text='Transacción DEBIT que reserva los fondos.',
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    amount_requested = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto solicitado por el artista.',
    )
    transfer_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Fee de la transferencia bancaria/proveedor.',
    )
    amount_to_transfer = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto que efectivamente recibirá el artista (amount_requested - transfer_fee).',
    )
    provider = models.CharField(max_length=15, choices=PROVIDER_CHOICES)
    bank_account = models.ForeignKey(
        'userinfo.BankAccount',
        on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Cuenta bancaria destino (solo para Bank Transfer).',
    )
    provider_account_ref = models.CharField(
        max_length=300, blank=True,
        help_text='Email PayPal, cuenta MercadoPago, etc.',
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING,
    )
    is_automatic = models.BooleanField(
        default=False,
        help_text='True si fue generado por el auto-payout mensual.',
    )

    # Timestamps de ciclo de vida
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_payouts',
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    provider_reference = models.CharField(
        max_length=300, blank=True,
        help_text='ID externo de la transferencia (proveedor de pagos).',
    )
    failure_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Payout Request'
        verbose_name_plural = 'Payout Requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['artist', 'status']),
            models.Index(fields=['status', 'requested_at']),
        ]

    def __str__(self):
        return (
            f'PayoutRequest #{self.pk} — {self.artist.username}  '
            f'{self.amount_requested} {self.currency}  [{self.status}]'
        )

    def approve(self, admin_user):
        """Transición PENDING → APPROVED."""
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = admin_user
        self.save(update_fields=['status', 'approved_at', 'approved_by'])

    def complete(self, provider_reference='', transfer_fee=None):
        """
        Transición APPROVED → COMPLETED.
        Finaliza la WalletTransaction DEBIT y actualiza total_withdrawn.
        """
        from django.db.models import F

        if transfer_fee is not None:
            self.transfer_fee = transfer_fee
            self.amount_to_transfer = self.amount_requested - transfer_fee

        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.provider_reference = provider_reference
        self.save(update_fields=[
            'status', 'completed_at', 'provider_reference',
            'transfer_fee', 'amount_to_transfer',
        ])

        self.wallet_transaction.status = WalletTransaction.STATUS_COMPLETED
        self.wallet_transaction.save(update_fields=['status'])

        ArtistWallet.objects.filter(pk=self.artist.wallet.pk).update(
            total_withdrawn=F('total_withdrawn') + self.amount_requested,
        )

    def cancel(self, reason=''):
        """
        Transición PENDING/APPROVED → CANCELLED.
        Revierte la reserva: devuelve fondos a balance_available.
        """
        from django.db.models import F

        self.status = self.STATUS_CANCELLED
        self.failure_reason = reason
        self.save(update_fields=['status', 'failure_reason'])

        self.wallet_transaction.status = WalletTransaction.STATUS_REVERSED
        self.wallet_transaction.save(update_fields=['status'])

        ArtistWallet.objects.filter(pk=self.artist.wallet.pk).update(
            balance_available=F('balance_available') + self.amount_requested,
        )
