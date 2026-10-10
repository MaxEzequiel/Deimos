from core.decorators import superuser_required
from django.views.decorators.http import require_http_methods
from datetime import datetime
from core.forms import DateRangeForm, StatisticsPeriodForm, CheckInWeekdayForm
from django.http import HttpResponseBadRequest
from django.utils import timezone

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from accounts.services.estadisticas_service import EstadisticasService
from accounts.services.reportes_service import ReportesService


@login_required
@superuser_required
@require_http_methods(["GET"])
def dashboard_usuarios(request):
	form = StatisticsPeriodForm(request.GET)
	if not form.is_valid():
		return HttpResponseBadRequest("Año o mes no válido")
	anio = form.cleaned_data["anio"]
	mes = form.cleaned_data["mes"]
	fechas = DateRangeForm(request.GET)
	if not fechas.is_valid():
		return HttpResponseBadRequest("Fechas no válidas: la fecha desde debe ser anterior o igual a la fecha hasta")
	ingresos = EstadisticasService.informe_ingresos_diarios(anio, mes, **fechas.cleaned_data)
	actividad_diaria = EstadisticasService.actividad_por_dia(anio, mes)
	suscripciones = EstadisticasService.informe_suscripciones()
	contexto = {
		"ingresos_diarios": ingresos["dias"],
		"totales_ingresos": ingresos["totales"],
		"ingresos_desde": fechas.cleaned_data["desde"],
		"ingresos_hasta": fechas.cleaned_data["hasta"],
		"mes_seleccionado": mes,
		"checkins_diarios": [row for row in actividad_diaria if row["checkins"]],
		"resumen_checkins": EstadisticasService.resumen_checkins(anio, mes),
		"total_checkins": sum(row["checkins"] for row in actividad_diaria),
		"resumen": EstadisticasService.resumen_general(),
		"resumen_suscripciones": EstadisticasService.resumen_suscripciones(
			suscripciones
		),
		"resumen_rutinas": EstadisticasService.resumen_rutinas(),
		"resumen_pagos": EstadisticasService.resumen_pagos(anio=anio, mes=mes),
		"anios_disponibles": EstadisticasService.anios_disponibles(),
		"anio_seleccionado": int(anio),
		"anio_actual": timezone.localdate().year,
	}
	return render(request, "estadisticas/dashboard.html", contexto)


@login_required
@superuser_required
@require_http_methods(["GET"])
def datos_graficos(request):
	form = StatisticsPeriodForm(request.GET)
	if not form.is_valid():
		return JsonResponse({"errors": form.errors}, status=400)
	anio = form.cleaned_data["anio"]
	mes = form.cleaned_data["mes"]

	return JsonResponse(
		{
			"resumen": EstadisticasService.resumen_general(),
			"por_mes": EstadisticasService.registros_por_mes(
				anio=anio, mes=mes
			),
			"actividad_diaria": EstadisticasService.actividad_por_dia(anio, mes),
			"pagos_mes": EstadisticasService.pagos_por_mes(anio=anio, mes=mes),
			"suscripciones_por_plan": EstadisticasService.suscripciones_por_plan(),
			"activos_inactivos": EstadisticasService.usuarios_activos_vs_inactivos(),
			"recientes": EstadisticasService.top_recientes(),
			"resumen_rutinas": EstadisticasService.resumen_rutinas(),
			"rutinas_mes": EstadisticasService.rutinas_por_mes(anio=anio),
			"top_clientes": EstadisticasService.top_clientes_con_rutinas(),
			"anio": int(anio),
			"mes": int(mes) if mes else None,
		}
	)


@login_required
@superuser_required
@require_http_methods(["GET"])
def informe_usuarios(request):
	date_form = DateRangeForm(request.GET)
	if not date_form.is_valid():
		return HttpResponseBadRequest("Fechas no válidas")
	filtros = {
		"desde": request.GET.get("desde") or "",
		"hasta": request.GET.get("hasta") or "",
		"grupo": request.GET.get("grupo") or "",
		"activo": request.GET.get("activo") or "",
		"staff": request.GET.get("staff") or "",
	}
	usuarios = EstadisticasService.informe_filtrado(**filtros)
	return render(
		request,
		"estadisticas/informe.html",
		{
			"usuarios": usuarios,
			"filtros": filtros,
			"grupos_disponibles": EstadisticasService.grupos_disponibles(),
			"total": len(usuarios),
		},
	)


@login_required
@superuser_required
@require_http_methods(["GET"])
def exportar_excel(request):
	date_form = DateRangeForm(request.GET)
	if not date_form.is_valid():
		return HttpResponseBadRequest("Fechas no válidas")
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
@superuser_required
@require_http_methods(["GET"])
def exportar_pdf(request):
	date_form = DateRangeForm(request.GET)
	if not date_form.is_valid():
		return HttpResponseBadRequest("Fechas no válidas")
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


@login_required
@superuser_required
@require_http_methods(["GET"])
def informe_checkins(request):
	form = StatisticsPeriodForm(request.GET)
	if not form.is_valid():
		return HttpResponseBadRequest("Año o mes no válido")
	anio = form.cleaned_data["anio"]
	mes = form.cleaned_data["mes"]
	if request.GET.get("todos") == "1":
		anio = mes = None
	fechas = DateRangeForm(request.GET)
	if not fechas.is_valid():
		return HttpResponseBadRequest("Fechas no válidas")
	semana = CheckInWeekdayForm(request.GET)
	if not semana.is_valid():
		return HttpResponseBadRequest("Día de la semana no válido")
	dia_semana = semana.cleaned_data["dia_semana"]
	nombre = request.GET.get("nombre", "").strip()
	dni = request.GET.get("dni", "").strip()
	checkins = EstadisticasService.checkins_en_periodo(
		anio, mes, nombre=nombre, dni=dni, **fechas.cleaned_data
	)
	asistencia_semana = EstadisticasService.asistencia_por_dia_semana(checkins)
	if dia_semana:
		checkins = checkins.filter(fecha__iso_week_day=dia_semana)
	return render(request, "estadisticas/checkins.html", {
		"asistencia_semana": asistencia_semana,
		"dias_mayor_asistencia": [dia for dia in asistencia_semana if dia["mayor_asistencia"]],
		"dia_semana": dia_semana,
		"checkins": checkins,
		"resumen_checkins": {"total": checkins.count()},
		"anio": anio, "mes": mes,
		"nombre": nombre, "dni": dni,
		"desde": fechas.cleaned_data["desde"],
		"hasta": fechas.cleaned_data["hasta"],
	})
