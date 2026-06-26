from django.core.validators import RegexValidator
from django.db import migrations, models
import django.db.models.deletion


GRUPOS_GENERALES = (
    ("CLIENTE", "CLIENTES_GENERALES", "Clientes generales"),
    ("PROVEEDOR", "PROVEEDORES_GENERALES", "Proveedores generales"),
)


def crear_grupos_y_asignar_roles(apps, schema_editor):
    Empresa = apps.get_model("nucleo", "Empresa")
    GrupoTercero = apps.get_model("terceros", "GrupoTercero")
    TerceroRol = apps.get_model("terceros", "TerceroRol")

    for empresa in Empresa.objects.all().iterator():
        for tipo, codigo, nombre in GRUPOS_GENERALES:
            grupo, _ = GrupoTercero.objects.get_or_create(
                empresa_id=empresa.pk,
                tipo=tipo,
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "observaciones": (
                        "Grupo general creado automáticamente "
                        "por la migración 0003."
                    ),
                    "activo": True,
                },
            )
            TerceroRol.objects.filter(
                tercero__empresa_id=empresa.pk,
                rol=tipo,
            ).update(grupo_id=grupo.pk)

    if TerceroRol.objects.filter(grupo__isnull=True).exists():
        raise RuntimeError(
            "La migración no pudo asignar un grupo a todos los roles."
        )


def desasignar_grupos(apps, schema_editor):
    TerceroRol = apps.get_model("terceros", "TerceroRol")
    TerceroRol.objects.update(grupo_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("terceros", "0002_catalogos_iniciales"),
    ]

    operations = [
        migrations.CreateModel(
            name="GrupoTercero",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("CLIENTE", "Cliente"),
                            ("PROVEEDOR", "Proveedor"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "codigo",
                    models.CharField(
                        max_length=30,
                        validators=[
                            RegexValidator(
                                message=(
                                    "El código debe usar mayúsculas, "
                                    "números, guion o guion bajo."
                                ),
                                regex="^[A-Z0-9_-]+$",
                            )
                        ],
                    ),
                ),
                ("nombre", models.CharField(max_length=160)),
                ("observaciones", models.TextField(blank=True)),
                ("activo", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="grupos_terceros",
                        to="nucleo.empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "grupo de tercero",
                "verbose_name_plural": "grupos de terceros",
                "db_table": "terceros_grupotercero",
                "ordering": [
                    "empresa__razon_social",
                    "tipo",
                    "-activo",
                    "nombre",
                    "codigo",
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="grupotercero",
            constraint=models.UniqueConstraint(
                fields=("empresa", "tipo", "codigo"),
                name="uniq_grupo_ter_emp_tipo_cod",
            ),
        ),
        migrations.AddConstraint(
            model_name="grupotercero",
            constraint=models.UniqueConstraint(
                fields=("empresa", "tipo", "nombre"),
                name="uniq_grupo_ter_emp_tipo_nom",
            ),
        ),
        migrations.AddIndex(
            model_name="grupotercero",
            index=models.Index(
                fields=["empresa", "tipo", "activo", "nombre"],
                name="idx_grupo_ter_tipo_act",
            ),
        ),
        migrations.AddField(
            model_name="tercerorol",
            name="grupo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="roles_terceros",
                to="terceros.grupotercero",
            ),
        ),
        migrations.RunPython(
            crear_grupos_y_asignar_roles,
            desasignar_grupos,
        ),
        migrations.AlterField(
            model_name="tercerorol",
            name="grupo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="roles_terceros",
                to="terceros.grupotercero",
            ),
        ),
    ]
