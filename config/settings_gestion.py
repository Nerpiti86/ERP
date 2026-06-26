from .settings import *  # noqa: F401,F403


ERP_APP_MODE = "gestion"
ROOT_URLCONF = "config.urls_gestion"
SESSION_COOKIE_NAME = "erp_gestion_sessionid"
CSRF_COOKIE_NAME = "erp_gestion_csrftoken"
