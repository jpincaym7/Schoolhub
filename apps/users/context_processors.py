# apps/users/context_processors.py

def is_admin(request):
    """
    Context processor to check if the logged-in user is an admin.
    """
    if request.user.is_authenticated:
        return {'is_admin': request.user.user_type == 'admin'}
    return {'is_admin': False}
