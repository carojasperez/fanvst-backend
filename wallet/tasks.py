import logging

from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='wallet.clear_pending_transactions')
def clear_pending_transactions():
    """
    Tarea periódica (cada hora) que mueve transacciones de PENDING → CLEARED
    cuando su available_at ya pasó.

    Por cada transacción que limpia:
    - Descuenta de balance_pending
    - Suma a balance_available

    Usa F() expressions + select_for_update() para evitar race conditions.
    """
    from wallet.models import WalletTransaction

    now = timezone.now()
    cleared_count = 0

    with transaction.atomic():
        pending = (
            WalletTransaction.objects
            .filter(
                type=WalletTransaction.TYPE_CREDIT,
                status=WalletTransaction.STATUS_PENDING,
                available_at__lte=now,
            )
            .select_related('wallet')
            .select_for_update()
        )

        for tx in pending:
            from wallet.models import ArtistWallet
            ArtistWallet.objects.filter(pk=tx.wallet_id).update(
                balance_pending=F('balance_pending') - tx.net_amount,
                balance_available=F('balance_available') + tx.net_amount,
            )
            tx.status = WalletTransaction.STATUS_CLEARED
            tx.save(update_fields=['status'])
            cleared_count += 1

    logger.info('wallet.clear_pending_transactions: cleared=%d', cleared_count)
    return {'cleared': cleared_count}
