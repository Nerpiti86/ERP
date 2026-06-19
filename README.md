# ERP

ERP administrativo, contable, fiscal, financiero y operativo orientado a empresas argentinas.

## Objetivo

Construir un sistema ERP modular para gestionar operaciones comerciales, compras, stock, tesorería, cuentas corrientes, contabilidad, impuestos, documentos, auditoría y reportes.

La implementación inicial se ejecuta en una PC Windows local que funciona como equipo de desarrollo y servidor interno. El acceso remoto previsto es mediante Tailscale y navegador web, sin exponer PostgreSQL ni abrir puertos públicos del router.

## Arquitectura

```text
Monolito modular local
+ Django
+ PostgreSQL
+ Django Templates
+ Bootstrap
+ HTMX cuando corresponda
+ servidor WSGI compatible con Windows
+ acceso remoto privado por Tailscale
```

Decisiones vigentes:

- una aplicación principal organizada por módulos
- sin microservicios en la etapa inicial
- sin Docker en la etapa inicial
- PostgreSQL como base principal
- Django Admin como backoffice técnico, no como interfaz final
- seguridad y permisos validados en backend
- autenticación propia del ERP sobre Django Auth

## Repositorio

```text
Local:  D:\NeriSoft2\ERP
Remoto: https://github.com/Nerpiti86/ERP.git
Rama:   main
```

## Estado actual

Corte documental: 19/06/2026.

Último cierre funcional verificado:

```text
TAREA 46 — Definir autenticación propia del ERP
Commit: 8e35e36ec3565affba379378aa818ac4cab4d1ba
Tests: 85 OK
Sincronización final: origin/main...HEAD = 0 0
```

El ERP ya cuenta con:

- proyecto Django conectado a PostgreSQL
- apps `core` y `nucleo`
- Empresa y Sucursal
- EjercicioFiscal y PeriodoContable
- accesos UsuarioEmpresa y UsuarioSucursal
- ParametroSistema
- Auditoria
- EventoNegocio
- DocumentoAdjunto
- roles y permisos funcionales propios
- cinco roles iniciales y veinticinco permisos
- empresa activa por sesión
- sucursal activa por sesión
- selección automática o manual según accesos
- autenticación propia mediante `/ingresar/`
- cierre de sesión mediante POST en `/salir/`
- portada protegida
- métricas acotadas al contexto del usuario
- Django Admin visible únicamente para usuarios `staff`

Estado operativo local conocido:

```text
Usuario real creado: ADMIN
Otros usuarios observados en tests: temporales y eliminados con la base de prueba
```

Próxima tarea funcional:

```text
TAREA 47 — Aplicar permisos funcionales a las vistas del ERP
Estado: pendiente de diseño
```

## Documentación

Índice documental:

```text
docs/README.md
```

Documentos rectores principales:

- `docs/00_decision_implementacion.md`
- `docs/01_nucleo_erp.md`
- `docs/02_politica_operativa_logs.md`
- `docs/03_contrato_operativo.md`
- `docs/04_roles_permisos.md`
- `docs/05_usuario_custom.md`
- `docs/06_empresa_activa_sesion.md`
- `docs/07_sucursal_activa_sesion.md`
- `docs/08_autenticacion_erp.md`
- `docs/09_mecanica_trabajo_tareas_txt.md`
- `docs/10_estado_actual_y_hoja_ruta.md`

## Mecánica de trabajo

Se trabaja mediante tareas ejecutables `.txt`:

```text
tareaNN_descripcion.txt
tareaNN_resumen_operativo.txt
```

Flujo:

1. Se define una sola tarea.
2. Se revisa `main` remoto antes de diseñarla.
3. Se entrega un script `.txt` ejecutable desde Git Bash.
4. El script valida Git, crea log y backup, realiza el cambio y ejecuta validaciones.
5. Solo si todo pasa hace commit y push.
6. Se devuelve el log completo.
7. Se verifica el commit contra GitHub.
8. Recién entonces la tarea se considera cerrada.

La mecánica completa está documentada en:

```text
docs/09_mecanica_trabajo_tareas_txt.md
```

## Reglas operativas esenciales

- una tarea lógica por vez
- rama única `main`
- working tree limpio al iniciar, salvo continuación explícita
- sincronización esperada `0 0` antes y después
- logs locales obligatorios en `logs/`
- backups locales por tarea en `logs/backup/`
- no versionar `.env`, secretos, logs, backups, dumps ni `.venv`
- commit claro y específico
- push automático únicamente después de validar
- si algo falla, no hacer commit ni push
- una continuación trabaja sobre el estado local dejado por la tarea fallida

## Validaciones Django mínimas

```bash
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py test apps.core apps.nucleo
.venv/Scripts/python.exe -m compileall config apps
```

Las tareas documentales ejecutan además:

```bash
git diff --check
```

## Logs

Los logs locales se guardan en:

```text
D:\NeriSoft2\ERP\logs
```

No se versionan. Cada log debe permitir reconstruir qué se hizo, qué se validó y si la tarea terminó sincronizada con `origin/main`.
