# core.views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum, Avg, F, Value
from django.db.models.functions import TruncDate, ExtractWeek, ExtractMonth, ExtractYear
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from datetime import datetime, date, timedelta
import json
import csv
from io import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
from decimal import Decimal
from .models import *
from .forms import *
from .decorators import *


# ==================== Public Views ====================

def home(request):
    """Home page view"""
    doctors = Doctor.objects.filter(is_available=True, is_active=True).select_related(
        'user', 'department'
    )[:8]

    departments = Department.objects.all()[:6]

    # Statistics for display
    stats = {
        'doctors': Doctor.objects.filter(is_active=True).count(),
        'patients': Patient.objects.filter(is_active=True).count(),
        'departments': Department.objects.count(),
        'experience': Doctor.objects.aggregate(total=Sum('experience'))['total'] or 0
    }

    context = {
        'doctors': doctors,
        'departments': departments,
        'stats': stats,
    }
    return render(request, 'public/index.html', context)

def about(request):
    """About page view"""
    return render(request, 'public/about.html')

def departments(request):
    """Departments listing view"""
    departments = Department.objects.annotate(
        total_doctors=Count('doctor', filter=Q(doctor__is_active=True))
    ).order_by('name')

    context = {
        'departments': departments,
    }
    return render(request, 'public/departments.html', context)

def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save contact message (in a real app, you'd save to database)
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Here you would typically send an email
            messages.success(
                request,
                f'Thank you {name}! Your message has been sent. We will contact you soon.'
            )
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
    }
    return render(request, 'public/contact.html', context)

def doctor_list(request):
    """Public doctor listing view"""
    doctors = Doctor.objects.filter(is_active=True).select_related(
        'user', 'department'
    ).order_by('user__last_name')

    # Filtering
    department_id = request.GET.get('department')
    if department_id:
        doctors = doctors.filter(department_id=department_id)

    search = request.GET.get('search')
    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialization__icontains=search) |
            Q(qualification__icontains=search)
        )

    departments_list = Department.objects.all()

    # Pagination
    paginator = Paginator(doctors, 12)
    page = request.GET.get('page')
    try:
        doctors = paginator.page(page)
    except PageNotAnInteger:
        doctors = paginator.page(1)
    except EmptyPage:
        doctors = paginator.page(paginator.num_pages)

    context = {
        'doctors': doctors,
        'departments': departments_list,
        'selected_department': department_id,
        'search_query': search,
    }
    return render(request, 'public/doctors.html', context)

def doctor_detail(request, pk):
    """Public doctor detail view"""
    doctor = get_object_or_404(
        Doctor.objects.select_related('user', 'department'),
        pk=pk,
        is_active=True
    )

    # Get doctor's upcoming available slots
    available_slots = doctor.generate_time_slots()

    # Get doctor's reviews
    reviews = DoctorRating.objects.filter(doctor=doctor).select_related('patient__user')

    context = {
        'doctor': doctor,
        'available_slots': available_slots,
        'reviews': reviews,
    }
    return render(request, 'public/doctor_detail.html', context)

# ==================== Authentication Views ====================

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')

            # Redirect based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def patient_register(request):
    """Patient registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        patient_form = PatientRegistrationForm(request.POST)

        if user_form.is_valid() and patient_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.role = 'patient'
            user.save()

            # Create patient
            patient = patient_form.save(commit=False)
            patient.user = user


            # Calculate age from date of birth
            dob_str = request.POST.get('date_of_birth')
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    patient.age = age
                    patient.save()
                except ValueError:
                    pass

            patient.save()
            # Authenticate and login
            user = authenticate(
                username=user_form.cleaned_data['username'],
                password=user_form.cleaned_data['password1']
            )
            if user:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to MediCare.')
                return redirect('patient_dashboard')
    else:
        user_form = CustomUserCreationForm()
        patient_form = PatientRegistrationForm()

    context = {
        'user_form': user_form,
        'patient_form': patient_form,
    }
    return render(request, 'auth/register.html', context)

@login_required
def dashboard(request):
    """Dashboard redirect based on user role"""
    user = request.user

    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'doctor':
        return redirect('doctor_dashboard')
    elif user.role == 'patient':
        return redirect('patient_dashboard')
    elif user.role == 'receptionist':
        return redirect('receptionist_dashboard')

    messages.warning(request, 'Unknown user role. Please contact administrator.')
    return redirect('home')

# ==================== Admin Views ====================

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard view"""
    # Basic statistics
    total_patients = Patient.objects.filter(is_active=True).count()
    total_doctors = Doctor.objects.filter(is_active=True).count()
    today = timezone.now().date()

    today_appointments = Appointment.objects.filter(
        date=today
    ).count()

    pending_appointments = Appointment.objects.filter(
        status='pending'
    ).count()

    # Revenue statistics
    revenue_data = Billing.objects.filter(
        created_at__date=today
    ).aggregate(
        total=Sum('total_amount'),
        paid=Sum('paid_amount'),
        due=Sum('due_amount')
    )

    # Recent appointments
    recent_appointments = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-date', '-time')[:10]

    # Doctors by department
    doctors_by_dept = Department.objects.annotate(
        total_doctors=Count('doctor', filter=Q(doctor__is_active=True))
    ).order_by('-total_doctors')[:5]

    # Monthly statistics
    monthly_stats = get_monthly_statistics()

    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'revenue_total': revenue_data['total'] or 0,
        'revenue_paid': revenue_data['paid'] or 0,
        'revenue_due': revenue_data['due'] or 0,
        'recent_appointments': recent_appointments,
        'doctors_by_dept': doctors_by_dept,
        'monthly_stats': monthly_stats,
    }
    return render(request, 'dashboard/admin/dashboard.html', context)

