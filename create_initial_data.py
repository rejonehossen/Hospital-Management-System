import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')
django.setup()

from core.models import User, Department, Doctor, Patient
from django.contrib.auth.hashers import make_password

# Create departments
departments = [
    ('Cardiology', 'Heart and cardiovascular system', 'fa-heart'),
    ('Neurology', 'Brain and nervous system', 'fa-brain'),
    ('Orthopedics', 'Bones and joints', 'fa-bone'),
    ('Pediatrics', 'Child healthcare', 'fa-baby'),
    ('Dermatology', 'Skin diseases', 'fa-allergies'),
    ('Ophthalmology', 'Eye care', 'fa-eye'),
    ('ENT', 'Ear, nose and throat', 'fa-ear'),
    ('Dental', 'Oral healthcare', 'fa-tooth'),
]

for name, desc, icon in departments:
    Department.objects.get_or_create(name=name, defaults={'description': desc, 'icon': icon})

print("Departments created successfully!")

# Create sample doctors
doctors_data = [
    ('john', 'password123', 'John', 'Smith', 'john@hospital.com', 'doctor', '1234567890', 1, 'MD Cardiology', 15, 150.00),
    ('sarah', 'password123', 'Sarah', 'Johnson', 'sarah@hospital.com', 'doctor', '9876543210', 2, 'MD Neurology', 10, 200.00),
    ('michael', 'password123', 'Michael', 'Brown', 'michael@hospital.com', 'doctor', '4561237890', 3, 'MS Orthopedics', 12, 180.00),
]

for username, password, first, last, email, role, phone, dept_id, qual, exp, fee in doctors_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first,
            'last_name': last,
            'email': email,
            'role': role,
            'phone': phone,
            'password': make_password(password)
        }
    )

    if created:
        Doctor.objects.create(
            user=user,
            department_id=dept_id,
            qualification=qual,
            experience=exp,
            consultation_fee=fee
        )

print("Doctors created successfully!")

# Create sample patient
patient_user = User.objects.create_user(
    username='patient1',
    password='password123',
    first_name='Jane',
    last_name='Doe',
    email='jane@example.com',
    role='patient',
    phone='5551234567'
)

Patient.objects.create(
    user=patient_user,
    age=30,
    gender='F',
    blood_group='O+',
    height=165,
    weight=60
)

print("Patient created successfully!")
print("Initial data setup complete!")
