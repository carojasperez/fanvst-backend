"""
Utilidades del sistema de wallets.

Usar credit_artist_wallet() desde cualquier view, task o signal
cuando se confirme un pago a un artista.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import ArtistWallet, WalletTransaction


def credit_artist_wallet(
    artist,
    gross_amount: Decimal,
    fee_amount: Decimal,
    currency: str,
    category: str,
    reference_obj=None,
    description: str = '',
) -> WalletTransaction:
    """
    Acredita la wallet de un artista.

    - Crea un WalletTransaction en estado PENDING.
    - Suma net_amount a balance_pending y total_earned.
    - available_at se calcula según el clearing_days del artista (o global).

    Args:
        artist:         instancia de User (el artista)
        gross_amount:   monto bruto que pagó el fan
        fee_amount:     fee de la plataforma (se descuenta aquí, al ingreso)
        currency:       código de moneda (ej. 'USD', 'PEN')
        category:       una de WalletTransaction.CAT_* constants
        reference_obj:  objeto origen del pago (PurchaseOrder, FanFunding, etc.)
        description:    texto libre para el historial

    Returns:
        WalletTransaction recién creada
    """
    wallet, _ = ArtistWallet.objects.get_or_create(
        artist=artist,
        defaults={'currency': currency},
    )

    net_amount = gross_amount - fee_amount
    clearing_days = wallet.get_clearing_days()
    available_at = timezone.now() + timedelta(days=clearing_days)

    ref_ct = None
    ref_id = None
    if reference_obj is not None:
        ref_ct = ContentType.objects.get_for_model(reference_obj)
        ref_id = reference_obj.pk

    tx = WalletTransaction.objects.create(
        wallet=wallet,
        type=WalletTransaction.TYPE_CREDIT,
        category=category,
        currency=currency,
        gross_amount=gross_amount,
        fee_amount=fee_amount,
        net_amount=net_amount,
        status=WalletTransaction.STATUS_PENDING,
        available_at=available_at,
        reference_ct=ref_ct,
        reference_id=ref_id,
        description=description,
    )

    # Actualizar balances usando F() para evitar race conditions
    from django.db.models import F
    ArtistWallet.objects.filter(pk=wallet.pk).update(
        balance_pending=F('balance_pending') + net_amount,
        total_earned=F('total_earned') + net_amount,
    )

    return tx


def debit_artist_wallet(
    artist,
    amount: Decimal,
    currency: str,
    category: str,
    description: str = '',
) -> WalletTransaction:
    """
    Debita la wallet de un artista (usado al aprobar un payout).

    - Crea un WalletTransaction DEBIT en estado PENDING.
    - Descuenta de balance_available (ya validado antes de llamar esta función).

    Returns:
        WalletTransaction recién creada
    """
    wallet = ArtistWallet.objects.get(artist=artist)

    tx = WalletTransaction.objects.create(
        wallet=wallet,
        type=WalletTransaction.TYPE_DEBIT,
        category=category,
        currency=currency,
        gross_amount=amount,
        fee_amount=Decimal('0.00'),
        net_amount=amount,
        status=WalletTransaction.STATUS_PENDING,
        description=description,
    )

    from django.db.models import F
    ArtistWallet.objects.filter(pk=wallet.pk).update(
        balance_available=F('balance_available') - amount,
    )

    return tx