@login_required
@admin_required
def manage_doctors(request):
    """Admin: Manage doctors view"""
    doctors = Doctor.objects.select_related('user', 'department').all()

    # Filtering
    search = request.GET.get('search', '')
    department = request.GET.get('department', '')
    availability = request.GET.get('availability', '')

    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(qualification__icontains=search)
        )

    if department:
        doctors = doctors.filter(department_id=department)

    if availability:
        doctors = doctors.filter(is_available=(availability == 'available'))

    # Add doctor form
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'],
            password = form.cleaned_data['password'],


            user = User.objects.create_user(
                username=username,
                password=password,
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                role='doctor'
            )

             # Create doctor
            doctor = Doctor.objects.create(
                user=user,
                department=form.cleaned_data['department'],
                qualification=form.cleaned_data['qualification'],
                experience=form.cleaned_data.get('experience', 0),
                consultation_fee=form.cleaned_data['consultation_fee'],
                working_hours_start=form.cleaned_data['working_hours_start'],
                working_hours_end=form.cleaned_data['working_hours_end'],
                max_patients_per_day=form.cleaned_data.get('max_patients_per_day', 20),
                bio=form.cleaned_data.get('bio', '')
            )

            # Send email with credentials (in production)
            messages.success(
                request,
                f'Doctor {user.get_full_name()} created successfully! '
                f'Username: {username}, Password: {password}'
            )
            return redirect('manage_doctors')
    else:
        form = DoctorRegistrationForm()

    departments_list = Department.objects.all()

    # Pagination
    paginator = Paginator(doctors, 10)
    page = request.GET.get('page')
    try:
        doctors = paginator.page(page)
    except PageNotAnInteger:
        doctors = paginator.page(1)
    except EmptyPage:
        doctors = paginator.page(paginator.num_pages)

    context = {
        'doctors': doctors,
        'form': form,
        'departments': departments_list,
        'search_query': search,
        'department_filter': department,
        'availability_filter': availability,
    }
    return render(request, 'dashboard/admin/doctors.html', context)

@login_required
@admin_required
def manage_patients(request):
    """Admin: Manage patients view"""
    patients = Patient.objects.select_related('user').filter(is_active=True)

    # Filtering
    search = request.GET.get('search', '')
    gender = request.GET.get('gender', '')
    blood_group = request.GET.get('blood_group', '')
    age_min = request.GET.get('age_min')
    age_max = request.GET.get('age_max')
    reg_date_start = request.GET.get('reg_date_start')
    reg_date_end = request.GET.get('reg_date_end')

    if search:
        patients = patients.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__phone__icontains=search)
        )

    if gender:
        patients = patients.filter(gender=gender)

    if blood_group:
        patients = patients.filter(blood_group=blood_group)

    if age_min:
        patients = patients.filter(age__gte=age_min)

    if age_max:
        patients = patients.filter(age__lte=age_max)

    if reg_date_start:
        patients = patients.filter(registration_date__date__gte=reg_date_start)

    if reg_date_end:
        patients = patients.filter(registration_date__date__lte=reg_date_end)

    # Statistics
    stats = {
        'total': patients.count(),
        'male': patients.filter(gender='M').count(),
        'female': patients.filter(gender='F').count(),
        'avg_age': patients.aggregate(avg=Avg('age'))['avg'] or 0,
        'new_today': patients.filter(registration_date__date=timezone.now().date()).count(),
    }

    # Blood groups
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    # Pagination
    paginator = Paginator(patients, 10)
    page = request.GET.get('page')
    try:
        patients = paginator.page(page)
    except PageNotAnInteger:
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages)

    context = {
        'patients': patients,
        'stats': stats,
        'blood_groups': blood_groups,
        'search_query': search,
        'gender_filter': gender,
        'blood_group_filter': blood_group,
        'age_min_filter': age_min,
        'age_max_filter': age_max,
        'reg_date_start': reg_date_start,
        'reg_date_end': reg_date_end,
    }
    return render(request, 'dashboard/admin/patients.html', context)

@login_required
@admin_required
def manage_appointments(request):
    """Admin: Manage appointments view"""
    appointments = Appointment.objects.select_related(
        'patient__user', 'doctor__user', 'department'
    ).all()

    # Filtering
    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_id = request.GET.get('doctor', '')
    patient_id = request.GET.get('patient', '')

    if status:
        appointments = appointments.filter(status=status)

    if date_filter:
        appointments = appointments.filter(date=date_filter)

    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)

    if patient_id:
        appointments = appointments.filter(patient_id=patient_id)

    # Statistics
    stats = {
        'total': appointments.count(),
        'pending': appointments.filter(status='pending').count(),
        'confirmed': appointments.filter(status='confirmed').count(),
        'completed': appointments.filter(status='completed').count(),
        'cancelled': appointments.filter(status='cancelled').count(),
    }

    doctors = Doctor.objects.filter(is_active=True)
    patients = Patient.objects.filter(is_active=True)

    # Pagination
    paginator = Paginator(appointments, 10)
    page = request.GET.get('page')
    try:
        appointments = paginator.page(page)
    except PageNotAnInteger:
        appointments = paginator.page(1)
    except EmptyPage:
        appointments = paginator.page(paginator.num_pages)

    context = {
        'appointments': appointments,
        'stats': stats,
        'doctors': doctors,
        'patients': patients,
        'status_filter': status,
        'date_filter': date_filter,
        'doctor_filter': doctor_id,
        'patient_filter': patient_id,
    }
    return render(request, 'dashboard/admin/appointments.html', context)

@login_required
@admin_required
def manage_billing(request):
    """Admin: Manage billing view"""
    bills = Billing.objects.select_related(
        'patient__user', 'doctor__user', 'appointment'
    ).all()

    # Filtering
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    patient_id = request.GET.get('patient', '')

    if status:
        bills = bills.filter(payment_status=status)

    if date_from:
        bills = bills.filter(created_at__date__gte=date_from)

    if date_to:
        bills = bills.filter(created_at__date__lte=date_to)

    if patient_id:
        bills = bills.filter(patient_id=patient_id)

    # Statistics
    stats = {
        'total_revenue': bills.aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_paid': bills.aggregate(paid=Sum('paid_amount'))['paid'] or 0,
        'total_due': bills.aggregate(due=Sum('due_amount'))['due'] or 0,
        'pending': bills.filter(payment_status='pending').count(),
        'partial': bills.filter(payment_status='partial').count(),
        'paid': bills.filter(payment_status='paid').count(),
    }

    patients = Patient.objects.filter(is_active=True)

    # Pagination
    paginator = Paginator(bills, 10)
    page = request.GET.get('page')
    try:
        bills = paginator.page(page)
    except PageNotAnInteger:
        bills = paginator.page(1)
    except EmptyPage:
        bills = paginator.page(paginator.num_pages)

    context = {
        'bills': bills,
        'stats': stats,
        'patients': patients,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
        'patient_filter': patient_id,
    }
    return render(request, 'dashboard/admin/billing.html', context)

