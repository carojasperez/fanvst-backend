"""
Throttle classes para Fanvst.

Nomenclatura de scopes → tasas configuradas en settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
Se agrupan en dos categorías:
  - Anónimos (AnonRateThrottle): endpoints de autenticación expuestos al público.
  - Usuarios autenticados (UserRateThrottle): endpoints financieros donde el abuso
    puede tener consecuencias económicas directas.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


# ── Autenticación (anónimos) ───────────────────────────────────────────────────

class LoginRateThrottle(AnonRateThrottle):
    """5 intentos/minuto — previene fuerza bruta contra login."""
    scope = 'login'


class SocialLoginRateThrottle(AnonRateThrottle):
    """10 intentos/minuto — login OAuth, algo más permisivo que el clásico."""
    scope = 'social_login'


class RegisterRateThrottle(AnonRateThrottle):
    """5 registros/hora — frena creación masiva de cuentas spam."""
    scope = 'register'


class PasswordResetRateThrottle(AnonRateThrottle):
    """3 solicitudes/hora — evita flood de correos de recuperación."""
    scope = 'password_reset'


class ResendValidationRateThrottle(AnonRateThrottle):
    """3 reenvíos/hora — evita flood de correos de validación."""
    scope = 'resend_validation'


class ValidateEmailRateThrottle(AnonRateThrottle):
    """20 intentos/hora — limita adivinación de tokens de validación."""
    scope = 'validate_email'


class ValidateTokenRateThrottle(AnonRateThrottle):
    """10 intentos/hora — limita adivinación de tokens de reset."""
    scope = 'validate_token'


# ── Endpoints financieros (usuarios autenticados) ─────────────────────────────

class FinancialRateThrottle(UserRateThrottle):
    """20 operaciones/hora — tips, contribuciones y confirmaciones PayPal."""
    scope = 'financial'


class SubscribeRateThrottle(UserRateThrottle):
    """30 operaciones/hora — suscripciones/bajas a tiers de artistas."""
    scope = 'subscribe'
