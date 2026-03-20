from django.contrib import admin
from django.utils.html import format_html

from .models import ArtistWallet, PayoutRequest, WalletConfig, WalletTransaction


@admin.register(WalletConfig)
class WalletConfigAdmin(admin.ModelAdmin):
    """Singleton de configuración — siempre edita el registro pk=1."""

    fieldsets = (
        ('Clearing', {
            'description': 'Días que los fondos permanecen en período de retención antes de '
                           'estar disponibles para retiro.',
            'fields': ('clearing_days_default',),
        }),
        ('Payouts', {
            'fields': ('min_payout_usd', 'auto_payout_day'),
        }),
    )

    def has_add_permission(self, request):
        return not WalletConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = (
        'type', 'category', 'currency',
        'gross_amount', 'fee_amount', 'net_amount',
        'status', 'available_at', 'description', 'created_at',
    )
    fields = readonly_fields
    can_delete = False
    max_num = 0
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ArtistWallet)
class ArtistWalletAdmin(admin.ModelAdmin):
    list_display = (
        'artist_username', 'currency',
        'balance_available', 'balance_pending',
        'total_earned', 'total_withdrawn',
        'clearing_days_display', 'auto_payout_enabled',
    )
    list_filter = ('currency', 'auto_payout_enabled')
    search_fields = ('artist__username', 'artist__email')
    readonly_fields = ('total_earned', 'total_withdrawn', 'created_at', 'updated_at')

    fieldsets = (
        ('Artista', {
            'fields': ('artist', 'currency'),
        }),
        ('Balances', {
            'fields': ('balance_available', 'balance_pending', 'total_earned', 'total_withdrawn'),
        }),
        ('Clearing', {
            'description': 'Dejar "Clearing days override" vacío para usar el valor global '
                           'definido en Wallet Configuration.',
            'fields': ('clearing_days',),
        }),
        ('Auto-payout', {
            'fields': ('auto_payout_enabled', 'auto_payout_threshold'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [WalletTransactionInline]

    @admin.display(description='Artist')
    def artist_username(self, obj):
        return obj.artist.username

    @admin.display(description='Clearing days')
    def clearing_days_display(self, obj):
        if obj.clearing_days is not None:
            return format_html('<b>{}</b> (override)', obj.clearing_days)
        global_val = WalletConfig.get().clearing_days_default
        return format_html('{} (global)', global_val)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'artist_username', 'type', 'category',
        'currency', 'gross_amount', 'fee_amount', 'net_amount',
        'status', 'available_at',
    )
    list_filter = ('type', 'category', 'status', 'currency')
    search_fields = ('wallet__artist__username', 'description')
    readonly_fields = (
        'wallet', 'type', 'category', 'currency',
        'gross_amount', 'fee_amount', 'net_amount',
        'reference_ct', 'reference_id',
        'available_at', 'created_at',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Transacción', {
            'fields': ('wallet', 'type', 'category', 'status'),
        }),
        ('Montos', {
            'fields': ('currency', 'gross_amount', 'fee_amount', 'net_amount'),
        }),
        ('Timing', {
            'fields': ('available_at', 'created_at'),
        }),
        ('Referencia', {
            'fields': ('reference_ct', 'reference_id', 'description'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Artist')
    def artist_username(self, obj):
        return obj.wallet.artist.username


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = (
        'requested_at', 'artist_username', 'currency',
        'amount_requested', 'transfer_fee', 'amount_to_transfer',
        'provider', 'status', 'is_automatic',
    )
    list_filter = ('status', 'provider', 'currency', 'is_automatic')
    search_fields = ('artist__username', 'artist__email', 'provider_account_ref', 'provider_reference')
    readonly_fields = (
        'artist', 'wallet_transaction', 'currency',
        'amount_requested', 'is_automatic',
        'requested_at', 'approved_at', 'approved_by',
        'processed_at', 'completed_at',
    )
    date_hierarchy = 'requested_at'
    ordering = ('-requested_at',)

    fieldsets = (
        ('Solicitud', {
            'fields': ('artist', 'currency', 'amount_requested', 'is_automatic', 'requested_at'),
        }),
        ('Transferencia', {
            'fields': (
                'provider', 'provider_account_ref', 'bank_account',
                'transfer_fee', 'amount_to_transfer',
            ),
        }),
        ('Estado', {
            'fields': ('status', 'provider_reference', 'failure_reason'),
        }),
        ('Admin', {
            'fields': ('approved_by', 'approved_at', 'completed_at', 'admin_notes'),
        }),
        ('Ledger', {
            'fields': ('wallet_transaction',),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description='Artist')
    def artist_username(self, obj):
        return obj.artist.username
