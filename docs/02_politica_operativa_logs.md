# DOCUMENTO 02 - POLITICA OPERATIVA DE LOGS

## 1. Objetivo

Definir una regla operativa para que cada tarea realizada sobre el ERP deje evidencia local en archivos de log.

Esta politica busca facilitar la revision posterior de comandos ejecutados, resultados obtenidos, errores, validaciones y estado final del repositorio.

---

## 2. Carpeta de logs

Los logs locales se guardaran en:

D:\NeriSoft2\ERP\logs

En Git Bash:

/d/NeriSoft2/ERP/logs

---

## 3. Regla principal

Toda tarea tecnica debera generar un archivo .txt dentro de la carpeta logs/.

Esto aplica a:

- validaciones Git
- creacion de documentos
- commits
- pushes
- instalacion de dependencias
- creacion de proyecto Django
- configuracion de PostgreSQL
- migraciones
- tests
- errores
- verificaciones de sincronizacion
- scripts de mantenimiento

---

## 4. Regla de versionado

La carpeta logs/ no se versiona en Git.

La regla esta definida en .gitignore:

logs/

Motivo:

Los logs pueden contener rutas locales, salidas de terminal, detalles de entorno, errores, pruebas y datos operativos que no deben subirse al repositorio.

---

## 5. Formato recomendado de cada log

Cada log deberia incluir:

1. Nombre de la tarea.
2. Fecha y hora.
3. Ubicacion del repositorio.
4. Rama actual.
5. Estado inicial.
6. Comandos o pasos ejecutados.
7. Resultado de cada paso.
8. Estado final.
9. Diferencia local versus remoto.
10. Ultimos commits si corresponde.

---

## 6. Nomenclatura sugerida

Los logs se nombraran con numeracion correlativa y descripcion corta.

Ejemplos:

0001_politica_logs_locales.txt
0002_validacion_gitignore_logs_locales.txt
0003_documentar_politica_operativa_logs.txt

---

## 7. Sincronizacion Git

Cuando una tarea modifique archivos versionables, se debera validar:

- git status --short
- git status -sb
- git rev-list --left-right --count origin/main...HEAD

Antes de comenzar una tarea importante, el estado esperado sera:

0 0

Despues del push, el estado esperado tambien sera:

0 0

---

## 8. Criterio operativo

Se trabajara una tarea a la vez.

No se mezclaran cambios sin relacion en un mismo commit.

Cada tarea debera tener su log local correspondiente.

Cada documento o cambio versionable debera tener commit claro y push validado.


---

## 9. Backups locales por tarea

Cuando una tarea modifique archivos versionables, el script debera crear backup local previo en:

```text
logs/backup/
```

Estos backups no se versionan.

El objetivo del backup es permitir recuperacion rapida si una tarea falla antes del commit.

El backup no reemplaza Git, pero ayuda a revisar o revertir cambios locales durante una tarea inconclusa.

---

## 10. Continuaciones explicitas

Si una tarea falla despues de modificar archivos, generar migraciones o aplicar cambios locales, la siguiente ejecucion debera tratarse como continuacion explicita.

En una continuacion explicita se permite que el working tree no este limpio, siempre que:

1. El estado sucio corresponda a la tarea fallida.
2. Se valide que los archivos esperados de la tarea estan presentes.
3. Se deje un nuevo log local.
4. Se haga backup antes de corregir.
5. Se repitan las validaciones completas.
6. No se haga commit ni push si las validaciones no pasan.

Ejemplo real:

```text
Tarea 34:
Crear ParametroSistema fallo por un test de normalizacion de clave.

Continuacion:
Se corrigio la normalizacion antes de los validadores de Django.
Se repitieron los tests.
Se hizo commit y push solo despues de 30 tests OK.
```

---

## 11. Decision final

A partir de este punto, toda tarea del ERP debera dejar log local en logs/.

La carpeta logs/ seguira ignorada por Git.

Los documentos de politica y arquitectura si se versionaran dentro de docs/.

---

## 12. Relación entre tarea, script y log

La mecánica operativa habitual usa:

```text
tareaNN_descripcion.txt
tareaNN_resumen_operativo.txt
```

El primer archivo es Bash ejecutable aunque tenga extensión `.txt`.

El script:

- no se versiona dentro del ERP
- se posiciona por sí mismo en el repositorio
- crea el log local oficial de la ejecución
- crea backup local cuando modifica archivos
- realiza commit y push solo si todas las validaciones pasan

El archivo de resumen no reemplaza el log. Describe el alcance previsto antes de ejecutar.

## 13. Devolución del log completo

Al finalizar una tarea, el usuario deberá copiar o adjuntar el log completo.

El log permite:

- confirmar cada validación
- identificar el punto exacto de un fallo
- preparar una continuación específica
- comprobar commit y push
- registrar la ruta del backup
- verificar el resultado final contra GitHub

Una captura parcial o una frase como “salió bien” no reemplaza el log cuando la tarea modifica el repositorio.

## 14. Diferencia entre script preparado y tarea cerrada

Un script preparado no significa que la tarea esté implementada.

La tarea solo queda cerrada cuando:

1. el script fue ejecutado
2. las validaciones pasaron
3. se creó el commit
4. se hizo push
5. el repositorio terminó limpio y sincronizado
6. el commit fue verificado contra GitHub

---

## 15. Logs como evidencia de diagnóstico y aprendizaje

El log completo no solo demuestra que una tarea se ejecutó.

También permite reconstruir el estado exacto cuando una tarea se detiene:

- último paso correcto
- comando que falló
- archivos pendientes
- migraciones creadas
- migraciones aplicadas
- cambios de base de datos
- pruebas ejecutadas
- existencia o ausencia de commit y push

Cuando una tarea use una fuente externa, el backup debe conservar cuando
corresponda:

- copia descargada
- URL
- SHA-256
- tamaño
- conteos extraídos
- validaciones aplicadas

Los logs y backups constituyen evidencia local. No deben versionarse, pero
sus conclusiones estables deben consolidarse en documentos del repositorio.
