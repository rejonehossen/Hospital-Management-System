#!/usr/bin/env python
"""
Setup script for MediCare Hospital Management System
"""

import os
import sys
import django
from pathlib import Path

def setup_environment():
    """Setup Django environment"""
    # Add project to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')

    # Setup Django
    django.setup()

def create_superuser():
    """Create superuser if not exists"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = 'admin'
    email = 'admin@medicare.com'
    password = 'admin123'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='System',
            last_name='Administrator',
            role='admin'
        )
        print(f"✅ Superuser created: {username} / {password}")
    else:
        print("ℹ️  Superuser already exists")

def create_sample_data():
    """Create sample data for testing"""
    from django.core.management import call_command

    call_command('create_sample_data')
    print("✅ Sample data created")

def run_migrations():
    """Run database migrations"""
    from django.core.management import call_command

    call_command('makemigrations')
    call_command('migrate')
    print("✅ Database migrations completed")

def collect_static():
    """Collect static files"""
    from django.core.management import call_command

    call_command('collectstatic', '--noinput')
    print("✅ Static files collected")

def check_dependencies():
    """Check if all dependencies are installed"""
    required_packages = [
        'Django>=4.2.0',
        'Pillow>=9.0.0',
        'reportlab>=3.6.0',
        'faker>=15.0.0',
        'django-cors-headers>=3.14.0',
        'djangorestframework>=3.14.0',
        'django-filter>=22.0.0',
    ]

    print("🔍 Checking dependencies...")
    for package in required_packages:
        try:
            pkg_name = package.split('>=')[0]
            __import__(pkg_name.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            return False

    return True

def setup_project():
    """Main setup function"""
    print("🚀 Setting up MediCare Hospital Management System")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies:")
        print("pip install -r requirements.txt")
        return

    # Setup environment
    setup_environment()

    # Run migrations
    print("\n📦 Setting up database...")
    run_migrations()

    # Create superuser
    print("\n👤 Creating superuser...")
    create_superuser()

    # Create sample data
    print("\n📊 Creating sample data...")
    create_sample_data()

    # Collect static files
    print("\n🎨 Collecting static files...")
    collect_static()

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n🎉 You can now run the development server:")
    print("python manage.py runserver")
    print("\n🔑 Admin login: admin / admin123")
    print("👨‍⚕️ Doctor login: doc[firstname]0 / doctor123")
    print("👤 Patient login: pat[firstname]0 / patient123")
    print("\n🌐 Open http://localhost:8000 in your browser")

if __name__ == '__main__':
    setup_project()
