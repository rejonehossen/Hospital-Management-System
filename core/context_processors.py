# core.context_processor
from django.conf import settings
from .models import Notification, HospitalSetting

def site_settings(request):
    """Add site settings to template context."""
    context = {
        'hospital_name': getattr(settings, 'HOSPITAL_NAME', 'MediCare Hospital'),
        'hospital_address': getattr(settings, 'HOSPITAL_ADDRESS', ''),
        'hospital_phone': getattr(settings, 'HOSPITAL_PHONE', ''),
        'hospital_email': getattr(settings, 'HOSPITAL_EMAIL', ''),
        'debug': settings.DEBUG,
    }

    # Add settings from database
    try:
        db_settings = HospitalSetting.objects.filter(is_active=True)
        for setting in db_settings:
            context[f'setting_{setting.key}'] = setting.value
    except:
        pass

    return context

def user_notifications(request):
    """Add user notifications to template context."""
    context = {}

    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        context['unread_notifications_count'] = unread_count

        # Recent notifications
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        context['recent_notifications'] = recent_notifications

    return context

def user_role_context(request):
    """Add user role information to template context."""
    context = {}

    if request.user.is_authenticated:
        context['user_role'] = request.user.role
        context['is_admin'] = request.user.role == 'admin'
        context['is_doctor'] = request.user.role == 'doctor'
        context['is_patient'] = request.user.role == 'patient'
        context['is_receptionist'] = request.user.role == 'receptionist'
        context['is_staff_user'] = request.user.role in ['admin', 'doctor', 'receptionist']

    return context
