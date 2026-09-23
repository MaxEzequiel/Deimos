from django.contrib.auth.decorators import login_required, user_passes_test


def _es_admin(user):
    """True si el usuario es superusuario o staff."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def admin_required(view_func):
    """Decorador: obliga login + ser admin. Redirige al login si no."""
    return user_passes_test(
        _es_admin,
        login_url="login",
        redirect_field_name=None,
    )(login_required(view_func))