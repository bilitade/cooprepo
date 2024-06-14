# file_management/decorators.py

from functools import wraps
from django.http import HttpResponseForbidden

def user_passes_permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            print(f"Checking permission {permission} for user {request.user.username}")
            if request.user.is_superuser:
                print(f"User {request.user.username} is superuser. Access granted.")
                return view_func(request, *args, **kwargs)
            if request.user.has_perm(permission):
                print(f"User {request.user.username} has permission {permission}. Access granted.")
                return view_func(request, *args, **kwargs)
            else:
                print(f"User {request.user.username} does not have permission {permission}. Access denied.")
                return HttpResponseForbidden('Access Denied')  # Or render a specific template
        return _wrapped_view
    return decorator
