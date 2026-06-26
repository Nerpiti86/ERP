# Lecciones aprendidas y estándar de implementación del ERP

Estado: vigente desde el corte documental D02.

Base verificada antes del corte:

```text
Repositorio: Nerpiti86/ERP
Rama: main
Commit: 4842d374f43d696e625368bc625a19dfc5a3ead6
Última tarea funcional cerrada: TAREA 0006
Pruebas: 243 OK
Migraciones de núcleo: hasta 0012
Catálogo ARCA-CLAE local: 958 actividades activas
```

## 1. Objetivo

Este documento consolida las lecciones técnicas, operativas y metodológicas
obtenidas durante la construcción del núcleo fiscal y empresarial del ERP.

No es un resumen histórico decorativo.

Su función es convertir lo aprendido en un estándar obligatorio para:

- diseñar tareas
- escribir scripts ejecutables
- modificar modelos Django
- aplicar migraciones
- integrar fuentes externas
- preservar datos históricos
- construir pantallas multiempresa
- definir permisos
- probar cambios
- documentar y cerrar tareas

Las reglas de este documento complementan el contrato operativo y la
mecánica de tareas TXT.

## 2. La fuente de verdad es el repositorio remoto

Antes de diseñar una tarea se debe revisar `main` remoto.

No alcanza con:

- recordar una conversación anterior
- usar un resumen histórico
- asumir que un archivo mantiene la misma estructura
- confiar en un script preparado antes de otros commits
- usar documentación desactualizada como representación del código vigente

La revisión mínima debe incluir:

1. SHA actual de `main`.
2. Archivos realmente relacionados con la tarea.
3. Modelos y migraciones vigentes.
4. Formularios, vistas, rutas y plantillas afectadas.
5. Permisos y roles existentes.
6. Pruebas que ya cubren la funcionalidad.
7. Documentos rectores y documentos específicos.
8. Estado real de datos locales cuando sea contractual.

Una tarea debe fijar un `HEAD_ESPERADO`.

Si `HEAD` cambia antes de ejecutarla, la tarea debe detenerse y revisarse.

## 3. Separar hechos, decisiones y suposiciones

Se deben distinguir tres categorías:

### Hecho verificado

Proviene de:

- código leído en GitHub
- log completo
- consulta de base de datos
- prueba ejecutada
- commit verificado
- fuente externa oficial descargada

### Decisión de diseño

Es una elección explícita adoptada para el ERP.

Ejemplos:

- no borrar actividades históricas
- separar catálogo oficial de asignaciones por empresa
- usar servicios transaccionales
- mantener el Django Admin como backoffice técnico

### Suposición pendiente

Es una inferencia que todavía necesita validación.

Una suposición no debe presentarse como funcionalidad existente ni usarse
como ancla contractual sin comprobarla.

## 4. Diseñar desde el dominio y no desde la pantalla

Una pantalla correcta no compensa un modelo débil.

La secuencia recomendada es:

```text
reglas de negocio
→ modelo
→ restricciones de base de datos
→ servicios transaccionales
→ formularios
→ vistas
→ permisos
→ plantillas
→ pruebas
→ documentación
```

Las reglas críticas deben existir en más de una capa cuando corresponda:

- validación amigable en formulario
- validación del modelo
- restricción en PostgreSQL
- operación atómica en servicio
- permiso validado en backend

La interfaz oculta o deshabilita acciones, pero no constituye seguridad.

## 5. PostgreSQL debe proteger invariantes críticas

El ERP usa PostgreSQL.

Cuando una regla puede expresarse en base de datos, debe evaluarse su
implementación mediante:

- `UniqueConstraint`
- restricciones únicas condicionales
- `CheckConstraint`
- claves foráneas con `PROTECT`
- índices orientados a consultas reales

Ejemplos implementados:

- una sola casa central activa por empresa
- una sola actividad principal activa por empresa
- una sola relación activa entre empresa y actividad
- una actividad principal debe estar activa
- una vigencia final no puede preceder a la inicial

La base de datos es la última barrera ante errores de concurrencia,
scripts manuales o futuras vistas defectuosas.

## 6. Los servicios concentran operaciones con efectos múltiples

