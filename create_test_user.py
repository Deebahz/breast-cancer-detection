import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('c:/Users/DibaAbdimujib/breast-cancer-detection')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'detection.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User

# Create test user
try:
    user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
    print('Test user created successfully')
except Exception as e:
    print(f'Error creating user: {e}')
