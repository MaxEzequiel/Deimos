from datetime import datetime
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User, Group

from memberships.models import Membership
from routines.models import Routine
from people.models import Person
from plans.models import Plan


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
    def por_grupo():
        rows = (
            User.objects.values("groups__name")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")
        )
        return [
            {"grupo": r["groups__name"] or "Sin grupo", "cantidad": r["cantidad"]}
            for r in rows
        ]

    @staticmethod
    def registros_por_mes(anio=None, mes=None):
        anio = int(anio) if anio else datetime.utcnow().year
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
        rows = User.objects.dates("date_joined", "year", order="DESC")
        return [d.year for d in rows] or [datetime.utcnow().year]

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
                "email": getattr(getattr(u, "person", None), "email", ""),
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
        total = Membership.objects.count()
        activas = Membership.objects.filter(status__iexact="active").count()
        inactivas = Membership.objects.filter(status__iexact="inactive").count()
        sin_membresia = User.objects.filter(membership__isnull=True).count()

        return {
            "total": total,
            "activas": activas,
            "vencidas": inactivas,   # el template sigue mostrando "Vencidas"
            "sin_membresia": sin_membresia,
            "porcentaje_activas": round((activas / total * 100), 2) if total else 0,
        }

    @staticmethod
    def membresias_por_estado():
        rows = (
            Membership.objects.values("status")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")
        )
        return [
            {"estado": r["status"] or "sin estado", "cantidad": r["cantidad"]}
            for r in rows
        ]

    @staticmethod
    def membresias_por_mes(anio=None):
        """Proxy: usa User.date_joined. La membresía se crea al registrar el user."""
        anio = int(anio) if anio else datetime.utcnow().year
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
        anio = int(anio) if anio else datetime.utcnow().year
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

        return [
            {
                "id": u.id,
                "username": u.username,
                "nombre": getattr(getattr(u, "person", None), "name", ""),
                "apellido": getattr(getattr(u, "person", None), "surname", ""),
                "email": getattr(getattr(u, "person", None), "email", ""),
                "dni": getattr(getattr(u, "person", None), "id_number", ""),
                "grupo": ", ".join(g.name for g in u.groups.all()) or "Sin grupo",
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "fecha_registro": u.date_joined.strftime("%d/%m/%Y %H:%M"),
            }
            for u in qs.order_by("-date_joined")
        ]

    @staticmethod
    def grupos_disponibles():
        return list(Group.objects.values_list("name", flat=True).order_by("name"))