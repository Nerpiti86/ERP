from dataclasses import dataclass
import re

from django.db import transaction

from .models import ParametroSistema


@dataclass(frozen=True)
class DefinicionParametroEmpresa:
    clave: str
    etiqueta: str
    valor_predeterminado: str
    tipo_valor: str
    descripcion: str

    @property
    def valor_predeterminado_legible(self):
        if self.tipo_valor == ParametroSistema.TipoValor.BOOLEANO:
            return "Sí" if self.valor_predeterminado == "si" else "No"

        if self.clave == "modo_numeracion_comprobantes":
            return (
                "Automática"
                if self.valor_predeterminado == "automatico"
                else "Manual"
            )

        return self.valor_predeterminado


PARAMETROS_EMPRESA_ESTANDAR = (
    DefinicionParametroEmpresa(
        clave="moneda_funcional",
        etiqueta="Moneda funcional",
        valor_predeterminado="ARS",
        tipo_valor=ParametroSistema.TipoValor.TEXTO,
        descripcion="Moneda funcional inicial de la empresa.",
    ),
    DefinicionParametroEmpresa(
        clave="permite_stock_negativo",
        etiqueta="Permitir stock negativo",
        valor_predeterminado="no",
        tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        descripcion="Define si la empresa permite operar con stock negativo.",
    ),
    DefinicionParametroEmpresa(
        clave="usa_centros_costo",
        etiqueta="Usar centros de costo",
        valor_predeterminado="si",
        tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        descripcion="Define si la empresa utiliza centros de costo.",
    ),
    DefinicionParametroEmpresa(
        clave="usa_proyectos",
        etiqueta="Usar proyectos",
        valor_predeterminado="no",
        tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        descripcion=(
            "Define si la empresa utiliza proyectos operativos o contables."
        ),
    ),
    DefinicionParametroEmpresa(
        clave="requiere_aprobacion_pagos",
        etiqueta="Requerir aprobación de pagos",
        valor_predeterminado="no",
        tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        descripcion="Define si los pagos requieren aprobación previa.",
    ),
    DefinicionParametroEmpresa(
        clave="requiere_aprobacion_compras",
        etiqueta="Requerir aprobación de compras",
        valor_predeterminado="no",
        tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        descripcion="Define si las compras requieren aprobación previa.",
    ),
    DefinicionParametroEmpresa(
        clave="punto_venta_default",
        etiqueta="Punto de venta predeterminado",
        valor_predeterminado="0001",
        tipo_valor=ParametroSistema.TipoValor.TEXTO,
        descripcion=(
            "Punto de venta inicial por defecto. Se guarda como texto "
            "para conservar ceros a la izquierda."
        ),
    ),
    DefinicionParametroEmpresa(
        clave="modo_numeracion_comprobantes",
        etiqueta="Numeración de comprobantes internos",
        valor_predeterminado="automatico",
        tipo_valor=ParametroSistema.TipoValor.TEXTO,
        descripcion=(
            "Modo inicial de numeración de comprobantes internos. "
            "No implica facturación electrónica ARCA/AFIP en esta etapa."
        ),
    ),
)

DEFINICIONES_POR_CLAVE = {
    definicion.clave: definicion
    for definicion in PARAMETROS_EMPRESA_ESTANDAR
}
CLAVES_PARAMETROS_EMPRESA = tuple(DEFINICIONES_POR_CLAVE)

_VALORES_BOOLEANOS_VERDADEROS = {"1", "true", "si", "sí", "s"}
_VALORES_BOOLEANOS_FALSOS = {"0", "false", "no", "n"}


def valores_predeterminados_formulario():
    return {
        definicion.clave: _deserializar_valor(
            definicion,
            definicion.valor_predeterminado,
        )
        for definicion in PARAMETROS_EMPRESA_ESTANDAR
    }


def _deserializar_valor(definicion, valor):
    texto = str(valor or "").strip()

    if definicion.tipo_valor == ParametroSistema.TipoValor.BOOLEANO:
        normalizado = texto.lower()

        if normalizado in _VALORES_BOOLEANOS_VERDADEROS:
            return True

        if normalizado in _VALORES_BOOLEANOS_FALSOS:
            return False

        raise ValueError(
            f"El valor de {definicion.etiqueta} no es booleano válido."
        )

    if definicion.clave == "moneda_funcional":
        normalizado = texto.upper()
        if not re.fullmatch(r"[A-Z]{3}", normalizado):
            raise ValueError("La moneda funcional debe tener tres letras.")
        return normalizado

    if definicion.clave == "punto_venta_default":
        if not re.fullmatch(r"\d{4}", texto):
            raise ValueError(
                "El punto de venta predeterminado debe tener cuatro dígitos."
            )
        return texto

    if definicion.clave == "modo_numeracion_comprobantes":
        normalizado = texto.lower()
        if normalizado not in {"automatico", "manual"}:
            raise ValueError(
                "El modo de numeración debe ser automático o manual."
            )
        return normalizado

    return texto


