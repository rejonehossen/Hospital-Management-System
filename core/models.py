# core.models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('receptionist', 'Receptionist'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() if full_name.strip() else self.username

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fa-heartbeat')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def doctor_count(self):
        return self.doctor_set.filter(is_active=True).count()

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True)
    experience = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    working_hours_start = models.TimeField(default='09:00')
    working_hours_end = models.TimeField(default='17:00')
    max_patients_per_day = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['is_available']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    @property
    def average_rating(self):
        ratings = self.doctorrating_set.all()
        if ratings.exists():
            return sum(r.rating for r in ratings) / ratings.count()
        return 0

    @property
    def available_slots(self):
        # Calculate available slots based on appointments
        today = timezone.now().date()
        appointments = self.appointment_set.filter(date=today).values_list('time', flat=True)
        all_slots = self.generate_time_slots()
        return [slot for slot in all_slots if slot not in appointments]

    def generate_time_slots(self):
        slots = []
        start_hour = int(self.working_hours_start.hour)
        end_hour = int(self.working_hours_end.hour)

        for hour in range(start_hour, end_hour):
            slots.append(f"{hour:02d}:00")
            slots.append(f"{hour:02d}:30")

        return slots

class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['gender']),
            models.Index(fields=['blood_group']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.user.get_full_name()

    @property
    def bmi(self):
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m * height_m), 2)
        return None

    @property
    def appointment_count(self):
        return self.appointment_set.count()

    @property
    def upcoming_appointments(self):
        return self.appointment_set.filter(date__gte=timezone.now().date()).count()

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )

    APPOINTMENT_TYPE_CHOICES = (
        ('in_person', 'In Person'),
        ('telemedicine', 'Telemedicine'),
        ('follow_up', 'Follow Up'),
        ('emergency', 'Emergency'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    symptoms = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='in_person')
    notes = models.TextField(blank=True)
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date', '-time']
        unique_together = ['doctor', 'date', 'time']
        indexes = [
            models.Index(fields=['date', 'time']),
            models.Index(fields=['status']),
            models.Index(fields=['patient', 'doctor']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.doctor} - {self.date} {self.time}"

    def save(self, *args, **kwargs):
        if not self.department and self.doctor:
            self.department = self.doctor.department
        if not self.end_time:
            # Calculate end time (30 minutes by default)
            self.end_time = (timezone.datetime.combine(self.date, self.time) +
                           timedelta(minutes=30)).time()
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )
        return appointment_datetime > now and self.status in ['pending', 'confirmed']

    @property
    def duration_minutes(self):
        if self.end_time:
            start = timezone.datetime.combine(self.date, self.time)
            end = timezone.datetime.combine(self.date, self.end_time)
            return (end - start).seconds // 60
        return 30

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)
    advice = models.TextField()
    is_active = models.BooleanField(default=True)
    refill_count = models.IntegerField(default=0)
    max_refills = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'doctor']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.medicine_name}"

class Billing(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('insurance', 'Insurance'),
        ('online', 'Online Payment'),
        ('cheque', 'Cheque'),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='billing')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    bill_number = models.CharField(max_length=50, unique=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    medicine_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    test_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    insurance_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bill_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['patient', 'doctor']),
        ]

    def __str__(self):
        return f"Bill {self.bill_number} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = f"BILL-{uuid.uuid4().hex[:8].upper()}"

        # Calculate due amount
        self.due_amount = self.total_amount - self.paid_amount

        # Update payment status
        if self.paid_amount == 0:
            self.payment_status = 'pending'
        elif self.paid_amount < self.total_amount:
            self.payment_status = 'partial'
        elif self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'

        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=15)

        super().save(*args, **kwargs)

class Payment(models.Model):
    bill = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Billing.PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of ${self.amount} for {self.bill}"

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = (
        ('diagnosis', 'Diagnosis'),
        ('lab_result', 'Lab Result'),
        ('xray', 'X-Ray'),
        ('scan', 'Scan'),
        ('prescription', 'Prescription'),
        ('progress_note', 'Progress Note'),
        ('discharge_summary', 'Discharge Summary'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='medical_records/', blank=True, null=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'record_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.title}"

class Test(models.Model):
    TEST_TYPE_CHOICES = (
        ('blood_test', 'Blood Test'),
        ('urine_test', 'Urine Test'),
        ('xray', 'X-Ray'),
        ('mri', 'MRI'),
        ('ct_scan', 'CT Scan'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('other', 'Other'),
    )

    TEST_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='tests')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    test_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='pending')
    result = models.TextField(blank=True)
    result_file = models.FileField(upload_to='test_results/', blank=True, null=True)
    test_date = models.DateField()
    result_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.patient} - {self.test_name}"

class Room(models.Model):
    ROOM_TYPE_CHOICES = (
        ('consultation', 'Consultation Room'),
        ('operation', 'Operation Theater'),
        ('emergency', 'Emergency Room'),
        ('ward', 'Ward'),
        ('icu', 'ICU'),
        ('lab', 'Laboratory'),
    )

    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)
    features = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number}"

class Inventory(models.Model):
    CATEGORY_CHOICES = (
        ('medicine', 'Medicine'),
        ('equipment', 'Equipment'),
        ('consumable', 'Consumable'),
        ('furniture', 'Furniture'),
        ('other', 'Other'),
    )

    UNIT_CHOICES = (
        ('piece', 'Piece'),
        ('box', 'Box'),
        ('bottle', 'Bottle'),
        ('pack', 'Pack'),
        ('ml', 'ml'),
        ('mg', 'mg'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    reorder_level = models.IntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.CharField(max_length=200, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Inventory'

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('appointment', 'Appointment'),
        ('prescription', 'Prescription'),
        ('billing', 'Billing'),
        ('system', 'System'),
        ('reminder', 'Reminder'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_id = models.IntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"

class DoctorRating(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['patient', 'doctor']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} rated Dr. {self.doctor.user.last_name} {self.rating} stars"

class HospitalSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key

# Signals for automatic actions
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Appointment)
def create_appointment_notification(sender, instance, created, **kwargs):
    if created:
        # Create notification for patient
        Notification.objects.create(
            user=instance.patient.user,
            notification_type='appointment',
            title='New Appointment Scheduled',
            message=f'Your appointment with Dr. {instance.doctor.user.get_full_name()} is scheduled for {instance.date} at {instance.time}',
            related_object_id=instance.id,
            related_object_type='appointment'
        )

        # Create notification for doctor
        Notification.objects.create(
            user=instance.doctor.user,
            notification_type='appointment',
            title='New Appointment',
            message=f'You have a new appointment with {instance.patient.user.get_full_name()} on {instance.date} at {instance.time}',
            related_object_id=instance.id,
            related_object_type='appointment'
        )

@receiver(post_save, sender=Billing)
def create_billing_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.patient.user,
            notification_type='billing',
            title='New Bill Generated',
            message=f'Bill #{instance.bill_number} for amount ${instance.total_amount} has been generated',
            related_object_id=instance.id,
            related_object_type='billing'
        )

@receiver(post_save, sender=Prescription)
def create_prescription_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.patient.user,
            notification_type='prescription',
            title='New Prescription',
            message=f'Dr. {instance.doctor.user.get_full_name()} has prescribed {instance.medicine_name}',
            related_object_id=instance.id,
            related_object_type='prescription'
        )
