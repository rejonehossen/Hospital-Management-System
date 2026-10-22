from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from faker import Faker
import random
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP

from ...models import (
    Department, User, Doctor, Patient, Appointment,
    Prescription, Billing,
)


class Command(BaseCommand):
    help = 'Create sample data for development'

    def handle(self, *args, **options):
        fake = Faker()

        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # ---------- Departments ----------
        departments_data = [
            ('Cardiology', 'Heart and cardiovascular diseases', 'fa-heart'),
            ('Neurology', 'Brain and nervous system disorders', 'fa-brain'),
            ('Orthopedics', 'Bones, joints, and muscles', 'fa-bone'),
            ('Pediatrics', 'Child healthcare', 'fa-baby'),
            ('Dermatology', 'Skin diseases and conditions', 'fa-allergies'),
            ('Ophthalmology', 'Eye care and vision', 'fa-eye'),
            ('ENT', 'Ear, nose, and throat diseases', 'fa-ear'),
            ('Dental', 'Oral healthcare', 'fa-tooth'),
            ('Gynecology', "Women's reproductive health", 'fa-female'),
            ('General Medicine', 'General healthcare', 'fa-stethoscope'),
        ]

        departments = []
        for name, desc, icon in departments_data:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'icon': icon}
            )
            departments.append(dept)
            if created:
                self.stdout.write(f'Created department: {name}')

        # ---------- Admin user ----------
        admin_user, admin_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@medicare.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'password': make_password('admin123'),
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        if admin_created:
            self.stdout.write('Created admin user')

        # ---------- Doctors ----------
        specialties = [
            'Cardiologist', 'Neurologist', 'Orthopedic Surgeon', 'Pediatrician',
            'Dermatologist', 'Ophthalmologist', 'ENT Specialist', 'Dentist',
            'Gynecologist', 'General Physician'
        ]
        qualifications = ['MD', 'MBBS', 'MS', 'MCh', 'DNB', 'FRCS']

        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f'doc{first_name.lower()}{i}'
            email = f'{username}@medicare.com'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': make_password('doctor123'),
                    'role': 'doctor',
                    'phone': fake.phone_number()[:15],
                    'is_verified': True,
                }
            )

            if created:
                Doctor.objects.create(
                    user=user,
                    department=random.choice(departments),
                    qualification=f'{random.choice(qualifications)} in {random.choice(specialties)}',
                    specialization=random.choice(specialties),
                    experience=random.randint(5, 30),
                    consultation_fee=random.randint(500, 2000),
                    bio=fake.text(max_nb_chars=200),
                    license_number=f'MED{random.randint(100000, 999999)}',
                    is_available=random.choice([True, True, True, False]),
                    max_patients_per_day=random.randint(15, 25),
                    working_hours_start='09:00',
                    working_hours_end='17:00',
                )
                self.stdout.write(f'Created doctor: Dr. {first_name} {last_name}')

        # ---------- Patients ----------
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

        for i in range(50):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f'pat{first_name.lower()}{i}'
            email = f'{username}@example.com'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': make_password('patient123'),
                    'role': 'patient',
                    'phone': fake.phone_number()[:15],
                    'address': fake.address()[:200],  # guard against max_length
                    'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                    'is_verified': True,
                }
            )

            if created:
                dob = user.date_of_birth
                today = datetime.now().date()
                age = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day)
                )

                Patient.objects.create(
                    user=user,
                    age=age,
                    gender=random.choice(['M', 'F']),
                    blood_group=random.choice(blood_groups),
                    height=round(random.uniform(150, 190), 1),
                    weight=round(random.uniform(50, 100), 1),
                    emergency_contact=fake.phone_number()[:15],
                    allergies=random.choice(['None', 'Penicillin', 'Dust', 'Peanuts', '']),
                    medical_history=random.choice([
                        'Hypertension', 'Diabetes', 'Asthma', 'None',
                        'Previous heart surgery', 'Migraine'
                    ]),
                    current_medications=random.choice(
                        ['None', 'Metformin 500mg', 'Amlodipine 5mg', '']
                    ),
                )
                self.stdout.write(f'Created patient: {first_name} {last_name}')

        # ---------- Appointments ----------
        doctors = list(Doctor.objects.all())
        patients = list(Patient.objects.all())

        if not doctors or not patients:
            self.stdout.write(self.style.WARNING(
                'Skipping appointments: need at least one doctor and one patient.'
            ))
            return

        type_choices = ['in_person', 'telemedicine', 'follow_up']

        for _ in range(100):
            doctor = random.choice(doctors)
            patient = random.choice(patients)

            days_offset = random.randint(-30, 30)
            appointment_date = datetime.now().date() + timedelta(days=days_offset)

            if days_offset < 0:
                status = random.choice(['completed', 'cancelled'])
            else:
                status = random.choice(['pending', 'confirmed'])

            hour = random.randint(9, 16)
            minute = random.choice([0, 30])
            appointment_time = time(hour, minute)

            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=appointment_date,
                time=appointment_time,
                reason=fake.text(max_nb_chars=100),
                symptoms=fake.text(max_nb_chars=200),
                status=status,
                appointment_type=random.choice(type_choices),
                is_urgent=random.choice([True, False, False, False]),
            )

            if status == 'completed':
                patient.last_visit = datetime.now()
                patient.save(update_fields=['last_visit'])

            self.stdout.write(
                f'Created appointment: {patient} with {doctor} on {appointment_date}'
            )

        # ---------- Prescriptions ----------
        appointments = list(Appointment.objects.filter(status='completed')[:30])
        medicines = [
            'Amoxicillin 500mg', 'Paracetamol 500mg', 'Ibuprofen 400mg',
            'Cetirizine 10mg', 'Omeprazole 20mg', 'Metformin 500mg',
            'Atorvastatin 20mg', 'Levothyroxine 50mcg', 'Losartan 50mg',
            'Amlodipine 5mg', 'Metoprolol 50mg', 'Furosemide 40mg'
        ]

        for appointment in appointments:
            for _ in range(random.randint(1, 3)):
                prescription = Prescription.objects.create(
                    appointment=appointment,
                    patient=appointment.patient,
                    doctor=appointment.doctor,
                    medicine_name=random.choice(medicines),
                    dosage=random.choice(['500mg', '250mg', '10mg', '20mg', '50mg']),
                    frequency=random.choice(
                        ['Once daily', 'Twice daily', 'Three times daily', 'As needed']
                    ),
                    duration=random.choice(['7 days', '14 days', '30 days', 'Continue']),
                    quantity=random.choice(['30 tablets', '60ml', '1 tube', '15 capsules']),
                    instructions=random.choice([
                        'Take after meals', 'Take on empty stomach',
                        'With plenty of water', 'Avoid alcohol', 'Take at bedtime'
                    ]),
                    advice=fake.text(max_nb_chars=200),
                    max_refills=random.randint(0, 3),
                    is_active=random.choice([True, False]),
                )
                self.stdout.write(
                    f'Created prescription: {prescription.medicine_name} for {appointment.patient}'
                )

        # ---------- Bills ----------
        completed_appointments = list(
            Appointment.objects.filter(status='completed')[:20]
        )
        tax_rate = Decimal('0.18')

        for appointment in completed_appointments:
            consultation_fee = Decimal(str(appointment.doctor.consultation_fee))
            medicine_charges = Decimal(str(random.randint(0, 1000)))
            test_charges = Decimal(str(random.randint(0, 2000)))
            other_charges = Decimal(str(random.randint(0, 500)))

            subtotal = consultation_fee + medicine_charges + test_charges + other_charges

            # Discount must not exceed subtotal
            max_discount = int(subtotal)
            discount = Decimal(str(random.randint(0, min(200, max_discount))))

            taxable = subtotal - discount
            tax_amount = (taxable * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_amount = (taxable + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Keep paid_amount and payment_status consistent
            pay_scenario = random.choice(['paid', 'partial', 'pending'])
            if pay_scenario == 'paid':
                paid_amount = total_amount
            elif pay_scenario == 'partial':
                paid_amount = (total_amount * Decimal('0.5')).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            else:
                paid_amount = Decimal('0.00')

            Billing.objects.create(
                appointment=appointment,
                patient=appointment.patient,
                doctor=appointment.doctor,
                consultation_fee=consultation_fee,
                medicine_charges=medicine_charges,
                test_charges=test_charges,
                other_charges=other_charges,
                tax_amount=tax_amount,
                discount=discount,
                total_amount=total_amount,
                paid_amount=paid_amount,
                payment_status=pay_scenario,
                payment_method=random.choice(['cash', 'card', 'online', 'insurance']),
                due_date=datetime.now().date() + timedelta(days=15),
            )
            self.stdout.write(
                f'Created bill: ${total_amount:.2f} for {appointment.patient}'
            )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
