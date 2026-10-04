# Suscripciones

La Gestion de socios esta integrada en **Suscripciones**, accesible desde el menu o `/payments/subscriptions/`.

La lista muestra socio, DNI, plan y descripcion, monto, estado y ultimo pago. Incluye usuarios sin plan para poder asignarles uno. La busqueda admite usuario, nombre y DNI y la lista esta paginada.

- Agregar plan / Editar plan abre la ficha del socio para asignar un plan y guardar el estado de la suscripcion.
- Pagar registra el cobro sin medio de pago.
- Ver pagos consulta el historial del socio y permite buscar por ID o anular un cobro desde Pagos.

La ficha contiene los formularios de plan y pago. El precio del plan se propone para nuevos cobros; una cuota existente conserva su monto. Los planes del perfil y de la membresia se sincronizan.

Los administradores gestionan planes. Los operadores con permisos de pagos registran cobros. Los socios consultan su propia suscripcion e historial.

Las direcciones anteriores de `/members/` conservan acceso a la interfaz unificada. La explicacion completa de cobros y anulaciones esta en `payments/README.md`.
