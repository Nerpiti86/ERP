import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.nucleo.models import (
    ActividadEconomica,
    ImportacionCatalogoActividad,
)


FUENTE_OFICIAL = (
    "https://serviciosweb.afip.gob.ar/"
    "genericos/nomencladorActividades/index.aspx"
)

CODIGOS_TESTIGO = {
    "259993",
    "259999",
    "464330",
    "477330",
    "620100",
}

PATRON_ACTIVIDAD = re.compile(
    r"^\s*(?P<codigo>\d{6})\s*:\s*(?P<descripcion>.+?)\s*$"
)


class ExtractorActividadesHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._nivel_li = 0
        self._fragmentos = []
        self.actividades = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "li":
            if self._nivel_li == 0:
                self._fragmentos = []
            self._nivel_li += 1

    def handle_data(self, data):
        if self._nivel_li:
            self._fragmentos.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "li" or not self._nivel_li:
            return

        self._nivel_li -= 1

        if self._nivel_li:
            return

        texto = " ".join(" ".join(self._fragmentos).split())
        coincidencia = PATRON_ACTIVIDAD.fullmatch(texto)

        if not coincidencia:
            return

        codigo = coincidencia.group("codigo")
        descripcion = coincidencia.group("descripcion").strip()

        anterior = self.actividades.get(codigo)

        if anterior is not None and anterior != descripcion:
            raise ValueError(
                f"El codigo {codigo} aparece con descripciones distintas."
            )

        self.actividades[codigo] = descripcion


def decodificar_html(contenido):
    for codificacion in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue

    raise CommandError(
        "No se pudo decodificar el archivo oficial."
    )


def extraer_actividades(contenido):
    parser = ExtractorActividadesHTML()

    try:
        parser.feed(decodificar_html(contenido))
        parser.close()
    except ValueError as exc:
        raise CommandError(str(exc)) from exc

    return parser.actividades


class Command(BaseCommand):
    help = (
        "Importa y sincroniza el catalogo ARCA CLAE desde una copia "
        "local de la pagina oficial."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo",
            required=True,
            help="Ruta al HTML descargado desde el nomenclador oficial.",
        )
        parser.add_argument(
            "--fuente-url",
            default=FUENTE_OFICIAL,
            help="URL oficial utilizada para obtener el archivo.",
        )
        parser.add_argument(
            "--minimo-registros",
            type=int,
            default=900,
            help=(
                "Cantidad minima aceptada para evitar importar "
                "una descarga parcial."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida y simula la sincronizacion sin persistir cambios.",
        )

    def handle(self, *args, **options):
        ruta = Path(options["archivo"]).expanduser().resolve()

        if not ruta.is_file():
            raise CommandError(
                f"No existe el archivo indicado: {ruta}"
            )

        contenido = ruta.read_bytes()

        if len(contenido) < 50000:
            raise CommandError(
                "El archivo es demasiado pequeno para ser "
                "el nomenclador oficial completo."
            )

        actividades = extraer_actividades(contenido)
        minimo = options["minimo_registros"]

        if len(actividades) < minimo:
            raise CommandError(
                f"Se encontraron {len(actividades)} actividades; "
                f"se requieren al menos {minimo}."
            )

        faltantes_testigo = sorted(
            CODIGOS_TESTIGO - set(actividades)
        )

        if faltantes_testigo:
            raise CommandError(
                "Faltan codigos testigo del nomenclador oficial: "
                + ", ".join(faltantes_testigo)
            )

        sha256 = hashlib.sha256(contenido).hexdigest()
        ahora = timezone.now()
        nomenclador = (
            ActividadEconomica.Nomenclador.ARCA_CLAE
        )

        resumen = {
            "creados": 0,
            "actualizados": 0,
            "reactivados": 0,
            "desactivados": 0,
        }

        with transaction.atomic():
            for codigo, descripcion in sorted(actividades.items()):
                actividad = ActividadEconomica.objects.filter(
                    nomenclador=nomenclador,
                    codigo=codigo,
                ).first()

                if actividad is None:
                    ActividadEconomica.objects.create(
                        nomenclador=nomenclador,
                        codigo=codigo,
                        descripcion=descripcion,
                        activa=True,
                        fuente_url=options["fuente_url"],
                        fuente_sha256=sha256,
                        ultima_sincronizacion_en=ahora,
                    )
                    resumen["creados"] += 1
                    continue

                campos_actualizados = []

                if actividad.descripcion != descripcion:
                    actividad.descripcion = descripcion
                    campos_actualizados.append("descripcion")

                if not actividad.activa:
                    actividad.activa = True
                    campos_actualizados.append("activa")
                    resumen["reactivados"] += 1

                if actividad.fuente_url != options["fuente_url"]:
                    actividad.fuente_url = options["fuente_url"]
                    campos_actualizados.append("fuente_url")

                if actividad.fuente_sha256 != sha256:
                    actividad.fuente_sha256 = sha256
                    campos_actualizados.append("fuente_sha256")

                actividad.ultima_sincronizacion_en = ahora
                campos_actualizados.append(
                    "ultima_sincronizacion_en"
                )

                if campos_actualizados:
                    actividad.full_clean()
                    actividad.save(
                        update_fields=sorted(
                            set(campos_actualizados)
                        )
                    )

                    if (
                        "descripcion" in campos_actualizados
                        or "fuente_url" in campos_actualizados
                        or "fuente_sha256" in campos_actualizados
                    ):
                        resumen["actualizados"] += 1

            desactivados = (
                ActividadEconomica.objects.filter(
                    nomenclador=nomenclador,
                    activa=True,
                )
                .exclude(codigo__in=actividades)
                .update(
                    activa=False,
                    fuente_url=options["fuente_url"],
                    fuente_sha256=sha256,
                    ultima_sincronizacion_en=ahora,
                )
            )
            resumen["desactivados"] = desactivados

            if options["dry_run"]:
                transaction.set_rollback(True)
            else:
                ImportacionCatalogoActividad.objects.create(
                    nomenclador=nomenclador,
                    fuente_url=options["fuente_url"],
                    archivo_nombre=ruta.name,
                    sha256=sha256,
                    total_registros=len(actividades),
                    creados=resumen["creados"],
                    actualizados=resumen["actualizados"],
                    reactivados=resumen["reactivados"],
                    desactivados=resumen["desactivados"],
                )

        modo = "SIMULACION" if options["dry_run"] else "IMPORTACION"

        self.stdout.write(
            self.style.SUCCESS(
                f"{modo} CLAE correcta: "
                f"total={len(actividades)}; "
                f"creados={resumen['creados']}; "
                f"actualizados={resumen['actualizados']}; "
                f"reactivados={resumen['reactivados']}; "
                f"desactivados={resumen['desactivados']}; "
                f"sha256={sha256}"
            )
        )
