import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.exceptions import DisallowedHost
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Sentry Configuration
# only enable in production
if os.environ.get("ENVIRONMENT") == "production":
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:

        def before_send(event, hint):
            """Filter out admin pages from Sentry reporting"""
            if "request" in event:
                url = event["request"].get("url", "")
                # Get admin URL pattern
                admin_url = os.environ.get("ADMIN_URL", "admin-lkj234234ljk8c8")

                # Check if URL contains admin paths
                admin_patterns = [
                    f"/{admin_url}/",
                    "/admin/",  # Standard Django admin
                ]

                for pattern in admin_patterns:
                    if pattern in url:
                        return None  # Don't send to Sentry

            # Also check transaction names
            if "transaction" in event:
                transaction = event["transaction"]
                admin_url = os.environ.get("ADMIN_URL", "admin-lkj234234ljk8c8")
                admin_patterns = [
                    f"{admin_url}/",
                    "admin/",
                    "admin_dashboard",
                    "admin_chart_data",
                    "memory_dashboard",
                ]

                for pattern in admin_patterns:
                    if pattern in transaction:
                        return None  # Don't send to Sentry

            return event

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_style="url",
                    middleware_spans=True,
                    signals_spans=True,
                ),
            ],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            send_default_pii=True,
            environment=os.environ.get("ENVIRONMENT", "development"),
            ignore_errors=[DisallowedHost, "asyncio.CancelledError"],
            enable_tracing=True,
            before_send=before_send,
        )

SECRET_KEY = os.environ.get("SECRET_KEY", "replace-this-with-a-secure-key")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(
    ","
) + ["gemnar.com", "www.gemnar.com", "localhost", "127.0.0.1", "0.0.0.0", "assignment-ov4q.onrender.com"]

# CSRF settings for API endpoints
CSRF_TRUSTED_ORIGINS = [
    "https://gemnar.com",
    "https://www.gemnar.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Site domain for generating absolute URLs (used by Instagram API)
SITE_DOMAIN = "gemnar.com"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",  # Required by allauth and admin
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # Must come before allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.twitter_oauth2",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "website",
    "channels",
    "chat",
    "organizations",
]

# Custom user model
AUTH_USER_MODEL = "website.User"

# Site ID for django.contrib.sites
SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "website.middleware.error_notification_middleware.ErrorNotificationMiddleware",
]

ROOT_URLCONF = "gemnar.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "chat.context_processors.unread_messages_count",
                "website.context_processors.default_brand_and_credits",
            ],
        },
    },
]

WSGI_APPLICATION = "gemnar.wsgi.application"

# Channels Configuration for WebSocket support
ASGI_APPLICATION = "gemnar.asgi.application"

# Channel Layers for WebSocket
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Database configuration based on environment
if ENVIRONMENT == "development":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Production/staging PostgreSQL - Use DATABASE_URL from Render
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ.get("DATABASE_URL"), 
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Email settings for production with Mailgun
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.mailgun.org"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get("SMTP_USERNAME")
    EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "support@gemnar.com")
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    EMAIL_TIMEOUT = 30

    # Additional email settings for better reliability
    EMAIL_USE_SSL = False  # Use TLS instead of SSL for port 587
    EMAIL_SSL_CERTFILE = None
    EMAIL_SSL_KEYFILE = None

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(BASE_DIR, "staticfiles"))
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "website", "static"),
]

# Media files (uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Create user_uploads directory if it doesn't exist
USER_UPLOADS_DIR = os.path.join(MEDIA_ROOT, "user_uploads")
os.makedirs(USER_UPLOADS_DIR, exist_ok=True)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB (total request size)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Maximum number of fields
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

# Admin URL configuration
ADMIN_URL = os.environ.get("ADMIN_URL", "admin-lkj234234ljk8c8")



# Allauth settings
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/landing/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Channels configuration
ASGI_APPLICATION = "gemnar.asgi.application"
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Chat Encryption Configuration
CHAT_ENCRYPTION_KEY = os.environ.get(
    "CHAT_ENCRYPTION_KEY",
    "your-super-secure-32-byte-key-here-change-me-in-production!!!",
)

# Background Task Processing
# We use cron jobs instead of Celery for simplicity
# Run: * * * * * cd /path/to/project && poetry run python manage.py send_brand_tweets
# This management command handles all background tasks including:
# - Posting scheduled tweets
# - Refreshing Twitter metrics
# - Processing queued operations

# Twitter API Configuration (for fallback only - users should provide their own credentials)
# These are kept for backward compatibility but are not required
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")

# Instagram OAuth Configuration
INSTAGRAM_APP_ID = os.environ.get("INSTAGRAM_APP_ID")
INSTAGRAM_APP_SECRET = os.environ.get("INSTAGRAM_APP_SECRET")
INSTAGRAM_REDIRECT_URI = os.environ.get("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/instagram/oauth-callback/")

# OpenAI Configuration moved to EncryptedVariable table in database

# Kie AI API Configuration (for Veo 3.1 video generation)
KIE_AI_API_KEY = os.environ.get("KIE_AI_API_KEY")

# AIML API Configuration (for video generation, image generation, and TTS)
AIML_API_KEY = os.environ.get("AIML_API_KEY")

# Cloudinary Configuration (for image uploads)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

# Django REST Framework Configuration - Token-based authentication only
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        # Removed SessionAuthentication for token-only auth
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 20,
}

# dj-rest-auth Configuration - Token-based authentication only
REST_AUTH = {
    "USE_JWT": False,
    "SESSION_LOGIN": False,  # Disable session-based login
    "REGISTER_SERIALIZER": "website.serializers.RegisterSerializer",
    "TOKEN_SERIALIZER": "dj_rest_auth.serializers.TokenSerializer",
    "LOGIN_SERIALIZER": "website.serializers.EmailLoginSerializer",
    "USER_DETAILS_SERIALIZER": ("dj_rest_auth.serializers.UserDetailsSerializer"),
    "SIGNUP_FIELDS": {
        "username": {"required": False},
        "email": {"required": True},
    },
}

# Allauth Configuration for dj-rest-auth
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
# Configure signup fields - new format replaces ACCOUNT_USERNAME_REQUIRED
ACCOUNT_SIGNUP_FIELDS = {
    "username": {"required": False},
    "email": {"required": True},
    "password1": {"required": True},
    "password2": {"required": True},
}

# Social Account Provider Configuration
SOCIALACCOUNT_PROVIDERS = {
    "twitter_oauth2": {
        "SCOPE": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
        "VERIFIED_EMAIL": True,
    }
}

# CORS Configuration - Token-based auth (no cookies needed)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # For convenience
    "http://127.0.0.1:3000",      # Primary - use this for development
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://gemnar.com",
    "https://www.gemnar.com",
    "https://gemnar.shubhsoch.workers.dev",  # Cloudflare Workers frontend
]

CORS_ALLOW_CREDENTIALS = False  # No credentials needed for token auth
CORS_ALLOW_PRIVATE_NETWORK = True

# Additional CORS headers for API compatibility
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-requested-with',
    # Removed CSRF-related headers for token-only auth
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Preflight options
CORS_PREFLIGHT_MAX_AGE = 86400
# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {module} {process:d} {thread:d} {message}"
            ),
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "detailed": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "formatter": "verbose",
        },
        "request_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "requests.log"),
            "formatter": "detailed",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "errors.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "request_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console", "request_file"],
            "level": "INFO",
            "propagate": False,
        },
        "website": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "chat": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "organizations": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "request_file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "request_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# ============================================================================
# Cloudinary Configuration
# ============================================================================
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')
