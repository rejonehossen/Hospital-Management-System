# core.urls
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==================== Public URLs ====================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('departments/', views.departments, name='departments'),
    path('contact/', views.contact, name='contact'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),

    # ==================== Authentication URLs ====================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.patient_register, name='register'),

    # Password reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # ==================== Dashboard URLs ====================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ==================== Admin URLs ====================
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_doctors/', views.manage_doctors, name='manage_doctors'),
    path('admin_patients/', views.manage_patients, name='manage_patients'),
    path('admin_appointments/', views.manage_appointments, name='manage_appointments'),
    path('admin_billing/', views.manage_billing, name='manage_billing'),
    path('admin_reports/', views.admin_reports, name='admin_reports'),
    path('admin_settings/', views.admin_settings, name='admin_settings'),
    # Premium Additions
    path('admin_inventory/', views.premium_inventory_dashboard, name='admin_inventory'),
    path('admin_lab_reports/', views.premium_lab_reports, name='admin_lab_reports'),
    path('admin_inventory/', views.premium_inventory_dashboard, name='admin_inventory'),
    path('admin_lab_reports/', views.premium_lab_reports, name='admin_lab_reports'),
    path('admin_create_patient/', views.admin_create_patient, name='admin_create_patient'),
    path('admin_quick_book/', views.admin_quick_book, name='admin_quick_book'),
    path('admin_premium_billing/', views.admin_premium_billing, name='admin_premium_billing'),

    # ==================== Doctor URLs ====================
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('doctor/prescriptions/create/', views.create_prescription, name='create_prescription'),
    path('doctor/prescriptions/create/<int:appointment_id>/', views.create_prescription, name='create_prescription_for_appointment'),
    path('doctor/schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctor/appointments/<int:appointment_id>/update-status/',
         views.update_appointment_status, name='update_appointment_status'),

    # ==================== Patient URLs ====================
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('patient/appointments/book/', views.book_appointment, name='book_appointment'),
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/medical-records/', views.patient_medical_records, name='patient_medical_records'),
    path('patient/billing/', views.patient_billing, name='patient_billing'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),

    # ==================== Common URLs ====================
    path('profile/update/', views.update_profile, name='update_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

    # ==================== AJAX URLs ====================
    path('ajax/get-slots/', views.get_available_slots, name='get_available_slots'),
    path('ajax/check-availability/', views.check_appointment_availability, name='check_appointment_availability'),
    path('ajax/patients/<int:patient_id>/', views.get_patient_details, name='get_patient_details'),
    path('ajax/search/doctors/', views.search_doctors, name='search_doctors'),
    path('ajax/search/patients/', views.search_patients, name='search_patients'),

    # ==================== PDF URLs ====================
    path('prescriptions/<int:prescription_id>/pdf/', views.generate_prescription_pdf, name='generate_prescription_pdf'),
    path('bills/<int:bill_id>/pdf/', views.generate_bill_pdf, name='generate_bill_pdf'),
]

# Error handlers
handler404 = views.handler404
handler500 = views.handler500
handler403 = views.handler403
handler400 = views.handler400
