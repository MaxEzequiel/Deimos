# Check-in y mensualidad

El ingreso se valida por el DNI de una persona registrada en `people.Person`. Si el DNI no existe o está duplicado, el formulario muestra un error y no crea el ingreso. La vigencia de la cuota y el estado de la cuenta del socio no bloquean el check-in. El operador sigue necesitando permiso para registrar ingresos.

La confirmación muestra el nombre y las iniciales, la fecha de alta del usuario, la fecha y hora del ingreso, el último pago registrado y la fecha de vencimiento de su cobertura.

## Cálculo del estado

Se toma la mensualidad con la fecha de pago más reciente que no sea futura. La cobertura vence el mismo día del mes siguiente a ese pago. Si ese día no existe en el siguiente mes, se utiliza su último día. Por ejemplo, un pago del 31/01/2026 vence el 28/02/2026.

- Verde: faltan más de 5 días para vencer.
- Naranja: faltan entre 0 y 5 días, incluido el día del vencimiento. El círculo y la línea se muestran a la mitad.
- Rojo: pasó la fecha de vencimiento o no hay pagos registrados.

El día de vencimiento conserva la cobertura hasta el final del día, según la zona horaria configurada en Django. Un pago del 15/10 vence el 15/11 y pasa a rojo el 16/11 si no se registra otro pago.

La fecha límite para pagar una cuota (`MonthlyPayment.due_date`) no determina la cobertura: esta se calcula a partir de `paid_on`. El estado mostrado es el vigente al consultar la pantalla, incluso al abrir un ingreso anterior. Las señales de estado incluyen texto para que no dependan únicamente del color.

Un operador que tiene permiso para registrar ingresos puede ver la confirmación de los ingresos que creó. El permiso para ver ingresos permite acceder también al historial y otras confirmaciones.

## Pruebas

```powershell
python manage.py test checkin.tests --noinput
```

Se verifican DNI inexistentes y duplicados, ingresos sin membresía o pago, permisos del operador, vigencia entre meses, límite de 5 días, día de vencimiento, pagos futuros, último pago, febrero y cambio de año.
