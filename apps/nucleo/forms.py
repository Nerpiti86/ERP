from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    ActividadEconomica,
    ConfiguracionIIBBEmpresa,
    Empresa,
    EmpresaActividad,
    EmpresaJurisdiccionIIBB,
    JurisdiccionFiscal,
    PerfilFiscalEmpresa,
    PuntoVenta,
    Sucursal,
)


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

        self.fields[
            "moneda_funcional"
        ].widget.attrs["class"] = "form-control"

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


class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = (
            "codigo",
            "nombre",
            "calle",
            "numero",
            "sector",
            "torre",
            "piso",
            "departamento",
            "barrio",
            "localidad",
            "codigo_postal",
            "partido_departamento",
            "provincia",
            "pais",
            "es_casa_central",
            "es_domicilio_fiscal_nacional",
            "es_domicilio_fiscal_provincial",
            "es_domicilio_legal",
            "es_principal_actividades",
            "es_deposito",
            "es_local_comercial",
            "es_oficina_administrativa",
            "otras_funciones",
            "activa",
        )
        labels = {
            "codigo": "Código",
            "nombre": "Nombre",
            "calle": "Calle",
            "numero": "Número",
            "sector": "Sector",
            "torre": "Torre",
            "piso": "Piso",
            "departamento": "Departamento",
            "barrio": "Barrio",
            "localidad": "Localidad",
            "codigo_postal": "Código postal",
            "partido_departamento": "Partido o departamento",
            "provincia": "Provincia",
            "pais": "País",
            "es_casa_central": "Casa central",
            "es_domicilio_fiscal_nacional": (
                "Domicilio fiscal nacional"
            ),
            "es_domicilio_fiscal_provincial": (
                "Domicilio fiscal provincial"
            ),
            "es_domicilio_legal": "Domicilio legal",
            "es_principal_actividades": (
                "Principal lugar de actividades"
            ),
            "es_deposito": "Depósito",
            "es_local_comercial": "Local comercial",
            "es_oficina_administrativa": (
                "Oficina administrativa"
            ),
            "otras_funciones": "Otras funciones",
            "activa": "Sucursal activa",
        }

    CAMPOS_DOMICILIO_OBLIGATORIOS = (
        "calle",
        "numero",
        "localidad",
        "codigo_postal",
        "provincia",
        "pais",
    )

    def __init__(self, *args, empresa, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.empresa_id != empresa.pk:
            raise ValueError(
                "La sucursal no pertenece a la empresa activa."
            )

        self.instance.empresa = empresa

        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

        for nombre in self.CAMPOS_DOMICILIO_OBLIGATORIOS:
            self.fields[nombre].required = True

        self.fields["codigo"].help_text = (
            "Mayúsculas, números, guion o guion bajo."
        )
        self.fields["otras_funciones"].help_text = (
            "Texto breve para funciones que no estén en la lista."
        )

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()

        duplicada = Sucursal.objects.filter(
            empresa=self.empresa,
            codigo=codigo,
        )

        if self.instance.pk:
            duplicada = duplicada.exclude(pk=self.instance.pk)

        if duplicada.exists():
            raise ValidationError(
                "Ya existe una sucursal con este código en la empresa."
            )

        return codigo

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("activa"):
            for campo, etiqueta in Sucursal.FUNCIONES_EXCLUSIVAS:
                if not cleaned_data.get(campo):
                    continue

                duplicada = Sucursal.objects.filter(
                    empresa=self.empresa,
                    activa=True,
                    **{campo: True},
                )

                if self.instance.pk:
                    duplicada = duplicada.exclude(pk=self.instance.pk)

                if duplicada.exists():
                    self.add_error(
                        campo,
                        (
                            "Ya existe otra sucursal activa marcada "
                            f"como {etiqueta.lower()}."
                        ),
                    )

        if (
            self.instance.pk
            and self.instance.activa
            and not cleaned_data.get("activa")
            and PuntoVenta.objects.filter(
                sucursal=self.instance,
                activo=True,
            ).exists()
        ):
            self.add_error(
                "activa",
                (
                    "Inactivá o reasigná los puntos de venta activos "
                    "antes de inactivar la sucursal."
                ),
            )

        return cleaned_data

    def save(self, commit=True):
        sucursal = super().save(commit=False)
        sucursal.empresa = self.empresa
        sucursal.full_clean()

        if commit:
            sucursal.save()

        return sucursal


class EmpresaActividadCrearForm(forms.Form):
    actividad_id = forms.IntegerField(
        widget=forms.HiddenInput(),
    )
    actividad_texto = forms.CharField(
        label="Actividad económica",
        max_length=500,
        help_text=(
            "Buscá por código o descripción y seleccioná "
            "una actividad del catálogo oficial."
        ),
    )
    principal = forms.BooleanField(
        label="Actividad principal",
        required=False,
    )
    orden = forms.IntegerField(
        label="Orden de visualización",
        min_value=0,
        initial=0,
    )
    vigencia_desde = forms.DateField(
        label="Vigencia desde",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    vigencia_hasta = forms.DateField(
        label="Vigencia hasta",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, empresa, **kwargs):
        self.empresa = empresa
        self.actividad = None
        super().__init__(*args, **kwargs)

        _estilizar_formulario_actividad(self)

        if not empresa.actividades_economicas.filter(
            activa=True
        ).exists():
            self.fields["principal"].initial = True

    def clean_actividad_id(self):
        actividad_id = self.cleaned_data["actividad_id"]

        actividad = ActividadEconomica.objects.filter(
            pk=actividad_id,
            nomenclador=(
                ActividadEconomica.Nomenclador.ARCA_CLAE
            ),
            activa=True,
        ).first()

        if actividad is None:
            raise ValidationError(
                "Seleccioná una actividad activa del catálogo oficial."
            )

        if EmpresaActividad.objects.filter(
            empresa=self.empresa,
            actividad=actividad,
            activa=True,
        ).exists():
            raise ValidationError(
                "La empresa ya tiene esta actividad activa."
            )

        self.actividad = actividad
        return actividad_id

    def clean(self):
        cleaned_data = super().clean()
        _validar_vigencias_formulario(self, cleaned_data)
        return cleaned_data


class EmpresaActividadEditarForm(forms.Form):
    principal = forms.BooleanField(
        label="Actividad principal",
        required=False,
    )
    orden = forms.IntegerField(
        label="Orden de visualización",
        min_value=0,
    )
    vigencia_desde = forms.DateField(
        label="Vigencia desde",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    vigencia_hasta = forms.DateField(
        label="Vigencia hasta",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
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
        empresa_actividad,
        **kwargs,
    ):
        self.empresa = empresa
        self.empresa_actividad = empresa_actividad

        if empresa_actividad.empresa_id != empresa.pk:
            raise ValueError(
                "La actividad no pertenece a la empresa activa."
            )

        if not empresa_actividad.activa:
            raise ValueError(
                "Una relación histórica inactiva no puede editarse."
            )

        if not args and "data" not in kwargs:
            initial = kwargs.setdefault("initial", {})
            initial.setdefault(
                "principal",
                empresa_actividad.principal,
            )
            initial.setdefault("orden", empresa_actividad.orden)
            initial.setdefault(
                "vigencia_desde",
                empresa_actividad.vigencia_desde,
            )
            initial.setdefault(
                "vigencia_hasta",
                empresa_actividad.vigencia_hasta,
            )
            initial.setdefault(
                "observaciones",
                empresa_actividad.observaciones,
            )

        super().__init__(*args, **kwargs)
        _estilizar_formulario_actividad(self)

    def clean(self):
        cleaned_data = super().clean()
        _validar_vigencias_formulario(self, cleaned_data)
        return cleaned_data


def _estilizar_formulario_actividad(form):
    for campo in form.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        elif isinstance(campo.widget, forms.HiddenInput):
            continue
        else:
            campo.widget.attrs["class"] = "form-control"

    if "actividad_texto" in form.fields:
        form.fields["actividad_texto"].widget.attrs.update(
            {
                "autocomplete": "off",
                "placeholder": "Código o descripción",
            }
        )


def _validar_vigencias_formulario(form, cleaned_data):
    vigencia_desde = cleaned_data.get("vigencia_desde")
    vigencia_hasta = cleaned_data.get("vigencia_hasta")

    if vigencia_hasta is None:
        return

    if vigencia_desde is None:
        form.add_error(
            "vigencia_desde",
            (
                "Informá la vigencia desde cuando existe "
                "una vigencia hasta."
            ),
        )
    elif vigencia_hasta < vigencia_desde:
        form.add_error(
            "vigencia_hasta",
            (
                "La vigencia hasta no puede ser anterior "
                "a la vigencia desde."
            ),
        )

class _PuntoVentaBaseForm(forms.Form):
    sucursal = forms.ModelChoiceField(
        label="Sucursal asociada",
        queryset=Sucursal.objects.none(),
        help_text=(
            "El domicilio del punto de venta se obtiene de esta sucursal."
        ),
    )
    nombre_fantasia = forms.CharField(
        label="Nombre de fantasía",
        max_length=200,
        required=False,
    )
    sistema_emision = forms.ChoiceField(
        label="Sistema de emisión",
        choices=PuntoVenta.SistemaEmision.choices,
    )
    descripcion_sistema_arca = forms.CharField(
        label="Descripción observada en ARCA",
        max_length=200,
        required=False,
        help_text=(
            "Opcional. Conservá aquí la denominación exacta mostrada por ARCA."
        ),
    )
    actividad_predeterminada = forms.ModelChoiceField(
        label="Actividad económica predeterminada",
        queryset=EmpresaActividad.objects.none(),
        required=False,
    )
    jurisdiccion_iibb_predeterminada = forms.ModelChoiceField(
        label="Jurisdicción de IIBB predeterminada",
        queryset=EmpresaJurisdiccionIIBB.objects.none(),
        required=False,
    )
    predeterminado = forms.BooleanField(
        label="Punto de venta predeterminado para la sucursal",
        required=False,
    )
    bloqueado = forms.BooleanField(
        label="Bloqueado en ARCA",
        required=False,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
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
        punto_venta=None,
        **kwargs,
    ):
        self.empresa = empresa
        self.punto_venta = punto_venta

        if punto_venta is not None:
            if punto_venta.empresa_id != empresa.pk:
                raise ValueError(
                    "El punto de venta no pertenece a la empresa activa."
                )
            if not punto_venta.activo:
                raise ValueError(
                    "Un punto de venta histórico inactivo no puede editarse."
                )

            if not args and "data" not in kwargs:
                initial = kwargs.setdefault("initial", {})
                initial.setdefault("sucursal", punto_venta.sucursal)
                initial.setdefault(
                    "nombre_fantasia",
                    punto_venta.nombre_fantasia,
                )
                initial.setdefault(
                    "sistema_emision",
                    punto_venta.sistema_emision,
                )
                initial.setdefault(
                    "descripcion_sistema_arca",
                    punto_venta.descripcion_sistema_arca,
                )
                initial.setdefault(
                    "actividad_predeterminada",
                    punto_venta.actividad_predeterminada,
                )
                initial.setdefault(
                    "jurisdiccion_iibb_predeterminada",
                    punto_venta.jurisdiccion_iibb_predeterminada,
                )
                initial.setdefault(
                    "predeterminado",
                    punto_venta.predeterminado,
                )
                initial.setdefault("bloqueado", punto_venta.bloqueado)
                initial.setdefault("fecha_alta", punto_venta.fecha_alta)
                initial.setdefault(
                    "observaciones",
                    punto_venta.observaciones,
                )

        super().__init__(*args, **kwargs)

        sucursales = Sucursal.objects.filter(
            empresa=empresa,
            activa=True,
        )
        actividades = EmpresaActividad.objects.filter(
            empresa=empresa,
            activa=True,
        ).select_related("actividad")
        jurisdicciones = (
            EmpresaJurisdiccionIIBB.objects.filter(
                configuracion__empresa=empresa,
                configuracion__activa=True,
                activa=True,
            )
            .select_related(
                "configuracion",
                "jurisdiccion",
            )
            .order_by(
                "-sede",
                "jurisdiccion__orden",
                "codigo_registrado",
            )
        )

        self.fields["sucursal"].queryset = sucursales.order_by(
            "codigo",
            "nombre",
        )
        self.fields[
            "actividad_predeterminada"
        ].queryset = actividades.order_by(
            "-principal",
            "orden",
            "codigo_registrado",
        )
        self.fields[
            "jurisdiccion_iibb_predeterminada"
        ].queryset = jurisdicciones

        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        sucursal = cleaned_data.get("sucursal")
        actividad = cleaned_data.get("actividad_predeterminada")
        jurisdiccion = cleaned_data.get(
            "jurisdiccion_iibb_predeterminada"
        )

        if sucursal is not None:
            if sucursal.empresa_id != self.empresa.pk:
                self.add_error(
                    "sucursal",
                    "La sucursal no pertenece a la empresa activa.",
                )
            elif not sucursal.activa:
                self.add_error(
                    "sucursal",
                    "Seleccioná una sucursal activa.",
                )

        if actividad is not None:
            if actividad.empresa_id != self.empresa.pk:
                self.add_error(
                    "actividad_predeterminada",
                    "La actividad no pertenece a la empresa activa.",
                )
            elif not actividad.activa:
                self.add_error(
                    "actividad_predeterminada",
                    "Seleccioná una actividad activa.",
                )

        if jurisdiccion is not None:
            if jurisdiccion.configuracion.empresa_id != self.empresa.pk:
                self.add_error(
                    "jurisdiccion_iibb_predeterminada",
                    "La jurisdicción no pertenece a la empresa activa.",
                )
            elif (
                not jurisdiccion.activa
                or not jurisdiccion.configuracion.activa
            ):
                self.add_error(
                    "jurisdiccion_iibb_predeterminada",
                    "Seleccioná una jurisdicción activa.",
                )

        return cleaned_data


class PuntoVentaCrearForm(_PuntoVentaBaseForm):
    numero = forms.IntegerField(
        label="Número de punto de venta",
        min_value=1,
        max_value=99998,
        help_text=(
            "ARCA admite cinco posiciones. Se mostrará con ceros "
            "a la izquierda, por ejemplo 00001."
        ),
    )

    def __init__(self, *args, numero_inicial=None, **kwargs):
        if (
            numero_inicial is not None
            and not args
            and "data" not in kwargs
        ):
            initial = kwargs.setdefault("initial", {})
            initial.setdefault("numero", numero_inicial)

        super().__init__(*args, **kwargs)

        orden = ["numero"] + [
            nombre
            for nombre in self.fields
            if nombre != "numero"
        ]
        self.order_fields(orden)
        self.fields["numero"].widget.attrs["class"] = "form-control"


class PuntoVentaEditarForm(_PuntoVentaBaseForm):
    pass


class ConfiguracionIIBBEmpresaForm(forms.Form):
    regimen = forms.ChoiceField(
        label="Régimen de inscripción",
        choices=ConfiguracionIIBBEmpresa.Regimen.choices,
    )
    tratamiento_general = forms.ChoiceField(
        label="Tratamiento fiscal general",
        choices=ConfiguracionIIBBEmpresa.TratamientoGeneral.choices,
    )
    numero_inscripcion = forms.CharField(
        label="Número de inscripción",
        max_length=50,
        required=False,
        help_text=(
            "Para Convenio Multilateral puede consignarse la CUIT "
            "o el identificador que figure en la constancia."
        ),
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta",
        required=False,
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, empresa, configuracion=None, **kwargs):
        self.empresa = empresa
        self.configuracion = configuracion

        if (
            configuracion is not None
            and configuracion.empresa_id != empresa.pk
        ):
            raise ValueError(
                "La configuración de IIBB no pertenece a la empresa activa."
            )

        if not args and "data" not in kwargs and configuracion is not None:
            initial = kwargs.setdefault("initial", {})
            initial.setdefault("regimen", configuracion.regimen)
            initial.setdefault(
                "tratamiento_general",
                configuracion.tratamiento_general,
            )
            initial.setdefault(
                "numero_inscripcion",
                configuracion.numero_inscripcion,
            )
            initial.setdefault("fecha_alta", configuracion.fecha_alta)
            initial.setdefault(
                "observaciones",
                configuracion.observaciones,
            )

        super().__init__(*args, **kwargs)
        _estilizar_formulario_iibb(self)

    def clean(self):
        cleaned_data = super().clean()
        regimen = cleaned_data.get("regimen")
        numero = (cleaned_data.get("numero_inscripcion") or "").strip()
        fecha_alta = cleaned_data.get("fecha_alta")

        if regimen == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO:
            numero = ""
            fecha_alta = None
            cleaned_data["numero_inscripcion"] = numero
            cleaned_data["fecha_alta"] = fecha_alta

            if (
                self.configuracion is not None
                and self.configuracion.jurisdicciones.filter(
                    activa=True
                ).exists()
            ):
                self.add_error(
                    "regimen",
                    (
                        "Inactivá las jurisdicciones antes de marcar "
                        "la empresa como no inscripta."
                    ),
                )
        elif regimen:
            if not numero:
                self.add_error(
                    "numero_inscripcion",
                    "El número de inscripción es obligatorio.",
                )
            if fecha_alta is None:
                self.add_error(
                    "fecha_alta",
                    "La fecha de alta es obligatoria.",
                )

        if (
            regimen == ConfiguracionIIBBEmpresa.Regimen.LOCAL
            and self.configuracion is not None
            and self.configuracion.jurisdicciones.filter(
                activa=True
            ).count() > 1
        ):
            self.add_error(
                "regimen",
                (
                    "El régimen local admite una sola jurisdicción activa. "
                    "Inactivá las restantes antes de cambiar el régimen."
                ),
            )

        cleaned_data["numero_inscripcion"] = numero
        cleaned_data["observaciones"] = (
            cleaned_data.get("observaciones") or ""
        ).strip()
        return cleaned_data


class EmpresaJurisdiccionIIBBCrearForm(forms.Form):
    jurisdiccion = forms.ModelChoiceField(
        label="Jurisdicción",
        queryset=JurisdiccionFiscal.objects.none(),
        empty_label="Seleccionar jurisdicción",
    )
    numero_inscripcion = forms.CharField(
        label="Número de inscripción o cuenta jurisdiccional",
        max_length=50,
        required=False,
    )
    sede = forms.BooleanField(
        label="Jurisdicción sede",
        required=False,
        help_text=(
            "La primera jurisdicción se establece como sede automáticamente."
        ),
    )
    tratamiento = forms.ChoiceField(
        label="Tratamiento en la jurisdicción",
        choices=EmpresaJurisdiccionIIBB.Tratamiento.choices,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta jurisdiccional",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, configuracion, **kwargs):
        self.configuracion = configuracion
        super().__init__(*args, **kwargs)

        asignadas = configuracion.jurisdicciones.filter(
            activa=True
        ).values_list("jurisdiccion_id", flat=True)

        self.fields["jurisdiccion"].queryset = (
            JurisdiccionFiscal.objects.filter(activa=True)
            .exclude(pk__in=asignadas)
            .order_by("orden", "codigo")
        )

        if not configuracion.jurisdicciones.filter(activa=True).exists():
            self.fields["sede"].initial = True

        if (
            configuracion.regimen
            == ConfiguracionIIBBEmpresa.Regimen.LOCAL
        ):
            self.fields["sede"].initial = True
            self.fields["sede"].disabled = True

        _estilizar_formulario_iibb(self)

    def clean(self):
        cleaned_data = super().clean()

        if not self.configuracion.activa:
            raise ValidationError(
                "La configuración de IIBB ya no está activa."
            )

        if (
            self.configuracion.regimen
            == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO
        ):
            raise ValidationError(
                "Una empresa no inscripta no admite jurisdicciones."
            )

        if (
            self.configuracion.regimen
            == ConfiguracionIIBBEmpresa.Regimen.LOCAL
            and self.configuracion.jurisdicciones.filter(
                activa=True
            ).exists()
        ):
            raise ValidationError(
                "El régimen local admite una sola jurisdicción activa."
            )

        cleaned_data["numero_inscripcion"] = (
            cleaned_data.get("numero_inscripcion") or ""
        ).strip()
        cleaned_data["observaciones"] = (
            cleaned_data.get("observaciones") or ""
        ).strip()
        return cleaned_data


class EmpresaJurisdiccionIIBBEditarForm(forms.Form):
    numero_inscripcion = forms.CharField(
        label="Número de inscripción o cuenta jurisdiccional",
        max_length=50,
        required=False,
    )
    sede = forms.BooleanField(
        label="Jurisdicción sede",
        required=False,
        help_text=(
            "Para cambiar la sede, editá otra jurisdicción y marcala como sede."
        ),
    )
    tratamiento = forms.ChoiceField(
        label="Tratamiento en la jurisdicción",
        choices=EmpresaJurisdiccionIIBB.Tratamiento.choices,
    )
    fecha_alta = forms.DateField(
        label="Fecha de alta jurisdiccional",
        input_formats=("%Y-%m-%d", "%d/%m/%Y"),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(
        self,
        *args,
        configuracion,
        relacion,
        **kwargs,
    ):
        self.configuracion = configuracion
        self.relacion = relacion

        if relacion.configuracion_id != configuracion.pk:
            raise ValueError(
                "La jurisdicción no pertenece a la configuración activa."
            )

        if not relacion.activa:
            raise ValueError(
                "Una jurisdicción histórica inactiva no puede editarse."
            )

        if not args and "data" not in kwargs:
            initial = kwargs.setdefault("initial", {})
            initial.setdefault(
                "numero_inscripcion",
                relacion.numero_inscripcion,
            )
            initial.setdefault("sede", relacion.sede)
            initial.setdefault("tratamiento", relacion.tratamiento)
            initial.setdefault("fecha_alta", relacion.fecha_alta)
            initial.setdefault("observaciones", relacion.observaciones)

        super().__init__(*args, **kwargs)

        if (
            configuracion.regimen
            == ConfiguracionIIBBEmpresa.Regimen.LOCAL
        ):
            self.fields["sede"].initial = True
            self.fields["sede"].disabled = True

        _estilizar_formulario_iibb(self)

    def clean(self):
        cleaned_data = super().clean()
        sede = bool(cleaned_data.get("sede"))

        if self.relacion.sede and not sede:
            self.add_error(
                "sede",
                (
                    "No podés quitar la sede directamente. "
                    "Marcá otra jurisdicción como sede."
                ),
            )

        cleaned_data["numero_inscripcion"] = (
            cleaned_data.get("numero_inscripcion") or ""
        ).strip()
        cleaned_data["observaciones"] = (
            cleaned_data.get("observaciones") or ""
        ).strip()
        return cleaned_data


def _estilizar_formulario_iibb(form):
    for campo in form.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        elif isinstance(campo.widget, forms.Select):
            campo.widget.attrs["class"] = "form-select"
        else:
            campo.widget.attrs["class"] = "form-control"
