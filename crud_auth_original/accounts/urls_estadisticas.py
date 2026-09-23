from django.urls import path
from accounts import views_estadisticas as estadisticas

urlpatterns = [
    path("", estadisticas.dashboard_usuarios, name="estadisticas_dashboard"),
    path("data/", estadisticas.datos_graficos, name="estadisticas_data"),
    path("informes/usuarios/", estadisticas.informe_usuarios, name="estadisticas_informe"),
    path("reportes/usuarios/excel/", estadisticas.exportar_excel, name="estadisticas_excel"),
    path("reportes/usuarios/pdf/", estadisticas.exportar_pdf, name="estadisticas_pdf"),

    path("reportes/dashboard/excel/", estadisticas.exportar_dashboard_excel, name="dashboard_excel"),
    path("reportes/dashboard/pdf/", estadisticas.exportar_dashboard_pdf, name="dashboard_pdf"),
    path("reportes/enviar-email/", estadisticas.enviar_dashboard_email, name="dashboard_email"),
]