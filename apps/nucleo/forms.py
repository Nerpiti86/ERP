from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Empresa, PerfilFiscalEmpresa


class ConfiguracionEmpresaForm(forms.Form):
    moneda_funcional = forms.RegexField(
        label="Moneda funcional",
        regex=r"^[A-Za-z]{3}$",
        max_length=3,
        min_length=3,
        help_text="Código de tres letras. Ejemplo: ARS.",
        error_messages={
            "invalid": "Ingresá una moneda de tres letras, por ejemplo ARS.",
        },
    )
    punto_venta_default = forms.RegexField(
        label="Punto de venta predeterminado",
        regex=r"^\d{4}$",
        max_length=4,
        min_length=4,
        help_text="Cuatro dígitos. Ejemplo: 0001.",
        error_messages={
            "invalid": "Ingresá cuatro dígitos, por ejemplo 0001.",
        },
    )
    modo_numeracion_comprobantes = forms.ChoiceField(
        label="Numeración de comprobantes internos",
        choices=(
            ("automatico", "Automática"),
            ("manual", "Manual"),
        ),
        help_text=(
            "Esta opción organiza comprobantes internos y no configura "
            "facturación electrónica ARCA/AFIP."
        ),
    )
    permite_stock_negativo = forms.BooleanField(
        label="Permitir stock negativo",
        required=False,
    )
    usa_centros_costo = forms.BooleanField(
        label="Usar centros de costo",
        required=False,
    )
    usa_proyectos = forms.BooleanField(
        label="Usar proyectos",
        required=False,
    )
    requiere_aprobacion_compras = forms.BooleanField(
        label="Requerir aprobación de compras",
        required=False,
    )
    requiere_aprobacion_pagos = forms.BooleanField(
        label="Requerir aprobación de pagos",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for nombre in (
            "moneda_funcional",
            "punto_venta_default",
        ):
            self.fields[nombre].widget.attrs["class"] = "form-control"

        self.fields[
            "modo_numeracion_comprobantes"
        ].widget.attrs["class"] = "form-select"

        for nombre in (
            "permite_stock_negativo",
            "usa_centros_costo",
            "usa_proyectos",
            "requiere_aprobacion_compras",
            "requiere_aprobacion_pagos",
        ):
            self.fields[nombre].widget.attrs["class"] = "form-check-input"

    def clean_moneda_funcional(self):
        return self.cleaned_data["moneda_funcional"].upper()


class DatosContribuyenteForm(forms.Form):
    cuit = forms.RegexField(
        label="CUIT",
        regex=r"^\d{11}$",
        max_length=11,
        min_length=11,
        help_text="Ingresá 11 dígitos sin guiones.",
        error_messages={
            "invalid": "El CUIT debe contener 11 dígitos sin guiones.",
        },
    )
    razon_social = forms.CharField(
        label="Razón social o apellido y nombre",
        max_length=200,
    )
    nombre_corto = forms.CharField(
        label="Nombre corto para listados",
        max_length=200,
    )
    naturaleza = forms.ChoiceField(
        label="Naturaleza del contribuyente",
        choices=PerfilFiscalEmpresa.NaturalezaContribuyente.choices,
    )
    condicion_iva = forms.ChoiceField(
        label="Condición frente al IVA",
        choices=Empresa.CondicionIVA.choices,
    )
    fecha_inicio_actividades = forms.DateField(
        label="Inicio de actividades",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    mes_cierre_ejercicio_predeterminado = forms.ChoiceField(
        label="Mes de cierre del ejercicio",
        choices=PerfilFiscalEmpresa.MESES_CIERRE,
        help_text=(
            "Se usa como propuesta para nuevos ejercicios. "
            "No modifica ejercicios ya creados."
        ),
    )
    activa = forms.BooleanField(
        label="Empresa activa",
        required=False,
    )
    apellido = forms.CharField(
        label="Apellido",
        max_length=120,
        required=False,
    )
    apellido_materno = forms.CharField(
        label="Apellido materno",
        max_length=120,
        required=False,
    )
    nombres = forms.CharField(
        label="Nombres",
        max_length=160,
        required=False,
    )
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    def __init__(
        self,
        *args,
        empresa,
        perfil=None,
        **kwargs,
    ):
        self.empresa = empresa
        self.perfil = perfil

        if not args and "data" not in kwargs:
            initial = kwargs.setdefault("initial", {})
            initial.setdefault("cuit", empresa.cuit)
            initial.setdefault("razon_social", empresa.razon_social)
            initial.setdefault(
                "nombre_corto",
                empresa.nombre_fantasia,
            )
            initial.setdefault("condicion_iva", empresa.condicion_iva)
            initial.setdefault("activa", empresa.activa)

            if perfil is not None:
                initial.setdefault("naturaleza", perfil.naturaleza)
                initial.setdefault(
                    "fecha_inicio_actividades",
                    perfil.fecha_inicio_actividades,
                )
                initial.setdefault(
                    "mes_cierre_ejercicio_predeterminado",
                    perfil.mes_cierre_ejercicio_predeterminado,
                )
                initial.setdefault("apellido", perfil.apellido)
                initial.setdefault(
                    "apellido_materno",
                    perfil.apellido_materno,
                )
                initial.setdefault("nombres", perfil.nombres)
                initial.setdefault(
                    "fecha_nacimiento",
                    perfil.fecha_nacimiento,
                )

        super().__init__(*args, **kwargs)

        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

    def clean_cuit(self):
        cuit = self.cleaned_data["cuit"]

        existe = (
            Empresa.objects.exclude(pk=self.empresa.pk)
            .filter(cuit=cuit)
            .exists()
        )

        if existe:
            raise ValidationError(
                "Ya existe otra empresa con este CUIT."
            )

        return cuit

    def clean_mes_cierre_ejercicio_predeterminado(self):
        return int(
            self.cleaned_data[
                "mes_cierre_ejercicio_predeterminado"
            ]
        )

    def clean(self):
        cleaned_data = super().clean()
        naturaleza = cleaned_data.get("naturaleza")

        naturaleza_personal = {
            PerfilFiscalEmpresa.NaturalezaContribuyente.PERSONA_HUMANA,
            PerfilFiscalEmpresa.NaturalezaContribuyente.SUCESION_INDIVISA,
        }

        if naturaleza in naturaleza_personal:
            if not (cleaned_data.get("apellido") or "").strip():
                self.add_error(
                    "apellido",
                    "El apellido es obligatorio para esta naturaleza.",
                )

            if not (cleaned_data.get("nombres") or "").strip():
                self.add_error(
                    "nombres",
                    "Los nombres son obligatorios para esta naturaleza.",
                )

            if cleaned_data.get("fecha_nacimiento") is None:
                self.add_error(
                    "fecha_nacimiento",
                    (
                        "La fecha de nacimiento es obligatoria "
                        "para esta naturaleza."
                    ),
                )
        elif naturaleza:
            cleaned_data["apellido"] = ""
            cleaned_data["apellido_materno"] = ""
            cleaned_data["nombres"] = ""
            cleaned_data["fecha_nacimiento"] = None

        return cleaned_data

    @transaction.atomic
    def save(self):
        if not self.is_valid():
            raise ValueError(
                "No se puede guardar un formulario inválido."
            )

        datos = self.cleaned_data

        self.empresa.cuit = datos["cuit"]
        self.empresa.razon_social = datos["razon_social"].strip()
        self.empresa.nombre_fantasia = datos["nombre_corto"].strip()
        self.empresa.condicion_iva = datos["condicion_iva"]
        self.empresa.activa = datos["activa"]
        self.empresa.full_clean()
        self.empresa.save()

        perfil, _ = PerfilFiscalEmpresa.objects.get_or_create(
            empresa=self.empresa
        )
        perfil.naturaleza = datos["naturaleza"]
        perfil.fecha_inicio_actividades = datos[
            "fecha_inicio_actividades"
        ]
        perfil.mes_cierre_ejercicio_predeterminado = datos[
            "mes_cierre_ejercicio_predeterminado"
        ]
        perfil.apellido = (datos.get("apellido") or "").strip()
        perfil.apellido_materno = (
            datos.get("apellido_materno") or ""
        ).strip()
        perfil.nombres = (datos.get("nombres") or "").strip()
        perfil.fecha_nacimiento = datos.get("fecha_nacimiento")
        perfil.full_clean()
        perfil.save()

        self.perfil = perfil
        return self.empresa, perfil
