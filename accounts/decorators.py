from django.http import HttpResponseForbidden
from functools import wraps

# def role_required(required_role):
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             if not request.user.is_authenticated:
#                 return HttpResponseForbidden("You must be logged in.")
#             if request.user.role != required_role:
#                 return HttpResponseForbidden("You do not have permission to access this page.")
#             return view_func(request, *args, **kwargs)
#         return _wrapped_view
#     return decorator
from django.shortcuts import render

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return render(request, 'accounts/403.html', status=403)
            if request.user.role != required_role:
                return render(request, 'accounts/403.html', status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
