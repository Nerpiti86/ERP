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

## 18. Continuacion explicita de tarea fallida

Si una tarea falla despues de modificar archivos, crear migraciones o aplicar cambios locales de base de datos, la siguiente ejecucion debera declararse como continuacion explicita.

En una continuacion explicita se permite que el working tree no este limpio, siempre que el estado sucio corresponda a la tarea fallida.

La continuacion explicita debera:

1. Validar rama `main`.
2. Validar sincronizacion `origin/main...HEAD = 0 0`.
3. Mostrar el working tree sucio esperado.
4. Validar que los archivos esperados de la tarea inconclusa existen.
5. Crear un nuevo log local.
6. Crear backup local antes de corregir.
7. Repetir validaciones completas.
8. Hacer commit y push solo si todo pasa.
9. Validar estado final `0 0`.

Ejemplo real:

```text
Tarea 34:
Crear ParametroSistema fallo por un test de normalizacion de clave.

Continuacion:
Se corrigio la normalizacion antes de validadores de Django.
Se repitieron 30 tests.
Se hizo commit y push solo despues de validar todo.
```

---

## 19. Backups locales obligatorios

Toda tarea que modifique archivos versionables debera crear backup local previo en:

```text
logs/backup/
```

Los backups locales no se versionan.

El backup local no reemplaza Git, pero permite recuperar rapidamente el estado anterior si una tarea falla antes del commit.

---

## 20. Validaciones minimas para tareas Django

Cuando una tarea modifique codigo Django, debera ejecutar segun corresponda:

```bash
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py test apps.core apps.nucleo
.venv/Scripts/python.exe -m compileall config apps
```

Cuando una tarea cree o modifique modelos, debera ejecutar ademas:

```bash
.venv/Scripts/python.exe manage.py makemigrations <app>
.venv/Scripts/python.exe manage.py migrate
```

Si una validacion falla, no se debera hacer commit ni push.

---

## 21. Django Admin e interfaz final

El Django Admin se usara como backoffice tecnico inicial.

Su objetivo es cargar datos maestros, validar modelos, probar relaciones y administrar datos iniciales mientras se construye el ERP.

El Django Admin no sera la interfaz final del ERP.

Las pantallas propias del ERP se construiran sobre:

- Django Templates
- Bootstrap
- HTMX cuando corresponda

---

## 22. Base de datos actual

La base local actual es:

```text
erp_local
```

La conexion local esperada es:

```text
127.0.0.1:5432
```

PostgreSQL no debera exponerse directamente a la red.

El archivo `.env` contiene la configuracion real de conexion y no debe versionarse.


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

---

## 23. Mecánica acordada de tareas TXT

La mecánica oficial entre el usuario y el asistente queda documentada en:

```text
docs/09_mecanica_trabajo_tareas_txt.md
```

Resumen obligatorio:

1. El usuario define una tarea.
2. El asistente revisa `main` remoto y los documentos relevantes.
3. El asistente entrega un script Bash con extensión `.txt` y un resumen operativo.
4. El usuario ejecuta el archivo desde Git Bash.
5. El script genera log y backup local.
6. El script hace commit y push únicamente si todo pasa.
7. El usuario devuelve el log completo.
8. El asistente verifica el commit contra GitHub.
9. Solo entonces se declara la tarea cerrada.

Los scripts de tareas no forman parte del código fuente del ERP y no se copiarán al repositorio salvo decisión explícita.

## 24. Estados formales de una tarea

Estados posibles:

```text
PREPARADA
EN EJECUCION
DETENIDA
EN CONTINUACION
CERRADA Y VERIFICADA
```

Una tarea preparada puede tener un script completo y todavía no formar parte de `main`.

Solo el estado `CERRADA Y VERIFICADA` implica:

- commit existente
- push realizado
- sincronización final `0 0`
- verificación remota

## 25. Cortes documentales

Los cortes documentales utilizan numeración independiente:

```text
CORTE DOCUMENTAL DNN
```

Su objetivo es:

- actualizar el estado general
- consolidar la hoja de ruta
- revisar contradicciones documentales
- actualizar la mecánica de trabajo
- evitar alterar la numeración de tareas funcionales

Los cortes documentales también deben generar log, backup, commit y push.

---

## 26. Revisión remota y validación del artefacto

Antes de preparar una tarea, el asistente deberá revisar el `main` remoto y
los archivos concretos que serán afectados.

No deberá diseñar cambios basándose únicamente en memoria, conversaciones
anteriores o documentos históricos.

Toda tarea deberá fijar el SHA esperado de inicio.

Los scripts generados deberán validarse antes de entregarse mediante:

- `bash -n`
- compilación de bloques Python embebidos
- compilación sintáctica de archivos Python generados
- comprobación de puntos de inserción
- verificación de lista exacta de archivos

La validación del artefacto preparado no reemplaza las comprobaciones en el
entorno real.

## 27. Anclas de modificación seguras

Las modificaciones automáticas no deberán depender de líneas completas
frágiles cuando puedan cambiar por:

- tildes
- espacios
- saltos de línea
- formato
- redacción menor

Se preferirán anclas semánticas estables, como nombres de clases, funciones
o encabezados.

Todo ancla deberá aparecer exactamente una vez. Si no aparece o aparece más
de una vez, la tarea deberá detenerse.

## 28. Inicialización de Django en bloques Python

Un bloque Python que importe modelos Django fuera de `manage.py` deberá
configurar `DJANGO_SETTINGS_MODULE` y ejecutar `django.setup()` antes de la
importación.

Cuando sea posible se preferirán:

- comandos de administración
- `manage.py shell`
- pruebas Django

## 29. Orden de efectos persistentes

Las migraciones, importaciones y transformaciones de datos deberán
ejecutarse después de:

- compilación
- `manage.py check`
- revisión de migraciones
- pruebas específicas
- suite completa
- validación de fuentes externas requeridas

Después de modificar la base se deberán verificar explícitamente los datos
resultantes antes del commit.

## 30. Restricciones, servicios y auditoría

Las reglas críticas deberán evaluarse en cuatro niveles:

1. base de datos
2. modelo
3. servicio transaccional
4. formulario o vista

Las operaciones con efectos múltiples deberán centralizarse en servicios
atómicos y registrar auditoría cuando sean funcionalmente relevantes.

## 31. Catálogos externos y datos históricos

Los catálogos oficiales externos deberán mantenerse localmente con fuente,
fecha, SHA-256 y auditoría de importación.

Los datos históricos que puedan cambiar en el catálogo deberán conservar
una instantánea cuando sea necesario reproducir el estado anterior.

Los catálogos oficiales y las relaciones administradas por servicios no
deberán quedar editables libremente en Django Admin.

## 32. Validación exacta de archivos y staging

Antes del commit se deberán comparar:

- archivos esperados
- archivos modificados
- archivos staged

Los conjuntos deberán coincidir.

Se mantiene prohibido usar `git add .`.

## 33. Estándar consolidado

El estándar completo surgido de estas lecciones está documentado en:

```text
docs/17_lecciones_aprendidas_y_estandar_implementacion.md
```

Sus reglas complementan este contrato y deberán aplicarse en las tareas
futuras.
