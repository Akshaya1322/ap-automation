from apps.audit_logs.context import clear_current_request, set_current_request


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditContextMiddleware:
    """Stashes the current user/IP in a thread-local so model-layer code
    (signals, service functions) can attribute audit log entries without
    threading `request` through every call."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        set_current_request(
            user if user and getattr(user, "is_authenticated", False) else None,
            _client_ip(request),
        )
        try:
            response = self.get_response(request)
        finally:
            clear_current_request()
        return response
