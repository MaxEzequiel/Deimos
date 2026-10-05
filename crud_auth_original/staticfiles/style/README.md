# Organización del CSS de Deimos

El CSS se organiza por responsabilidad. Para modificar una pantalla, editar el módulo correspondiente en lugar de agregar reglas a `style.css`.

## Componentes compartidos

Los archivos de `components/` se cargan desde `crud_auth/templates/includes/component_styles.html`, en este orden:

| Archivo | Responsabilidad |
| --- | --- |
| `base-components.css` | Reset, contenedores, bienvenida, tarjetas y selección de contenido. |
| `form-layout.css` | Estructura de formularios, campos, etiquetas y mensajes de ayuda. |
| `buttons.css` | Botones principales, secundarios y grupos de botones. |
| `member-content.css` | Clases, selección, perfiles y rutinas. |
| `plans-tables.css` | Módulo de planes, tablas, celdas y acciones de filas. |
| `publications.css` | Tarjetas, imágenes y contenido de publicaciones. |
| `notifications.css` | Alertas, notificaciones y sus animaciones. |
| `shared-overrides.css` | Ajustes compartidos de tamaño, tarjetas y animación de entrada. |
| `navigation.css` | Panel, barra lateral, barra superior y herramientas del usuario. |
| `auth-layout.css` | Contenedores de ingreso y autenticación. |
| `filters-audit.css` | Filtros, búsqueda, auditoría, paginación y botones de filtro. |
| `statistics.css` | Filtros y tarjetas de estadísticas. |
| `home.css` | Presentación, datos y accesos de la página de inicio. |

Las reglas adaptables propias de cada módulo permanecen junto a sus componentes. Se conservó el orden original de todas las reglas para evitar cambios en la cascada.

## Estilos especializados

Después de los componentes, las plantillas cargan:

- `responsive-fix.css`: ajustes compartidos de navegación móvil, tablas y tamaños de pantalla.
- `forms.css`: controles y validación comunes para formularios del sistema y autenticación.
- `deimos-design.css`: paleta clara/oscura, tipografía y apariencia común de Deimos. Se carga al final para unificar los componentes.

La pantalla de recepción usa `checkin-kiosk.css`, de manera independiente del panel. La administración de Django usa `admin-theme.css`, `forms.css` y `deimos-design.css`.

`style.css` contiene únicamente importaciones como entrada de compatibilidad. Las plantillas del sistema utilizan enlaces directos a los componentes para que el navegador pueda descargarlos en paralelo. No cargar ambas entradas en una misma página.

## Criterio para nuevos estilos

Agregar cada regla al archivo de su componente. Usar las variables de `deimos-design.css` para los colores compartidos. Mantener los ajustes móviles junto a las reglas del componente; reservar `responsive-fix.css` para cambios que afectan varias pantallas. Crear otro archivo cuando aparezca una responsabilidad nueva, no por cada botón o página.
