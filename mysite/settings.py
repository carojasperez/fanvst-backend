"""
Django settings for Fanvst Backend.
Todas las claves sensibles se leen desde el archivo .env
usando python-decouple.
"""

import os
from decouple import config, Csv

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Seguridad ─────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT    = config('SECURE_SSL_REDIRECT',    default=False, cast=bool)
SESSION_COOKIE_SECURE  = config('SESSION_COOKIE_SECURE',  default=False, cast=bool)
CSRF_COOKIE_SECURE     = config('CSRF_COOKIE_SECURE',     default=False, cast=bool)


# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_USE_TLS       = config('EMAIL_USE_TLS',       default=True,  cast=bool)
EMAIL_HOST          = config('EMAIL_HOST',          default='localhost')
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_PORT          = config('EMAIL_PORT',          default=587,   cast=int)
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='Fanvst <no-reply@fanvst.com>')


# ── Google OAuth ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')


# ── Apps instaladas ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'import_export',
    'admintool',
    'admintool.financial',
    'adminsite',
    'adminsite.baseinfo',
    'adminsite.userinfo',
    'legal',
    'blog',
    'fanvst',
    'wallet',
    'notifications',
]


# ── Celery ────────────────────────────────────────────────────────────────────
from celery.schedules import crontab  # noqa: E402

CELERY_TIMEZONE   = config('CELERY_TIMEZONE',   default='America/Lima')
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost')

CELERY_BEAT_SCHEDULE = {
    # Libera fondos en clearing que ya superaron su available_at
    'wallet-clear-pending': {
        'task': 'wallet.clear_pending_transactions',
        'schedule': crontab(minute=0),  # Cada hora
    },
    # Resumen diario de usuarios registrados → Telegram grupo Fan Registration
    'notify-daily-fan-summary': {
        'task': 'notifications.notify_daily_fan_summary',
        'schedule': crontab(hour=20, minute=0),  # 20:00 hora Lima
    },
}


# ── Telegram (Staff Notifications) ───────────────────────────────────────────
# Configurar en .env una vez que tengas el bot creado con @BotFather
TELEGRAM_BOT_TOKEN          = config('TELEGRAM_BOT_TOKEN',          default='')
TELEGRAM_CHAT_ARTIST_REG    = config('TELEGRAM_CHAT_ARTIST_REG',    default='')
TELEGRAM_CHAT_FAN_REG       = config('TELEGRAM_CHAT_FAN_REG',       default='')
TELEGRAM_CHAT_PAYMENTS      = config('TELEGRAM_CHAT_PAYMENTS',      default='')


# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGIN_WHITELIST = config(
    'CORS_ORIGIN_WHITELIST',
    default='http://localhost:4200',
    cast=Csv(),
)


# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'mysite.wsgi.application'


# ── Base de datos ─────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='fanvst'),
        'USER':     config('DB_USER',     default='fanvst_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
    }
}


# ── Validación de contraseñas ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Cache ─────────────────────────────────────────────────────────────────────
# Si REDIS_URL está definido en .env → Redis (producción / staging).
# Si no está definido          → LocMemCache (desarrollo local, sin dependencias).
# Los throttles de DRF usan este cache; con LocMemCache funcionan igualmente
# pero los contadores se resetean al reiniciar el proceso.
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'fanvst',
            'TIMEOUT': 300,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'fanvst-throttle',
        }
    }


# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fanvst.authentication.CookieTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # fallback para header Authorization
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DATE_INPUT_FORMATS': ["%d/%m/%Y", "%Y-%m-%d"],
    # ── Rate limiting ──────────────────────────────────────────────────────────
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Globales (fallback para endpoints sin throttle específico)
        'anon': '200/day',
        'user': '2000/day',
        # Autenticación — anónimos
        'login':             '5/min',
        'social_login':      '10/min',
        'register':          '5/hour',
        'password_reset':    '3/hour',
        'resend_validation': '3/hour',
        'validate_email':    '20/hour',
        'validate_token':    '10/hour',
        # Financieros — usuarios autenticados
        'financial':  '20/hour',
        'subscribe':  '30/hour',
    },
}


# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}


# ── Internacionalización ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'es-pe'
USE_I18N  = True
USE_L10N  = True
USE_TZ    = True
TIME_ZONE = 'America/Lima'


# ── Archivos estáticos y media ────────────────────────────────────────────────
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL  = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL  = '/media/'
