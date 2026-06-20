from django.urls import path

from . import views


app_name = "contabilidad"

urlpatterns = [
    path(
        "plan-de-cuentas/",
        views.plan_cuentas,
        name="plan_cuentas",
    ),
    path(
        "plan-de-cuentas/nueva/",
        views.crear_cuenta,
        name="crear_cuenta",
    ),
]
