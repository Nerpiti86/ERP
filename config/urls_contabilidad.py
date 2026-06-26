from django.contrib import admin
from django.urls import include, path

from apps.core.estado_aplicacion import estado_aplicacion


urlpatterns = [
    path("_estado/", estado_aplicacion, name="estado_aplicacion"),
    path("admin/", admin.site.urls),
    path("nucleo/", include("apps.nucleo.urls")),
    path("contabilidad/", include("apps.contabilidad.urls")),
    path("", include("apps.core.urls")),
]