Cuando una operación modifica más de un registro o debe conservar
trazabilidad, no debe implementarse únicamente en una vista o formulario.

Debe existir una capa de servicio.

Un servicio debe:

1. abrir una transacción
2. bloquear los registros relevantes cuando exista concurrencia posible
3. validar pertenencia a la empresa activa
4. aplicar todos los cambios
5. registrar auditoría
6. devolver un resultado explícito
7. revertir todo ante cualquier error

Ejemplo:

```text
cambiar actividad principal
→ bloquear actividades activas de la empresa
→ desmarcar principal anterior
→ marcar nueva principal
→ registrar estados anterior y nuevo
→ confirmar una única transacción
```

## 7. Multiempresa desde la consulta inicial

Todo dato funcional de empresa debe filtrarse por la empresa activa.

Nunca se debe:

- buscar un objeto solo por ID
- confiar en un ID recibido desde el navegador
- mostrar opciones de otra empresa
- modificar una relación sin validar pertenencia
- usar datos globales cuando deberían tener alcance empresarial

Patrón obligatorio:

```python
get_object_or_404(
    Modelo,
    pk=objeto_id,
    empresa=request.empresa_activa,
)
```

Las pruebas deben intentar manipular IDs de otra empresa.

## 8. Permisos funcionales en backend

Cada módulo funcional debe definir permisos explícitos.

No se debe reutilizar un permiso amplio por comodidad cuando el dominio
merezca permisos propios.

Para actividades económicas se definieron:

```text
actividades.ver
actividades.crear
actividades.editar
```

La implementación completa de permisos incluye:

1. definición en la matriz inicial
2. asignación a roles
3. carga idempotente
4. decoradores de vistas
5. validaciones adicionales para acciones POST
6. contexto de navegación
7. pruebas de lectura, escritura y denegación
8. verificación de que `staff` no reemplaza el permiso funcional
9. excepción técnica controlada para superusuarios, según política vigente

## 9. No inferir datos existentes sin evidencia

Las migraciones y tareas no deben deducir automáticamente información
fiscal o jurídica a partir de nombres, textos libres o convenciones.

Ejemplos:

- no marcar una sucursal como casa central por llamarse “Central”
- no convertir un domicilio histórico en campos estructurados por heurística
- no elegir una actividad principal por parecido textual
- no asignar actividades a empresas por datos incompletos

Cuando no existe certeza:

- se preserva el dato anterior
- se agregan campos nuevos vacíos
- se exige revisión humana
- se documenta la transición

## 10. Baja lógica e historia

Los datos maestros y fiscales no deben borrarse cuando poseen valor
histórico.

Patrones preferidos:

- `activa`
- vigencia desde
- vigencia hasta
- fecha de actualización
- observaciones
- auditoría
- snapshot histórico

Una baja lógica permite:

- conservar comprobantes y relaciones antiguas
- explicar decisiones pasadas
- reactivar cuando corresponda
- evitar claves foráneas rotas
- diferenciar presente de historia

## 11. Snapshot histórico frente a catálogos cambiantes

Una clave foránea a un catálogo vigente no alcanza para preservar la
representación histórica.

Si la fuente externa puede cambiar la descripción, la relación histórica
debe guardar una instantánea.

En `EmpresaActividad` se conservan:

```text
nomenclador_registrado
codigo_registrado
descripcion_registrada
fuente_sha256_registrada
```

Así, una actualización futura del catálogo ARCA no reescribe la
descripción que la empresa utilizó al registrar su actividad.

Regla general:

```text
relación al maestro actual
+ snapshot del dato relevante
= consulta vigente e historia reproducible
```

## 12. Fuentes oficiales externas

Una fuente externa oficial no debe consultarse en cada apertura de pantalla.

El patrón adoptado es:

```text
fuente oficial
→ descarga controlada
→ validación estructural
→ dry-run
→ catálogo local
→ auditoría de importación
→ uso funcional
```

La sincronización debe registrar:

- URL de origen
- fecha
- nombre del archivo
- SHA-256
- cantidad total
- registros creados
- registros actualizados
- registros reactivados
- registros desactivados

