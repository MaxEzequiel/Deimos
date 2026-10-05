# Pantalla de ingreso al gimnasio

Abrir `/checkin/` en el equipo de recepción con una sesión que tenga el permiso `checkin.add_checkin`. El socio solo ingresa su DNI; no necesita iniciar una sesión personal. El botón de la esquina superior derecha activa pantalla completa cuando el navegador lo permite. También se puede utilizar F11.

La pantalla admite teclado de PC: escribir el DNI y presionar Enter. Al confirmar, el servidor valida el DNI y registra el ingreso. El botón muestra “Registrando…” mientras se envía el formulario. Los errores aparecen junto al DNI y permiten corregirlo.

La confirmación muestra nombre, hora de entrada y estado de la cobertura: verde para vigente, amarillo cuando está próxima a vencer y rojo cuando está vencida o no hay pago. Registrar el ingreso no significa que la suscripción esté pagada. Se conserva la regla existente que permite registrar una entrada incluso sin cobertura vigente.

La confirmación permanece visible hasta presionar Enter, Escape o “Siguiente ingreso”. No hay regreso automático. La barra indica la proporción de días restantes desde el último pago hasta su vencimiento, cambia gradualmente de verde a naranja y se vacía al vencer. Desde el día del vencimiento el estado es rojo. Sin JavaScript, el formulario y el enlace siguen funcionando. La pantalla compartida no muestra el listado de otros socios, sus DNI ni observaciones internas. El historial administrativo continúa en `/checkin/history/`.

## Código

- `templates/checkin/kiosk_base.html`: estructura independiente del panel administrativo, marca, reloj, pantalla completa y archivos estáticos.
- `checkin_home.html`: formulario de DNI e indicación de la tecla Enter. Se conserva POST y protección CSRF.
- `checkin_success.html`: confirmación y estado de cobertura. El resultado real procede de `member_checkin_status()`.
- `staticfiles/style/checkin-kiosk.css`: diseño adaptable a monitores y dispositivos pequeños, contraste, foco visible y preferencia de movimiento reducido. Las fuentes web son opcionales y tienen alternativas locales.
- `staticfiles/js/checkin-kiosk.js`: reloj de Argentina, teclado, estado de envío y regreso con Enter o Escape. El servidor sigue siendo quien valida y registra el ingreso.
- `forms.py`: solicita teclado numérico y limita visualmente a diez dígitos, manteniendo la validación del DNI en el servidor.
- `views.py`: utiliza las nuevas plantillas y deja de consultar o exponer el listado de ingresos en la pantalla compartida.

Validación: pruebas de check-in, revisión del JavaScript y comprobación en Chrome de tamaños móviles y de escritorio, teclado de PC, DNI inválido y regreso automático.
