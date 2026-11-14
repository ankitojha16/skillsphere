"""
Django settings for SkillSphere project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables (.env.local takes precedence for local overrides, then .env)
load_dotenv(BASE_DIR / '.env.local')
load_dotenv(BASE_DIR / '.env')

# Environment Detection
IS_VERCEL = bool(os.getenv('VERCEL'))

# SECURITY WARNING: don't run with debug turned on in production!
# On Vercel, DEBUG defaults to False unless explicitly overridden
DEBUG = os.getenv('DEBUG', 'False' if IS_VERCEL else 'True') == 'True'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG or IS_VERCEL:
        import secrets
        SECRET_KEY = os.getenv('SECRET_KEY_FALLBACK') or secrets.token_urlsafe(50)
    else:
        SECRET_KEY = 'django-insecure-skillsphere-development-key-phase1-production-ready-2026'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',') if h.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')
if '.vercel.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.vercel.app')
vercel_url = os.getenv('VERCEL_URL')
if vercel_url and vercel_url not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_url)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # SkillSphere Custom Apps
    'accounts.apps.AccountsConfig',
    'courses.apps.CoursesConfig',
    'learning.apps.LearningConfig',
    'dashboard.apps.DashboardConfig',
    'goals.apps.GoalsConfig',

    # Phase 2 AI & Career Apps
    'assistant.apps.AssistantConfig',
    'roadmaps.apps.RoadmapsConfig',
    'assessments.apps.AssessmentsConfig',
    'interviews.apps.InterviewsConfig',
    'projects.apps.ProjectsConfig',
    'gamification.apps.GamificationConfig',

    # Phase 3 Career, Portfolio, Community & Opportunities Apps
    'careers.apps.CareersConfig',
    'portfolios.apps.PortfoliosConfig',
    'resumes.apps.ResumesConfig',
    'opportunities.apps.OpportunitiesConfig',
    'community.apps.CommunityConfig',
    'collaboration.apps.CollaborationConfig',
    'events.apps.EventsConfig',
    'certificates.apps.CertificatesConfig',
    'notifications.apps.NotificationsConfig',

    # Phase 15 Analytics & Beta Operations
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.RequestCorrelationMiddleware',
    'config.middleware.PerformanceMonitoringMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.SecurityCacheHeadersMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.student_profile_context',
                'notifications.context_processors.notifications_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Supports PostgreSQL with optional fallback to SQLite when PostgreSQL server is not running locally.
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')
DB_NAME = os.getenv('DB_NAME', 'skillsphere_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
USE_SQLITE_FALLBACK = os.getenv('USE_SQLITE_FALLBACK', 'True') == 'True'

# Check if PostgreSQL connection can be configured, or fallback gracefully
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif os.getenv('DATABASE_URL'):
    import dj_database_url
    default_db = dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=int(os.getenv('CONN_MAX_AGE', '0' if IS_VERCEL else '60')),
        conn_health_checks=True,
    )
    # In PgBouncer transaction pooling (port 6543), server-side cursors must be disabled in Django
    default_db['DISABLE_SERVER_SIDE_CURSORS'] = True
    default_db.setdefault('OPTIONS', {})
    default_db['OPTIONS'].update({
        # Fast failure on database network drop (libpq parameter)
        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '5')),
        # Hard 10-second statement timeout to protect the connection pool from runaway queries
        'options': f"-c statement_timeout={os.getenv('DB_STATEMENT_TIMEOUT', '10000')}",
    })
    DATABASES = {'default': default_db}
elif not USE_SQLITE_FALLBACK:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }
else:
    # Try testing PostgreSQL or fallback to SQLite for immediate usability
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=2
        )
        conn.close()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': DB_NAME,
                'USER': DB_USER,
                'PASSWORD': DB_PASSWORD,
                'HOST': DB_HOST,
                'PORT': DB_PORT,
            }
        }
    except Exception:
        # Graceful SQLite fallback for local developer workflow
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# Cache configuration: Shared Redis (for multi-instance serverless consistency) with LocMemCache fallback
REDIS_URL = os.environ.get('REDIS_URL') or os.environ.get('CACHE_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'config.cache.FaultTolerantRedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 300,  # 5 minutes TTL
            'KEY_PREFIX': 'skillsphere',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'skillsphere-cache-layer',
            'TIMEOUT': 300,  # 5 minutes TTL ensures fast multi-instance convergence
            'KEY_PREFIX': 'skillsphere',
            'OPTIONS': {
                'MAX_ENTRIES': 2000,
            }
        }
    }

# Session engine: Cached database backend eliminates redundant DB hits on authenticated requests
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Static files storage
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files (User uploads, avatars, course thumbnails)
MEDIA_URL = '/media/'
if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    MEDIA_ROOT = Path('/tmp/media')
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Reverse proxy SSL header (Essential for Vercel edge proxy)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ['127.0.0.1', 'localhost', '*']]
CSRF_TRUSTED_ORIGINS.extend([
    'https://skillsphere-cyan.vercel.app',
    'https://*.vercel.app',
    'https://*.supabase.co',
])

# Authentication redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Email settings: SMTP when configured via environment, else safe console output
if os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'SkillSphere <noreply@skillsphere.app>')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Authoritative Learning & Certificate Eligibility Configuration
ASSESSMENT_UNLOCK_THRESHOLD = int(os.getenv('ASSESSMENT_UNLOCK_THRESHOLD', 80))
CERTIFICATE_ELIGIBILITY_THRESHOLD = int(os.getenv('CERTIFICATE_ELIGIBILITY_THRESHOLD', 85))
ASSESSMENT_PASSING_PERCENTAGE = int(os.getenv('ASSESSMENT_PASSING_PERCENTAGE', 70))

# Gemini AI Engine Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')
GEMINI_FALLBACK_MODEL = os.getenv('GEMINI_FALLBACK_MODEL', 'gemini-3.6-flash')
GEMINI_LIGHTWEIGHT_MODEL = os.getenv('GEMINI_LIGHTWEIGHT_MODEL', 'gemini-3.5-flash-lite')
_raw_cascade = os.getenv('GEMINI_MODELS_CASCADE', '')
GEMINI_MODELS_CASCADE = [m.strip() for m in _raw_cascade.split(',') if m.strip()] if _raw_cascade else [
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
    GEMINI_LIGHTWEIGHT_MODEL,
]
AI_REQUEST_TIMEOUT = int(os.getenv('AI_REQUEST_TIMEOUT', 12))  # per-request timeout in seconds
AI_TOTAL_DEADLINE = int(os.getenv('AI_TOTAL_DEADLINE', 25))    # overall execution budget in seconds
AI_RATE_LIMIT_PER_MINUTE = int(os.getenv('AI_RATE_LIMIT_PER_MINUTE', 20))
AI_MAX_INPUT_LENGTH = int(os.getenv('AI_MAX_INPUT_LENGTH', 3000))

# Structured Application Logging with Request Correlation IDs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'correlation_id': {
            '()': 'config.middleware.CorrelationIdFilter',
        },
    },
    'formatters': {
        'structured': {
            'format': '[%(asctime)s] [%(correlation_id)s] [%(levelname)s] [%(name)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
            'filters': ['correlation_id'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'skillsphere': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
