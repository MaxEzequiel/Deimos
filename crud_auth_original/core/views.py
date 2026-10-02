from core.decorators import superuser_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import AuditLog

# Create your views here.


@login_required
@superuser_required
@require_http_methods(['GET'])
def list_audit(request):
    if request.method == "GET":
        audit_logs = list(AuditLog.objects.select_related('user').order_by("-modify_date"))
        for log in audit_logs:
            action = log.action.lower()
            log.badge_class = 'audit-badge-' + (action if action in {'create', 'update', 'delete', 'deactivate', 'inscribe'} else 'other')
        return render(request, "list_audit.html", {"audit_logs": audit_logs})