def _serializar_valor(definicion, valor):
    if definicion.tipo_valor == ParametroSistema.TipoValor.BOOLEANO:
        return "si" if bool(valor) else "no"

    texto = str(valor or "").strip()

    if definicion.clave == "moneda_funcional":
        return texto.upper()

    if definicion.clave == "modo_numeracion_comprobantes":
        return texto.lower()

    return texto


def obtener_estado_parametros_empresa(empresa):
    parametros = {
        parametro.clave: parametro
        for parametro in ParametroSistema.objects.filter(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=empresa,
            clave__in=CLAVES_PARAMETROS_EMPRESA,
        )
    }

    faltantes = tuple(
        definicion
        for definicion in PARAMETROS_EMPRESA_ESTANDAR
        if definicion.clave not in parametros
    )
    inactivos = tuple(
        definicion
        for definicion in PARAMETROS_EMPRESA_ESTANDAR
        if definicion.clave in parametros
        and not parametros[definicion.clave].activo
    )
    configurados = (
        len(PARAMETROS_EMPRESA_ESTANDAR)
        - len(faltantes)
        - len(inactivos)
    )

    return {
        "total": len(PARAMETROS_EMPRESA_ESTANDAR),
        "configurados": configurados,
        "faltantes": faltantes,
        "inactivos": inactivos,
        "completa": not faltantes and not inactivos,
    }


@transaction.atomic
def inicializar_parametros_empresa(empresa):
    creados = []
    reactivados = []
    existentes = []

    for definicion in PARAMETROS_EMPRESA_ESTANDAR:
        parametro = (
            ParametroSistema.objects.select_for_update()
            .filter(
                ambito=ParametroSistema.Ambito.EMPRESA,
                empresa=empresa,
                clave=definicion.clave,
            )
            .first()
        )

        if parametro is None:
            parametro = ParametroSistema(
                ambito=ParametroSistema.Ambito.EMPRESA,
                empresa=empresa,
                clave=definicion.clave,
                valor=definicion.valor_predeterminado,
                tipo_valor=definicion.tipo_valor,
                descripcion=definicion.descripcion,
                activo=True,
            )
            parametro.full_clean()
            parametro.save()
            creados.append(definicion.clave)
            continue

        if not parametro.activo:
            parametro.activo = True
            parametro.full_clean()
            parametro.save()
            reactivados.append(definicion.clave)
            continue

        existentes.append(definicion.clave)

    return {
        "creados": tuple(creados),
        "reactivados": tuple(reactivados),
        "existentes": tuple(existentes),
    }


def obtener_datos_configuracion_empresa(empresa):
    parametros = {
        parametro.clave: parametro
        for parametro in ParametroSistema.objects.filter(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=empresa,
            clave__in=CLAVES_PARAMETROS_EMPRESA,
            activo=True,
        )
    }
    datos = valores_predeterminados_formulario()
    advertencias = []

    for definicion in PARAMETROS_EMPRESA_ESTANDAR:
        parametro = parametros.get(definicion.clave)

        if parametro is None:
            continue

        try:
            datos[definicion.clave] = _deserializar_valor(
                definicion,
                parametro.valor,
            )
        except ValueError as exc:
            advertencias.append(
                (
                    f"{definicion.etiqueta}: {exc} "
                    "Se propone el valor predeterminado."
                )
            )

    return datos, tuple(advertencias)


@transaction.atomic
def guardar_configuracion_empresa(empresa, datos):
    creados = []
    actualizados = []

    for definicion in PARAMETROS_EMPRESA_ESTANDAR:
        parametro = (
            ParametroSistema.objects.select_for_update()
            .filter(
                ambito=ParametroSistema.Ambito.EMPRESA,
                empresa=empresa,
                clave=definicion.clave,
            )
            .first()
        )
        creado = parametro is None

        if creado:
            parametro = ParametroSistema(
                ambito=ParametroSistema.Ambito.EMPRESA,
                empresa=empresa,
                clave=definicion.clave,
            )

        parametro.valor = _serializar_valor(
            definicion,
            datos[definicion.clave],
        )
        parametro.tipo_valor = definicion.tipo_valor
        parametro.descripcion = definicion.descripcion
        parametro.activo = True
        parametro.full_clean()
        parametro.save()

        if creado:
            creados.append(definicion.clave)
        else:
            actualizados.append(definicion.clave)

    return {
        "creados": tuple(creados),
        "actualizados": tuple(actualizados),
    }
