# ERP

ERP administrativo, contable, fiscal, financiero y operativo orientado a empresas argentinas.

## Arquitectura

```text
Monolito modular local
+ Django
+ PostgreSQL
+ Django Templates
+ Bootstrap
+ acceso remoto privado previsto mediante Tailscale
```

Decisiones vigentes:

- rama única `main`;
- PostgreSQL como base principal;
- Django Admin como backoffice técnico;
- seguridad validada en backend;
- autenticación propia sobre Django Auth;
- roles funcionales por empresa;
- contexto activo de empresa y sucursal;
- servicios transaccionales y auditoría para cambios de dominio.

## Repositorio

```text
Local:  D:\NeriSoft2\ERP
Remoto: https://github.com/Nerpiti86/ERP.git
Rama:   main
```

## Estado real verificado

```text
Fecha del corte: 26/06/2026
Base auditada: 0f9712ff85cb38deb2a5442bcbed5b5598f8b959
Aplicaciones propias: 5
Modelos propios: 34
Roles iniciales: 5
Permisos iniciales: 40
Relaciones rol-permiso: 110
Suite completa: 425 pruebas
Migraciones pendientes: 0
```

Módulos funcionales disponibles:

- núcleo empresarial, accesos, contexto de empresa y sucursal, parámetros y auditoría;
- configuración fiscal de empresa, actividades económicas, Ingresos Brutos y puntos de venta;
- autenticación propia y autorización funcional por empresa;
- maestro de terceros con roles de cliente/proveedor, domicilios y contactos;
- maestro de productos y servicios con categorías, marcas, unidades, IVA e interfaz funcional.

Todavía no existen como circuitos operativos completos:

- ventas
- compras
- stock
- tesoreria
- cuentas corrientes
- impuestos
- reportes

El detalle canónico está en `docs/22_estado_real_integral_erp.md`. Los riesgos y deudas detectados están en `docs/23_riesgos_y_deuda_tecnica.md`.

## Ejecución y validaciones

```bash
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe -m compileall config apps
git diff --check
```

## Documentación

- índice y jerarquía: `docs/README.md`;
- contrato operativo: `docs/03_contrato_operativo.md`;
- mecánica de tareas: `docs/09_mecanica_trabajo_tareas_txt.md`;
- estado integral vigente: `docs/22_estado_real_integral_erp.md`;
- riesgos y deuda: `docs/23_riesgos_y_deuda_tecnica.md`.

## Mecánica de trabajo

Cada cambio se ejecuta como una única tarea lógica mediante un `.txt` para Git Bash. La tarea valida repositorio, rama, sincronización, working tree, migraciones y pruebas. Solo después realiza commit, push y verificación remota. Si una validación falla, no se publica.


## Doble entrada local

```text
ERP_GESTION.pyw      → http://127.0.0.1:8001/
ERP_CONTABILIDAD.pyw → http://127.0.0.1:8002/
```

Ambos accesos comparten la misma base PostgreSQL, usuarios, empresas, modelos y
migraciones. El detalle está en
`docs/25_doble_entrada_gestion_contabilidad.md`.