También debe incluir defensas contra descargas incompletas:

- tamaño mínimo
- cantidad mínima
- formato esperado
- códigos testigo
- descripciones no vacías
- transacción atómica

## 13. Los datos importados no viajan necesariamente con Git

Una migración puede crear tablas sin transportar el contenido operativo
importado localmente.

En el catálogo CLAE:

- Git contiene modelos, migración y sincronizador
- la base local contiene las 958 actividades importadas
- una instalación nueva queda con el catálogo vacío después de `migrate`
- se debe ejecutar la sincronización oficial para cargarlo

Las pantallas dependientes de un catálogo deben detectar el estado vacío y
mostrar una explicación operativa, no un error técnico.

## 14. Catálogos oficiales y Django Admin

El Django Admin es backoffice técnico, no una vía alternativa para
saltarse las reglas del ERP.

Un catálogo controlado por fuente oficial debe ser de solo lectura en
Admin:

```python
has_add_permission = False
has_change_permission = False
has_delete_permission = False
```

Las relaciones que requieren servicios, permisos y auditoría también
pueden ser de solo lectura en Admin.

Esto evita:

- códigos inventados
- descripciones alteradas manualmente
- cambios sin auditoría
- violación de reglas transaccionales
- divergencia respecto de la fuente oficial

## 15. Formularios para catálogos grandes

Un `<select>` con cientos o miles de opciones es válido técnicamente, pero
malo funcionalmente.

Para 958 actividades se adoptó:

- búsqueda por código
- búsqueda por descripción
- resultados limitados
- selección explícita
- ID oculto
- validación final en backend
- rechazo de actividades inactivas
- rechazo de relaciones activas duplicadas

La búsqueda mejora la experiencia, pero el backend sigue siendo la
autoridad.

## 16. Scripts de tarea: validación contractual

Todo script normal debe validar antes de modificar:

- repositorio exacto
- remote exacto
- rama `main`
- SHA esperado
- `git fetch origin main`
- sincronización `0 0`
- working tree limpio
- migraciones previas requeridas
- archivos y datos contractuales necesarios

Una continuación debe validar:

- el mismo SHA base
- sincronización `0 0`
- conjunto exacto de archivos pendientes
- migraciones aplicadas o pendientes
- datos modificados antes del corte
- ausencia de archivos ajenos

No se debe limpiar el repositorio para forzar una continuación.

## 17. Evitar anclas textuales frágiles

Una tarea falló porque buscó literalmente:

```text
Gestion funcional
```

y el documento real contenía:

```text
Gestión funcional
```

Lección:

- no depender de una línea completa si puede cambiar por tildes, espacios o formato
- preferir encabezados estructurales estables
- verificar que el ancla aparezca exactamente una vez
- usar nombres de clases, funciones o secciones semánticas
- abortar si el contexto no coincide
- probar la transformación contra el archivo remoto real

Una inserción automática debe cumplir:

```text
ancla encontrada exactamente una vez
+ resultado validado
+ conjunto final de archivos exacto
```

## 18. Inicialización de Django en scripts Python

Otra tarea falló al importar modelos Django desde Python directo sin
configurar el entorno.

Para usar modelos fuera de `manage.py`:

```python
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()
```

Alternativas preferibles:

- comando de administración
- `manage.py shell`
- prueba Django
- módulo ejecutado dentro del ciclo normal de Django

Regla:

No importar modelos Django desde un bloque Python independiente antes de
inicializar el registro de aplicaciones.

## 19. Orden seguro de validaciones y efectos

Los pasos irreversibles o con efectos persistentes deben ejecutarse al
final del proceso de validación.

Orden recomendado:

```text
generar archivos
→ normalizar
→ git diff --check
→ compilar Python
→ cargar plantillas
→ manage.py check
→ makemigrations --check
→ revisar sqlmigrate
→ revisar migrate --plan
→ pruebas específicas
→ suite completa
→ validar fuente externa real
→ backup de datos
→ aplicar migración
→ importar o transformar datos
→ verificar datos posteriores
→ staging selectivo
→ commit
→ push
→ verificación remota
```

Cuando sea posible, validar la fuente externa antes de alterar la base.

