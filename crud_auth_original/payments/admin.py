from django.contrib import admin

from .models import PaymentMovement


@admin.register(PaymentMovement)
class PaymentMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "charge", "amount", "paid_on", "reversal_of", "recorded_by")
    search_fields = ("charge__member__username", "reference")
    readonly_fields = tuple(field.name for field in PaymentMovement._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
