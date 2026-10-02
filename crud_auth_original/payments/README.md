# Seguimiento de mensualidades

Abrir **Mensualidades** en el menu lateral (`/payments/`) para consultar pagos, deudas y vigencias.

## Flujo principal

1. Como administrador, abrir **Gestion de socios** (`/members/`).
2. Elegir el socio y entrar a **Gestionar**.
3. En **Registrar mensualidad**, ingresar el periodo administrativo, importe, fecha de pago, medio de pago y referencia opcional.
4. Al confirmar el pago, se registra la mensualidad y se calcula la vigencia individual:
   - inicio de vigencia = fecha de pago
   - fin de vigencia = mismo dia del mes siguiente

Ejemplo:

- Juan paga el 15/10: vigencia del 15/10 al 15/11.
- Maria paga el 20/10: vigencia del 20/10 al 20/11.

El listado de **Mensualidades** permite filtrar por periodo, socio y estado. Tambien muestra importe, vencimiento administrativo, fecha de pago y rango de vigencia.

## Relacion con otros modulos

- **Personas/Socios**: cada mensualidad pertenece a un usuario socio.
- **Planes**: el precio sugerido del pago sale del plan asignado al socio.
- **Membresias**: el estado activo o inactivo se calcula usando la vigencia del ultimo pago.
- **Check-in**: usa la vigencia de la mensualidad para mostrar si el socio esta activo, proximo a vencer o vencido.
- **Auditoria**: registrar, eliminar o generar mensualidades deja una accion registrada.

## Generacion masiva

La funcion interna de generacion masiva de cuotas existe para crear deudas administrativas por periodo, pero no es el flujo principal visible. Para este proyecto se prioriza el registro por socio, porque cada socio puede iniciar y vencer en fechas diferentes.

## Verificacion

Para instalar cambios de base de datos:

```powershell
python manage.py migrate
```

Para verificar el modulo:

```powershell
python manage.py test payments
```