@login_required
@admin_required
def admin_reports(request):
    """Admin: Reports view"""
    # Date range
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).date())
    date_to = request.GET.get('date_to', timezone.now().date())

    # Appointment statistics
    appointments = Appointment.objects.filter(
        date__range=[date_from, date_to]
    )

    appointment_stats = {
        'total': appointments.count(),
        'by_status': appointments.values('status').annotate(count=Count('id')),
        'by_department': appointments.values('department__name').annotate(count=Count('id')),
        'by_doctor': appointments.values('doctor__user__first_name', 'doctor__user__last_name').annotate(count=Count('id')),
    }

    # Billing statistics
    bills = Billing.objects.filter(
        created_at__date__range=[date_from, date_to]
    )

    billing_stats = {
        'total_revenue': bills.aggregate(total=Sum('total_amount'))['total'] or 0,
        'revenue_by_day': bills.values('created_at__date').annotate(
            total=Sum('total_amount'),
            paid=Sum('paid_amount')
        ).order_by('created_at__date'),
        'by_payment_method': bills.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ),
    }

    # Patient statistics
    patients = Patient.objects.filter(
        registration_date__date__range=[date_from, date_to]
    )

    patient_stats = {
        'new_patients': patients.count(),
        'by_gender': patients.values('gender').annotate(count=Count('id')),
        'by_age_group': {
            '0-18': patients.filter(age__range=[0, 18]).count(),
            '19-35': patients.filter(age__range=[19, 35]).count(),
            '36-60': patients.filter(age__range=[36, 60]).count(),
            '61+': patients.filter(age__gte=61).count(),
        }
    }

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'appointment_stats': appointment_stats,
        'billing_stats': billing_stats,
        'patient_stats': patient_stats,
    }
    return render(request, 'dashboard/admin/reports.html', context)

@login_required
@admin_required
def admin_settings(request):
    """Admin: Settings view"""
    if request.method == 'POST':
        # Handle settings update
        for key in request.POST:
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                value = request.POST[key]

                setting, created = HospitalSetting.objects.get_or_create(
                    key=setting_key,
                    defaults={'value': value}
                )

                if not created:
                    setting.value = value
                    setting.save()

        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_settings')

    # Get current settings
    settings = {
        'hospital_name': HospitalSetting.objects.filter(key='hospital_name').first(),
        'hospital_address': HospitalSetting.objects.filter(key='hospital_address').first(),
        'hospital_phone': HospitalSetting.objects.filter(key='hospital_phone').first(),
        'hospital_email': HospitalSetting.objects.filter(key='hospital_email').first(),
        'consultation_fee_default': HospitalSetting.objects.filter(key='consultation_fee_default').first(),
        'tax_rate': HospitalSetting.objects.filter(key='tax_rate').first(),
        'appointment_reminder_hours': HospitalSetting.objects.filter(key='appointment_reminder_hours').first(),
        'max_appointments_per_day': HospitalSetting.objects.filter(key='max_appointments_per_day').first(),
    }

    context = {
        'settings': settings,
    }
    return render(request, 'dashboard/admin/settings.html', context)

# ==================== Doctor Views ====================

