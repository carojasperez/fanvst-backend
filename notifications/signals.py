"""
Signal handlers para notificaciones Telegram.

Todos los handlers son no-bloqueantes: encolan una Celery task en lugar
de llamar directamente a la API de Telegram.

Detectores de cambio de estado:
  - pre_save guarda el valor previo en el atributo _old_*
  - post_save compara el nuevo valor contra el guardado
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from adminsite.userinfo.models import Profile
from wallet.models import PayoutRequest, WalletTransaction


# ── 1. Nuevo artista ──────────────────────────────────────────────────────────

@receiver(pre_save, sender=Profile)
def _cache_profile_is_artist(sender, instance, **kwargs):
    """Guarda el valor previo de is_artist antes de guardar."""
    if instance.pk:
        try:
            instance._old_is_artist = (
                Profile.objects
                .values_list('is_artist', flat=True)
                .get(pk=instance.pk)
            )
        except Profile.DoesNotExist:
            instance._old_is_artist = False
    else:
        instance._old_is_artist = False


@receiver(post_save, sender=Profile)
def _on_artist_activated(sender, instance, created, **kwargs):
    """
    Dispara notify_new_artist cuando is_artist pasa de False → True.
    También aplica a perfiles recién creados con is_artist=True (poco común pero posible).
    """
    old = getattr(instance, '_old_is_artist', False)
    if instance.is_artist and not old:
        from notifications.tasks import notify_new_artist
        notify_new_artist.delay(instance.user_id)


# ── 2. Wallet credit (pago recibido por artista) ──────────────────────────────

@receiver(post_save, sender=WalletTransaction)
def _on_wallet_credit(sender, instance, created, **kwargs):
    """Notifica cuando se acredita un pago nuevo a la wallet de un artista."""
    if created and instance.type == WalletTransaction.TYPE_CREDIT:
        from notifications.tasks import notify_wallet_credit
        notify_wallet_credit.delay(instance.pk)


# ── 3. Payout request lifecycle ───────────────────────────────────────────────

@receiver(pre_save, sender=PayoutRequest)
def _cache_payout_status(sender, instance, **kwargs):
    """Guarda el status previo del PayoutRequest antes de guardar."""
    if instance.pk:
        try:
            instance._old_status = (
                PayoutRequest.objects
                .values_list('status', flat=True)
                .get(pk=instance.pk)
            )
        except PayoutRequest.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=PayoutRequest)
def _on_payout_change(sender, instance, created, **kwargs):
    """
    Notifica al grupo Payments en cada transición de estado del PayoutRequest.
    """
    from notifications.tasks import (
        notify_payout_approved,
        notify_payout_cancelled,
        notify_payout_completed,
        notify_payout_created,
    )

    if created:
        notify_payout_created.delay(instance.pk)
        return

    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    if old_status == new_status:
        return

    dispatch = {
        PayoutRequest.STATUS_APPROVED: notify_payout_approved,
        PayoutRequest.STATUS_COMPLETED: notify_payout_completed,
        PayoutRequest.STATUS_CANCELLED: notify_payout_cancelled,
        PayoutRequest.STATUS_FAILED: notify_payout_cancelled,
    }

    task = dispatch.get(new_status)
    if task:
        task.delay(instance.pk)
