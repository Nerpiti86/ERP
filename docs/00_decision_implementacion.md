# DOCUMENTO 00 - DECISION DE IMPLEMENTACION DEL ERP

## 1. Proyecto

Proyecto: ERP

Repositorio local:
D:\NeriSoft2\ERP

Repositorio remoto:
https://github.com/Nerpiti86/ERP.git

Rama de trabajo:
main

---

## 2. Objetivo general

Construir un ERP administrativo, contable, fiscal, financiero y operativo orientado a empresas argentinas.

El sistema debera permitir gestionar operaciones comerciales, compras, stock, tesoreria, cuentas corrientes, contabilidad, impuestos, documentos, auditoria y reportes.

La implementacion inicial se hara en una PC Windows que funcionara como equipo de desarrollo y servidor interno inicial.

El sistema podra ser usado por otra persona de forma remota mediante Tailscale, accediendo unicamente por navegador web.

---

## 3. Tipo de implementacion elegida

Se elige una implementacion de tipo:

Monolito modular local con acceso remoto privado por Tailscale.

Esto significa que el ERP sera una sola aplicacion principal, organizada internamente por modulos funcionales.

No se usara arquitectura de microservicios en la etapa inicial.

No se expondra la base de datos directamente a otros equipos.

No se abriran puertos publicos del router.

---

## 4. Stack tecnico elegido

Backend:
- Python
- Django

Base de datos:
- PostgreSQL local

Frontend:
- Django Templates
- HTMX
- Bootstrap

Servidor local:
- Waitress u otro servidor WSGI compatible con Windows

Acceso remoto:
- Tailscale

Archivos adjuntos:
- Carpeta local media/

Backups:
- Backups automaticos de PostgreSQL mediante pg_dump

---

## 5. Arquitectura general

PC principal Windows
|
|-- PostgreSQL
|   |-- Base de datos ERP
|
|-- Django
|   |-- Aplicacion ERP
|
|-- Waitress
|   |-- Servidor web local para Django
|
|-- Tailscale
|   |-- Acceso remoto privado
|
|-- media/
|   |-- Documentos adjuntos
|
|-- backups/
    |-- Copias automaticas de la base de datos

El usuario remoto no accedera directamente a PostgreSQL.

El usuario remoto no accedera directamente al sistema de archivos de Windows.

El usuario remoto no usara escritorio remoto para operar el ERP.

El usuario remoto ingresara al ERP desde un navegador web mediante la red privada de Tailscale.

---

## 6. Forma de acceso prevista

Acceso local desde la PC principal:
http://127.0.0.1:8000

Acceso remoto desde otra PC autorizada dentro de Tailscale:
http://IP_TAILSCALE_DE_LA_PC:8000

Mas adelante podra evaluarse el uso de MagicDNS o Tailscale Serve para mejorar la URL de acceso.

---

## 7. Decisiones tecnicas tomadas

### 7.1. Django en lugar de Flask

Se elige Django porque el ERP necesita desde el inicio estructura fuerte para usuarios, autenticacion, permisos, formularios, validaciones, migraciones, modelos, administracion interna, seguridad web y organizacion por modulos.

Flask queda descartado para esta implementacion inicial porque obligaria a construir manualmente demasiadas piezas estructurales.

### 7.2. PostgreSQL en lugar de SQLite

Se elige PostgreSQL desde el inicio.

SQLite queda descartado como base principal porque el ERP tendra operaciones contables, fiscales, financieras y administrativas que requieren integridad transaccional.

PostgreSQL permitira trabajar mejor con transacciones, integridad referencial, indices, consultas complejas, reportes, auditoria, JSONB, backups consistentes y crecimiento futuro.

### 7.3. Templates + HTMX en lugar de React

Se elige Django Templates + HTMX porque la mayor parte del ERP estara compuesta por ABM, formularios, grillas, filtros, comprobantes, imputaciones, reportes, modales y validaciones.

