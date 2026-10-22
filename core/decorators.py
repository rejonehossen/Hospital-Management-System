# core.decorators
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect

def admin_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is an admin,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'admin',
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def doctor_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is a doctor,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'doctor',
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def patient_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is a patient,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'patient',
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def receptionist_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is a receptionist,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'receptionist',
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is staff (admin, doctor, or receptionist),
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role in ['admin', 'doctor', 'receptionist'],
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def verified_user_required(function=None, login_url='login'):
    """
    Decorator for views that checks if the user is verified,
    redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_verified,
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def ajax_required(function):
    """
    Decorator for views that should only be accessed via AJAX.
    """
    def wrap(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return redirect('home')
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def has_permission(permission):
    """
    Decorator for views that checks if the user has specific permission.
    """
    def decorator(function):
        def wrap(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            return function(request, *args, **kwargs)
        wrap.__doc__ = function.__doc__
        wrap.__name__ = function.__name__
        return wrap
    return decorator

def check_ownership(model_class, owner_field='user'):
    """
    Decorator that checks if the user owns the object they're trying to access.
    """
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            # Get the object id from kwargs
            obj_id = kwargs.get('pk') or kwargs.get('id') or kwargs.get('appointment_id') or kwargs.get('prescription_id')

            if not obj_id:
                return view_func(request, *args, **kwargs)

            try:
                obj = model_class.objects.get(pk=obj_id)

                # Check ownership
                if request.user.role == 'admin':
                    # Admin can access everything
                    return view_func(request, *args, **kwargs)

                elif request.user.role == 'doctor':
                    # Doctor can access their own records
                    if hasattr(obj, 'doctor') and obj.doctor.user == request.user:
                        return view_func(request, *args, **kwargs)

                    # Doctor can access appointments with them
                    if model_class == Appointment and obj.doctor.user == request.user:
                        return view_func(request, *args, **kwargs)

                elif request.user.role == 'patient':
                    # Patient can access their own records
                    if hasattr(obj, 'patient') and obj.patient.user == request.user:
                        return view_func(request, *args, **kwargs)

                    # Patient can access their appointments
                    if model_class == Appointment and obj.patient.user == request.user:
                        return view_func(request, *args, **kwargs)

                # If we get here, user doesn't have permission
                messages.error(request, 'You do not have permission to access this resource.')
                return redirect('dashboard')

            except model_class.DoesNotExist:
                messages.error(request, 'The requested resource does not exist.')
                return redirect('dashboard')

        wrap.__doc__ = view_func.__doc__
        wrap.__name__ = view_func.__name__
        return wrap
    return decorator

def rate_limit(max_requests, period=60):
    """
    Simple rate limiting decorator.
    """
    from django.core.cache import cache
    from django.http import HttpResponseForbidden
    import time

    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            # Create a unique key for this user and view
            if request.user.is_authenticated:
                key = f"rate_limit:{request.user.id}:{view_func.__name__}"
            else:
                ip = request.META.get('REMOTE_ADDR', '')
                key = f"rate_limit:{ip}:{view_func.__name__}"

            # Get current count
            current = cache.get(key, [])

            # Remove old timestamps
            now = time.time()
            current = [timestamp for timestamp in current if timestamp > now - period]

            # Check if limit exceeded
            if len(current) >= max_requests:
                return HttpResponseForbidden("Rate limit exceeded. Please try again later.")

            # Add current timestamp
            current.append(now)
            cache.set(key, current, period)

            return view_func(request, *args, **kwargs)

        wrap.__doc__ = view_func.__doc__
        wrap.__name__ = view_func.__name__
        return wrap
    return decorator
