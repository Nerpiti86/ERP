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
Fecha del corte: 2026-06-29
Base auditada antes del commit documental: 2e6094a4e6dd5b2cf4ee0710febbcca2a9e65e2e
Aplicaciones propias: 5
Modelos propios: 36
Tablas propias detectadas: 36
Migraciones propias aplicadas: 22
Roles funcionales activos: 5
Permisos funcionales activos: 40
Relaciones rol-permiso activas: 110
Suite completa: 494 pruebas
Migraciones pendientes: 0
```

Módulos funcionales disponibles:

- núcleo empresarial, accesos, contexto de empresa y sucursal, parámetros y auditoría;
- configuración fiscal, actividades económicas, Ingresos Brutos y puntos de venta;
- autenticación propia y autorización funcional por empresa;
- Plan de cuentas mínimo con listado, filtros y alta;
- maestro de terceros con roles, grupos de clientes/proveedores, domicilios y contactos;
- maestro de productos y servicios con proveedores asociados, categorías, marcas, unidades, IVA e interfaz funcional;
- entradas locales especializadas `NeriSoft Gestión` y `NeriSoft Contabilidad`.

Todavía no existen como circuitos operativos completos:

- ventas;
- compras;
- stock;
- tesorería;
- cuentas corrientes;
- asientos y procesos contables operativos;
- impuestos transaccionales;
- reportes operativos.

El detalle canónico está en `docs/22_estado_real_integral_erp.md`. Los riesgos y
deudas se registran en `docs/23_riesgos_y_deuda_tecnica.md`.

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
