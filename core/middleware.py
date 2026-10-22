# core.middleware
from django.utils import timezone
from django.contrib import messages
from .models import Notification
import threading

class UserActivityMiddleware:
    """
    Middleware to track user activity and update last seen timestamp.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last login time
            request.user.last_login = timezone.now()
            request.user.save(update_fields=['last_login'])

        response = self.get_response(request)
        return response

class NotificationMiddleware:
    """
    Middleware to add unread notifications count to request context.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            request.unread_notifications_count = unread_count
        else:
            request.unread_notifications_count = 0

        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            response.context_data['unread_notifications_count'] = getattr(
                request, 'unread_notifications_count', 0
            )
        return response

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # CSP Header (Content Security Policy)
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdnjs.cloudflare.com https://fonts.googleapis.com 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp

        return response

class RequestLoggingMiddleware:
    """
    Middleware to log requests for debugging and monitoring.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request information (in production, use proper logging)
        import logging
        logger = logging.getLogger('request')

        log_data = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

        logger.info(f"Request: {log_data}")

        response = self.get_response(request)

        # Log response information
        log_data.update({
            'status': response.status_code,
            'content_type': response.get('Content-Type', ''),
        })

        logger.info(f"Response: {log_data}")

        return response

class MaintenanceModeMiddleware:
    """
    Middleware to enable maintenance mode.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        from django.conf import settings

        if getattr(settings, 'MAINTENANCE_MODE', False):
            # Allow staff users and login page
            if (request.user.is_staff or
                request.path.startswith('/admin/') or
                request.path == '/login/'):
                return self.get_response(request)

            # Show maintenance page for others
            from django.shortcuts import render
            return render(request, 'maintenance.html', status=503)

        return self.get_response(request)
