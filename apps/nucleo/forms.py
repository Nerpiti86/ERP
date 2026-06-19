from django import forms


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
