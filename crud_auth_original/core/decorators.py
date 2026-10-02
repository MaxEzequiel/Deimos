from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def user_is_active(user):
    return user.is_active and user.is_authenticated


def superuser_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_active and request.user.is_superuser):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view