@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard view"""
    doctor = request.user.doctor_profile
    today = timezone.now().date()

    # Statistics
    total_appointments = Appointment.objects.filter(doctor=doctor).count()
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        date=today
    ).count()

    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).count()

    total_patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct().count()

    # Today's schedule
    todays_schedule = Appointment.objects.filter(
        doctor=doctor,
        date=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient__user').order_by('time')

    # Recent patients
    recent_patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct().select_related('user').order_by('-last_visit')[:5]

    # Upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient__user').order_by('date', 'time')[:5]

    context = {
        'doctor': doctor,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_patients': total_patients,
        'todays_schedule': todays_schedule,
        'recent_patients': recent_patients,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'dashboard/doctor/dashboard.html', context)

@login_required
@doctor_required
def doctor_appointments(request):
    """Doctor: My appointments view"""
    doctor = request.user.doctor_profile
    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related('patient__user').order_by('-date', '-time')

    # Filtering
    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    patient_search = request.GET.get('patient', '')

    if status:
        appointments = appointments.filter(status=status)

    if date_filter:
        appointments = appointments.filter(date=date_filter)

    if patient_search:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=patient_search) |
            Q(patient__user__last_name__icontains=patient_search)
        )

    # Statistics
    stats = {
        'total': appointments.count(),
        'pending': appointments.filter(status='pending').count(),
        'confirmed': appointments.filter(status='confirmed').count(),
        'completed': appointments.filter(status='completed').count(),
    }

    # Pagination
    paginator = Paginator(appointments, 10)
    page = request.GET.get('page')
    try:
        appointments = paginator.page(page)
    except PageNotAnInteger:
        appointments = paginator.page(1)
    except EmptyPage:
        appointments = paginator.page(paginator.num_pages)

    context = {
        'appointments': appointments,
        'stats': stats,
        'status_filter': status,
        'date_filter': date_filter,
        'patient_search': patient_search,
    }
    return render(request, 'dashboard/doctor/appointments.html', context)

@login_required
@doctor_required
def doctor_patients(request):
    """Doctor: My patients view"""
    doctor = request.user.doctor_profile
    patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct().select_related('user')

    # Filtering
    search = request.GET.get('search', '')
    if search:
        patients = patients.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )

    # Statistics
    stats = {
        'total': patients.count(),
        'male': patients.filter(gender='M').count(),
        'female': patients.filter(gender='F').count(),
        'avg_age': patients.aggregate(avg=Avg('age'))['avg'] or 0,
    }

    # Pagination
    paginator = Paginator(patients, 10)
    page = request.GET.get('page')
    try:
        patients = paginator.page(page)
    except PageNotAnInteger:
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages)

    context = {
        'patients': patients,
        'stats': stats,
        'search_query': search,
    }
    return render(request, 'dashboard/doctor/patients.html', context)

@login_required
@doctor_required
def doctor_prescriptions(request):
    """Doctor: My prescriptions view"""
    doctor = request.user.doctor_profile
    prescriptions = Prescription.objects.filter(
        doctor=doctor
    ).select_related('patient__user', 'appointment')

    # Filtering
    search = request.GET.get('search', '')
    patient_id = request.GET.get('patient', '')
    active_only = request.GET.get('active', 'false') == 'true'

    if search:
        prescriptions = prescriptions.filter(
            Q(medicine_name__icontains=search) |
            Q(patient__user__first_name__icontains=search) |
            Q(patient__user__last_name__icontains=search)
        )

    if patient_id:
        prescriptions = prescriptions.filter(patient_id=patient_id)

    if active_only:
        prescriptions = prescriptions.filter(is_active=True)

    patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct()

    # Statistics
    stats = {
        'total': prescriptions.count(),
        'active': prescriptions.filter(is_active=True).count(),
        'refillable': prescriptions.filter(refill_count__lt=F('max_refills')).count(),
    }

    # Pagination
    paginator = Paginator(prescriptions, 10)
    page = request.GET.get('page')
    try:
        prescriptions = paginator.page(page)
    except PageNotAnInteger:
        prescriptions = paginator.page(1)
    except EmptyPage:
        prescriptions = paginator.page(paginator.num_pages)

    context = {
        'prescriptions': prescriptions,
        'patients': patients,
        'stats': stats,
        'search_query': search,
        'patient_filter': patient_id,
        'active_only': active_only,
    }
    return render(request, 'dashboard/doctor/prescriptions.html', context)

@login_required
@doctor_required
def create_prescription(request, appointment_id=None):
    """Doctor: Create prescription view"""
    doctor = request.user.doctor_profile

    if appointment_id:
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=doctor
        )
        patient = appointment.patient
    else:
        appointment = None
        patient = None

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = doctor

            if appointment:
                prescription.appointment = appointment
                prescription.patient = appointment.patient
            else:
                # Get patient from form or request
                patient_id = request.POST.get('patient')
                if patient_id:
                    prescription.patient = get_object_or_404(Patient, id=patient_id)
                else:
                    messages.error(request, 'Please select a patient.')
                    return redirect('create_prescription')

            prescription.save()

            # Create notification for patient
            Notification.objects.create(
                user=prescription.patient.user,
                notification_type='prescription',
                title='New Prescription',
                message=f'Dr. {doctor.user.get_full_name()} has prescribed {prescription.medicine_name}',
                related_object_id=prescription.id,
                related_object_type='prescription'
            )

            messages.success(request, 'Prescription created successfully!')

            if appointment:
                return redirect('doctor_appointments')
            else:
                return redirect('doctor_prescriptions')
    else:
        form = PrescriptionForm()

    # Get doctor's recent patients
    recent_patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct().select_related('user')[:10]

    context = {
        'form': form,
        'appointment': appointment,
        'patient': patient,
        'recent_patients': recent_patients,
    }
    return render(request, 'dashboard/doctor/create_prescription.html', context)

@login_required
@doctor_required
def update_appointment_status(request, appointment_id):
    """Doctor: Update appointment status"""
    doctor = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.notes = notes
            appointment.save()

            # Create notification
            Notification.objects.create(
                user=appointment.patient.user,
                notification_type='appointment',
                title=f'Appointment {new_status.title()}',
                message=f'Your appointment with Dr. {doctor.user.get_full_name()} has been {new_status}',
                related_object_id=appointment.id,
                related_object_type='appointment'
            )

            messages.success(request, f'Appointment status updated to {new_status}.')

    return redirect('doctor_appointments')

@login_required
@doctor_required
def doctor_schedule(request):
    """Doctor: Schedule view"""
    doctor = request.user.doctor_profile

    # Get date range (default: current week)
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today - timedelta(days=today.weekday()))
    end_date = request.GET.get('end_date', start_date + timedelta(days=6))

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Get appointments in date range
    appointments = Appointment.objects.filter(
        doctor=doctor,
        date__range=[start_date, end_date]
    ).select_related('patient__user').order_by('date', 'time')

    # Group by date
    schedule_by_date = {}
    current_date = start_date
    while current_date <= end_date:
        schedule_by_date[current_date] = appointments.filter(date=current_date)
        current_date += timedelta(days=1)

    # Get available time slots
    available_slots = doctor.generate_time_slots()

    context = {
        'doctor': doctor,
        'start_date': start_date,
        'end_date': end_date,
        'schedule_by_date': schedule_by_date,
        'available_slots': available_slots,
        'today': today,
    }
    return render(request, 'dashboard/doctor/schedule.html', context)

@login_required
@doctor_required
def doctor_profile(request):
    """Doctor: Profile view"""
    doctor = request.user.doctor_profile

    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        doctor_form = DoctorUpdateForm(request.POST, instance=doctor)

        if user_form.is_valid() and doctor_form.is_valid():
            user_form.save()
            doctor_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('doctor_profile')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        doctor_form = DoctorUpdateForm(instance=doctor)

    # Statistics for profile
    stats = {
        'total_appointments': Appointment.objects.filter(doctor=doctor).count(),
        'total_patients': Patient.objects.filter(appointment__doctor=doctor).distinct().count(),
        'average_rating': doctor.average_rating,
        'completion_rate': Appointment.objects.filter(
            doctor=doctor,
            status='completed'
        ).count() / max(Appointment.objects.filter(doctor=doctor).count(), 1) * 100,
    }

    context = {
        'user_form': user_form,
        'doctor_form': doctor_form,
        'doctor': doctor,
        'stats': stats,
    }
    return render(request, 'dashboard/doctor/profile.html', context)

# ==================== Patient Views ====================

@login_required
@patient_required
def patient_dashboard(request):
    """Patient dashboard view"""
    patient = request.user.patient_profile

    # Update last visit
    patient.last_visit = timezone.now()
    patient.save()

    # Statistics
    total_appointments = patient.appointment_set.count()
    upcoming_appointments = patient.appointment_set.filter(
        date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).count()

    prescriptions_count = patient.prescription_set.count()
    active_prescriptions = patient.prescription_set.filter(is_active=True).count()

    # Upcoming appointments
    upcoming = patient.appointment_set.filter(
        date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).select_related('doctor__user').order_by('date', 'time')[:5]

    # Recent prescriptions
    recent_prescriptions = patient.prescription_set.select_related(
        'doctor__user'
    ).order_by('-created_at')[:5]

    # Medical records
    recent_records = patient.medical_records.order_by('-created_at')[:5]

    # Notifications
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]

    context = {
        'patient': patient,
        'total_appointments': total_appointments,
        'upcoming_appointments': upcoming_appointments,
        'prescriptions_count': prescriptions_count,
        'active_prescriptions': active_prescriptions,
        'upcoming': upcoming,
        'recent_prescriptions': recent_prescriptions,
        'recent_records': recent_records,
        'notifications': notifications,
    }
    return render(request, 'dashboard/patient/dashboard.html', context)

@login_required
@patient_required
def patient_appointments(request):
    """Patient: My appointments view"""
    patient = request.user.patient_profile
    appointments = patient.appointment_set.select_related(
        'doctor__user', 'department'
    ).order_by('-date', '-time')

    # Filtering
    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_id = request.GET.get('doctor', '')

    if status:
        appointments = appointments.filter(status=status)

    if date_filter:
        appointments = appointments.filter(date=date_filter)

    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)

    # Statistics
    stats = {
        'total': appointments.count(),
        'upcoming': appointments.filter(
            date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count(),
        'completed': appointments.filter(status='completed').count(),
        'cancelled': appointments.filter(status='cancelled').count(),
    }

    # Get doctors the patient has visited
    doctors = Doctor.objects.filter(
        appointment__patient=patient
    ).distinct().select_related('user')

    # Pagination
    paginator = Paginator(appointments, 10)
    page = request.GET.get('page')
    try:
        appointments = paginator.page(page)
    except PageNotAnInteger:
        appointments = paginator.page(1)
    except EmptyPage:
        appointments = paginator.page(paginator.num_pages)

    context = {
        'appointments': appointments,
        'stats': stats,
        'doctors': doctors,
        'status_filter': status,
        'date_filter': date_filter,
        'doctor_filter': doctor_id,
    }
    return render(request, 'dashboard/patient/appointments.html', context)

@login_required
@patient_required
def book_appointment(request):
    """Patient: Book appointment view"""
    patient = request.user.patient_profile

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.save()

            messages.success(request, 'Appointment booked successfully!')
            return redirect('patient_appointments')
    else:
        form = AppointmentForm()

    # Get available doctors
    doctors = Doctor.objects.filter(is_available=True, is_active=True).select_related(
        'user', 'department'
    )

    # Get patient's recent doctors
    recent_doctors = Doctor.objects.filter(
        appointment__patient=patient
    ).distinct().select_related('user')[:5]

    context = {
        'form': form,
        'doctors': doctors,
        'recent_doctors': recent_doctors,
    }
    return render(request, 'dashboard/patient/book_appointment.html', context)

@login_required
@patient_required
def patient_prescriptions(request):
    """Patient: My prescriptions view"""
    patient = request.user.patient_profile
    prescriptions = patient.prescription_set.select_related(
        'doctor__user', 'appointment'
    ).order_by('-created_at')

    # Filtering
    search = request.GET.get('search', '')
    active_only = request.GET.get('active', 'false') == 'true'

    if search:
        prescriptions = prescriptions.filter(
            Q(medicine_name__icontains=search) |
            Q(doctor__user__first_name__icontains=search) |
            Q(doctor__user__last_name__icontains=search)
        )

    if active_only:
        prescriptions = prescriptions.filter(is_active=True)

    # Statistics
    stats = {
        'total': prescriptions.count(),
        'active': prescriptions.filter(is_active=True).count(),
        'refillable': prescriptions.filter(refill_count__lt=F('max_refills')).count(),
    }

    # Pagination
    paginator = Paginator(prescriptions, 10)
    page = request.GET.get('page')
    try:
        prescriptions = paginator.page(page)
    except PageNotAnInteger:
        prescriptions = paginator.page(1)
    except EmptyPage:
        prescriptions = paginator.page(paginator.num_pages)

    context = {
        'prescriptions': prescriptions,
        'stats': stats,
        'search_query': search,
        'active_only': active_only,
    }
    return render(request, 'dashboard/patient/prescriptions.html', context)

@login_required
@patient_required
def patient_medical_records(request):
    """Patient: Medical records view"""
    patient = request.user.patient_profile
    records = patient.medical_records.select_related('doctor__user').order_by('-created_at')

    # Filtering
    record_type = request.GET.get('type', '')
    doctor_id = request.GET.get('doctor', '')

    if record_type:
        records = records.filter(record_type=record_type)

    if doctor_id:
        records = records.filter(doctor_id=doctor_id)

    # Get record type choices
    record_types = MedicalRecord.RECORD_TYPE_CHOICES

    # Get doctors who created records
    doctors = Doctor.objects.filter(
        medicalrecord__patient=patient
    ).distinct().select_related('user')

    # Pagination
    paginator = Paginator(records, 10)
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    context = {
        'records': records,
        'record_types': record_types,
        'doctors': doctors,
        'type_filter': record_type,
        'doctor_filter': doctor_id,
    }
    return render(request, 'dashboard/patient/medical_records.html', context)

@login_required
@patient_required
def patient_billing(request):
    """Patient: Billing view"""
    patient = request.user.patient_profile
    bills = patient.billing_set.select_related('doctor__user', 'appointment').order_by('-created_at')

    # Filtering
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if status:
        bills = bills.filter(payment_status=status)

    if date_from:
        bills = bills.filter(created_at__date__gte=date_from)

    if date_to:
        bills = bills.filter(created_at__date__lte=date_to)

    # Statistics
    stats = {
        'total_bills': bills.count(),
        'total_amount': bills.aggregate(total=Sum('total_amount'))['total'] or 0,
        'paid_amount': bills.aggregate(paid=Sum('paid_amount'))['paid'] or 0,
        'due_amount': bills.aggregate(due=Sum('due_amount'))['due'] or 0,
        'pending': bills.filter(payment_status='pending').count(),
        'partial': bills.filter(payment_status='partial').count(),
        'paid': bills.filter(payment_status='paid').count(),
    }

    # Pagination
    paginator = Paginator(bills, 10)
    page = request.GET.get('page')
    try:
        bills = paginator.page(page)
    except PageNotAnInteger:
        bills = paginator.page(1)
    except EmptyPage:
        bills = paginator.page(paginator.num_pages)

    context = {
        'bills': bills,
        'stats': stats,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'dashboard/patient/billing.html', context)

@login_required
@patient_required
def patient_profile(request):
    """Patient: Profile view"""
    patient = request.user.patient_profile

    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        patient_form = PatientUpdateForm(request.POST, instance=patient)

        if user_form.is_valid() and patient_form.is_valid():
            user_form.save()
            patient_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('patient_profile')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        patient_form = PatientUpdateForm(instance=patient)

    # Health statistics
    health_stats = {
        'bmi': patient.bmi,
        'appointments': patient.appointment_set.count(),
        'prescriptions': patient.prescription_set.count(),
        'medical_records': patient.medical_records.count(),
    }

    context = {
        'user_form': user_form,
        'patient_form': patient_form,
        'patient': patient,
        'health_stats': health_stats,
    }
    return render(request, 'dashboard/patient/profile.html', context)

# ==================== Common Views ====================

@login_required
def update_profile(request):
    """Update user profile (common)"""
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()

        messages.success(request, 'Profile updated successfully!')

    # Redirect back based on role
    if user.role == 'patient':
        return redirect('patient_profile')
    elif user.role == 'doctor':
        return redirect('doctor_profile')
    else:
        return redirect('dashboard')

@login_required
def notifications(request):
    """User notifications view"""
    notifications = request.user.notifications.order_by('-created_at')

    # Mark as read if requested
    if request.GET.get('mark_read') == 'all':
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')

    # Pagination
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        notifications = paginator.page(paginator.num_pages)

    context = {
        'notifications': notifications,
    }
    return render(request, 'common/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()

    return JsonResponse({'success': True})

# ==================== AJAX Views ====================

@login_required
def get_available_slots(request):
    """Get available time slots for a doctor on a specific date"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Get booked slots for the day
        booked_slots = Appointment.objects.filter(
            doctor=doctor,
            date=date_obj,
            status__in=['pending', 'confirmed', 'in_progress']
        ).values_list('time', flat=True)

        # Generate all slots based on doctor's working hours
        all_slots = doctor.generate_time_slots()

        # Filter out booked slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]

        return JsonResponse({'slots': available_slots})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def check_appointment_availability(request):
    """Check if a specific time slot is available"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')

    if not all([doctor_id, date_str, time_str]):
        return JsonResponse({'available': False, 'error': 'Missing parameters'})

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Check for conflicts
        conflicting = Appointment.objects.filter(
            doctor=doctor,
            date=date_obj,
            time=time_obj,
            status__in=['pending', 'confirmed', 'in_progress']
        ).exists()

        # Check if within working hours
        within_hours = doctor.working_hours_start <= time_obj <= doctor.working_hours_end

        # Check if doctor has reached max patients
        daily_count = Appointment.objects.filter(
            doctor=doctor,
            date=date_obj
        ).count()
        max_reached = daily_count >= doctor.max_patients_per_day

        available = not conflicting and within_hours and not max_reached

        return JsonResponse({
            'available': available,
            'conflicting': conflicting,
            'within_hours': within_hours,
            'max_reached': max_reached,
            'daily_count': daily_count,
            'max_patients': doctor.max_patients_per_day,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_patient_details(request, patient_id):
    """Get patient details for doctor's view"""
    patient = get_object_or_404(
        Patient.objects.select_related('user'),
        id=patient_id
    )

    # Check if doctor has access to this patient
    if request.user.role == 'doctor':
        has_access = Appointment.objects.filter(
            doctor=request.user.doctor_profile,
            patient=patient
        ).exists()
        if not has_access:
            return JsonResponse({'error': 'Access denied'}, status=403)

    # Get patient data
    data = {
        'id': patient.id,
        'name': patient.user.get_full_name(),
        'age': patient.age,
        'gender': patient.get_gender_display(),
        'blood_group': patient.blood_group or 'Not specified',
        'height': str(patient.height) if patient.height else 'Not specified',
        'weight': str(patient.weight) if patient.weight else 'Not specified',
        'bmi': patient.bmi,
        'allergies': patient.allergies or 'None reported',
        'medical_history': patient.medical_history or 'None reported',
        'current_medications': patient.current_medications or 'None',
        'emergency_contact': patient.emergency_contact or 'Not specified',
        'email': patient.user.email,
        'phone': patient.user.phone,
    }

    return JsonResponse(data)

