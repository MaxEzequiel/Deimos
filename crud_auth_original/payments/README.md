# Suscripciones y Pagos

## Pantallas

**Suscripciones** (`/payments/subscriptions/`) unifica la antigua Gestion de socios con Suscripciones. Lista los usuarios con y sin plan, permite buscar por usuario, nombre o DNI y muestra plan, descripcion, monto, estado y ultimo pago. Las acciones son Agregar/Editar plan, Pagar y Ver pagos. Al editar un plan se abre la ficha del socio con los formularios de plan y pago. Los administradores gestionan planes; los gestores con permisos de pagos registran cobros; cada socio consulta solo su propia suscripcion.

El monto corresponde al registro del mes actual cuando existe; de lo contrario se utiliza el precio del plan. Los cambios de plan no alteran importes ya registrados.

**Pagos** (`/payments/history/`) muestra los cobros realizados y las anulaciones. Ver pagos desde Suscripciones filtra el historial por usuario. El filtro ID busca un movimiento exacto; Limpiar muestra todo el historial permitido.

Pagar solicita mes, monto, fecha y referencia opcional. No se solicita ni almacena medio de pago. El monto debe coincidir con el precio del plan o con el importe de la cuota previamente registrada.

Anular conserva el cobro original y crea otro registro por el mismo monto en negativo. La cuota queda pendiente y puede volver a pagarse. No se permite anular dos veces el mismo cobro ni anular un movimiento negativo.

## Codigo explicado

- `models.py`: `MonthlyPayment` conserva internamente la relacion usuario/mes usada por membresias y check-in; no tiene una pantalla ni un modulo de Mensualidades. `PaymentMovement` guarda cada cobro y anulacion con su monto, fecha, referencia y operador. `reversal_of` relaciona la anulacion con el cobro original y permite una sola contrapartida.
- `forms.py`: valida los datos del cobro. La fecha no puede ser futura y un pago existente conserva su importe.
- `services.py`: `register_member_payment()` registra el cobro y crea su movimiento positivo. `reverse_payment()` crea `amount=-original.amount` y deja el registro interno pendiente. Las transacciones evitan cambios parciales. Ejemplo: +100, -100, +100 equivale a un total neto de 100.
- `memberships/management_views.py`: centraliza la lista paginada de Suscripciones y la ficha de plan y pago. `payments/views.py` reutiliza esa misma lista y contiene cobro, historial y anulacion. El historial suma los montos con signo y limita a cada socio a sus propios registros. Un ID invalido muestra una lista vacia.
- `urls.py`: publica esas pantallas. `/payments/` muestra Suscripciones. Las rutas antiguas de generar mensualidades y registrar cuotas ya no existen.
- `templates/payments/`: muestra las dos secciones, el formulario de cobro y la confirmacion de anulacion. Los formularios incluyen CSRF y solo modifican datos mediante POST.
- `admin.py`: permite consultar el historial como solo lectura; no publica la administracion de mensualidades.

Los gestores necesitan los permisos `pagos.view_monthlypayment` y `pagos.change_monthlypayment`, cuyos identificadores se mantienen por compatibilidad. Los socios solo pueden consultar.

## Migraciones

`0002` crea el historial y `0003` incorpora los cobros existentes. `0004` elimina el medio de pago de ambos modelos y la validacion que lo exigia. Los registros de cobro y anulacion se conservan.

Para aplicar en otra instalacion:

```powershell
python manage.py migrate
python manage.py test payments
```

Las pruebas verifican cobro sin medio de pago, anulacion, duplicados, nuevo cobro, total neto, filtros, permisos y eliminacion de las rutas de Mensualidades.

## Unificacion

El menu tiene una sola entrada Suscripciones. La lista utiliza `memberships/member_list.html`; la ficha utiliza `memberships/manage_member.html` y su URL es `/payments/subscriptions/<id>/`. Las antiguas direcciones `/members/` muestran la misma lista y `/members/<id>/` redirige a la ficha unificada. Se conserva compatibilidad sin duplicar la interfaz. Esta unificacion no requiere migraciones.

## Integracion con NoeGao/Deimos

Se mantienen las fechas `coverage_start` y `coverage_end` del nuevo repositorio. Cada cobro calcula su vigencia; al anular se limpian ambas fechas del registro interno. La migracion `0005_merge_payment_coverage` integra las dos ramas de migraciones sin borrar cobros ni historial.
