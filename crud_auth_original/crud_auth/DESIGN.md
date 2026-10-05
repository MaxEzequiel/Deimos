# Apariencia del sistema

Deimos es el único diseño disponible. Extiende la identidad de la pantalla de ingreso: superficies limpias, tipografía condensada en títulos, tarjetas redondeadas y acentos verde lima. El botón Claro/Oscuro cambia la paleta sin recargar la página. Su etiqueta indica el tema al que se cambiará. Las preferencias guardadas del diseño anterior se ignoran.

La elección se guarda en este navegador y se aplica al navegar entre módulos, ingresar al sistema y abrir el check-in. Si no se eligió un tema, se utiliza la preferencia del sistema operativo. Sin almacenamiento disponible se puede cambiar de apariencia durante la sesión de la página.

## Archivos

- `staticfiles/style/components/`: estilos compartidos divididos por responsabilidad. `templates/includes/component_styles.html` mantiene su orden de carga. La guía completa está en `staticfiles/style/README.md`; `style.css` es una entrada de compatibilidad con importaciones.
- `templates/includes/appearance_controls.html`: control compartido del tema claro u oscuro.
- `staticfiles/js/appearance.js`: fija `data-design="deimos"` y aplica `data-theme` al documento antes de mostrarlo, conserva el tema y sincroniza otras pestañas. Mantiene la clase `light-mode` para los componentes compartidos.
- `staticfiles/style/deimos-design.css`: paleta y estilos del único diseño disponible, Deimos, con tema claro u oscuro. Incluye navegación, tablas, formularios, tarjetas, acceso y administración. Los colores de ingreso y egreso mantienen su significado.
- `base.html`, `base_login.html`, `base_auth.html` y `admin/base_site.html`: incorporan los recursos y los controles.
- `staticfiles/js/estadisticas.js`: ajusta las leyendas y ejes de los gráficos al tema elegido, sin volver a consultar los datos.
- `checkin-kiosk.css`: presenta la pantalla de recepción en claro u oscuro. El check-in utiliza teclado físico y Enter, sin teclado táctil. La confirmación conserva su retorno automático.

Las fuentes de Google son opcionales; se usan fuentes locales de respaldo si no hay conexión. El diseño respeta movimiento reducido y conserva indicaciones de foco para el teclado.

Comprobaciones: renderizado de 40 páginas sin errores de plantillas; 48 combinaciones de páginas, temas y tamaños en Chrome sin desbordamiento horizontal ni errores de JavaScript; gráficos en claro y oscuro, persistencia, regreso al diseño clásico y envío por Enter; 17 pruebas de check-in aprobadas.

El CSS base conserva la estructura compartida de los componentes y las reglas responsive. Se eliminaron las paletas del diseño clásico, sus variantes violetas, degradados y efectos de vidrio. La administración usa los mismos colores de Deimos.
