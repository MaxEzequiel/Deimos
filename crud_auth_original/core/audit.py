from core.models import AuditLog


def audit(request, action, detail):
    if request.user.is_authenticated:
        user = request.user.id
    else:
        return

    AuditLog.objects.create(
        user_id=user,
        action=action,
        detail=detail,
        path=request.path,
    )