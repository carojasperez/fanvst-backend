"""
Celery tasks para notificaciones Telegram al Staff.

Reglas de diseño:
- Nunca bloquear un request HTTP → siempre .delay()
- Si Telegram no está configurado, loguear y continuar sin error
- Mensajes en HTML para mejor legibilidad en Telegram
"""
import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from .telegram import send_message

logger = logging.getLogger(__name__)


# ── 1. Nuevo artista registrado ───────────────────────────────────────────────

@shared_task(name='notifications.notify_new_artist')
def notify_new_artist(user_id: int):
    """
    Envía notificación inmediata al grupo "Artist Registration"
    cuando un usuario activa su perfil de artista.
    """
    from adminsite.userinfo.models import Profile

    try:
        profile = Profile.objects.select_related('user').get(user_id=user_id)
    except Profile.DoesNotExist:
        logger.warning('[Notify] Profile not found for user_id=%s', user_id)
        return

    user = profile.user
    artist_type = profile.get_artist_type_display() if profile.artist_type else '—'
    stage_name = profile.stage_name or '—'
    location = profile.location_display or '—'
    genres = ', '.join(profile.genres.values_list('name', flat=True)) or '—'
    registered_at = user.date_joined.astimezone(timezone.get_current_timezone())

    text = (
        '🎨 <b>Nuevo artista registrado</b>\n'
        '\n'
        f'👤 <b>Username:</b> @{user.username}\n'
        f'✉️ <b>Email:</b> {user.email}\n'
        f'🎭 <b>Tipo:</b> {artist_type}\n'
        f'🎤 <b>Nombre artístico:</b> {stage_name}\n'
        f'🎵 <b>Géneros:</b> {genres}\n'
        f'📍 <b>Ubicación:</b> {location}\n'
        f'🕐 <b>Registrado:</b> {registered_at.strftime("%d/%m/%Y %H:%M")}'
    )

    send_message('artist_registration', text)


# ── 2. Resumen diario de fans registrados ─────────────────────────────────────

@shared_task(name='notifications.notify_daily_fan_summary')
def notify_daily_fan_summary():
    """
    Tarea periódica (20:00 hora Lima) que envía al grupo "Fan Registration"
    el total de nuevos usuarios registrados en el día.
    """
    from django.contrib.auth.models import User

    today = timezone.localdate()
    total = User.objects.filter(date_joined__date=today).count()
    artists_today = User.objects.filter(
        date_joined__date=today,
        profile__is_artist=True,
    ).count()
    fans_today = total - artists_today

    if total == 0:
        text = (
            f'📊 <b>Resumen del día — {today.strftime("%d/%m/%Y")}</b>\n'
            '\n'
            '😔 Sin nuevos registros hoy.'
        )
    else:
        text = (
            f'📊 <b>Resumen del día — {today.strftime("%d/%m/%Y")}</b>\n'
            '\n'
            f'👥 <b>Total nuevos registros:</b> {total}\n'
            f'🎨 <b>Artistas:</b> {artists_today}\n'
            f'🎤 <b>Fans:</b> {fans_today}'
        )

    send_message('fan_registration', text)


# ── 3. Notificaciones de pagos ────────────────────────────────────────────────

@shared_task(name='notifications.notify_wallet_credit')
def notify_wallet_credit(transaction_id: int):
    """
    Notifica al grupo Payments cuando un artista recibe un nuevo pago.
    """
    from wallet.models import WalletTransaction

    try:
        tx = WalletTransaction.objects.select_related('wallet__artist').get(pk=transaction_id)
    except WalletTransaction.DoesNotExist:
        return

    artist = tx.wallet.artist
    category_label = tx.get_category_display()
    tz = timezone.get_current_timezone()
    available_at = tx.available_at.astimezone(tz).strftime('%d/%m/%Y') if tx.available_at else '—'

    text = (
        '💸 <b>Nuevo pago recibido</b>\n'
        '\n'
        f'🎨 <b>Artista:</b> @{artist.username}\n'
        f'📂 <b>Tipo:</b> {category_label}\n'
        f'💰 <b>Bruto:</b> {tx.gross_amount} {tx.currency}\n'
        f'🏦 <b>Fee plataforma:</b> {tx.fee_amount} {tx.currency}\n'
        f'✅ <b>Neto artista:</b> {tx.net_amount} {tx.currency}\n'
        f'⏳ <b>Disponible:</b> {available_at}'
    )

    send_message('payments', text)


