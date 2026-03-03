import os
from pathlib import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, 'subdir')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------
# Security
# ------------------------------
SECRET_KEY = 'django-insecure-1234567890abcdef1234567890abcdef'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
TIME_ZONE = 'Africa/Nairobi'  # Change to your local timezone
USE_TZ = True
LOGIN_REDIRECT_URL = 'home'   # after login
LOGOUT_REDIRECT_URL = 'login'      # after logout
LOGIN_URL = 'login'
REGISTRATION_FEE = 5000  # KES

# ------------------------------
# Applications
# ------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',

    # Your apps
    'students_app',
    'widget_tweaks',
    'fees.apps.FeesConfig',  # Only include the AppConfig, remove 'fees' duplicate
]
# ------------------------------
# Middleware
# ------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ------------------------------
# Templates
# ------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # ✅ Project-level templates folder
        'DIRS': [os.path.join(BASE_DIR, 'templates')],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ------------------------------
# Database
# ------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # Use os.path.join since BASE_DIR is a string
    }
}

# ------------------------------
# Static files (CSS, JS, Images)
# ------------------------------
STATIC_URL = '/static/'

# ------------------------------
# Media files (uploads, receipts)
# ------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # This is where uploaded files will be stored

# ------------------------------
# Default primary key field type
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
