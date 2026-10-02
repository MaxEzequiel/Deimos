from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from core.audit import audit
from core.decorators import superuser_required
from payments.forms import MemberPaymentForm
from payments.models import MonthlyPayment
from payments.services import register_member_payment
from people.models import Person
from plans.models import Plan
from .forms import MemberManagementForm
from .models import Membership
from .services import with_last_payment


@login_required
@superuser_required
@require_GET
def member_list(request):
    search = request.GET.get('q', '').strip()
    users = User.objects.select_related('person', 'person__plan', 'membership', 'membership__plan').order_by('username')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(person__name__icontains=search) | Q(person__surname__icontains=search) | Q(person__id_number__icontains=search))
    users = with_last_payment(users, 'pk')
    page = Paginator(users, 25).get_page(request.GET.get('page'))
    for user in page:
        membership = getattr(user, 'membership', None)
        if membership:
            membership.last_paid_on = user.last_paid_on
            membership.last_coverage_end = user.last_coverage_end
            user.membership_status = membership.effective_status
    return render(request, 'memberships/member_list.html', {'page': page, 'search': search, 'total_users': page.paginator.count})


@login_required
@superuser_required
@require_http_methods(['GET', 'POST'])
def manage_member(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    person = Person.objects.select_related('plan').filter(user=user).first()
    membership = Membership.objects.select_related('plan').filter(user=user).first()
    if membership is None:
        membership = Membership(user=user, plan=person.plan if person else None)
    elif membership.plan_id is None and person and person.plan_id:
        membership.plan = person.plan
    today = timezone.localdate()
    period = today.replace(day=1)
    pending = MonthlyPayment.objects.filter(member=user, period=period, paid_on__isnull=True).first()
    initial = {'period': period, 'paid_on': today, 'amount': pending.amount if pending else (membership.plan.base_price if membership.plan else None)}
    action = request.POST.get('action') if request.method == 'POST' else None
    membership_form = MemberManagementForm(request.POST if action == 'membership' else None, instance=membership)
    payment_form = MemberPaymentForm(request.POST if action == 'payment' else None, member=user, initial=initial)
    if action == 'membership' and membership_form.is_valid():
        with transaction.atomic():
            saved = membership_form.save()
            audit(request, 'UPDATE', f'Membresía del usuario {user.pk}: estado {saved.status}, plan {saved.plan_id}')
        messages.success(request, 'Plan y membresía guardados')
        return redirect('manage_member', user_id=user.pk)
    if action == 'payment' and payment_form.is_valid():
        try:
            with transaction.atomic():
                payment = register_member_payment(user, payment_form.cleaned_data, request.user)
                audit(request, 'UPDATE', f'Pago de mensualidad {payment.pk}: {user.username}, {payment.period:%m/%Y}, importe {payment.amount}')
        except ValidationError as error:
            payment_form.add_error(None, error)
        else:
            messages.success(request, 'Pago registrado. La membresía y el check-in ya reflejan la vigencia de la mensualidad')
            return redirect('manage_member', user_id=user.pk)
    if request.method == 'POST' and action not in {'membership', 'payment'}:
        return render(request, '403.html', status=400)
    from checkin.services import member_checkin_status
    status = member_checkin_status(person)
    plan_prices = {str(plan.pk): str(plan.base_price or 0) for plan in Plan.objects.all()}
    return render(request, 'memberships/manage_member.html', {
        'member': user, 'person': person, 'membership': membership,
        'membership_form': membership_form, 'payment_form': payment_form,
        'membership_status': membership.effective_status, 'has_plans': Plan.objects.exists(),
        'payment_amount_locked': bool(pending),
        'plan_prices': plan_prices,
        'payments': MonthlyPayment.objects.filter(member=user).select_related('recorded_by')[:24],
        'monthly_status': status,
    })
