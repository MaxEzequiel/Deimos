import ast
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
	PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "crud_auth_original"
for name, file in [
	("Informe", "ARIALUNI.TTF"), ("InformeBold", "arialbd.ttf"),
	("Code", "consola.ttf"),
]:
	pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / file)))
pdfmetrics.registerFontFamily("Informe", normal="Informe", bold="InformeBold")
styles = getSampleStyleSheet()
for style in styles.byName.values():
	style.fontName = "Informe"
styles["BodyText"].fontSize = 10
styles["BodyText"].leading = 15
styles["BodyText"].spaceAfter = 7
styles["Heading2"].fontName = "InformeBold"
styles["Heading2"].spaceBefore = 14
code_style = ParagraphStyle(
	"CodeBlock", fontName="Code", fontSize=7, leading=10,
	backColor=colors.HexColor("#f1f4f1"), borderPadding=7, spaceAfter=12,
)
story = []


def add(text, style="BodyText"):
	story.append(Paragraph(text, styles[style]))


def table(rows, widths):
	grid = Table([
		[Paragraph(escape(cell), styles["BodyText"]) for cell in row]
		for row in rows
	], colWidths=widths, repeatRows=1)
	grid.setStyle(TableStyle([
		("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e1eae1")),
		("VALIGN", (0, 0), (-1, -1), "TOP"),
		("TOPPADDING", (0, 0), (-1, -1), 7),
		("BOTTOMPADDING", (0, 0), (-1, -1), 7),
		("LINEBELOW", (0, 0), (-1, -1), .3, colors.grey),
	]))
	story.append(grid)


add("Deimos Gym · Suscripciones, Pagos y Factura", "Title")
add("Informe técnico y funcional · 9 de octubre de 2026")
add("1. Funcionamiento y relaciones", "Heading2")
add(
	"Suscripciones abre la ficha del socio. En un solo formulario se elige "
	"plan, estado, período, fecha y medio de pago. Confirmar pago valida y "
	"guarda la membresía y el cobro juntos. Si algo falla, se revierte la "
	"operación. Una cuota pendiente conserva su importe original."
)
table([
	["Relación", "Función"],
	["Usuario → Person", "Perfil: nombre, apellido y DNI."],
	["Usuario → Membership → Plan", "Membresía, estado y precio del plan."],
	["Usuario → MonthlyPayment", "Una cuota por usuario y mes."],
	["MonthlyPayment → PaymentMovement", "Cobros y anulaciones de esa cuota."],
	["PaymentMovement → reversal_of", "La anulación enlaza al cobro original."],
], [210, 295])
add("2. Medios de pago, cobertura y factura", "Heading2")
add(
	"El medio es obligatorio: Efectivo (cash), Transferencia (transfer) o "
	"Tarjeta (card). Se almacena en method de la cuota y del movimiento; "
	"el historial y la factura muestran su etiqueta. La anulación conserva "
	"el medio original. Los pagos históricos sin ese dato muestran "
	"Sin registrar. La migración 0006_payment_method agrega los campos."
)
add(
	"La cobertura comienza en la fecha de pago y vence el mismo día del mes "
	"siguiente, ajustado al último día si corresponde. La vigencia efectiva "
	"exige membresía activa y pago vigente; el vencimiento es inclusivo."
)
add(
	"Pagos permite buscar por DNI o nombre y calcula ingresos, anulaciones "
	"y neto. ID MOVI. identifica el movimiento; ID FACT es la referencia "
	"automática PAGO-00000003, por ejemplo. Anular mantiene el cobro positivo "
	"y agrega uno negativo; la cuota queda pendiente y permite otro cobro."
)
add(
	"La factura es una vista del movimiento, no un modelo independiente. "
	"Conserva su importe y medio, pero muestra el plan actual del socio: "
	"no se almacena el nombre histórico del plan. Es un comprobante interno "
	"sin validez fiscal. Los socios acceden solo a sus propios registros."
)
story.append(PageBreak())
add("3. Gráfico del flujo", "Heading2")
diagram = Drawing(505, 575)
ink = colors.HexColor("#19372b")


