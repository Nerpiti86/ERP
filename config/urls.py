from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("nucleo/", include("apps.nucleo.urls")),
    path("contabilidad/", include("apps.contabilidad.urls")),
    path("", include("apps.core.urls")),
]
