import base64
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet


class ReportesService:

    # ---------- EXCEL ----------
    @staticmethod
    def usuarios_a_excel(usuarios):
        wb = Workbook()
        ws = wb.active
        ws.title = "Usuarios"

        headers = ["ID", "Usuario", "Nombre", "Apellido", "Email",
                   "DNI", "Grupo", "Activo", "Staff", "Fecha registro"]
        ws.append(headers)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="34495E")
        for col, _ in enumerate(headers, 1):
            c = ws.cell(row=1, column=col)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center")

        for u in usuarios:
            ws.append([
                u["id"], u["username"], u["nombre"], u["apellido"],
                u["email"], u["dni"], u["grupo"],
                "Sí" if u["is_active"] else "No",
                "Sí" if u["is_staff"] else "No",
                u["fecha_registro"],
            ])

        # Ancho automático
        for col in ws.columns:
            max_len = max(len(str(c.value)) if c.value else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = max_len + 3

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    # ---------- PDF ----------
    @staticmethod
    def usuarios_a_pdf(usuarios, titulo="Informe de Usuarios", filtros=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(A4),
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph(f"<b>{titulo}</b>", styles["Title"]))
        elementos.append(Spacer(1, 0.4 * cm))

        if filtros:
            texto_filtros = " | ".join(f"{k}: {v}" for k, v in filtros.items() if v)
            if texto_filtros:
                elementos.append(Paragraph(f"<i>Filtros: {texto_filtros}</i>",
                                            styles["Normal"]))
                elementos.append(Spacer(1, 0.4 * cm))

        data = [["ID", "Usuario", "Nombre", "Apellido", "Email",
                 "Grupo", "Activo", "Fecha"]]
        for u in usuarios:
            data.append([
                u["id"], u["username"], u["nombre"], u["apellido"],
                u["email"], u["grupo"],
                "Sí" if u["is_active"] else "No",
                u["fecha_registro"],
            ])

        tabla = Table(data, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F2F2")]),
        ]))
        elementos.append(tabla)

        doc.build(elementos)
        buffer.seek(0)
        return buffer
	
	
    # ============================================
    # ESTADÍSTICAS CON GRÁFICOS
    # ============================================

    @staticmethod
    def _imagen_desde_base64(data_url):
        """Convierte 'data:image/png;base64,XXX' a BytesIO."""
        if not data_url:
            return None
        if "," in data_url:
            data_url = data_url.split(",", 1)[1]
        return BytesIO(base64.b64decode(data_url))

    @staticmethod
    def estadisticas_a_excel(datos, imagenes):
        """Excel con hoja de datos + hoja con imágenes de gráficos."""
        from openpyxl.drawing.image import Image as XLImage

        wb = Workbook()

        # --- Hoja 1: datos numéricos ---
        ws = wb.active
        ws.title = "Datos"
        ws.append(["Sección", "Métrica", "Valor"])
        ws.append(["Usuarios", "Total", datos["resumen"]["total"]])
        ws.append(["Usuarios", "Activos", datos["resumen"]["activos"]])
        ws.append(["Usuarios", "Inactivos", datos["resumen"]["inactivos"]])
        ws.append(["Usuarios", "Staff", datos["resumen"]["staff"]])
        ws.append(["Membresías", "Total", datos["resumen_membresias"]["total"]])
        ws.append(["Membresías", "Activas", datos["resumen_membresias"]["activas"]])
        ws.append(["Membresías", "Vencidas", datos["resumen_membresias"]["vencidas"]])
        ws.append(["Rutinas", "Total", datos["resumen_rutinas"]["total"]])
        ws.append(["Rutinas", "Con cliente", datos["resumen_rutinas"]["con_cliente"]])
        ws.append(["Rutinas", "Sin cliente", datos["resumen_rutinas"]["sin_cliente"]])
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 15

        # --- Hoja 2: gráficos ---
        ws_img = wb.create_sheet("Gráficos")
        fila = 1
        for titulo, data_url in imagenes.items():
            ws_img.cell(row=fila, column=1, value=titulo)
            fila += 1

            img = XLImage(ReportesService._imagen_desde_base64(data_url))
            img.width = 500
            img.height = 280
            img.anchor = f"A{fila}"
            ws_img.add_image(img)

            fila += 16

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def estadisticas_a_pdf(datos, imagenes):
        """PDF con tabla de datos + imágenes de gráficos."""
        from reportlab.platypus import Image as RLImage, PageBreak

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph("<b>Informe de Estadísticas</b>", styles["Title"]))
        elementos.append(Spacer(1, 0.5 * cm))

        filas = [
            ["Sección", "Métrica", "Valor"],
            ["Usuarios", "Total", datos["resumen"]["total"]],
            ["Usuarios", "Activos", datos["resumen"]["activos"]],
            ["Usuarios", "Inactivos", datos["resumen"]["inactivos"]],
            ["Usuarios", "Staff", datos["resumen"]["staff"]],
            ["Membresías", "Total", datos["resumen_membresias"]["total"]],
            ["Membresías", "Activas", datos["resumen_membresias"]["activas"]],
            ["Membresías", "Vencidas", datos["resumen_membresias"]["vencidas"]],
            ["Rutinas", "Total", datos["resumen_rutinas"]["total"]],
            ["Rutinas", "Con cliente", datos["resumen_rutinas"]["con_cliente"]],
        ]

        tabla = Table(filas, colWidths=[5 * cm, 5 * cm, 3 * cm])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabla)

        if imagenes:
            elementos.append(PageBreak())
            elementos.append(Paragraph("<b>Gráficos</b>", styles["Heading1"]))
            elementos.append(Spacer(1, 0.5 * cm))

            for titulo, data_url in imagenes.items():
                elementos.append(Paragraph(f"<b>{titulo}</b>", styles["Heading3"]))
                elementos.append(RLImage(
                    ReportesService._imagen_desde_base64(data_url),
                    width=15 * cm, height=8 * cm,
                ))
                elementos.append(Spacer(1, 0.5 * cm))

        doc.build(elementos)
        buffer.seek(0)
        return buffer