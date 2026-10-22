# core.forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import *

from .premium_models import *
import re

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation
            phone_pattern = r'^[\d\s\-\+\(\)]{10,}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError('Please enter a valid phone number.')
        return phone

class PatientRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Patient
        fields = ('gender', 'blood_group', 'height', 'weight', 'emergency_contact',
                  'allergies', 'medical_history')
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Height in cm',
                'step': '0.1'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Weight in kg',
                'step': '0.1'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact number'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any known allergies'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any relevant medical history'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')

        if height and height <= 0:
            self.add_error('height', 'Height must be positive.')

        if weight and weight <= 0:
            self.add_error('weight', 'Weight must be positive.')

        return cleaned_data

class DoctorRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=True)

    consultation_fee = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )

    working_hours_start = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )

    working_hours_end = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Doctor
        fields = ('department', 'qualification', 'specialization', 'experience',
                  'consultation_fee', 'license_number', 'bio', 'working_hours_start',
                  'working_hours_end', 'max_patients_per_day')
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MD Cardiology'
            }),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Heart Surgery'
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medical license number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Doctor biography and expertise'
            }),
            'max_patients_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('working_hours_start')
        end_time = cleaned_data.get('working_hours_end')

        if start_time and end_time and start_time >= end_time:
            self.add_error('working_hours_end', 'End time must be after start time.')

        return cleaned_data

class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Appointment
        fields = ('doctor', 'date', 'time', 'reason', 'symptoms', 'appointment_type', 'is_urgent')
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for appointment'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe your symptoms (optional)'
            }),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available doctors
        self.fields['doctor'].queryset = Doctor.objects.filter(is_available=True, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if doctor and date and time:
            # Check if doctor has reached max patients for the day
            daily_appointments = Appointment.objects.filter(
                doctor=doctor,
                date=date
            ).count()

            if daily_appointments >= doctor.max_patients_per_day:
                raise ValidationError(
                    f'Doctor has reached the maximum appointments ({doctor.max_patients_per_day}) for this day.'
                )

            # Check for conflicting appointments
            conflicting = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
                status__in=['pending', 'confirmed', 'in_progress']
            ).exists()

            if conflicting:
                raise ValidationError('This time slot is already booked. Please choose another time.')

            # Check if time is within doctor's working hours
            if time < doctor.working_hours_start or time > doctor.working_hours_end:
                raise ValidationError(
                    f'Doctor is only available between {doctor.working_hours_start} and {doctor.working_hours_end}'
                )

        return cleaned_data

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ('medicine_name', 'dosage', 'frequency', 'duration', 'quantity',
                  'instructions', 'advice', 'max_refills')
        widgets = {
            'medicine_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medicine name'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg'
            }),
            'frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3 times daily'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 7 days'
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 30 tablets'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Specific instructions for taking the medicine'
            }),
            'advice': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Medical advice and precautions'
            }),
            'max_refills': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }

class BillingForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ('consultation_fee', 'medicine_charges', 'test_charges',
                  'other_charges', 'tax_amount', 'discount', 'payment_method',
                  'insurance_coverage', 'notes', 'due_date')
        widgets = {
            'consultation_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'medicine_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'test_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'other_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'insurance_coverage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Calculate total amount
        consultation_fee = cleaned_data.get('consultation_fee', 0)
        medicine_charges = cleaned_data.get('medicine_charges', 0)
        test_charges = cleaned_data.get('test_charges', 0)
        other_charges = cleaned_data.get('other_charges', 0)
        tax_amount = cleaned_data.get('tax_amount', 0)
        discount = cleaned_data.get('discount', 0)

        subtotal = consultation_fee + medicine_charges + test_charges + other_charges
        total = subtotal + tax_amount - discount

        if total < 0:
            raise ValidationError('Total amount cannot be negative.')

        cleaned_data['total_amount'] = total
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'payment_method', 'transaction_id', 'notes')
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Payment amount'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction ID (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes (optional)'
            }),
        }

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ('record_type', 'title', 'description', 'file', 'findings',
                  'recommendations', 'is_critical')
        widgets = {
            'record_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Record title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Record description'
            }),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Medical findings'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations'
            }),
            'is_critical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TestForm(forms.ModelForm):
    test_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    result_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Test
        fields = ('test_type', 'test_name', 'description', 'test_date', 'notes')
        widgets = {
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'test_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Test name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Test description'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }

class InventoryForm(forms.ModelForm):
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Inventory
        fields = ('name', 'category', 'description', 'quantity', 'unit',
                  'reorder_level', 'unit_price', 'supplier', 'expiry_date',
                  'location', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item name'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'reorder_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Storage location'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('room_number', 'room_type', 'department', 'capacity',
                  'is_available', 'features')
        widgets = {
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Room number'
            }),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Room features and equipment'
            }),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PatientUpdateForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ('age', 'gender', 'blood_group', 'height', 'weight',
                  'emergency_contact', 'allergies', 'medical_history',
                  'current_medications', 'insurance_provider', 'insurance_policy_number')
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '150'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'insurance_provider': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DoctorUpdateForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ('department', 'qualification', 'specialization', 'experience',
                  'consultation_fee', 'license_number', 'bio', 'working_hours_start',
                  'working_hours_end', 'max_patients_per_day', 'is_available')
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'working_hours_start': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'working_hours_end': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'max_patients_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your phone number'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message'
        })
    )

class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('status', 'notes')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }

class TestResultForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('status', 'result', 'result_file', 'result_date')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'result': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Test results'
            }),
            'result_file': forms.FileInput(attrs={'class': 'form-control'}),
            'result_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
# core/forms.py (Add to bottom)

class AdminPatientCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Patient
        fields = ('gender', 'blood_group', 'age')
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AdminAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('doctor', 'date', 'time', 'reason', 'is_urgent')
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminLabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ('patient', 'test_name', 'test_date', 'status')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Complete Blood Count'}),
            'test_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
