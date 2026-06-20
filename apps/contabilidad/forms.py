from django import forms
from django.core.exceptions import ValidationError

from .codigo_cuentas import CODIGO_CUENTA_REGEX
from .models import CuentaContable
from .services import crear_cuenta_contable


class CuentaContableCrearForm(forms.Form):
    codigo = forms.RegexField(
        label="Código",
        regex=CODIGO_CUENTA_REGEX,
        max_length=13,
        min_length=13,
        help_text="Máscara obligatoria: 9.9.99.99.999.",
        error_messages={
            "invalid": "El código debe respetar la máscara 9.9.99.99.999.",
        },
    )
    nombre = forms.CharField(
        label="Nombre",
        max_length=150,
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    tipo_contable = forms.ChoiceField(
        label="Tipo contable",
        choices=CuentaContable.TipoContable.choices,
    )
    naturaleza = forms.ChoiceField(
        label="Naturaleza",
        required=False,
        choices=(
            ("", "Sin naturaleza — cuenta agrupadora"),
            *CuentaContable.Naturaleza.choices,
        ),
        help_text=(
            "Es obligatoria solamente para cuentas imputables de nivel 5."
        ),
    )
    habilitada = forms.BooleanField(
        label="Habilitada",
        required=False,
        initial=True,
        help_text="Las cuentas habilitadas pueden utilizarse operativamente.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for nombre in ("codigo", "nombre", "descripcion"):
            self.fields[nombre].widget.attrs["class"] = "form-control"

        self.fields["codigo"].widget.attrs.update(
            {
                "placeholder": "1.1.01.01.001",
                "autocomplete": "off",
            }
        )
        self.fields["nombre"].widget.attrs["autocomplete"] = "off"

        for nombre in ("tipo_contable", "naturaleza"):
            self.fields[nombre].widget.attrs["class"] = "form-select"

        self.fields["habilitada"].widget.attrs["class"] = "form-check-input"

    def clean_codigo(self):
        return self.cleaned_data["codigo"].strip()

    def clean_nombre(self):
        return " ".join(self.cleaned_data["nombre"].split())

    def clean_descripcion(self):
        return self.cleaned_data["descripcion"].strip()

    def clean_naturaleza(self):
        return self.cleaned_data["naturaleza"] or None

    def clean(self):
        cleaned_data = super().clean()
        codigo = cleaned_data.get("codigo")
        naturaleza = cleaned_data.get("naturaleza")

        if not codigo:
            return cleaned_data

        nivel = CuentaContable.nivel_desde_codigo(codigo)

        if nivel is None:
            self.add_error(
                "codigo",
                (
                    "El código no puede informar niveles después de un "
                    "segmento en cero."
                ),
            )
        elif nivel == 5 and naturaleza is None:
            self.add_error(
                "naturaleza",
                "La naturaleza es obligatoria para una cuenta imputable.",
            )
        elif nivel != 5 and naturaleza is not None:
            self.add_error(
                "naturaleza",
                "Las cuentas agrupadoras no deben tener naturaleza.",
            )

        return cleaned_data

    def _incorporar_error_servicio(self, error):
        if hasattr(error, "message_dict"):
            errores = error.message_dict
        else:
            errores = {"__all__": error.messages}

        for campo, mensajes in errores.items():
            if campo in self.fields:
                destino = campo
            elif campo == "parent":
                destino = "codigo"
            else:
                destino = None

            for mensaje in mensajes:
                self.add_error(destino, mensaje)

    def crear(self, *, empresa):
        if not self.is_valid():
            raise RuntimeError(
                "No se puede crear una cuenta desde un formulario inválido."
            )

        try:
            return crear_cuenta_contable(
                empresa=empresa,
                codigo=self.cleaned_data["codigo"],
                nombre=self.cleaned_data["nombre"],
                descripcion=self.cleaned_data["descripcion"],
                tipo_contable=self.cleaned_data["tipo_contable"],
                naturaleza=self.cleaned_data["naturaleza"],
                habilitada=self.cleaned_data["habilitada"],
            )
        except ValidationError as error:
            self._incorporar_error_servicio(error)
            return None
