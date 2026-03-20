"""
Cliente Telegram para notificaciones internas al Staff de Fanvst.

Configuración requerida en .env:
    TELEGRAM_BOT_TOKEN              Token del bot (obtenido con @BotFather)
    TELEGRAM_CHAT_ARTIST_REG        Chat ID del grupo "Fanvst Artist Registration"
    TELEGRAM_CHAT_FAN_REG           Chat ID del grupo "Fanvst Fan Registration"
    TELEGRAM_CHAT_PAYMENTS          Chat ID del grupo "Fanvst Payments"

Para obtener el Chat ID de un grupo:
    1. Agregar el bot al grupo
    2. Enviar un mensaje en el grupo
    3. GET https://api.telegram.org/bot<TOKEN>/getUpdates
    4. El campo "chat.id" (suele ser negativo para grupos)
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'


def _get_config():
    """Retorna token y chat IDs desde settings. Lanza ValueError si no están configurados."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chats = {
        'artist_registration': getattr(settings, 'TELEGRAM_CHAT_ARTIST_REG', ''),
        'fan_registration': getattr(settings, 'TELEGRAM_CHAT_FAN_REG', ''),
        'payments': getattr(settings, 'TELEGRAM_CHAT_PAYMENTS', ''),
    }
    return token, chats


def send_message(group: str, text: str) -> bool:
    """
    Envía un mensaje HTML a un grupo de Telegram.

    Args:
        group:  'artist_registration' | 'fan_registration' | 'payments'
        text:   Mensaje en formato HTML (<b>, <i>, <code>, etc.)

    Returns:
        True si el mensaje fue enviado correctamente, False si hay error
        o si el bot no está configurado aún (modo placeholder).
    """
    token, chats = _get_config()
    chat_id = chats.get(group, '')

    if not token or not chat_id:
        logger.info(
            '[Telegram] Bot no configurado — grupo=%s | mensaje=%s',
            group,
            text[:80],
        )
        return False

    url = TELEGRAM_API.format(token=token)
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error('[Telegram] Error enviando mensaje al grupo %s: %s', group, exc)
        return False
