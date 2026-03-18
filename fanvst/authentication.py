from rest_framework.authentication import TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    """
    Lee el token DRF desde la cookie HttpOnly 'auth_token'.
    Si no hay cookie, intenta el header Authorization como fallback
    (para compatibilidad con herramientas como Postman o servicios legacy).
    """

    def authenticate(self, request):
        token = request.COOKIES.get('auth_token')
        if token:
            return self.authenticate_credentials(token)
        return super().authenticate(request)
