# Gestión de socios

Ingresar como administrador y abrir **Gestión de socios** en el menú, o acceder a `/members/`. También hay accesos desde Usuarios y Mensualidades.

1. Buscar al usuario por nombre, nombre de usuario o DNI.
2. Abrir **Gestionar socio**.
3. Seleccionar un plan y el estado de la membresía; guardar los cambios.
4. Completar mensualidad, importe, fecha de pago, medio y referencia opcional; confirmar el pago.

Guardar un plan propone su precio para los nuevos pagos. Si ya existe una cuota pendiente del mes, debe pagarse por el importe original. Los registros pagados no se sobrescriben y se permite una mensualidad por usuario y mes.

La cuota pagada se refleja en Mensualidades y Check-in. Si su cobertura sigue vigente, activa la membresía. El vencimiento es el mismo día del mes siguiente al pago, utilizando el último día del mes si la fecha original no existe.

Los planes asignados se sincronizan entre el perfil y la membresía para que la generación de cuotas use el mismo plan. Los cambios de plan no modifican los importes de cuotas existentes. Inicio, Gestión de socios y Estadísticas consultan el estado vigente de la membresía y reflejan el vencimiento de los pagos sin requerir una actualización manual diaria.

El estado administrativo de una membresía puede establecerse manualmente. La vigencia del pago que muestra Check-in se calcula por separado: mantener una membresía activa sin pago no genera un pago ni cambia el indicador de mensualidad.

Los usuarios que todavía no tienen perfil personal pueden recibir un plan, una membresía y un pago. La pantalla permite completar sus datos y DNI para habilitar su identificación en Check-in. Los planes previamente asignados se conservan al completar ese perfil.

El módulo de gestión requiere una cuenta de administrador. Los socios pueden consultar sus mensualidades desde la pantalla habitual, sin modificar pagos ni asignaciones. Cada modificación realizada desde este módulo queda registrada en auditoría y se guarda dentro de una transacción.

## Validación

```powershell
python manage.py test --noinput
python manage.py makemigrations --check --dry-run
```

71 pruebas aprobadas, incluidas 20 pruebas de esta gestión e integración con los otros módulos. No requiere cambios de esquema ni migraciones nuevas. No se cargaron pagos de prueba en la base de datos del proyecto.
