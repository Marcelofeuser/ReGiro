import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("REGIRO_DEBUG") == "1"
SECRET_KEY = os.getenv("REGIRO_SECRET_KEY") or ("local-development-only" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("Configure REGIRO_SECRET_KEY ou use REGIRO_DEBUG=1 localmente.")
allowed_hosts = os.getenv("REGIRO_HOSTS", "localhost,127.0.0.1").split(",")
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_domain:
    allowed_hosts.append(railway_domain)
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts if host.strip()]
csrf_origins = os.getenv("REGIRO_CSRF_TRUSTED_ORIGINS", "").split(",")
if railway_domain:
    csrf_origins.append(f"https://{railway_domain}")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins if origin.strip()]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "market",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "market.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "market.context.branding",
    ]},
}]
database_url = os.getenv("DATABASE_URL")
if database_url:
    database = dj_database_url.parse(database_url, conn_health_checks=True)
    if database["ENGINE"] != "django.db.backends.postgresql":
        raise RuntimeError("DATABASE_URL deve apontar para um banco PostgreSQL.")
    database["OPTIONS"].setdefault("sslmode", "require")
    database["DISABLE_SERVER_SIDE_CURSORS"] = True
elif DEBUG:
    database = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "regiro.sqlite3",
        "OPTIONS": {"transaction_mode": "IMMEDIATE"},
    }
else:
    raise RuntimeError("Configure DATABASE_URL para executar fora do modo local.")
DATABASES = {"default": database}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"django.contrib.auth.password_validation.{name}"}
    for name in ("UserAttributeSimilarityValidator", "MinimumLengthValidator",
                 "CommonPasswordValidator", "NumericPasswordValidator")
]
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "catalog"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
