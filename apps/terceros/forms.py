from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import (
    CondicionIVA,
    ContactoTercero,
    DomicilioTercero,
    Tercero,
    TerceroRol,
    TipoDocumento,
)


def aplicar_estilo(form):
    for campo in form.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        elif isinstance(campo.widget, forms.Select):
            campo.widget.attrs["class"] = "form-select"
        else:
            campo.widget.attrs["class"] = "form-control"


class TerceroForm(forms.Form):
    codigo = forms.CharField(
        label="Código interno",
        max_length=30,
        required=False,
        help_text="Opcional al crear. Si queda vacío se genera automáticamente.",
    )
    tipo_persona = forms.ChoiceField(
        label="Tipo de persona",
        choices=Tercero.TipoPersona.choices,
    )
    tipo_documento = forms.ModelChoiceField(
        label="Tipo de documento",
        queryset=TipoDocumento.objects.none(),
    )
    numero_documento = forms.CharField(
        label="Número de documento",
        max_length=30,
        required=False,
        help_text="Podés ingresarlo con o sin guiones.",
    )
    denominacion = forms.CharField(
        label="Razón social, apellido y nombre o denominación",
        max_length=200,
    )
    nombre_fantasia = forms.CharField(
        label="Nombre de fantasía",
        max_length=200,
        required=False,
    )
    condicion_iva = forms.ModelChoiceField(
        label="Condición frente al IVA",
        queryset=CondicionIVA.objects.none(),
    )
    telefono = forms.CharField(
        label="Teléfono general",
        max_length=60,
        required=False,
    )
    email = forms.EmailField(
        label="Correo general",
        max_length=180,
        required=False,
    )
    sitio_web = forms.URLField(
        label="Sitio web",
        max_length=300,
        required=False,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        initial=timezone.localdate,
    )
    es_cliente = forms.BooleanField(label="Cliente", required=False)
    es_proveedor = forms.BooleanField(label="Proveedor", required=False)
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, empresa, tercero=None, **kwargs):
        self.empresa = empresa
        self.tercero = tercero

        datos_recibidos = args[0] if args else kwargs.get("data")

        if tercero is not None and datos_recibidos is None:
            initial = kwargs.setdefault("initial", {})
            initial.update(
                {
                    "codigo": tercero.codigo,
                    "tipo_persona": tercero.tipo_persona,
                    "tipo_documento": tercero.tipo_documento,
                    "numero_documento": tercero.numero_documento,
                    "denominacion": tercero.denominacion,
                    "nombre_fantasia": tercero.nombre_fantasia,
                    "condicion_iva": tercero.condicion_iva,
                    "telefono": tercero.telefono,
                    "email": tercero.email,
                    "sitio_web": tercero.sitio_web,
                    "fecha_alta": tercero.fecha_alta,
                    "es_cliente": tercero.es_cliente,
                    "es_proveedor": tercero.es_proveedor,
                    "observaciones": tercero.observaciones,
                }
            )

        super().__init__(*args, **kwargs)

        tipos = TipoDocumento.objects.filter(activo=True)
        condiciones = CondicionIVA.objects.filter(activo=True)

        if tercero is not None:
            tipos = TipoDocumento.objects.filter(
                Q(activo=True) | Q(pk=tercero.tipo_documento_id)
            )
            condiciones = CondicionIVA.objects.filter(
                Q(activo=True) | Q(pk=tercero.condicion_iva_id)
            )
            self.fields["codigo"].disabled = True
            self.fields["codigo"].initial = tercero.codigo
            self.fields["codigo"].help_text = (
                "Código interno del tercero. No puede modificarse."
            )

        self.fields["tipo_documento"].queryset = tipos.order_by(
            "codigo_arca",
            "nombre",
        )
        self.fields["condicion_iva"].queryset = condiciones.order_by(
            "codigo_arca",
            "nombre",
        )
        aplicar_estilo(self)

    def clean(self):
        cleaned_data = super().clean()

        if (
            not cleaned_data.get("es_cliente")
            and not cleaned_data.get("es_proveedor")
        ):
            mensaje = "Seleccioná al menos un rol: cliente o proveedor."
            self.add_error("es_cliente", mensaje)
            self.add_error("es_proveedor", mensaje)

        return cleaned_data

    @property
    def roles_seleccionados(self):
        roles = set()
        if self.cleaned_data.get("es_cliente"):
            roles.add(TerceroRol.Rol.CLIENTE)
        if self.cleaned_data.get("es_proveedor"):
            roles.add(TerceroRol.Rol.PROVEEDOR)
        return roles


class DomicilioTerceroForm(forms.Form):
    tipo = forms.ChoiceField(
        label="Tipo de domicilio",
        choices=DomicilioTercero.Tipo.choices,
    )
    nombre = forms.CharField(
        label="Referencia o nombre",
        max_length=120,
        required=False,
    )
    calle = forms.CharField(label="Calle", max_length=160)
    numero = forms.CharField(label="Número", max_length=30, required=False)
    sector = forms.CharField(label="Sector", max_length=80, required=False)
    torre = forms.CharField(label="Torre", max_length=50, required=False)
    piso = forms.CharField(label="Piso", max_length=30, required=False)
    departamento = forms.CharField(
        label="Departamento",
        max_length=30,
        required=False,
    )
    barrio = forms.CharField(label="Barrio", max_length=120, required=False)
    localidad = forms.CharField(label="Localidad", max_length=120)
    codigo_postal = forms.CharField(
        label="Código postal",
        max_length=20,
        required=False,
    )
    partido_departamento = forms.CharField(
        label="Partido o departamento",
        max_length=120,
        required=False,
    )
    provincia = forms.CharField(
        label="Provincia",
        max_length=120,
        initial="Santa Fe",
    )
    pais = forms.CharField(
        label="País",
        max_length=120,
        initial="Argentina",
    )
    principal = forms.BooleanField(
        label="Principal para este tipo",
        required=False,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        initial=timezone.localdate,
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, domicilio=None, **kwargs):
        self.domicilio = domicilio
        if domicilio is not None and not args and "data" not in kwargs:
            initial = kwargs.setdefault("initial", {})
            for nombre in self.base_fields:
                initial[nombre] = getattr(domicilio, nombre)

        super().__init__(*args, **kwargs)
        aplicar_estilo(self)


class ContactoTerceroForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=150)
    cargo = forms.CharField(label="Cargo", max_length=120, required=False)
    area = forms.CharField(label="Área", max_length=120, required=False)
    telefono = forms.CharField(
        label="Teléfono",
        max_length=60,
        required=False,
    )
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=180,
        required=False,
    )
    principal = forms.BooleanField(
        label="Contacto principal",
        required=False,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        initial=timezone.localdate,
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, contacto=None, **kwargs):
        self.contacto = contacto
        if contacto is not None and not args and "data" not in kwargs:
            initial = kwargs.setdefault("initial", {})
            for nombre in self.base_fields:
                initial[nombre] = getattr(contacto, nombre)

        super().__init__(*args, **kwargs)
        aplicar_estilo(self)

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("telefono") and not cleaned_data.get("email"):
            mensaje = "Informá al menos un teléfono o un correo electrónico."
            self.add_error("telefono", mensaje)
            self.add_error("email", mensaje)

        return cleaned_data
