from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.audit_logs.context import set_current_request


class AuditAwareJWTAuthentication(JWTAuthentication):
    """Standard SimpleJWT authentication that also records the resolved
    user into the audit thread-local, since Django's session-based
    AuthenticationMiddleware never sees JWT-authenticated users."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
                "REMOTE_ADDR"
            )
            set_current_request(user, ip)
        return result
