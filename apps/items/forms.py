from django import forms
from django.db.models import Q

from apps.terceros.models import Tercero, TerceroRol

from .models import (
    AlicuotaIVA,
    CategoriaItem,
    Item,
    ItemProveedor,
    Marca,
    UnidadMedida,
)


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

        bloqueo_relaciones = bool(
            self.item is not None
            and self.item.se_compra
            and not cleaned_data.get("se_compra")
            and self.item.relaciones_proveedores.filter(activo=True).exists()
        )
        if bloqueo_relaciones:
            self.add_error(
                "se_compra",
                "Primero inactivá las relaciones activas con proveedores.",
            )

        if (
            not cleaned_data.get("se_compra")
            and not cleaned_data.get("se_vende")
        ):
            mensaje = "Seleccioná al menos una capacidad: compra o venta."
            if not bloqueo_relaciones:
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

class ItemProveedorForm(forms.Form):
    proveedor = forms.ModelChoiceField(
        label="Proveedor",
        queryset=Tercero.objects.none(),
        empty_label="Seleccionar proveedor",
    )
    codigo_proveedor = forms.CharField(
        label="Código del proveedor",
        max_length=80,
        required=False,
        help_text="Código utilizado por el proveedor para identificar el ítem.",
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(
        self,
        *args,
        empresa,
        item,
        relacion=None,
        **kwargs,
    ):
        self.empresa = empresa
        self.item = item
        self.relacion = relacion
        datos = args[0] if args else kwargs.get("data")

        if relacion is not None:
            initial = kwargs.setdefault("initial", {})
            initial["proveedor"] = relacion.proveedor
            if datos is None:
                initial["codigo_proveedor"] = relacion.codigo_proveedor
                initial["observaciones"] = relacion.observaciones

        super().__init__(*args, **kwargs)

        if relacion is None:
            proveedores = (
                Tercero.objects.filter(
                    empresa=empresa,
                    activo=True,
                    roles__rol=TerceroRol.Rol.PROVEEDOR,
                    roles__activo=True,
                )
                .exclude(relaciones_items_proveedor__item=item)
                .distinct()
                .order_by("denominacion", "codigo")
            )
        else:
            proveedores = Tercero.objects.filter(
                pk=relacion.proveedor_id,
                empresa=empresa,
            )
            self.fields["proveedor"].disabled = True
            self.fields["proveedor"].help_text = (
                "El proveedor identifica la relación y no puede modificarse."
            )

        self.fields["proveedor"].queryset = proveedores
        aplicar_estilo(self)
