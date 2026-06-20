import hashlib
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .management.commands.actualizar_catalogo_clae import (
    CODIGOS_TESTIGO,
    extraer_actividades,
)
from .models import (
    ActividadEconomica,
    ImportacionCatalogoActividad,
)


def html_catalogo(registros):
    items = "\n".join(
        f"<li>{codigo}: {descripcion}</li>"
        for codigo, descripcion in registros
    )
    relleno = " " * 60000

    return (
        "<!doctype html><html><body>"
        f"<ul>{items}</ul>"
        f"<!-- {relleno} -->"
        "</body></html>"
    ).encode("utf-8")


def registros_base():
    return [
        ("259993", "Fabricacion de productos metalicos de torneria"),
        ("259999", "Fabricacion de productos elaborados de metal n.c.p."),
        ("464330", "Venta mayorista de instrumental medico"),
        ("477330", "Venta minorista de instrumental medico"),
        ("620100", "Servicios de consultores en informatica"),
    ]


class ParserCatalogoCLAETests(TestCase):
    def test_extrae_codigos_y_descripciones(self):
        actividades = extraer_actividades(
            html_catalogo(registros_base())
        )

        self.assertEqual(
            actividades["259999"],
            "Fabricacion de productos elaborados de metal n.c.p.",
        )
        self.assertEqual(set(actividades), CODIGOS_TESTIGO)

    def test_rechaza_codigo_repetido_con_descripcion_distinta(self):
        contenido = html_catalogo(
            registros_base()
            + [("259999", "Descripcion incompatible")]
        )

        with self.assertRaises(CommandError):
            extraer_actividades(contenido)


class ActualizarCatalogoCLAECommandTests(TestCase):
    def ejecutar(self, registros, **opciones):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "nomenclador.html"
            contenido = html_catalogo(registros)
            ruta.write_bytes(contenido)

            call_command(
                "actualizar_catalogo_clae",
                archivo=str(ruta),
                fuente_url="https://oficial.example/clae",
                minimo_registros=5,
                **opciones,
            )

            return contenido

    def test_importa_catalogo_y_registra_auditoria(self):
        contenido = self.ejecutar(registros_base())

        self.assertEqual(
            ActividadEconomica.objects.filter(activa=True).count(),
            5,
        )
        actividad = ActividadEconomica.objects.get(
            codigo="259999"
        )
        self.assertEqual(
            actividad.nomenclador,
            ActividadEconomica.Nomenclador.ARCA_CLAE,
        )
        self.assertEqual(
            actividad.fuente_sha256,
            hashlib.sha256(contenido).hexdigest(),
        )

        importacion = ImportacionCatalogoActividad.objects.get()
        self.assertEqual(importacion.total_registros, 5)
        self.assertEqual(importacion.creados, 5)
        self.assertEqual(importacion.desactivados, 0)

    def test_actualiza_reactiva_y_desactiva_sin_borrar(self):
        primera = registros_base() + [
            ("692000", "Servicios contables"),
        ]
        self.ejecutar(primera)

        actividad = ActividadEconomica.objects.get(codigo="259993")
        actividad.activa = False
        actividad.save(update_fields=["activa"])

        segunda = [
            (
                "259993",
                "Fabricacion de productos metalicos "
                "de torneria y matriceria",
            ),
            *registros_base()[1:],
        ]
        self.ejecutar(segunda)

        actividad.refresh_from_db()
        retirada = ActividadEconomica.objects.get(codigo="692000")

        self.assertTrue(actividad.activa)
        self.assertIn("matriceria", actividad.descripcion)
        self.assertFalse(retirada.activa)
        self.assertEqual(
            ImportacionCatalogoActividad.objects.count(),
            2,
        )

    def test_dry_run_no_persiste(self):
        self.ejecutar(registros_base(), dry_run=True)

        self.assertEqual(ActividadEconomica.objects.count(), 0)
        self.assertEqual(
            ImportacionCatalogoActividad.objects.count(),
            0,
        )

    def test_rechaza_archivo_incompleto(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "incompleto.html"
            ruta.write_bytes(html_catalogo(registros_base()))

            with self.assertRaises(CommandError):
                call_command(
                    "actualizar_catalogo_clae",
                    archivo=str(ruta),
                    minimo_registros=900,
                )
