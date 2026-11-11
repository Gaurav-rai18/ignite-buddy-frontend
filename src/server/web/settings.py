import secrets
from server import config

SECRET_KEY = secrets.token_hex(32)        # nothing persisted depends on it (no sessions/cookies/DB)
DEBUG = config.DEBUG
ALLOWED_HOSTS = config.ALLOWED_HOSTS
INSTALLED_APPS = [
    "daphne",
    "channels",
    "rest_framework",
]
ROOT_URLCONF = "server.web.urls"
ASGI_APPLICATION = "server.web.asgi.application"
DATABASES = {}
USE_TZ = False
# Configure timezone for timestamps, daily recaps, and scheduling.
# Uses ASSISTANT_TIMEZONE (e.g. "Asia/Kolkata") when provided; falls back to "UTC"
# to satisfy Django's strict requirement for a valid timezone string identifier.
TIME_ZONE = config.TIMEZONE or "UTC"
if config.REDIS_URL:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer",
                                  "CONFIG": {"hosts": [config.REDIS_URL]}}}
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "server.api.auth.AdminTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}
