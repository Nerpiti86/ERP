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

## 9. Decision final

A partir de este punto, toda tarea del ERP debera dejar log local en logs/.

La carpeta logs/ seguira ignorada por Git.

Los documentos de politica y arquitectura si se versionaran dentro de docs/.
