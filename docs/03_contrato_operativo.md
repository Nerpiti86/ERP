# DOCUMENTO 03 - CONTRATO OPERATIVO DEL PROYECTO ERP

## 1. Objetivo

Este documento define las reglas operativas obligatorias para trabajar sobre el proyecto ERP.

Su objetivo es evitar cambios desordenados, perdida de trazabilidad, commits mezclados, errores de sincronizacion y exposicion accidental de informacion local o sensible.

---

## 2. Proyecto

Nombre del proyecto:

ERP

Repositorio local:

D:\NeriSoft2\ERP

Repositorio remoto:

https://github.com/Nerpiti86/ERP.git

Rama de trabajo:

main

---

## 3. Regla principal

Se trabajara una tarea a la vez.

Cada tarea debera tener:

1. Objetivo claro.
2. Script o comandos definidos.
3. Log local en logs/.
4. Validacion inicial.
5. Validacion final.
6. Commit especifico si modifica archivos versionables.
7. Push validado si corresponde.

No se mezclaran cambios sin relacion en un mismo commit.

---

## 4. Rama de trabajo

La rama de trabajo sera siempre:

main

No se crearan ramas salvo decision explicita posterior.

Antes de iniciar una tarea se debera validar:

git branch --show-current

El resultado esperado sera:

main

---

## 5. Sincronizacion obligatoria

Antes de comenzar una tarea importante se debera validar:

git status -sb
git rev-list --left-right --count origin/main...HEAD

El estado esperado sera:

0 0

Despues de cada push tambien se debera validar:

git status -sb
git rev-list --left-right --count origin/main...HEAD

El estado final esperado sera:

0 0

---

## 6. Working tree limpio

Antes de modificar archivos versionables, el working tree debera estar limpio.

Validacion:

git status --short

Resultado esperado:

sin salida

Si hay cambios pendientes, no se debera iniciar una nueva tarea hasta resolverlos, salvo que la tarea sea especificamente continuar o corregir esos cambios.

---

## 7. Logs locales obligatorios

Toda tarea tecnica debera dejar un log local en:

logs/

Los logs no se versionan.

La carpeta logs/ esta ignorada por Git mediante .gitignore.

Cada log debera incluir, cuando corresponda:

- nombre de la tarea
- fecha y hora
- ubicacion del repo
- rama actual
- remoto configurado
- estado inicial
- comandos ejecutados
- salida relevante
- estado final
- diferencia local versus remoto
- ultimos commits

---

## 8. Archivos que no deben versionarse

No deben subirse al repositorio:

- logs/
- .env
- archivos con contrasenas
- dumps de base de datos
- backups locales
- archivos temporales
- credenciales
- certificados privados
- archivos de configuracion sensible
- entornos virtuales
- caches

La regla minima actual ya ignora logs/.

Las demas reglas deberan incorporarse a .gitignore antes de crear archivos sensibles.

---

## 9. Commits

Cada commit debera representar una sola tarea logica.

El mensaje de commit debera ser claro y corto.

Ejemplos validos:

- Documentar decision de implementacion ERP
- Documentar nucleo ERP
- Ignorar logs locales
- Documentar politica operativa de logs
- Documentar contrato operativo del proyecto

No se deberan hacer commits con mensajes genericos como:

- cambios
- update
- cosas
- fix
- prueba

---

## 10. Push

Despues de un commit versionable, se debera hacer push a origin/main.

Luego del push, se debera validar:

git status -sb
git rev-list --left-right --count origin/main...HEAD

El resultado esperado sera:

0 0

---

## 11. PostgreSQL

PostgreSQL no debera exponerse directamente a la red.

La aplicacion Django sera la unica capa que acceda a la base de datos.

El usuario remoto accedera al ERP por navegador mediante Tailscale.

No se abrira PostgreSQL al exterior.

No se abriran puertos publicos del router para PostgreSQL.

---

## 12. Tailscale

El acceso remoto inicial sera mediante Tailscale.

La otra persona usuaria del sistema debera acceder por navegador.

No se usara escritorio remoto como forma normal de operacion del ERP.

El acceso por Tailscale no reemplaza los usuarios, roles y permisos propios del ERP.

---

## 13. Seguridad de aplicacion

Cada persona debera tener usuario propio dentro del ERP.

No se usaran usuarios compartidos.

Las acciones criticas deberan auditarse.

Los permisos deberan validarse en backend.

La interfaz no reemplaza la seguridad del backend.

---

## 14. Estructura documental

Los documentos de arquitectura, decisiones y politicas se guardaran en:

docs/

Los documentos versionables actuales son:

- docs/00_decision_implementacion.md
- docs/01_nucleo_erp.md
- docs/02_politica_operativa_logs.md
- docs/03_contrato_operativo.md

---

## 15. Criterio para scripts futuros

Todo script futuro debera:

1. Posicionarse en /d/NeriSoft2/ERP.
2. Crear log local en logs/.
3. Validar rama main.
4. Validar sincronizacion local/remoto.
5. Validar estado inicial.
6. Ejecutar una sola tarea.
7. Mostrar salida relevante.
8. Validar estado final.
9. No cerrar la terminal.
10. No usar exit final obligatorio.

Si la tarea modifica archivos versionables, el script debera permitir revisar antes del commit salvo instruccion contraria.

---

## 16. Decision final

Este contrato operativo queda como regla base del proyecto ERP.

A partir de este documento, cada avance debera respetar:

- una tarea a la vez
- rama main
- sincronizacion 0 0 antes y despues
- logs locales obligatorios
- commits especificos
- push validado
- no versionar informacion sensible

---

## 17. Commit y push automatico si todo sale bien

Cuando una tarea modifique archivos versionables y todas las validaciones sean correctas, el mismo script podra realizar automaticamente:

1. git add de los archivos modificados.
2. git commit con mensaje especifico.
3. git push a origin/main.
4. validacion final de sincronizacion local/remoto.

El estado final esperado sera:

0 0

Si una validacion falla, no se debera hacer commit ni push.

Si hay errores de compilacion, migracion, tests, sincronizacion o working tree sucio no esperado, el script debera detener la tarea operativa, dejar log local y evitar subir cambios incorrectos.

Esta regla busca reducir pasos manuales sin perder trazabilidad.
