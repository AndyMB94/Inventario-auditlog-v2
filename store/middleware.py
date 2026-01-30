from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationMiddleware:
    """
    Middleware que autentica JWT antes del AuditlogMiddleware,
    permitiendo que auditlog capture el usuario y la IP correctamente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Intentar autenticar con JWT
        try:
            auth = JWTAuthentication()
            auth_result = auth.authenticate(request)
            if auth_result:
                request.user, _ = auth_result
        except Exception:
            pass  # Si falla, continuar sin autenticar

        return self.get_response(request)