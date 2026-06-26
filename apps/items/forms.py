from django import forms
from django.db.models import Q

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida


def aplicar_estilo(form):
    for campo in form.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        elif isinstance(campo.widget, forms.Select):
            campo.widget.attrs["class"] = "form-select"
        else:
            campo.widget.attrs["class"] = "form-control"


class CategoriaItemForm(forms.Form):
    codigo = forms.CharField(label="Código", max_length=30)
    nombre = forms.CharField(label="Nombre", max_length=160)
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, categoria=None, **kwargs):
        self.categoria = categoria
        datos = args[0] if args else kwargs.get("data")
        if categoria is not None:
            initial = kwargs.setdefault("initial", {})
            initial["codigo"] = categoria.codigo
            if datos is None:
                initial.update(
                    {
                        "nombre": categoria.nombre,
                        "descripcion": categoria.descripcion,
                    }
                )

        super().__init__(*args, **kwargs)
        if categoria is not None:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "El código identifica la categoría y no puede modificarse."
            )
        aplicar_estilo(self)


class MarcaForm(forms.Form):
    codigo = forms.CharField(label="Código", max_length=30)
    nombre = forms.CharField(label="Nombre", max_length=160)

    def __init__(self, *args, marca=None, **kwargs):
        self.marca = marca
        datos = args[0] if args else kwargs.get("data")
        if marca is not None:
            initial = kwargs.setdefault("initial", {})
            initial["codigo"] = marca.codigo
            if datos is None:
                initial["nombre"] = marca.nombre

        super().__init__(*args, **kwargs)
        if marca is not None:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "El código identifica la marca y no puede modificarse."
            )
        aplicar_estilo(self)


class ItemForm(forms.Form):
    codigo = forms.CharField(
        label="Código interno",
        max_length=30,
        help_text=(
            "Obligatorio, único dentro de la empresa y no modificable "
            "después del alta."
        ),
    )
    nombre = forms.CharField(label="Nombre", max_length=200)
    descripcion = forms.CharField(
        label="Descripción ampliada",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=Item.Tipo.choices,
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=CategoriaItem.objects.none(),
        required=False,
        empty_label="Sin categoría",
    )
    marca = forms.ModelChoiceField(
        label="Marca",
        queryset=Marca.objects.none(),
        required=False,
        empty_label="Sin marca",
    )
    unidad_medida = forms.ModelChoiceField(
        label="Unidad de medida base",
        queryset=UnidadMedida.objects.none(),
    )
    se_compra = forms.BooleanField(label="Se compra", required=False)
    se_vende = forms.BooleanField(label="Se vende", required=False)
    controla_stock = forms.BooleanField(
        label="Controla stock",
        required=False,
        help_text="Solo puede activarse para productos.",
    )
    tratamiento_iva = forms.ChoiceField(
        label="Tratamiento de IVA",
        choices=Item.TratamientoIVA.choices,
    )
    alicuota_iva = forms.ModelChoiceField(
        label="Alícuota de IVA",
        queryset=AlicuotaIVA.objects.none(),
        required=False,
        empty_label="Seleccionar alícuota",
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, empresa, item=None, **kwargs):
        self.empresa = empresa
        self.item = item
        datos = args[0] if args else kwargs.get("data")

        if item is not None:
            initial = kwargs.setdefault("initial", {})
            initial["codigo"] = item.codigo
            if datos is None:
                for nombre in self.base_fields:
                    initial[nombre] = getattr(item, nombre)

        super().__init__(*args, **kwargs)

        categorias = CategoriaItem.objects.filter(
            empresa=empresa,
            activo=True,
        )
        marcas = Marca.objects.filter(
            empresa=empresa,
            activo=True,
        )
        unidades = UnidadMedida.objects.filter(activo=True)
        alicuotas = AlicuotaIVA.objects.filter(activo=True)

        if item is not None:
            if item.categoria_id:
                categorias = CategoriaItem.objects.filter(
                    Q(empresa=empresa, activo=True)
                    | Q(pk=item.categoria_id, empresa=empresa)
                )
            if item.marca_id:
                marcas = Marca.objects.filter(
                    Q(empresa=empresa, activo=True)
                    | Q(pk=item.marca_id, empresa=empresa)
                )
            unidades = UnidadMedida.objects.filter(
                Q(activo=True) | Q(pk=item.unidad_medida_id)
            )
            if item.alicuota_iva_id:
                alicuotas = AlicuotaIVA.objects.filter(
                    Q(activo=True) | Q(pk=item.alicuota_iva_id)
                )

            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "El código interno del ítem no puede modificarse."
            )

        self.fields["categoria"].queryset = categorias.order_by("nombre", "codigo")
        self.fields["marca"].queryset = marcas.order_by("nombre", "codigo")
        self.fields["unidad_medida"].queryset = unidades.order_by("nombre", "codigo")
        self.fields["alicuota_iva"].queryset = alicuotas.order_by(
            "porcentaje",
            "nombre",
        )
        aplicar_estilo(self)

    def clean(self):
        cleaned_data = super().clean()

        if (
            not cleaned_data.get("se_compra")
            and not cleaned_data.get("se_vende")
        ):
            mensaje = "Seleccioná al menos una capacidad: compra o venta."
            self.add_error("se_compra", mensaje)
            self.add_error("se_vende", mensaje)

        if (
            cleaned_data.get("tipo") == Item.Tipo.SERVICIO
            and cleaned_data.get("controla_stock")
        ):
            self.add_error(
                "controla_stock",
                "Un servicio no puede controlar stock.",
            )

        tratamiento = cleaned_data.get("tratamiento_iva")
        alicuota = cleaned_data.get("alicuota_iva")
        if tratamiento == Item.TratamientoIVA.GRAVADO and alicuota is None:
            self.add_error(
                "alicuota_iva",
                "Un ítem gravado requiere alícuota de IVA.",
            )
        elif tratamiento and tratamiento != Item.TratamientoIVA.GRAVADO and alicuota:
            self.add_error(
                "alicuota_iva",
                "Los ítems exentos o no gravados no llevan alícuota.",
            )

        return cleaned_data
