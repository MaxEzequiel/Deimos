from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from accounts.services.estadisticas_service import EstadisticasService
from accounts.services.reportes_service import ReportesService


@login_required
def dashboard_usuarios(request):
    anio = request.GET.get("anio") or datetime.utcnow().year
    contexto = {
        "resumen": EstadisticasService.resumen_general(),
        "resumen_membresias": EstadisticasService.resumen_membresias(),
        "resumen_rutinas": EstadisticasService.resumen_rutinas(),
        "grupos_disponibles": EstadisticasService.grupos_disponibles(),
        "anios_disponibles": EstadisticasService.anios_disponibles(),
        "anio_seleccionado": int(anio),
        "anio_actual": datetime.utcnow().year,
    }
    return render(request, "estadisticas/dashboard.html", contexto)


@login_required
def datos_graficos(request):
    anio = request.GET.get("anio") or datetime.utcnow().year
    mes = request.GET.get("mes") or None

    return JsonResponse({
        "resumen": EstadisticasService.resumen_general(),
        "por_grupo": EstadisticasService.por_grupo(),
        "por_mes": EstadisticasService.registros_por_mes(anio=anio, mes=mes),
        "activos_inactivos": EstadisticasService.usuarios_activos_vs_inactivos(),
        "recientes": EstadisticasService.top_recientes(),
        "resumen_membresias": EstadisticasService.resumen_membresias(),
        "membresias_estado": EstadisticasService.membresias_por_estado(),
        "membresias_mes": EstadisticasService.membresias_por_mes(anio=anio),
        "resumen_rutinas": EstadisticasService.resumen_rutinas(),
        "rutinas_mes": EstadisticasService.rutinas_por_mes(anio=anio),
        "top_clientes": EstadisticasService.top_clientes_con_rutinas(),
        "anio": int(anio),
        "mes": int(mes) if mes else None,
    })


@login_required
def informe_usuarios(request):
    filtros = {
        "desde": request.GET.get("desde") or "",
        "hasta": request.GET.get("hasta") or "",
        "grupo": request.GET.get("grupo") or "",
        "activo": request.GET.get("activo") or "",
        "staff": request.GET.get("staff") or "",
    }
    usuarios = EstadisticasService.informe_filtrado(**filtros)
    return render(request, "estadisticas/informe.html", {
        "usuarios": usuarios,
        "filtros": filtros,
        "grupos_disponibles": EstadisticasService.grupos_disponibles(),
        "total": len(usuarios),
    })


@login_required
def exportar_excel(request):
    filtros = {
        "desde": request.GET.get("desde") or None,
        "hasta": request.GET.get("hasta") or None,
        "grupo": request.GET.get("grupo") or None,
        "activo": request.GET.get("activo") or None,
        "staff": request.GET.get("staff") or None,
    }
    usuarios = EstadisticasService.informe_filtrado(**filtros)
    buffer = ReportesService.usuarios_a_excel(usuarios)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="usuarios_{datetime.now():%Y%m%d_%H%M}.xlsx"'
    )
    return response


@login_required
def exportar_pdf(request):
    filtros = {
        "desde": request.GET.get("desde") or None,
        "hasta": request.GET.get("hasta") or None,
        "grupo": request.GET.get("grupo") or None,
        "activo": request.GET.get("activo") or None,
        "staff": request.GET.get("staff") or None,
    }
    usuarios = EstadisticasService.informe_filtrado(**filtros)
    buffer = ReportesService.usuarios_a_pdf(
        usuarios,
        titulo="Informe de Usuarios — Deimos",
        filtros={k: v for k, v in filtros.items() if v},
    )
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="usuarios_{datetime.now():%Y%m%d_%H%M}.pdf"'
    )
    return response