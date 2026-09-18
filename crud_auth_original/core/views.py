from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import AuditLog

# Create your views here.


@login_required
def list_audit(request):
    if request.method == "GET":
        audit_logs = AuditLog.objects.all().order_by("-modify_date")
        return render(request, "list_audit.html", {"audit_logs": audit_logs})