## 20. Validar el artefacto generado, no solo el generador

Un script puede ser sintácticamente válido y generar código inválido.

Antes de entregarlo se debe validar:

- `bash -n`
- bloques Python embebidos
- archivos Python escritos por heredoc
- puntos de inserción
- balance básico de plantillas
- lista exacta de archivos previstos
- finales de archivo
- ausencia de espacios finales

Durante la ejecución se debe volver a validar el resultado real:

- `py_compile`
- `compileall`
- carga de templates
- `manage.py check`
- migraciones
- pruebas

La validación previa reduce errores; no reemplaza la validación en el
entorno real.

## 21. Finales de archivo y CRLF

En Windows, Git puede advertir:

```text
LF will be replaced by CRLF the next time Git touches it
```

La advertencia no equivale por sí sola a un error.

La autoridad es:

```bash
git diff --check
```

Los archivos generados deben normalizarse con:

- UTF-8
- exactamente un salto final
- sin líneas en blanco adicionales al final
- sin espacios finales

No se debe modificar masivamente el repositorio solo para eliminar una
advertencia de conversión si el diff es correcto.

## 22. Staging selectivo

Nunca usar:

```bash
git add .
```

Cada tarea debe enumerar sus archivos.

Antes del commit se compara:

```text
archivos esperados
versus
archivos modificados
versus
archivos staged
```

Los tres conjuntos deben coincidir.

Esto evita incluir:

- logs
- archivos temporales
- cambios manuales ajenos
- descargas
- backups
- secretos

## 23. Continuaciones explícitas

Cuando una tarea falla después de generar cambios:

- no se ejecuta nuevamente el script original
- no se hace `reset --hard`
- no se borra el trabajo
- no se exige árbol limpio
- no se inicia otra tarea

Se crea una continuación que:

1. reconoce el estado exacto
2. respalda el estado pendiente
3. corrige la causa concreta
4. repite todas las validaciones
5. continúa desde el punto seguro
6. hace commit solo si todo pasa

La continuación debe aprender del fallo, no limitarse a mover el error al
paso siguiente.

## 24. Logs completos como herramienta de ingeniería

El log completo permitió identificar con precisión:

- la línea que falló
- el comando exacto
- los archivos ya generados
- si la migración fue creada
- si la migración fue aplicada
- si la base fue modificada
- si hubo commit
- si hubo push
- qué pruebas habían pasado

Una captura o un resumen no habría permitido preparar una continuación
segura.

El log es evidencia operativa y material de aprendizaje.

## 25. Backups orientados al riesgo

No alcanza con copiar archivos fuente.

Según la tarea, el backup puede incluir:

- archivos modificados
- diff previo
- estado Git
- base SQLite si existiera
- exportaciones JSON de tablas afectadas
- asignaciones de permisos
- registros históricos
- fuente externa descargada
- SHA de la fuente
- conteos antes de modificar

El backup debe corresponder al riesgo real de la tarea.

## 26. Pruebas por capas

Una funcionalidad completa necesita pruebas en varias capas.

### Modelo y base

- constraints
- validaciones
- normalización
- relaciones protegidas

### Servicio

- transacciones
- cambio de principal
- reactivación
- inactivación
- auditoría
- rollback

### Formulario

- datos requeridos
- vigencias
- catálogo inactivo
- duplicados
- pertenencia

### Vista y HTTP

- permisos
- GET y POST
- códigos de respuesta
- redirecciones
- mensajes
- catálogo vacío

### Multiempresa

- aislamiento de listados
- rechazo de IDs ajenos
- búsqueda global controlada
- acciones restringidas a la empresa activa

### Integración

- tarjeta de configuración
- estado completo o incompleto
- navegación
- roles iniciales
- contexto

Las pruebas específicas detectan rápido. La suite completa detecta
regresiones.

## 27. Definición de terminado

Una tarea no está terminada cuando:

- el código parece correcto
- el script fue entregado
- una pantalla abre
- la migración fue creada
- los tests específicos pasan
- el commit existe solo localmente

Está `CERRADA Y VERIFICADA` cuando:

