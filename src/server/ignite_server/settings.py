"""
Django settings for Ignite Buddy unified backend.
Integrates Admin Console REST APIs, Trainee Assistant Channels WebSocket,
and RAG Knowledge Base.
"""
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or os.getenv("ASSISTANT_SECRET_KEY", "ignite-buddy-dev-secret-key-32chars-min!!")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

# Application definition
INSTALLED_APPS = [
    # Channels
    "channels",

    # Django contrib
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third Party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",

    # Ignite Buddy Unified Apps
    "server.apps.accounts",
    "server.apps.buddy_controller",
    "server.apps.notifications",
    "server.apps.schedules",
    "server.apps.documents",
    "server.apps.dashboard",
    "server.apps.telemetry",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.ignite_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.ignite_server.wsgi.application"
ASGI_APPLICATION = "server.ignite_server.asgi.application"

# Database Configuration
# Supports PostgreSQL in production or when DATABASE_URL is postgres://,
# and falls back cleanly to SQLite for local development / testing without requiring PostgreSQL service.
DB_ENGINE = os.getenv("DJANGO_DB_ENGINE", "").lower()
USE_POSTGRES = DB_ENGINE == "postgresql" or os.getenv("DATABASE_URL", "").startswith("postgres")

if USE_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "ignite_buddy_db"),
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "root"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    raw_data_dir = os.getenv("ASSISTANT_DATA")
    if raw_data_dir:
        data_dir = Path(raw_data_dir).expanduser()
        if not data_dir.is_absolute():
            root_data = (BASE_DIR.parent.parent / data_dir).resolve()
            if root_data.exists():
                data_dir = root_data
            else:
                data_dir = (BASE_DIR.parent / data_dir).resolve()
    else:
        root_data = (BASE_DIR.parent.parent / "data").resolve()
        if (root_data / "ignite_buddy.sqlite3").exists() or root_data.exists():
            data_dir = root_data
        else:
            data_dir = (BASE_DIR.parent / "data").resolve()

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        data_dir = BASE_DIR.parent

    db_file = data_dir / "ignite_buddy.sqlite3"
    fallback_file = BASE_DIR.parent / "data" / "ignite_buddy.sqlite3"
    if not db_file.exists() and fallback_file.exists():
        db_file = fallback_file

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(db_file),
        }
    }

import sys

if "test" in sys.argv:
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("ASSISTANT_TIMEZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR.parent / "data" / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# REST Framework & JWT Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "server.api.auth.AdminTokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS & CSRF Configuration
cors_origins_env = os.getenv("DJANGO_CORS_ALLOWED_ORIGINS")
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8777",
        "http://127.0.0.1:8777",
    ]

csrf_origins_env = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS")
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins_env.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8777",
        "http://127.0.0.1:8777",
    ]

CORS_ALLOW_CREDENTIALS = True

# Production Security Headers
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() in ("true", "1")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").lower() in ("true", "1")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# Channels Layer
REDIS_URL = os.getenv("ASSISTANT_REDIS_URL")
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
