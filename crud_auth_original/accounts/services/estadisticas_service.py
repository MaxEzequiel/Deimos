from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Q

from memberships.models import Membership
from routines.models import Routine
from people.models import Person
from plans.models import Plan
from memberships.services import with_last_payment
from payments.models import PaymentMovement
from collections import Counter


class EstadisticasService:
    """Todas las queries agregadas viven acá. Las vistas NO calculan nada."""

    # ================= USUARIOS =================

    @staticmethod
    def resumen_general():
        total = User.objects.count()
        activos = User.objects.filter(is_active=True).count()
        staff = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        return {
            "total": total,
            "activos": activos,
            "inactivos": total - activos,
            "staff": staff,
            "superusers": superusers,
            "porcentaje_activos": round((activos / total * 100), 2) if total else 0,
        }

    @staticmethod
    def registros_por_mes(anio=None, mes=None):
        anio = int(anio) if anio else timezone.localdate().year
        qs = User.objects.filter(date_joined__year=anio)
        if mes:
            qs = qs.filter(date_joined__month=int(mes))

        rows = (
            qs.annotate(mes=TruncMonth("date_joined"))
            .values("mes")
            .annotate(cantidad=Count("id"))
            .order_by("mes")
        )

        if mes:
            total = sum(r["cantidad"] for r in rows)
            return [{"mes": int(mes), "cantidad": total}]

        data = {m: 0 for m in range(1, 13)}
        for r in rows:
            if r["mes"]:
                data[r["mes"].month] = r["cantidad"]
        return [{"mes": m, "cantidad": c} for m, c in data.items()]

    @staticmethod
    def anios_disponibles():
        user_years = User.objects.dates("date_joined", "year", order="DESC")
        payment_years = PaymentMovement.objects.dates("paid_on", "year", order="DESC")
        years = {item.year for item in user_years}
        years.update(item.year for item in payment_years)
        return sorted(years or {timezone.localdate().year}, reverse=True)

    @staticmethod
    def usuarios_activos_vs_inactivos():
        return {
            "activos": User.objects.filter(is_active=True).count(),
            "inactivos": User.objects.filter(is_active=False).count(),
        }

    @staticmethod
    def top_recientes(limite=10):
        users = User.objects.select_related("person").order_by("-date_joined")[:limite]
        return [
            {
                "id": u.id,
                "username": u.username,
                "nombre": getattr(getattr(u, "person", None), "name", ""),
                "apellido": getattr(getattr(u, "person", None), "surname", ""),
                "email": u.email,
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "fecha_registro": u.date_joined.isoformat(),
            }
            for u in users
        ]

    # ================= MEMBRESÍAS =================
    # Membership NO tiene created_at.
    # Para el gráfico temporal usamos User.date_joined como proxy,
    # ya que Membership se crea al mismo tiempo que el User (ver views.py).

    @staticmethod
    def resumen_membresias():
        memberships = list(with_last_payment(Membership.objects.all()))
        total = len(memberships)
        activas = sum(membership.effective_status == 'active' for membership in memberships)
        inactivas = total - activas
        sin_membresia = User.objects.filter(membership__isnull=True).count()

        return {
            "total": total,
            "activas": activas,
            "vencidas": inactivas,   # el template sigue mostrando "Vencidas"
            "sin_membresia": sin_membresia,
            "porcentaje_activas": round((activas / total * 100), 2) if total else 0,
        }

    @staticmethod
    def membresias_por_mes(anio=None):
        """Proxy: usa User.date_joined. La membresía se crea al registrar el user."""
        anio = int(anio) if anio else timezone.localdate().year
        rows = (
            User.objects.filter(
                date_joined__year=anio,
                membership__isnull=False,
            )
            .annotate(mes=TruncMonth("date_joined"))
            .values("mes")
            .annotate(cantidad=Count("id"))
            .order_by("mes")
        )
        data = {m: 0 for m in range(1, 13)}
        for r in rows:
            if r["mes"]:
                data[r["mes"].month] = r["cantidad"]
        return [{"mes": m, "cantidad": c} for m, c in data.items()]

    @staticmethod
    def membresias_por_plan():
        rows = (
            Membership.objects.values("plan__name")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")
        )
        return [
            {"plan": r["plan__name"] or "Sin plan", "cantidad": r["cantidad"]}
            for r in rows
        ]

    # ================= PAGOS =================

    @staticmethod
    def _movimientos_en_periodo(anio=None, mes=None):
        movimientos = PaymentMovement.objects.all()
        if anio:
            movimientos = movimientos.filter(paid_on__year=int(anio))
        if mes:
            movimientos = movimientos.filter(paid_on__month=int(mes))
        return movimientos

    @staticmethod
    def resumen_pagos(anio=None, mes=None):
        movimientos = EstadisticasService._movimientos_en_periodo(anio, mes)
        pagos = movimientos.filter(amount__gt=0).aggregate(
            cantidad=Count("pk"), monto=Sum("amount")
        )
        anulaciones = movimientos.filter(amount__lt=0).aggregate(
            cantidad=Count("pk"), monto=Sum("amount")
        )
        monto_pagos = pagos["monto"] or 0
        monto_anulaciones = -(anulaciones["monto"] or 0)
        return {
            "pagos_cantidad": pagos["cantidad"],
            "pagos_monto": monto_pagos,
            "anulaciones_cantidad": anulaciones["cantidad"],
            "anulaciones_monto": monto_anulaciones,
            "neto": monto_pagos - monto_anulaciones,
        }

    @staticmethod
    def pagos_por_mes(anio=None, mes=None):
        anio = int(anio) if anio else timezone.localdate().year
        movimientos = EstadisticasService._movimientos_en_periodo(anio, mes)
        rows = (
            movimientos.annotate(mes=TruncMonth("paid_on"))
            .values("mes")
            .annotate(
                pagos=Count("pk", filter=Q(amount__gt=0)),
                anulaciones=Count("pk", filter=Q(amount__lt=0)),
            )
            .order_by("mes")
        )

        data = {month: {"pagos": 0, "anulaciones": 0} for month in range(1, 13)}
        for row in rows:
            if row["mes"]:
                data[row["mes"].month] = {
                    "pagos": row["pagos"],
                    "anulaciones": row["anulaciones"],
                }
        months = [int(mes)] if mes else range(1, 13)
        return [
            {"mes": month, **data[month]}
            for month in months
        ]

    @staticmethod
    def informe_pagos(anio=None, mes=None):
        movimientos = (
            EstadisticasService._movimientos_en_periodo(anio, mes)
            .select_related("charge__member", "recorded_by")
            .order_by("-paid_on", "-created_at", "-pk")
        )
        return [
            {
                "fecha": movimiento.paid_on.strftime("%d/%m/%Y"),
                "usuario": movimiento.charge.member.username,
                "periodo": movimiento.charge.period.strftime("%m/%Y"),
                "tipo": "Anulación" if movimiento.amount < 0 else "Pago realizado",
                "monto": abs(movimiento.amount),
                "referencia": movimiento.reference,
                "registrado_por": movimiento.recorded_by.username if movimiento.recorded_by else "—",
            }
            for movimiento in movimientos
        ]

    # ================= SUSCRIPCIONES =================

    @staticmethod
    def informe_suscripciones():
        memberships = with_last_payment(
            Membership.objects.select_related("user", "user__person", "plan")
        ).order_by("user__username")
        rows = []
        membership_user_ids = set()
        for membership in memberships:
            membership_user_ids.add(membership.user_id)
            person = getattr(membership.user, "person", None)
            plan = membership.plan or (person.plan if person else None)
            if not plan:
                continue
            rows.append({
                "usuario": membership.user.username,
                "nombre": (
                    f"{person.surname}, {person.name}".strip(", ")
                    if person else membership.user.get_full_name() or membership.user.username
                ),
                "plan": plan.name or "Plan sin nombre",
                "precio": plan.base_price,
                "estado": membership.effective_status,
                "estado_label": "Activa" if membership.effective_status == "active" else "Inactiva",
            })

        users_without_membership = (
            User.objects.filter(membership__isnull=True, person__plan__isnull=False)
            .select_related("person", "person__plan")
            .order_by("username")
        )
        for user in users_without_membership:
            person = user.person
            plan = person.plan
            rows.append({
                "usuario": user.username,
                "nombre": f"{person.surname}, {person.name}".strip(", "),
                "plan": plan.name or "Plan sin nombre",
                "precio": plan.base_price,
                "estado": "active",
                "estado_label": "Activa",
            })
        return sorted(rows, key=lambda row: row["usuario"].casefold())

    @staticmethod
    def resumen_suscripciones(suscripciones=None):
        suscripciones = suscripciones if suscripciones is not None else EstadisticasService.informe_suscripciones()
        activas = sum(row["estado"] == "active" for row in suscripciones)
        total = len(suscripciones)
        return {
            "total": total,
            "activas": activas,
            "inactivas": total - activas,
        }

    @staticmethod
    def suscripciones_por_plan(suscripciones=None):
        suscripciones = suscripciones if suscripciones is not None else EstadisticasService.informe_suscripciones()
        planes = {}
        for suscripcion in suscripciones:
            plan = planes.setdefault(
                suscripcion["plan"],
                {"plan": suscripcion["plan"], "activas": 0, "inactivas": 0},
            )
            key = "activas" if suscripcion["estado"] == "active" else "inactivas"
            plan[key] += 1
        return [
            {**plan, "cantidad": plan["activas"] + plan["inactivas"]}
            for plan in sorted(planes.values(), key=lambda row: row["plan"].casefold())
        ]

    # ================= RUTINAS =================

    @staticmethod
    def resumen_rutinas():
        total = Routine.objects.count()
        con_cliente = Routine.objects.filter(client__isnull=False).count()
        clientes_unicos = (
            Routine.objects.filter(client__isnull=False)
            .values("client").distinct().count()
        )
        return {
            "total": total,
            "con_cliente": con_cliente,
            "sin_cliente": total - con_cliente,
            "clientes_unicos": clientes_unicos,
            "promedio_por_cliente": (
                round(total / clientes_unicos, 2) if clientes_unicos else 0
            ),
        }

    @staticmethod
    def rutinas_por_mes(anio=None):
        anio = int(anio) if anio else timezone.localdate().year
        rows = (
            Routine.objects.filter(created_at__year=anio)
            .annotate(mes=TruncMonth("created_at"))
            .values("mes")
            .annotate(cantidad=Count("id"))
            .order_by("mes")
        )
        data = {m: 0 for m in range(1, 13)}
        for r in rows:
            if r["mes"]:
                data[r["mes"].month] = r["cantidad"]
        return [{"mes": m, "cantidad": c} for m, c in data.items()]

    @staticmethod
    def top_clientes_con_rutinas(limite=10):
        rows = (
            Routine.objects.filter(client__isnull=False)
            .values("client__id", "client__name", "client__surname")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")[:limite]
        )
        return [
            {
                "cliente_id": r["client__id"],
                "nombre": f'{r["client__surname"] or ""}, {r["client__name"] or ""}'.strip(", "),
                "cantidad": r["cantidad"],
            }
            for r in rows
        ]

    # ================= INFORMES / FILTROS =================

    @staticmethod
    def informe_filtrado(desde=None, hasta=None, grupo=None, activo=None, staff=None):
        qs = User.objects.select_related("person").prefetch_related("groups")
        if desde:
            qs = qs.filter(date_joined__date__gte=desde)
        if hasta:
            qs = qs.filter(date_joined__date__lte=hasta)
        if grupo:
            qs = qs.filter(groups__name=grupo)
        if activo in ("1", "true", "True", True):
            qs = qs.filter(is_active=True)
        elif activo in ("0", "false", "False", False):
            qs = qs.filter(is_active=False)
        if staff in ("1", "true", "True", True):
            qs = qs.filter(is_staff=True)
        elif staff in ("0", "false", "False", False):
            qs = qs.filter(is_staff=False)

        return [
            {
                "id": u.id,
                "username": u.username,
                "nombre": getattr(getattr(u, "person", None), "name", ""),
                "apellido": getattr(getattr(u, "person", None), "surname", ""),
                "email": u.email,
                "dni": getattr(getattr(u, "person", None), "id_number", ""),
                "grupo": ", ".join(g.name for g in u.groups.all()) or "Sin grupo",
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "fecha_registro": timezone.localtime(u.date_joined).strftime("%d/%m/%Y %H:%M"),
            }
            for u in qs.order_by("-date_joined")
        ]

    @staticmethod
    def grupos_disponibles():
        return list(Group.objects.values_list("name", flat=True).order_by("name"))
