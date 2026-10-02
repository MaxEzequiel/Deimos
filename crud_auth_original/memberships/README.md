# Gestion de socios

Este proyecto mantiene varias apps Django separadas por responsabilidad tecnica, pero en la interfaz se presentan como un solo modulo funcional: **Gestion de socios**.

## Por que se unifica visualmente

El flujo real de administracion de un gimnasio no ocurre en pantallas aisladas. Cuando se administra un socio se necesita ver y modificar informacion relacionada:

- cuenta de usuario
- datos personales
- plan asignado
- membresia
- mensualidades y pagos
- vigencia del ultimo pago
- estado para check-in

Por eso, aunque el codigo siga distribuido en apps tecnicas, la entrada principal del menu es **Gestion de socios**.

## Apps tecnicas que participan

- `accounts`: cuentas de usuario, login, permisos y administracion de usuarios.
- `people`: perfil personal del socio, DNI, nombre, telefono y plan asociado.
- `plans`: planes y precios.
- `memberships`: pantalla central de gestion del socio y estado de membresia.
- `payments`: historial de mensualidades, registro de pagos y vigencias.
- `checkin`: consulta si el socio tiene la mensualidad activa, vencida o proxima a vencer.
- `core`: auditoria de acciones importantes.

## Flujo principal

1. Entrar como administrador.
2. Abrir **Gestion de socios** desde el menu lateral.
3. Buscar el socio por usuario, nombre o DNI.
4. Entrar a **Gestionar socio**.
5. Desde la misma pantalla:
   - asignar o cambiar plan
   - modificar estado administrativo de membresia
   - registrar una mensualidad
   - consultar ultimos pagos
   - ver la vigencia usada por check-in

## Mensualidades dentro del flujo

Las mensualidades se registran por socio. Cada pago tiene una vigencia individual:

- Juan paga el 15/10: vigencia del 15/10 al 15/11.
- Maria paga el 20/10: vigencia del 20/10 al 20/11.

El historial completo sigue disponible desde el acceso **Historial de mensualidades**, pero la carga principal del pago se hace desde la ficha del socio.

## Relacion con rollback

Las operaciones sensibles se guardan en transacciones. Por ejemplo, al eliminar una mensualidad se borra el pago y se registra auditoria dentro de una misma transaccion. Si falla una parte, se ejecuta rollback para no dejar datos inconsistentes.

## Validacion

```powershell
python manage.py test payments memberships checkin
python manage.py makemigrations --check --dry-run
```