def box(x, y, width, title, detail):
	diagram.add(Rect(x, y, width, 45, rx=6,
		fillColor=colors.HexColor("#e8efe9"), strokeColor=ink))
	for n, text in enumerate([title, detail]):
		diagram.add(String(x + width / 2, y + 28 - n * 12, text,
			fontName="Informe", fontSize=8, textAnchor="middle"))


def arrow(x, top, bottom):
	diagram.add(Line(x, top, x, bottom, strokeColor=ink))
	diagram.add(Polygon([x, bottom, x - 4, bottom + 7, x + 4, bottom + 7],
		fillColor=ink, strokeColor=ink))


steps = [
	("SUSCRIPCIONES · abrir ficha", "manage_member() · GET"),
	("Plan + estado + período + fecha + medio", "Confirmar pago · POST"),
	("Validar ambos formularios", "Plan positivo / importe / fecha / medio"),
	("TRANSACCIÓN · guardar Membership", "Sincronizar Person.plan"),
	("register_member_payment()", "Crear o saldar cuota + cobertura + medio"),
	("create_payment_movement()", "Ingreso positivo + referencia + auditoría"),
	("PAGOS · payment_history()", "Búsqueda / totales / acciones"),
]
for n, (title, detail) in enumerate(steps):
	y = 520 - n * 65
	box(110, y, 285, title, detail)
	if n:
		arrow(252, y + 65, y + 45)
box(3, 15, 235, "IMPRIMIR · payment_invoice()",
	"Comprobante → window.print() → PDF")
box(265, 15, 235, "ANULAR · reverse_payment()",
	"Negativo + cuota pendiente → nuevo cobro")
