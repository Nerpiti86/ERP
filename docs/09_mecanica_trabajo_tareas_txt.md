# Mecánica de trabajo mediante tareas ejecutables TXT

Estado: revisada y ampliada en el corte documental D02.

## 1. Objetivo

Definir la forma de trabajo entre el usuario y el asistente para que cada cambio del ERP sea:

- comprensible
- reproducible
- auditable
- reversible antes del commit
- validado antes del push
- verificable contra GitHub

## 2. Unidad de trabajo

Se trabaja una sola tarea lógica por vez.

Formato habitual:

```text
TAREA NN — Descripción
```

Los cortes documentales usan una numeración separada:

```text
CORTE DOCUMENTAL DNN — Descripción
```

Esto evita alterar la secuencia funcional del ERP.

## 3. Archivos entregados

Por cada tarea se entregan normalmente dos archivos:

```text
tareaNN_descripcion.txt
tareaNN_resumen_operativo.txt
```

El primer archivo contiene Bash ejecutable, aunque use extensión `.txt`.

El segundo explica:

- objetivo
- alcance
- archivos previstos
- validaciones
- exclusiones
- commit esperado
- próximo paso

## 4. Ubicación de los scripts

Los archivos de tarea no se copian dentro del repositorio salvo decisión explícita.

Pueden ejecutarse desde Descargas, Escritorio u otra carpeta:

```bash
bash "D:\ruta\tareaNN_descripcion.txt"
```

El propio script debe posicionarse en:

```text
/d/NeriSoft2/ERP
```

Los scripts de tarea son instrumentos de ejecución, no código fuente del ERP.

## 5. Preparación por parte del asistente

Antes de generar una tarea técnica, el asistente debe:

1. revisar el estado vigente de `main` remoto
2. leer los archivos relevantes
3. respetar documentos rectores
4. distinguir hechos seguros de suposiciones
5. no afirmar que una tarea está implementada solo porque su script fue preparado
6. diseñar una tarea pequeña y auditable
7. indicar claramente qué queda fuera de alcance

## 6. Ejecución por parte del usuario

El usuario:

1. descarga el `.txt`
2. lo ejecuta desde Git Bash
3. no modifica manualmente el repositorio durante la ejecución
4. copia o adjunta el log completo
5. no inicia otra tarea hasta cerrar la actual o declarar una continuación

## 7. Contrato mínimo del Bash

Todo script normal debe:

1. usar el repositorio `/d/NeriSoft2/ERP`
2. validar el remote esperado
3. ejecutar `git fetch origin main`
4. validar rama `main`
5. validar `origin/main...HEAD = 0 0`
6. exigir working tree limpio
7. crear log en `logs/`
8. crear backup en `logs/backup/` si modifica archivos
9. validar archivos esperados
10. realizar una sola tarea
11. mostrar el diff relevante
12. ejecutar `git diff --check`
13. ejecutar validaciones específicas
14. evitar commit y push ante cualquier fallo
15. hacer `git add` selectivo
16. crear un commit específico
17. hacer push a `origin/main`
18. validar working tree limpio y sincronización final `0 0`
19. mostrar al final log, backup, commit y resultado

El script no debe:

- usar colores ANSI como requisito de lectura
- ocultar errores
- commitear archivos ajenos a la tarea
- usar `git add .`
- cerrar intencionalmente la terminal
- ejecutar `git reset --hard`
- borrar cambios locales no comprendidos
- versionar logs, backups, `.env` o secretos

## 8. Validaciones mínimas

Para código Django:

```bash
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py test apps.core apps.nucleo
.venv/Scripts/python.exe -m compileall config apps
```

Para documentación:

```bash
git diff --check
```

Una tarea puede agregar validaciones dirigidas.

## 9. Commit y push

El script puede hacer commit y push automáticamente únicamente si todas las validaciones pasan.

Reglas:

- un commit por tarea lógica
- mensaje breve y específico
- `git add` de archivos enumerados
- push a `origin/main`
- cierre con `0 0`

Preparar un script no equivale a ejecutar una tarea.

Ejecutar localmente sin push tampoco equivale a cerrarla.

## 10. Revisión del resultado

Después de recibir el log, el asistente debe:

1. verificar que las validaciones pasaron
2. comprobar commit y push
3. verificar el commit contra GitHub
4. confirmar el SHA completo
5. registrar tests, log y backup
6. declarar la tarea cerrada solo después de esa verificación

## 11. Continuación explícita

Si una tarea falla después de modificar archivos:

- no se inicia una tarea distinta
- no se exige árbol limpio artificialmente
- se prepara una continuación específica
- se valida que el estado sucio corresponda a la tarea fallida
- se crea un nuevo backup
- se corrige solo el problema observado
- se repiten todas las validaciones
- se hace commit y push únicamente si todo pasa

Nomenclatura sugerida:

```text
tareaNN_continuacion_1_descripcion.txt
tareaNN_continuacion_2_descripcion.txt
```

La continuación no debe aplicar soluciones genéricas sin analizar el log real.

## 12. Comunicación

Se usan estas etiquetas:

```text
[SEGURO]
[SUPOSICION]
```

`[SEGURO]` identifica hechos comprobados en archivos, logs o GitHub.

`[SUPOSICION]` identifica decisiones provisionales o inferencias que todavía deben validarse.

El resultado debe ser legible para una persona no especializada, sin perder precisión técnica.

## 13. Estado de una tarea

Una tarea puede estar:

```text
PREPARADA
EN EJECUCIÓN
DETENIDA
EN CONTINUACIÓN
CERRADA Y VERIFICADA
```

Solo `CERRADA Y VERIFICADA` significa que la funcionalidad forma parte de `main`.

## 14. Ventajas observadas

La mecánica permite:

- reducir edición manual
- evitar instrucciones fragmentadas
- conservar logs completos
- detectar fallos antes del commit
- retomar tareas incompletas sin perder contexto
- mantener `main` alineada con el remoto
- revisar cada cambio como una unidad
- documentar con precisión qué está realmente terminado

## 15. Reglas incorporadas en D02

Antes de entregar un script, el asistente debe validar no solo el Bash, sino
también el código que el Bash generará.

Validaciones previas recomendadas:

- `bash -n`
- compilación de Python embebido
- compilación sintáctica de archivos Python heredoc
- prueba de anclas contra archivos reales
- verificación de finales de archivo
- lista exacta de archivos esperados

## 16. Prohibición de anclas frágiles

No se debe buscar una línea documental completa si una tilde, un espacio o
una modificación menor puede invalidarla.

Cada transformación debe:

1. usar una referencia semántica
2. exigir una única coincidencia
3. validar el resultado
4. abortar ante cualquier ambigüedad

## 17. Bloques Python conscientes de Django

Cuando un bloque Python importe modelos Django fuera de `manage.py`, deberá
inicializar Django antes de importar los modelos.

Se preferirá ejecutar la lógica mediante comandos de administración o
`manage.py shell`.

## 18. Orden de validación mejorado

La tarea debe retrasar migraciones e importaciones hasta que hayan pasado:

- controles estáticos
- carga de plantillas
- `manage.py check`
- revisión de migraciones
- pruebas específicas
- suite completa
- validación de fuentes externas

Las comprobaciones posteriores de datos son obligatorias antes del commit.

## 19. Referencia consolidada

Las lecciones completas, incluyendo arquitectura, fuentes externas,
historial, permisos, multiempresa, pruebas y definición de terminado, están
en:

```text
docs/17_lecciones_aprendidas_y_estandar_implementacion.md
```
