# Entornos y ramas

La aplicación usa `DJANGO_ENV`: `DEV` activa depuración; `QA` y `MAIN` la desactivan. Las credenciales se cargan por variables de entorno.

Flujo: `dev` para desarrollo, `qa` para validación y `main` para producción. Promover sólo cambios revisados y, antes de hacerlo, ejecutar `python manage.py migrate`, `python manage.py check` y pruebas. La migración `audit.0001_initial` crea la tabla de auditoría.
