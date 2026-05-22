from django.contrib.auth.decorators import user_passes_test

def user_is_active(user):
    return user.is_active and user.is_authenticated

