from django.core.management.base import BaseCommand, CommandError

from apps.items.catalogos_iniciales import (
    ALICUOTAS_IVA_INICIALES,
    FECHA_SNAPSHOT,
    FUENTE_ALICUOTAS,
    FUENTE_UNIDADES,
    UNIDADES_MEDIDA_INICIALES,
    cargar_catalogos_items_iniciales,
    verificar_catalogos_items_iniciales,
)


class Command(BaseCommand):
    help = (
        "Crea o actualiza de forma idempotente las unidades de medida "
        "y alícuotas de IVA iniciales del maestro de ítems."
    )

    def handle(self, *args, **options):
        resumen = cargar_catalogos_items_iniciales()
        errores = verificar_catalogos_items_iniciales()

        if errores:
            detalle = "\n".join(f"- {error}" for error in errores)
            raise CommandError(
                "La carga terminó con errores de verificación:\n" + detalle
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogos iniciales de ítems cargados correctamente."
            )
        )
        self.stdout.write(f"Snapshot: {FECHA_SNAPSHOT}")
        self.stdout.write(
            f"Unidades esperadas: {len(UNIDADES_MEDIDA_INICIALES)}"
        )
        self.stdout.write(
            f"Alícuotas esperadas: {len(ALICUOTAS_IVA_INICIALES)}"
        )
        self.stdout.write(
            "Unidades creadas: "
            f"{resumen['unidades_creadas']} | "
            "actualizadas: "
            f"{resumen['unidades_actualizadas']} | "
            "sin cambios: "
            f"{resumen['unidades_sin_cambios']}"
        )
        self.stdout.write(
            "Alícuotas creadas: "
            f"{resumen['alicuotas_creadas']} | "
            "actualizadas: "
            f"{resumen['alicuotas_actualizadas']} | "
            "sin cambios: "
            f"{resumen['alicuotas_sin_cambios']}"
        )
        self.stdout.write(f"Fuente unidades: {FUENTE_UNIDADES}")
        self.stdout.write(f"Fuente alícuotas: {FUENTE_ALICUOTAS}")