1. todas las validaciones pasaron
2. la migración requerida fue aplicada
3. los datos posteriores fueron verificados
4. la suite completa pasó
5. el conjunto de archivos fue validado
6. se creó un commit específico
7. se hizo push
8. el working tree quedó limpio
9. la sincronización terminó `0 0`
10. el commit fue verificado directamente en GitHub

## 28. Documentación como parte de la implementación

La documentación específica debe modificarse dentro de la misma tarea
funcional.

Debe registrar:

- decisión de arquitectura
- reglas de negocio
- modelos
- permisos
- rutas
- estados
- migraciones
- comandos operativos
- limitaciones
- próxima etapa

La hoja de ruta general puede quedar histórica, pero debe recibir cortes
documentales para evitar representar como pendiente algo ya implementado.

No usar documentación antigua como ancla sin compararla con el código
actual.

## 29. Lista de control para tareas futuras

Antes de entregar una tarea:

```text
[ ] main remoto revisado
[ ] SHA esperado fijado
[ ] documentos rectores leídos
[ ] alcance y exclusiones definidos
[ ] reglas de dominio identificadas
[ ] restricciones de base evaluadas
[ ] permisos definidos
[ ] aislamiento multiempresa previsto
[ ] impacto en datos existentes analizado
[ ] backup proporcional al riesgo
[ ] anclas probadas contra archivos reales
[ ] Bash validado con bash -n
[ ] Python embebido compilado
[ ] archivos generados compilados
[ ] lista exacta de archivos prevista
[ ] pruebas específicas diseñadas
[ ] suite completa prevista
[ ] migración y datos posteriores verificados
[ ] staging selectivo
[ ] commit y push condicionados al éxito
[ ] verificación remota prevista
```

## 30. Principio final

El objetivo no es evitar para siempre cualquier error.

El objetivo es que:

- los errores se detecten antes del commit
- no se pierdan datos
- el estado quede observable
- la recuperación sea específica
- cada fallo mejore el método
- el repositorio remoto permanezca confiable
- la arquitectura sea más fuerte después de cada tarea

El aprendizaje solo queda incorporado cuando se convierte en una regla,
una validación, una prueba o una decisión documentada.

<!-- BEGIN LECCIONES_TAREA_0016 -->
## Lecciones incorporadas por la TAREA 0016

- una sincronización documental integral debe relevar código, migraciones, rutas, permisos, comandos, plantillas y pruebas;
- los números de pruebas, permisos y relaciones deben obtenerse de fuentes ejecutables, no copiarse de cortes anteriores;
- la documentación histórica debe conservarse, pero debe quedar subordinada a una fotografía vigente claramente identificada;
- un permiso definido para un módulo futuro no convierte ese módulo en funcionalidad implementada;
- los hallazgos técnicos detectados durante una tarea documental se registran y se corrigen en tareas independientes;
- el README debe ser una síntesis actual y no una acumulación de estados obsoletos;
- el documento canónico de estado no reemplaza los documentos rectores de dominio ni el contrato operativo.
<!-- END LECCIONES_TAREA_0016 -->


<!-- BEGIN ESTANDAR_LISTADOS_TAREA_0018 -->
## Estándar de listados incorporado por la TAREA 0018

- las métricas sin acción inmediata no deben desplazar la tabla principal;
- cada listado debe presentar primero el título y las acciones principales;
- la búsqueda principal utiliza `GET`, parámetro `q` y entrada `type="search"`;
- los filtros específicos del dominio conservan su semántica backend;
- las acciones se denominan `Buscar` y `Limpiar` y mantienen un orden uniforme;
- `Limpiar` se muestra únicamente cuando existen filtros efectivos;
- cada tabla informa la cantidad de resultados después de aplicar los filtros;
- los contenedores visuales compartidos se resuelven con clases de
  `static/css/erp.css`, sin duplicar reglas entre módulos;
- la unificación visual no autoriza a alterar permisos, aislamiento,
  parámetros, modelos ni servicios de dominio;
- paginación, ordenamiento dinámico y búsqueda asincrónica requieren tareas
  independientes.
<!-- END ESTANDAR_LISTADOS_TAREA_0018 -->
