import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Esto apunta a la carpeta raíz 'data-easy'
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tu-llave-secreta-aqui'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# --- 1. APLICACIÓN REGISTRADA ---
# Aquí nos aseguramos de que Django sepa que tu app 'dataeasy' existe.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tu aplicación
    'dataeasy',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'miweb.urls' # Apunta al urls.py de la carpeta 'miweb'


# --- 2. UBICACIÓN DE TEMPLATES (HTML) ---
# Esta es la configuración clave que solucionó tu error NoReverseMatch.
# Le dice a Django que busque tus archivos HTML en la carpeta 'templates' 
# que está en la raíz del proyecto.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # <-- ¡LÍNEA IMPORTANTE!
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

WSGI_APPLICATION = 'miweb.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es-cl' # Español de Chile

TIME_ZONE = 'America/Santiago' # Zona horaria de Chile

USE_I18N = True

USE_TZ = True


# --- 3. UBICACIÓN DE ARCHIVOS ESTÁTICOS (CSS, JS, Imágenes) ---
# Al igual que con los templates, le decimos a Django dónde
# encontrar tu carpeta 'static' en la raíz del proyecto.

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static', # <-- ¡LÍNEA IMPORTANTE!
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dataeasy',
        'USER': 'root',
        'PASSWORD': 'Admin1234',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

TEMPLATES = [
    {
        # ESTA LÍNEA ES LA QUE SEGURAMENTE FALTA O ESTÁ ROTA:
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Aquí está la línea nueva para tus alertas del sidebar:
                'dataeasy.context_processors.alertas_sidebar',
            ],
        },
    },
]