@login_required
def search_doctors(request):
    """Search doctors by name or specialization"""
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'doctors': []})

    doctors = Doctor.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(specialization__icontains=query) |
        Q(qualification__icontains=query),
        is_active=True,
        is_available=True
    ).select_related('user', 'department')[:10]

    results = []
    for doctor in doctors:
        results.append({
            'id': doctor.id,
            'name': f"Dr. {doctor.user.get_full_name()}",
            'specialization': doctor.specialization or doctor.qualification,
            'department': doctor.department.name if doctor.department else 'General',
            'fee': str(doctor.consultation_fee),
            'rating': doctor.average_rating,
        })

    return JsonResponse({'doctors': results})

@login_required
def search_patients(request):
    """Search patients by name (for doctors and admin)"""
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'patients': []})

    # Permission check
    if request.user.role == 'doctor':
        # Doctors can only see their patients
        doctor = request.user.doctor_profile
        patients = Patient.objects.filter(
            appointment__doctor=doctor,
            user__first_name__icontains=query
        ).distinct().select_related('user')[:10]
    elif request.user.role == 'admin':
        # Admin can see all patients
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query),
            is_active=True
        ).select_related('user')[:10]
    else:
        return JsonResponse({'patients': []})

    results = []
    for patient in patients:
        results.append({
            'id': patient.id,
            'name': patient.user.get_full_name(),
            'age': patient.age,
            'gender': patient.get_gender_display(),
            'email': patient.user.email,
            'phone': patient.user.phone,
        })

    return JsonResponse({'patients': results})

