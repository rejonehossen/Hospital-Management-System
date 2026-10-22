# core.admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture', 'date_of_birth')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'qualification', 'consultation_fee', 'is_available', 'is_active')
    list_filter = ('department', 'is_available', 'is_active', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'qualification', 'specialization')
    # raw_id_fields = ('user',)
    list_editable = ('is_available', 'is_active')



    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                role='doctor',
                doctor_profile__isnull=True
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    fieldsets = (
        ('Personal Info', {'fields': ('user', 'department')}),
        ('Professional Info', {'fields': ('qualification', 'specialization', 'experience', 'license_number')}),
        ('Fees & Availability', {'fields': ('consultation_fee', 'is_available', 'is_active')}),
        ('Schedule', {'fields': ('working_hours_start', 'working_hours_end', 'max_patients_per_day')}),
        ('Bio', {'fields': ('bio',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'blood_group', 'registration_date', 'is_active')
    list_filter = ('gender', 'blood_group', 'is_active', 'registration_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__phone')
    raw_id_fields = ('user',)
    list_editable = ('is_active',)

    fieldsets = (
        ('Personal Info', {'fields': ('user', 'age', 'gender', 'blood_group')}),
        ('Health Info', {'fields': ('height', 'weight', 'allergies', 'medical_history', 'current_medications')}),
        ('Contact & Insurance', {'fields': ('emergency_contact', 'insurance_provider', 'insurance_policy_number')}),
        ('Status', {'fields': ('is_active', 'last_visit')}),
        ('Timestamps', {'fields': ('registration_date',)}),
    )

    readonly_fields = ('registration_date', 'last_visit')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status', 'appointment_type', 'is_urgent')
    list_filter = ('status', 'appointment_type', 'is_urgent', 'date', 'department')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                     'doctor__user__first_name', 'doctor__user__last_name', 'reason')
    raw_id_fields = ('patient', 'doctor')
    list_editable = ('status',)

    fieldsets = (
        ('Appointment Details', {'fields': ('patient', 'doctor', 'department', 'date', 'time', 'end_time')}),
        ('Medical Info', {'fields': ('reason', 'symptoms', 'appointment_type')}),
        ('Status', {'fields': ('status', 'is_urgent', 'notes', 'reminder_sent')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'medicine_name', 'dosage', 'duration', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'doctor', 'patient')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                     'doctor__user__first_name', 'doctor__user__last_name',
                     'medicine_name')
    raw_id_fields = ('patient', 'doctor', 'appointment')

    fieldsets = (
        ('Prescription Info', {'fields': ('appointment', 'patient', 'doctor')}),
        ('Medicine Details', {'fields': ('medicine_name', 'dosage', 'frequency', 'duration', 'quantity', 'instructions')}),
        ('Additional Info', {'fields': ('advice', 'max_refills', 'refill_count', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

class BillingAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'patient', 'doctor', 'total_amount', 'paid_amount', 'due_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('bill_number', 'patient__user__first_name', 'patient__user__last_name',
                     'doctor__user__first_name', 'doctor__user__last_name')
    raw_id_fields = ('patient', 'doctor', 'appointment')
    list_editable = ('payment_status',)

    fieldsets = (
        ('Billing Info', {'fields': ('bill_number', 'appointment', 'patient', 'doctor')}),
        ('Charges', {'fields': ('consultation_fee', 'medicine_charges', 'test_charges', 'other_charges')}),
        ('Financials', {'fields': ('tax_amount', 'discount', 'total_amount', 'paid_amount', 'due_amount')}),
        ('Payment Info', {'fields': ('payment_status', 'payment_method', 'insurance_coverage')}),
        ('Additional Info', {'fields': ('notes', 'due_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('bill_number', 'created_at', 'updated_at')

class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'record_type', 'title', 'is_critical', 'created_at')
    list_filter = ('record_type', 'is_critical', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                     'doctor__user__first_name', 'doctor__user__last_name',
                     'title', 'description')
    raw_id_fields = ('patient', 'doctor', 'appointment')

    fieldsets = (
        ('Record Info', {'fields': ('patient', 'doctor', 'appointment', 'record_type', 'title')}),
        ('Content', {'fields': ('description', 'file', 'findings', 'recommendations')}),
        ('Status', {'fields': ('is_critical',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'unit', 'unit_price', 'needs_reorder', 'is_active')
    list_filter = ('category', 'is_active', 'expiry_date')
    search_fields = ('name', 'description', 'supplier')
    list_editable = ('quantity', 'is_active')

    fieldsets = (
        ('Item Info', {'fields': ('name', 'category', 'description')}),
        ('Stock Info', {'fields': ('quantity', 'unit', 'reorder_level', 'unit_price')}),
        ('Supplier Info', {'fields': ('supplier', 'expiry_date', 'location')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

    def needs_reorder(self, obj):
        return obj.needs_reorder
    needs_reorder.boolean = True
    needs_reorder.short_description = 'Needs Reorder'

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(Payment)
admin.site.register(MedicalRecord, MedicalRecordAdmin)
admin.site.register(Test)
admin.site.register(Room)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(DoctorRating)
admin.site.register(HospitalSetting)









from .premium_models import *

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'patient', 'doctor', 'status', 'test_date')
    list_filter = ('status', 'test_date', 'test_name')
    search_fields = ('test_name', 'patient__user__first_name', 'patient__user__last_name')
    list_editable = ('status',)
    date_hierarchy = 'test_date'

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'unit_price', 'needs_reorder')
    list_filter = ('category', 'expiry_date')
    search_fields = ('name',)
    list_editable = ('quantity', 'unit_price')

    def needs_reorder(self, obj):
        return obj.needs_reorder
    needs_reorder.boolean = True
    needs_reorder.short_description = 'Needs Reorder?'

@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'patient', 'room_type', 'check_in', 'check_out', 'is_active')
    list_filter = ('room_type', 'is_active', 'check_in')
    search_fields = ('room_number', 'patient__user__first_name', 'patient__user__last_name')
    list_editable = ('is_active',)

@admin.register(HospitalConfig)
class HospitalConfigAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'phone', 'email', 'currency_symbol')

    def has_add_permission(self, request):
        # Only allow one settings record
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
