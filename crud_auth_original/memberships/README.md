# Suscripciones

La Gestion de socios esta integrada en **Suscripciones**, accesible desde el menu o `/payments/subscriptions/`.

La lista muestra socio, DNI, plan y descripcion, monto, estado y ultimo pago. Incluye usuarios sin plan para poder asignarles uno. La busqueda admite usuario, nombre y DNI y la lista esta paginada.

- Agregar plan / Editar plan abre la ficha del socio para elegir el plan y confirmar el pago junto con la suscripción.
- Pagar registra el cobro sin medio de pago.
- Ver pagos consulta el historial del socio y permite buscar por ID o anular un cobro desde Pagos.

La ficha contiene un único formulario de plan y pago con el botón
**Confirmar pago**. El precio corresponde al plan seleccionado; una cuota
pendiente conserva su importe original. El plan, el estado y el pago se
guardan en una misma transacción. Si falla la validación o el cobro, no se
guarda ningún cambio. Los planes del perfil y de la membresía se sincronizan.

Los administradores gestionan planes. Los operadores con permisos de pagos registran cobros. Los socios consultan su propia suscripcion e historial.

Las direcciones anteriores de `/members/` conservan acceso a la interfaz unificada. La explicacion completa de cobros y anulaciones esta en `payments/README.md`.
