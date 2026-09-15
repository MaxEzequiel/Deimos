from audit.models import AuditEvent


class AuditMiddleware:
    """Registra operaciones que modifican estado después de una respuesta exitosa."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and 200 <= response.status_code < 400:
            action = "DELETE" if request.method == "DELETE" or "delete" in request.path else ("CREATE" if "create" in request.path else "UPDATE")
            AuditEvent.objects.create(
                actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                action=action,
                resource=request.resolver_match.view_name if request.resolver_match else request.path,
                path=request.path[:255],
                details={"method": request.method, "status_code": response.status_code},
                ip_address=self._client_ip(request),
            )
        return response

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
