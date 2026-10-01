from django.contrib import admin

from .models import MonthlyPayment


@admin.register(MonthlyPayment)
class MonthlyPaymentAdmin(admin.ModelAdmin):
    list_display = ("member", "period", "amount", "due_date", "status_label", "paid_on", "method")
    list_filter = ("period", "method", "paid_on")
    search_fields = ("member__username", "reference")
    readonly_fields = ("recorded_by", "created_at")

    def save_model(self, request, obj, form, change):
        if obj.paid_on and (not change or "paid_on" in form.changed_data or "method" in form.changed_data):
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