diagram.add(Line(252, 130, 252, 85, strokeColor=ink))
diagram.add(Line(120, 85, 380, 85, strokeColor=ink))
arrow(120, 85, 60)
arrow(380, 85, 60)
story.append(diagram)
add(
	"Si la validación falla, se muestran errores sin guardar. Si falla "
	"el cobro o la auditoría durante la transacción, se revierten todos "
	"los cambios. Imprimir no crea movimientos ni modifica el pago."
)
story.append(PageBreak())
add("4. Bloques de código y ubicación de cada operación", "Heading2")
add(
	"Los bloques siguientes se extraen del código actual. Las rutas son "
	"relativas a crud_auth_original. Cada línea conserva su número para "
	"localizar la operación; estos números pueden variar con futuras ediciones."
)
blocks = [
	("memberships/management_views.py", "manage_member",
	 "Recibe el formulario único; valida plan y pago. El bloque "
	 "transaction.atomic() guarda Membership, limpia las relaciones "
	 "en caché, llama al servicio del cobro y audita. El GET no cobra."),
	("memberships/forms.py", "MemberManagementForm",
	 "Obliga a elegir plan y valida que tenga precio positivo. El estado "
	 "es administrativo; no reemplaza la validación de cobertura."),
	("payments/forms.py", "MemberPaymentForm",
	 "Exige medio de pago y normaliza el período. Valida importe del plan "
	 "o cuota pendiente y rechaza meses ya pagados. El atributo readonly "
	 "es visual; las validaciones del servidor impiden alterar el importe."),
	("payments/services.py", "register_member_payment",
	 "Obtiene o crea MonthlyPayment y bloquea la cuota. Guarda fecha, "
	 "medio y operador, aplica cobertura y llama al creador del movimiento. "
	 "La función devuelve la cuota; el movimiento se crea por separado."),
	("payments/services.py", "create_payment_movement",
	 "Aquí se crea el INGRESO positivo. Copia importe, fecha, operador y "
	 "medio de la cuota a PaymentMovement. Genera la referencia con el ID "
	 "del movimiento y la guarda también en la cuota."),
	("payments/services.py", "apply_payment_coverage",
	 "Define el inicio y fin desde la fecha real de pago; utiliza "
	 "next_month_expiry() para ajustar meses con distinta cantidad de días."),
	("memberships/services.py", "membership_coverage",
	 "Combina estado administrativo con último pago y vencimiento. Al "
	 "anular un pago puede quedar disponible la cobertura de uno anterior."),
	("payments/views.py", "payment_history",
	 "Consulta movimientos respetando permisos, aplica búsqueda por socio "
	 "y calcula ingresos, egresos y neto. Los filtros internos por ID "
	 "sirven a los enlaces de cobro/anulación, no al buscador visible."),
	("payments/views.py", "cancel_payment",
	 "GET muestra la confirmación. POST ejecuta reverse_payment() y "
	 "audita; requiere permisos de consulta y modificación de pagos."),
	("payments/services.py", "reverse_payment",
	 "Aquí se crea la ANULACIÓN negativa. reversal_of enlaza al original; "
	 "conserva cuota, referencia y medio. Limpia fecha y cobertura de la "
	 "cuota para habilitar un nuevo pago. Impide anulaciones repetidas."),
	("payments/views.py", "payment_invoice",
	 "Aquí se consulta el COMPROBANTE. Reúne movimiento, cuota, usuario, "
	 "perfil y membresía; verifica acceso y renderiza invoice.html. "
	 "No guarda una factura ni genera otro movimiento."),
	("accounts/signals.py", "sync_membership_plan",
	 "Al guardar Membership sincroniza el plan en Person. La señal "
	 "queda incluida en la transacción que confirma el pago."),
	("accounts/signals.py", "activate_paid_membership",
	 "Al guardar una cuota pagada obtiene o crea la membresía si falta. "
	 "No cambia el estado manual de una membresía existente."),
]
for index, (file, name, explanation) in enumerate(blocks, 1):
	source = (PROJECT / file).read_text(encoding="utf-8")
	node = next(n for n in ast.walk(ast.parse(source))
		if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
	start = min([node.lineno] + [n.lineno for n in node.decorator_list])
	end = node.end_lineno
	add(f"4.{index}. {name}", "Heading2")
	add(f"<b>Ubicación:</b> {file} · líneas {start}–{end}")
	add(explanation)
	lines = source.splitlines()[start - 1:end]
	for offset in range(0, len(lines), 25):
		code = "\n".join(
			f"{start + offset + n:>3}  {line.expandtabs(4)}"
			for n, line in enumerate(lines[offset:offset + 25])
		)
		story.append(Preformatted(code, code_style, maxLineLength=110,
			splitChars=" ,", newLineChars="     "))
add("5. Interfaz y almacenamiento", "Heading2")
for text in [
	"<b>memberships/templates/memberships/manage_member.html:</b> "
	"formulario POST con CSRF y un único botón Confirmar pago.",
	"<b>staticfiles/js/member-payment.js:</b> actualiza el importe visible "
	"al seleccionar plan. La validación definitiva está en Python.",
	"<b>payments/templates/payments/history.html:</b> presenta cada "
	"movimiento con DNI, medio, referencia, estado y acciones.",
	"<b>payments/templates/payments/invoice.html:</b> presenta la factura. "
	"payment-invoice.css define el estilo y payment-invoice.js ejecuta "
	"window.print(). Ambos están en staticfiles/style y staticfiles/js.",
	"<b>payments/models.py:</b> define cuota, movimientos, relaciones y "
	"PAYMENT_METHODS. payments/migrations/0006_payment_method.py agrega "
	"method a los dos modelos sin inventar medios para pagos anteriores.",
]:
	add(text)


def footer(canvas, doc):
	canvas.saveState()
	canvas.setFont("Informe", 8)
	canvas.drawString(45, 25, "Deimos Gym · Informe técnico de pagos")
	canvas.drawRightString(A4[0] - 45, 25, f"Página {doc.page}")
	canvas.restoreState()


output = Path(__file__).with_name("Informe_Suscripciones_Pagos_Factura.pdf")
SimpleDocTemplate(
	str(output), pagesize=A4, leftMargin=45, rightMargin=45,
	topMargin=42, bottomMargin=55,
	title="Suscripciones, Pagos y Factura: código y flujo", author="Deimos Gym",
).build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
