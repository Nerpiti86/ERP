# ERP

ERP administrativo, contable, fiscal, financiero y operativo orientado a empresas argentinas.

## Objetivo

Construir un sistema ERP modular para gestionar operaciones comerciales, compras, stock, tesoreria, cuentas corrientes, contabilidad, impuestos, documentos, auditoria y reportes.

La implementacion inicial esta pensada para ejecutarse en una PC Windows local, que funcionara como equipo de desarrollo y servidor interno inicial.

El acceso remoto previsto sera mediante Tailscale, permitiendo que otra persona autorizada use el sistema desde un navegador web sin exponer la base de datos ni abrir puertos publicos del router.

---

## Stack tecnico elegido

- Python
- Django
- PostgreSQL local
- Django Templates
- HTMX
- Bootstrap
- Waitress u otro servidor WSGI compatible con Windows
- Tailscale para acceso remoto privado

---

## Tipo de arquitectura

El proyecto se implementara como:

Monolito modular local con acceso remoto privado por Tailscale.

Esto significa que sera una sola aplicacion principal, organizada internamente por modulos funcionales.

No se usaran microservicios en la etapa inicial.

No se usara Docker en la primera etapa.

No se usara SQLite como base principal.

No se expondra PostgreSQL directamente a la red.

---

## Repositorio

Repositorio local principal:

D:\NeriSoft2\ERP

Repositorio remoto:

https://github.com/Nerpiti86/ERP.git

Rama de trabajo:

main

---

## Documentacion

La documentacion del proyecto se encuentra en la carpeta docs/.

Documentos iniciales:

- docs/00_decision_implementacion.md
- docs/01_nucleo_erp.md
- docs/02_politica_operativa_logs.md
- docs/03_contrato_operativo.md

---

## Politica operativa

Reglas principales del proyecto:

- Se trabaja una tarea a la vez.
- Se trabaja siempre sobre la rama main.
- Se valida sincronizacion local/remoto antes y despues de cada tarea.
- El estado esperado de sincronizacion es 0 0.
- Toda tarea tecnica debe dejar log local en logs/.
- La carpeta logs/ no se versiona.
- No se deben commitear secretos, .env, backups, dumps ni archivos locales sensibles.
- Cada commit debe representar una sola tarea logica.
- Despues de cada commit versionable se debe hacer push y validar sincronizacion final.

---

## Logs locales

Los logs de trabajo se guardan localmente en:

logs/

Esta carpeta esta ignorada por Git.

Los logs sirven para registrar comandos ejecutados, resultados, errores, validaciones y estado final de cada tarea.

---

## Seguridad inicial

Reglas iniciales:

- Cada persona debe tener su propio usuario dentro del ERP.
- No se usaran usuarios compartidos.
- PostgreSQL no debe exponerse directamente a la red.
- El acceso remoto sera mediante Tailscale.
- No se abriran puertos publicos del router.
- Los permisos deben validarse en backend.
- Las acciones criticas deberan auditarse.

---

## Estado actual

El proyecto se encuentra en etapa documental y preparacion de base tecnica.

Proxima etapa prevista:

- Crear base tecnica Django.
- Crear entorno virtual local.
- Instalar dependencias iniciales.
- Conectar Django con PostgreSQL.
- Crear estructura modular inicial.
