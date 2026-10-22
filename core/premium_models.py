# core/premium_models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

# 1. Detailed Lab Test Reports
class LabTest(models.Model):
    TEST_STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('sample_collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    )
    patient = models.ForeignKey('core.Patient', on_delete=models.CASCADE, related_name='lab_tests')
    doctor = models.ForeignKey('core.Doctor', on_delete=models.SET_NULL, null=True, related_name='ordered_lab_tests')
    test_name = models.CharField(max_length=200)
    test_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='requested')
    result_summary = models.TextField(blank=True)
    result_file = models.FileField(upload_to='lab_results/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient}"

# 2. Non-User Inventory Management
class InventoryItem(models.Model):
    CATEGORY_CHOICES = (
        ('medicine', 'Medicine'),
        ('equipment', 'Medical Equipment'),
        ('consumable', 'Consumable'),
        ('office', 'Office Supplies'),
    )
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    reorder_level = models.IntegerField(default=10, help_text="Alert when quantity falls below this")
    last_restocked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} in stock)"

    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level

# 3. Room / Bed Booking System
class RoomBooking(models.Model):
    ROOM_CHOICES = (
        ('general', 'General Ward'),
        ('private', 'Private Room'),
        ('icu', 'ICU'),
        ('operation', 'Operation Theater'),
    )
    patient = models.ForeignKey('core.Patient', on_delete=models.CASCADE)
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=20, choices=ROOM_CHOICES)
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.patient}"

# 4. Global Settings (Premium Config)
class HospitalConfig(models.Model):
    hospital_name = models.CharField(max_length=200, default="MediCare Hospital")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='hospital_logo/', blank=True, null=True)
    currency_symbol = models.CharField(max_length=5, default="$")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return self.hospital_name
