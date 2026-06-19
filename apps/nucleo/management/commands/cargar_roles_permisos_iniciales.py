from django.core.management.base import BaseCommand, CommandError

from apps.nucleo.roles_iniciales import (
    PERMISOS_INICIALES,
    PERMISOS_POR_ROL,
    ROLES_INICIALES,
    cargar_roles_permisos_iniciales,
    verificar_roles_permisos_iniciales,
)


class Command(BaseCommand):
    help = (
        "Crea o actualiza los roles, permisos y relaciones iniciales "
        "del ERP de manera idempotente."
    )

    def handle(self, *args, **options):
        resumen = cargar_roles_permisos_iniciales()
        errores = verificar_roles_permisos_iniciales()

        if errores:
            detalle = "\n".join(f"- {error}" for error in errores)
            raise CommandError(
                "La carga termino con errores de verificacion:\n" + detalle
            )

        relaciones_esperadas = sum(
            len(permisos) for permisos in PERMISOS_POR_ROL.values()
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Roles y permisos iniciales cargados correctamente."
            )
        )
        self.stdout.write(f"Roles iniciales: {len(ROLES_INICIALES)}")
        self.stdout.write(f"Permisos iniciales: {len(PERMISOS_INICIALES)}")
        self.stdout.write(
            f"Relaciones iniciales esperadas: {relaciones_esperadas}"
        )
        self.stdout.write(
            "Roles creados: "
            f"{resumen['roles_creados']} | "
            "roles existentes: "
            f"{resumen['roles_existentes']}"
        )
        self.stdout.write(
            "Permisos creados: "
            f"{resumen['permisos_creados']} | "
            "permisos existentes: "
            f"{resumen['permisos_existentes']}"
        )
        self.stdout.write(
            "Relaciones creadas: "
            f"{resumen['relaciones_creadas']} | "
            "reactivadas: "
            f"{resumen['relaciones_activadas']} | "
            "sin cambios: "
            f"{resumen['relaciones_sin_cambios']}"
        )