@shared_task(name='notifications.notify_payout_created')
def notify_payout_created(payout_id: int):
    """
    Notifica al grupo Payments cuando un artista solicita un payout.
    El staff debe procesar la solicitud.
    """
    from wallet.models import PayoutRequest

    try:
        payout = PayoutRequest.objects.select_related('artist').get(pk=payout_id)
    except PayoutRequest.DoesNotExist:
        return

    provider_label = payout.get_provider_display()
    tz = timezone.get_current_timezone()
    requested_at = payout.requested_at.astimezone(tz).strftime('%d/%m/%Y %H:%M')

    account_ref = payout.provider_account_ref or '—'
    if payout.bank_account_id:
        try:
            ba = payout.bank_account
            account_ref = f'{ba.bank} ···{ba.account_number[-4:] if ba.account_number else ""}'
        except Exception:
            pass

    text = (
        '📤 <b>Nueva solicitud de payout</b>\n'
        '\n'
        f'🎨 <b>Artista:</b> @{payout.artist.username}\n'
        f'💰 <b>Monto:</b> {payout.amount_requested} {payout.currency}\n'
        f'🏦 <b>Proveedor:</b> {provider_label}\n'
        f'📧 <b>Cuenta destino:</b> {account_ref}\n'
        f'🕐 <b>Solicitado:</b> {requested_at}\n'
        f'\n'
        f'⚠️ <b>Acción requerida:</b> Aprobar en el panel admin.'
    )

    send_message('payments', text)


@shared_task(name='notifications.notify_payout_approved')
def notify_payout_approved(payout_id: int):
    from wallet.models import PayoutRequest

    try:
        payout = PayoutRequest.objects.select_related('artist', 'approved_by').get(pk=payout_id)
    except PayoutRequest.DoesNotExist:
        return

    approver = payout.approved_by.username if payout.approved_by else 'sistema'

    text = (
        '✅ <b>Payout aprobado</b>\n'
        '\n'
        f'🎨 <b>Artista:</b> @{payout.artist.username}\n'
        f'💰 <b>Monto:</b> {payout.amount_requested} {payout.currency}\n'
        f'🏦 <b>Proveedor:</b> {payout.get_provider_display()}\n'
        f'👮 <b>Aprobado por:</b> @{approver}'
    )

    send_message('payments', text)


@shared_task(name='notifications.notify_payout_completed')
def notify_payout_completed(payout_id: int):
    from wallet.models import PayoutRequest

    try:
        payout = PayoutRequest.objects.select_related('artist').get(pk=payout_id)
    except PayoutRequest.DoesNotExist:
        return

    ref = payout.provider_reference or '—'

    text = (
        '🎉 <b>Payout completado</b>\n'
        '\n'
        f'🎨 <b>Artista:</b> @{payout.artist.username}\n'
        f'💰 <b>Monto transferido:</b> {payout.amount_to_transfer} {payout.currency}\n'
        f'🏦 <b>Fee transferencia:</b> {payout.transfer_fee} {payout.currency}\n'
        f'🔖 <b>Referencia:</b> <code>{ref}</code>'
    )

    send_message('payments', text)


@shared_task(name='notifications.notify_payout_cancelled')
def notify_payout_cancelled(payout_id: int):
    from wallet.models import PayoutRequest

    try:
        payout = PayoutRequest.objects.select_related('artist').get(pk=payout_id)
    except PayoutRequest.DoesNotExist:
        return

    reason = payout.failure_reason or '—'

    text = (
        '❌ <b>Payout cancelado</b>\n'
        '\n'
        f'🎨 <b>Artista:</b> @{payout.artist.username}\n'
        f'💰 <b>Monto:</b> {payout.amount_requested} {payout.currency}\n'
        f'📝 <b>Motivo:</b> {reason}'
    )

    send_message('payments', text)