React queda reservado para una etapa futura, solo si aparecen pantallas que realmente lo justifiquen.

### 7.4. Sin Docker al inicio

No se usara Docker en la primera etapa.

La aplicacion correra directamente en Windows con Python, PostgreSQL y entorno virtual.

Docker podra evaluarse mas adelante si el sistema se migra a un servidor Linux o si se requiere empaquetar la instalacion.

### 7.5. Sin microservicios

No se usaran microservicios.

El sistema sera un monolito modular.

Esta decision reduce complejidad inicial y permite avanzar mas rapido sin perder orden interno.

---

## 8. Seguridad inicial obligatoria

Desde el inicio se deberan cumplir estas condiciones:

1. Cada persona tendra su propio usuario.
2. No se usara usuario compartido.
3. PostgreSQL no se expondra a la red.
4. El acceso remoto sera solamente por Tailscale.
5. No se abriran puertos del router.
6. Se configurara ALLOWED_HOSTS en Django.
7. Se debera desactivar DEBUG para uso real.
8. Se registraran acciones criticas en auditoria.
9. Se haran backups automaticos.
10. Se controlara el acceso desde firewall de Windows si corresponde.

---

## 9. Estructura inicial prevista del proyecto

erp/
|-- manage.py
|-- requirements.txt
|-- .env
|-- config/
|   |-- settings.py
|   |-- urls.py
|   |-- wsgi.py
|   |-- asgi.py
|
|-- apps/
|   |-- core/
|   |-- seguridad/
|   |-- empresas/
|   |-- terceros/
|   |-- contabilidad/
|   |-- productos/
|   |-- stock/
|   |-- ventas/
|   |-- compras/
|   |-- tesoreria/
|   |-- impuestos/
|   |-- documentos/
|   |-- reporting/
|
|-- templates/
|-- static/
|-- media/
|-- backups/
|-- docs/

---

## 10. Primera etapa de trabajo

La primera etapa sera la base tecnica.

### ETAPA 0 - Base tecnica

Objetivo: dejar el ERP corriendo en la PC principal, conectado a PostgreSQL y accesible desde otra PC por Tailscale.

Tareas:

1. Crear carpeta del proyecto.
2. Crear entorno virtual.
3. Instalar Django.
4. Instalar dependencias iniciales.
5. Instalar PostgreSQL local.
6. Crear base de datos.
7. Conectar Django con PostgreSQL.
8. Crear estructura modular inicial.
9. Crear app core.
10. Crear app empresas.
11. Crear modelo Empresa.
12. Crear modelo Sucursal.
13. Crear usuario administrador.
14. Levantar servidor local.
15. Probar acceso local.
16. Probar acceso desde otra PC por Tailscale.
17. Configurar backups basicos.

---

## 11. Primer modulo funcional

Luego de la base tecnica se desarrollara el primer modulo funcional:

MODULO 1 - NUCLEO ERP

Este modulo sera responsable de:

- empresas
- sucursales
- usuarios
- roles
- permisos
- parametros del sistema
- auditoria
- eventos del sistema

Este modulo sera la base para todos los demas modulos.

---

## 12. Modulos futuros

Luego del Nucleo ERP, el orden sugerido sera:

1. Terceros
2. Plan de cuentas
3. Ejercicios y periodos contables
4. Productos y servicios
5. Ventas
6. Compras
7. Cuenta corriente
8. Tesoreria
9. Stock
10. Contabilidad automatica
11. IVA e impuestos
12. Reportes
13. Auditoria avanzada
14. Documentos adjuntos
15. Acceso remoto mas robusto

---

## 13. Decision final

La implementacion elegida para comenzar sera:

Django + PostgreSQL + HTMX + Bootstrap,
corriendo en una PC Windows,
con acceso remoto privado por Tailscale,
y PostgreSQL cerrado al exterior.

Esta implementacion permite empezar de forma simple en infraestructura, manteniendo una arquitectura preparada para crecer.
