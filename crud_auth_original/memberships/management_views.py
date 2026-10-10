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
from payments.services import register_member_payment, available_payment_courses
from people.models import Person
from plans.models import Plan
from .forms import MemberManagementForm
from .models import Membership
from .services import with_last_payment


@login_required
@require_GET
def member_list(request):
	search = request.GET.get("q", "").strip()
	users = User.objects.select_related(
		"person", "person__plan", "membership", "membership__plan"
	).order_by("username")
	can_view_all = request.user.has_perm("pagos.view_monthlypayment")
	if not can_view_all:
		users = users.filter(pk=request.user.pk)
	if search:
		users = users.filter(
			Q(username__icontains=search)
			| Q(person__name__icontains=search)
			| Q(person__surname__icontains=search)
			| Q(person__id_number__icontains=search)
		)
	users = with_last_payment(users, "pk")
	page = Paginator(users, 25).get_page(request.GET.get("page"))
	charges = {
		charge.member_id: charge
		for charge in MonthlyPayment.objects.filter(
			member_id__in=[user.pk for user in page],
			period=timezone.localdate().replace(day=1),
		)
	}
	for user in page:
		membership = getattr(user, "membership", None)
		person = getattr(user, "person", None)
		user.subscription_plan = (membership.plan if membership else None) or (
			person.plan if person else None
		)
		charge = charges.get(user.pk)
		user.subscription_amount = (
			charge.amount
			if charge
			else (
				user.subscription_plan.base_price
				if user.subscription_plan
				else None
			)
		)
		user.can_pay_subscription = (
			user.is_active
			and (user.subscription_plan or available_payment_courses(user).exists())
						and (not charge or not charge.paid_on)
		)
		if membership:
			membership.last_paid_on = user.last_paid_on
			membership.last_coverage_end = user.last_coverage_end
			user.membership_status = membership.effective_status
	return render(
		request,
		"memberships/member_list.html",
		{
			"page": page,
			"search": search,
			"total_users": page.paginator.count,
			"can_view_all": can_view_all,
		},
	)


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def manage_member(request, user_id):
	user = get_object_or_404(User, pk=user_id)
	person = Person.objects.select_related("plan").filter(user=user).first()
	membership = (
		Membership.objects.select_related("plan").filter(user=user).first()
	)
	if membership is None:
		membership = Membership(user=user, plan=person.plan if person else None)
	elif membership.plan_id is None and person and person.plan_id:
		membership.plan = person.plan
	today = timezone.localdate()
	period = today.replace(day=1)
	pending = MonthlyPayment.objects.filter(
		member=user, period=period, paid_on__isnull=True
	).first()
	initial = {
		"period": period,
		"kind": pending.kind if pending else "gym",
		"paid_on": today,
		"amount": (
			pending.amount
			if pending
			else (membership.plan.base_price if membership.plan else None)
		),
	}
	data = request.POST if request.method == "POST" else None
	membership_form = MemberManagementForm(data, instance=membership)
	membership_valid = membership_form.is_valid() if data is not None else False
	selected_plan = (
		membership_form.cleaned_data.get("plan")
		if membership_valid else membership.plan
	)
	payment_form = MemberPaymentForm(
		data, member=user, initial=initial, selected_plan=selected_plan,
	)
	payment_valid = payment_form.is_valid() if data is not None else False
	if membership_valid and payment_valid:
		try:
			with transaction.atomic():
				User.objects.select_for_update().get(pk=user.pk)
				saved = membership_form.save()
				user._state.fields_cache.pop("membership", None)
				user._state.fields_cache.pop("person", None)
				payment = register_member_payment(
					user, payment_form.cleaned_data, request.user,
				)
				audit(
					request, "UPDATE",
					f"Membresía {saved.pk}, plan {saved.plan_id}; "
					f"pago {payment.pk}: {payment.amount}",
				)
		except ValidationError as error:
			payment_form.add_error(None, error)
		else:
			messages.success(
				request,
				f"Suscripción y pago registrados. ID FACT: {payment.reference}.",
			)
			return redirect("manage_member", user_id=user.pk)
	from checkin.services import member_checkin_status

	status = member_checkin_status(person)
	plan_prices = {
		str(plan.pk): str(plan.base_price or 0) for plan in Plan.objects.all()
	}
	return render(
		request,
		"memberships/manage_member.html",
		{
			"member": user,
			"person": person,
			"membership": membership,
			"membership_form": membership_form,
			"payment_form": payment_form,
			"membership_status": membership.effective_status,
			"has_plans": Plan.objects.exists(),
			"payment_amount_locked": bool(pending),
			"plan_prices": plan_prices,
			"course_prices": {str(c.pk): str(c.price) for c in payment_form.fields["courses"].queryset},
			"payments": MonthlyPayment.objects.filter(
				member=user
			).select_related("recorded_by")[:24],
			"monthly_status": status,
		},
	)
