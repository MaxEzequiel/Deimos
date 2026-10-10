from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from people.models import Person
from memberships.models import Membership
from payments.models import MonthlyPayment
from memberships.services import next_month_expiry
from django.utils import timezone

User = get_user_model()


def clear_permission_cache(user):
	for name in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
		user.__dict__.pop(name, None)


@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=User.user_permissions.through)
def permissions_changed(sender, instance, action, reverse, **kwargs):
	if not reverse and action in {"post_add", "post_remove", "post_clear"}:
		clear_permission_cache(instance)


@receiver(post_save, sender=Person)
def sync_profile_email(
	sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
	if raw or (update_fields is not None and "email" not in update_fields):
		return
	email = instance.email or ""
	User.objects.using(using).filter(pk=instance.user_id).exclude(
		email=email
	).update(email=email)
	if "user" in instance._state.fields_cache:
		instance.user.email = email


@receiver(post_save, sender=User)
def sync_user_email(
	sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
	if raw or (update_fields is not None and "email" not in update_fields):
		return
	Person.objects.using(using).filter(user_id=instance.pk).exclude(
		email=instance.email
	).update(email=instance.email)
	if "person" in instance._state.fields_cache:
		instance.person.email = instance.email


@receiver(post_save, sender=Membership)
def sync_membership_plan(
	sender,
	instance,
	created=False,
	raw=False,
	update_fields=None,
	using=None,
	**kwargs
):
	if raw or (
		update_fields is not None
		and "plan" not in update_fields
		and "plan_id" not in update_fields
	):
		return
	if created and instance.plan_id is None:
		plan_id = (
			Person.objects.using(using)
			.filter(user_id=instance.user_id)
			.values_list("plan_id", flat=True)
			.first()
		)
		if plan_id is not None:
			Membership.objects.using(using).filter(pk=instance.pk).update(
				plan_id=plan_id
			)
			instance.plan_id = plan_id
	Person.objects.using(using).filter(user_id=instance.user_id).update(
		plan_id=instance.plan_id
	)


@receiver(post_save, sender=Person)
def sync_person_plan(
	sender,
	instance,
	created=False,
	raw=False,
	update_fields=None,
	using=None,
	**kwargs
):
	if raw or (
		update_fields is not None
		and "plan" not in update_fields
		and "plan_id" not in update_fields
	):
		return
	if created and instance.plan_id is None:
		plan_id = (
			Membership.objects.using(using)
			.filter(user_id=instance.user_id)
			.values_list("plan_id", flat=True)
			.first()
		)
		if plan_id is not None:
			Person.objects.using(using).filter(pk=instance.pk).update(
				plan_id=plan_id
			)
			instance.plan_id = plan_id
	Membership.objects.using(using).filter(user_id=instance.user_id).update(
		plan_id=instance.plan_id
	)


@receiver(post_save, sender=MonthlyPayment)
def activate_paid_membership(sender, instance, raw=False, using=None, **kwargs):
	if raw or not instance.paid_on or instance.paid_on > timezone.localdate():
		return
	if next_month_expiry(instance.paid_on) < timezone.localdate():
		return
	plan_id = (
		Person.objects.using(using)
		.filter(user_id=instance.member_id)
		.values_list("plan_id", flat=True)
		.first()
	)
	membership, _ = Membership.objects.using(using).get_or_create(
		user_id=instance.member_id,
		defaults={"plan_id": plan_id, "status": "active"},
	)
