from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieTokenAuthentication(TokenAuthentication):
    """
    Lee el token DRF desde la cookie HttpOnly 'auth_token'.
    Si no hay cookie, intenta el header Authorization como fallback
    (para compatibilidad con herramientas como Postman o servicios legacy).
    Si la cookie existe pero el token no es válido (p.ej. tras un reset de BD),
    retorna None en lugar de lanzar 401, permitiendo que vistas AllowAny funcionen.
    """

    def authenticate(self, request):
        token = request.COOKIES.get('auth_token')
        if token:
            try:
                return self.authenticate_credentials(token)
            except AuthenticationFailed:
                return None
        return super().authenticate(request)
