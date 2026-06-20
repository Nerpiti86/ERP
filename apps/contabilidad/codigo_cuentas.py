import re


CODIGO_CUENTA_REGEX = r"^[0-9]\.[0-9]\.[0-9]{2}\.[0-9]{2}\.[0-9]{3}$"
CODIGO_CUENTA_ESTRUCTURAL_REGEX = (
    r"^(?:"
    r"[1-9]\.0\.00\.00\.000|"
    r"[1-9]\.[1-9]\.00\.00\.000|"
    r"[1-9]\.[1-9]\.(?:0[1-9]|[1-9][0-9])\.00\.000|"
    r"[1-9]\.[1-9]\.(?:0[1-9]|[1-9][0-9])\."
    r"(?:0[1-9]|[1-9][0-9])\.000|"
    r"[1-9]\.[1-9]\.(?:0[1-9]|[1-9][0-9])\."
    r"(?:0[1-9]|[1-9][0-9])\."
    r"(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})"
    r")$"
)

_ANCHOS_SEGMENTOS = (1, 1, 2, 2, 3)


def segmentos_desde_codigo(codigo):
    if not codigo or not re.fullmatch(CODIGO_CUENTA_REGEX, codigo):
        return None
    return [int(segmento) for segmento in codigo.split(".")]


def nivel_desde_codigo(codigo):
    segmentos = segmentos_desde_codigo(codigo)
    if segmentos is None:
        return None

    encontro_cero = False
    nivel = 0
    for posicion, segmento in enumerate(segmentos, start=1):
        if segmento == 0:
            encontro_cero = True
            continue
        if encontro_cero:
            return None
        nivel = posicion
    return nivel or None


def codigo_padre_desde_codigo(codigo):
    segmentos = segmentos_desde_codigo(codigo)
    nivel = nivel_desde_codigo(codigo)
    if segmentos is None or nivel is None or nivel == 1:
        return None

    segmentos[nivel - 1] = 0
    return ".".join(
        f"{segmento:0{ancho}d}"
        for segmento, ancho in zip(
            segmentos,
            _ANCHOS_SEGMENTOS,
            strict=True,
        )
    )