# ==================== PDF Generation Views ====================

@login_required
def generate_prescription_pdf(request, prescription_id):
    """Generate PDF for prescription"""
    prescription = get_object_or_404(
        Prescription.objects.select_related('patient__user', 'doctor__user'),
        id=prescription_id
    )

    # Permission check
    if request.user.role == 'patient' and prescription.patient.user != request.user:
        raise PermissionDenied
    elif request.user.role == 'doctor' and prescription.doctor.user != request.user:
        raise PermissionDenied

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Content
    content = []

    # Header
    header_style = styles['Heading1']
    header_style.alignment = 1  # Center
    content.append(Paragraph("MEDICARE HOSPITAL", header_style))
    content.append(Paragraph("123 Healthcare Street, Medical District", styles['Normal']))
    content.append(Paragraph("Phone: +1 (555) 123-4567 | Email: info@medicare.com", styles['Normal']))
    content.append(Spacer(1, 20))

    # Title
    title_style = styles['Heading2']
    title_style.alignment = 1
    content.append(Paragraph("MEDICAL PRESCRIPTION", title_style))
    content.append(Spacer(1, 20))

    # Patient Info
    content.append(Paragraph("<b>Patient Information:</b>", styles['Normal']))
    patient_info = [
        f"Name: {prescription.patient.user.get_full_name()}",
        f"Age: {prescription.patient.age} years",
        f"Gender: {prescription.patient.get_gender_display()}",
        f"Date: {prescription.created_at.strftime('%B %d, %Y')}"
    ]
    for info in patient_info:
        content.append(Paragraph(info, styles['Normal']))

    content.append(Spacer(1, 20))

    # Doctor Info
    content.append(Paragraph("<b>Prescribing Doctor:</b>", styles['Normal']))
    doctor_info = [
        f"Name: Dr. {prescription.doctor.user.get_full_name()}",
        f"Qualification: {prescription.doctor.qualification}",
        f"Department: {prescription.doctor.department.name if prescription.doctor.department else 'General'}"
    ]
    for info in doctor_info:
        content.append(Paragraph(info, styles['Normal']))

    content.append(Spacer(1, 20))

    # Prescription Details
    content.append(Paragraph("<b>Prescription Details:</b>", styles['Heading3']))

    prescription_data = [
        ['Medicine', 'Dosage', 'Frequency', 'Duration', 'Quantity'],
        [
            prescription.medicine_name,
            prescription.dosage,
            prescription.frequency,
            prescription.duration,
            prescription.quantity
        ]
    ]

    table = Table(prescription_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(table)

    content.append(Spacer(1, 20))

    # Instructions and Advice
    if prescription.instructions:
        content.append(Paragraph("<b>Instructions:</b>", styles['Normal']))
        content.append(Paragraph(prescription.instructions, styles['Normal']))
        content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Doctor's Advice:</b>", styles['Normal']))
    content.append(Paragraph(prescription.advice, styles['Normal']))

    content.append(Spacer(1, 30))

    # Signature
    signature = f"Signature: _________________________<br/>Dr. {prescription.doctor.user.get_full_name()}<br/>{prescription.doctor.qualification}"
    content.append(Paragraph(signature, styles['Normal']))

    # Build PDF
    doc.build(content)

    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()

    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    response.write(pdf)

    return response

@login_required
def generate_bill_pdf(request, bill_id):
    """Generate PDF for bill"""
    bill = get_object_or_404(
        Billing.objects.select_related('patient__user', 'doctor__user', 'appointment'),
        id=bill_id
    )

    # Permission check
    if request.user.role == 'patient' and bill.patient.user != request.user:
        raise PermissionDenied

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Content
    content = []

    # Header
    header_style = styles['Heading1']
    header_style.alignment = 1
    content.append(Paragraph("MEDICARE HOSPITAL", header_style))
    content.append(Paragraph("INVOICE", styles['Heading2']))
    content.append(Spacer(1, 20))

    # Bill Info
    bill_info_data = [
        ['Bill Number:', bill.bill_number],
        ['Date:', bill.created_at.strftime('%B %d, %Y')],
        ['Due Date:', bill.due_date.strftime('%B %d, %Y')],
        ['Payment Status:', bill.get_payment_status_display()],
    ]

    bill_info_table = Table(bill_info_data, colWidths=[150, 200])
    bill_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    content.append(bill_info_table)

    content.append(Spacer(1, 20))

    # Patient Info
    content.append(Paragraph("<b>Billed To:</b>", styles['Normal']))
    patient_info = [
        f"Name: {bill.patient.user.get_full_name()}",
        f"Email: {bill.patient.user.email}",
        f"Phone: {bill.patient.user.phone}"
    ]
    for info in patient_info:
        content.append(Paragraph(info, styles['Normal']))

    content.append(Spacer(1, 20))

    # Bill Details
    content.append(Paragraph("<b>Bill Details:</b>", styles['Heading3']))

    if bill.appointment:
        content.append(Paragraph(f"Appointment: {bill.appointment.date} at {bill.appointment.time}", styles['Normal']))
        content.append(Paragraph(f"Doctor: Dr. {bill.appointment.doctor.user.get_full_name()}", styles['Normal']))

    content.append(Spacer(1, 10))

    # Charges Table
    charges_data = [
        ['Description', 'Amount ($)'],
        ['Consultation Fee', f"{bill.consultation_fee:.2f}"],
        ['Medicine Charges', f"{bill.medicine_charges:.2f}"],
        ['Test Charges', f"{bill.test_charges:.2f}"],
        ['Other Charges', f"{bill.other_charges:.2f}"],
        ['Subtotal', f"{bill.consultation_fee + bill.medicine_charges + bill.test_charges + bill.other_charges:.2f}"],
        ['Tax', f"{bill.tax_amount:.2f}"],
        ['Discount', f"-{bill.discount:.2f}"],
        ['Insurance Coverage', f"-{bill.insurance_coverage:.2f}"],
        ['Total Amount', f"<b>{bill.total_amount:.2f}</b>"],
        ['Paid Amount', f"{bill.paid_amount:.2f}"],
        ['Due Amount', f"<b>{bill.due_amount:.2f}</b>"],
    ]

    charges_table = Table(charges_data, colWidths=[300, 100])
    charges_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(charges_table)

    content.append(Spacer(1, 30))

    # Payment Info
    if bill.payment_method:
        content.append(Paragraph(f"Payment Method: {bill.get_payment_method_display()}", styles['Normal']))

    if bill.notes:
        content.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        content.append(Paragraph(bill.notes, styles['Normal']))

    content.append(Spacer(1, 20))

    # Footer
    footer = "Thank you for choosing MediCare Hospital.<br/>Please contact billing department for any queries."
    content.append(Paragraph(footer, styles['Normal']))

    # Build PDF
    doc.build(content)

    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()

    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{bill.bill_number}.pdf"'
    response.write(pdf)

    return response

# ==================== Utility Functions ====================

def get_monthly_statistics():
    """Get monthly statistics for dashboard"""
    today = timezone.now()
    start_of_month = today.replace(day=1)

    # Monthly appointments
    monthly_appointments = Appointment.objects.filter(
        date__gte=start_of_month
    ).count()

    # Monthly revenue
    monthly_revenue = Billing.objects.filter(
        created_at__gte=start_of_month
    ).aggregate(
        total=Sum('total_amount'),
        paid=Sum('paid_amount')
    )

    # Monthly new patients
    monthly_patients = Patient.objects.filter(
        registration_date__gte=start_of_month
    ).count()

    return {
        'appointments': monthly_appointments,
        'revenue_total': monthly_revenue['total'] or 0,
        'revenue_paid': monthly_revenue['paid'] or 0,
        'new_patients': monthly_patients,
    }

def send_appointment_reminders():
    """Send appointment reminders (to be called by cron job)"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        date=tomorrow,
        reminder_sent=False,
        status__in=['pending', 'confirmed']
    ).select_related('patient__user', 'doctor__user')

    for appointment in appointments:
        # Create notification
        Notification.objects.create(
            user=appointment.patient.user,
            notification_type='reminder',
            title='Appointment Reminder',
            message=f'Reminder: Your appointment with Dr. {appointment.doctor.user.get_full_name()} is tomorrow at {appointment.time}',
            related_object_id=appointment.id,
            related_object_type='appointment'
        )

        # Mark as sent
        appointment.reminder_sent = True
        appointment.save()

    return len(appointments)

# ==================== Error Handlers ====================

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)














@login_required
@admin_required
def premium_inventory_dashboard(request):
    """Admin view for Inventory Management"""
    from .premium_models import InventoryItem
    items = InventoryItem.objects.all().order_by('quantity')
    low_stock = items.filter(quantity__lte=models.F('reorder_level'))

    context = {
        'items': items,
        'low_stock_count': low_stock.count(),
        'total_value': sum(item.quantity * item.unit_price for item in items),
    }
    return render(request, 'dashboard/admin/inventory.html', context)

@login_required
@admin_required
def premium_lab_reports(request):
    """Admin view for Lab Test Reports"""
    from .premium_models import LabTest
    tests = LabTest.objects.select_related('patient__user', 'doctor__user').all().order_by('-test_date')

    context = {
        'tests': tests,
        'pending_tests': tests.filter(status__in=['requested', 'processing']).count(),
    }
    return render(request, 'dashboard/admin/lab_reports.html', context)








from django.contrib.auth.hashers import make_password
from .premium_models import InventoryItem, LabTest
from .forms import AdminPatientCreateForm, AdminAppointmentForm, AdminLabTestForm

# ==================== PREMIUM ADMIN RECEPTIONIST VIEWS ====================

@login_required
@admin_required
def premium_lab_reports(request):
    """Admin view for Lab Test Reports & Creation"""
    if request.method == 'POST':
        form = AdminLabTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lab Test booked successfully!')
            return redirect('premium_lab_reports')
    else:
        form = AdminLabTestForm()

    tests = LabTest.objects.select_related('patient__user', 'doctor__user').all().order_by('-test_date')
    context = {
        'tests': tests,
        'form': form,
        'pending_tests': tests.filter(status__in=['requested', 'processing']).count(),
    }
    return render(request, 'dashboard/admin/lab_reports.html', context)

@login_required
@admin_required
def premium_inventory_dashboard(request):
    """Admin view for Inventory Management"""
    items = InventoryItem.objects.all().order_by('quantity')
    low_stock = items.filter(quantity__lte=models.F('reorder_level'))
    context = {
        'items': items,
        'low_stock_count': low_stock.count(),
        'total_value': sum(item.quantity * item.unit_price for item in items),
    }
    return render(request, 'dashboard/admin/inventory.html', context)

@login_required
@admin_required
def admin_create_patient(request):
    """Admin creates a walk-in patient instantly"""
    if request.method == 'POST':
        form = AdminPatientCreateForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            # Create User Account
            user = User.objects.create(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                role='patient',
                is_verified=True
            )
            # Assign to patient
            patient.user = user
            patient.save()
            messages.success(request, f'Walk-in patient {user.get_full_name()} registered!')
            return redirect('admin_create_patient') # Or redirect to book appointment
    else:
        form = AdminPatientCreateForm()
    return render(request, 'dashboard/admin/create_patient.html', {'form': form})

@login_required
@admin_required
def admin_quick_book(request):
    """Admin books an appointment for a walk-in patient"""
    if request.method == 'POST':
        form = AdminAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)

            # Safe extraction of discount
            discount_str = request.POST.get('discount_amount', '0.00')
            try:
                discount = Decimal(discount_str)
            except (ValueError, TypeError):
                discount = Decimal('0.00')

            appointment.save()

            # Auto-create a bill with this discount
            # This requires importing Billing and creating a record here,
            # but for now, let the appointment save.

            messages.success(request, 'Appointment booked successfully!')
            return redirect('admin_quick_book')
    else:
        form = AdminAppointmentForm()

    return render(request, 'dashboard/admin/quick_book.html', {'form': form})

@login_required
@admin_required
def admin_premium_billing(request):
    """Admin handles payments and applies discounts"""
    bills = Billing.objects.all().order_by('-created_at')

    if request.method == 'POST':
        bill_id = request.POST.get('bill_id')

        try:
            discount = Decimal(request.POST.get('discount_amount', 0))
            paid = Decimal(request.POST.get('paid_amount', 0))
        except (ValueError, TypeError):
            messages.error(request, "Invalid number format.")
            return redirect('admin_premium_billing')

        bill = get_object_or_404(Billing, id=bill_id)

        # Apply the new values
        bill.discount = discount
        bill.paid_amount = paid

        # Recalculate total_amount based on subtotal minus discount
        subtotal = bill.consultation_fee + bill.medicine_charges + bill.test_charges + bill.other_charges + bill.tax_amount
        bill.total_amount = subtotal - discount

        # The bill.save() method automatically calculates `due_amount` and `payment_status`!
        bill.save()

        messages.success(request, 'Bill updated and discount applied!')
        return redirect('admin_premium_billing')

    context = {'bills': bills}
    return render(request, 'dashboard/admin/premium_billing.html', context)
