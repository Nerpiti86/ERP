# Configuración fiscal y registral de empresa

Estado: relevamiento funcional y técnico aprobado para implementación gradual.

Fecha del relevamiento: 20/06/2026.

## 1. Objetivo

Definir cómo debe evolucionar la configuración de empresa del ERP para
representar correctamente:

- identidad del contribuyente
- naturaleza jurídica
- condición frente al IVA
- inicio de actividades
- cierre de ejercicio predeterminado
- domicilios fiscales y operativos
- actividades económicas
- situación frente a Ingresos Brutos
- jurisdicciones
- condición de agente de retención o percepción
- sistemas de presentación tributaria

El documento evita copiar literalmente la estructura de otro software y
establece un modelo propio, gradual, auditable y compatible con el diseño
multiempresa del ERP.

No constituye asesoramiento impositivo. Las reglas tributarias concretas
deben verificarse por período y jurisdicción antes de automatizar cálculos
o presentaciones.

## 2. Estado actual verificado

El modelo `Empresa` guarda actualmente:

- CUIT
- razón social
- nombre de fantasía
- condición frente al IVA
- estado activo
- fechas técnicas de creación y actualización

El modelo `Sucursal` guarda actualmente:

- empresa
- código
- nombre
- domicilio como texto libre
- localidad
- provincia como texto libre
- país
- estado activo

La portada integrada de configuración ya separa:

- Datos de la empresa
- Sucursales
- Parámetros operativos
- Usuarios y accesos

El documento rector original del núcleo ya preveía conceptualmente datos
adicionales como:

- ingresos brutos
- actividad principal
- domicilio fiscal
- provincia
- código postal
- inicio de actividades
- contacto

Por lo tanto, esta evolución completa una parte del diseño inicial y no
introduce un dominio ajeno al ERP.

## 3. Hallazgos externos relevantes

### 3.1. Actividades económicas

ARCA administra las actividades económicas mediante el Registro Único
Tributario y un nomenclador vigente.

Un contribuyente puede declarar varias actividades. Debe existir una
actividad principal, determinada por el criterio aplicable de mayor
facturación o ingresos.

La actividad declarada debe ser compatible con el nomenclador nacional
y, cuando corresponda, con NAES o con los códigos de las jurisdicciones.

Conclusión:

- no se crearán columnas `otra_actividad_1` a `otra_actividad_14`
- las actividades serán registros dinámicos
- deberá existir exactamente una actividad principal activa por empresa
- el nomenclador y su vigencia deberán identificarse

### 3.2. Domicilios

ARCA y el Registro Único Tributario distinguen domicilios y
caracterizaciones.

El domicilio fiscal nacional puede diferir del domicilio fiscal
provincial. También existe la caracterización `Principal de actividades`
para el domicilio donde se desarrolla la actividad principal.

Conclusión:

- domicilio fiscal no es sinónimo de sucursal
- provincia no debe duplicarse sin control dentro de `Empresa`
- una empresa puede necesitar más de un domicilio
- un mismo domicilio puede cumplir varias caracterizaciones
- las sucursales seguirán representando establecimientos operativos

### 3.3. Ingresos Brutos

Santa Fe distingue, entre otros, contribuyentes locales y contribuyentes
de Convenio Multilateral.

Los contribuyentes locales operan mediante el padrón provincial.
Convenio Multilateral administra inscripción, jurisdicciones, actividades
y modificaciones mediante los sistemas federales habilitados.

Conclusión:

- `condición frente a IIBB` no debe ser un único texto ambiguo
- se debe separar régimen de inscripción, tratamiento fiscal y
  jurisdicciones
- una empresa puede tener varias jurisdicciones activas
- la jurisdicción sede debe representarse expresamente

### 3.4. Agentes de recaudación

La condición de agente de retención o percepción puede depender de:

- jurisdicción
- tipo de agente
- vigencia
- designación
- sistema de presentación

Santa Fe utiliza sistemas como SIPRIB y, para determinados agentes de
Convenio Multilateral, SIRCAR.

Conclusión:

- `es agente de retención` y `es agente de percepción` no deben quedar
  como simples booleanos globales en `Empresa`
- SIRCAR no debe modelarse como configuración general de toda empresa
- la condición de agente debe tener jurisdicción, tipo, vigencia y
  sistema de presentación

## 4. Decisiones de modelado

## 4.1. Empresa conserva la identidad principal

`Empresa` seguirá representando al contribuyente y al ámbito multiempresa
del ERP.

Datos que permanecen en `Empresa`:

- `cuit`
- `razon_social`
- nombre corto o nombre de fantasía
- `condicion_iva`
- `activa`
- datos técnicos de auditoría temporal

Decisión de interfaz:

El campo actual `nombre_fantasia` podrá mostrarse inicialmente como:

`Nombre corto para listados`

No se hará una migración destructiva solo para cambiar el rótulo.

## 4.2. Usuario propietario no es un dato fiscal

No se agregará un campo `usuario_propietario` a `Empresa`.

El ERP ya resuelve acceso y responsabilidad mediante:

- `UsuarioEmpresa`
- `UsuarioRolEmpresa`
- roles funcionales
- permisos por empresa

Si en el futuro se necesita un responsable administrativo interno, será
una relación funcional explícita y no un supuesto propietario tributario.

## 4.3. Naturaleza del contribuyente

Se propone una clasificación explícita:

- `PERSONA_HUMANA`
- `PERSONA_JURIDICA`
- `SUCESION_INDIVISA`
- `OTRA`

No se utilizará simultáneamente:

- tipo `Persona Física`
- booleano `Sucesión indivisa`

La sucesión indivisa será una naturaleza propia y no una marca
redundante.

Terminología de interfaz:

Se usará `Persona humana`, salvo que una integración externa requiera
otra denominación.

## 4.4. Datos personales estructurados

Los datos siguientes solo tendrán sentido cuando la naturaleza lo
requiera:

- apellido
- apellido materno opcional
- nombres
- fecha de nacimiento

No deben aparecer ni ser obligatorios para personas jurídicas.

Se recomienda concentrarlos en un perfil fiscal asociado a la empresa,
con validaciones condicionales.

## 4.5. Denominación y razón social

No se duplicará `Denominación` si representa el mismo dato que
`razon_social`.

La razón social debe contener la denominación fiscal oficial o, para una
persona humana, el nombre legal utilizado como contribuyente.

El nombre corto se utilizará únicamente para listados e interfaz.

## 4.6. Inicio de actividades

Se incorporará una fecha de inicio de actividades dentro del perfil
fiscal.

Debe distinguirse de:

- fecha de creación del registro en el ERP
- fecha de alta de una jurisdicción
- fecha de inicio de una actividad económica específica
- fecha de inicio de una sucursal

## 4.7. Cierre del ejercicio

El ERP ya tiene `EjercicioFiscal` con fechas exactas.

Se podrá guardar un:

`mes_cierre_ejercicio_predeterminado`

Su función será proponer nuevos ejercicios.

No reemplazará ni modificará automáticamente las fechas de los ejercicios
ya creados.

## 5. Sucursales y domicilios

## 5.1. Decisión de arquitectura

Los domicilios físicos se administran dentro de `Sucursal`.

No se crea un modelo `DomicilioEmpresa` independiente en esta etapa.

Cada sucursal representa un establecimiento físico y contiene:

- identificación operativa
- domicilio estructurado
- estado activo o inactivo
- funciones que cumple para la empresa

Las jurisdicciones de Ingresos Brutos continúan separadas porque una
empresa puede estar inscripta en una jurisdicción sin poseer allí una
sucursal física.

## 5.2. Domicilio estructurado de Sucursal

Campos incorporados:

- calle
- número
- sector
- torre
- piso
- departamento
- barrio
- localidad
- código postal
- partido o departamento
- provincia
- país

El campo histórico `domicilio` se conserva durante la transición y no se
borra ni transforma automáticamente.

La presentación usa el domicilio estructurado cuando está completo y
recurre al texto histórico como respaldo cuando todavía no fue migrado
manualmente.

## 5.3. Funciones del establecimiento

Una misma sucursal puede cumplir varias funciones:

- casa central
- domicilio fiscal nacional
- domicilio fiscal provincial
- domicilio legal
- principal lugar de actividades
- depósito
- local comercial
- oficina administrativa
- otras funciones

Las cinco primeras funciones son exclusivas entre sucursales activas de
una misma empresa.

Una sucursal inactiva puede conservar esas marcas como información
histórica sin bloquear la designación de una sucursal activa actual.

## 5.4. Estado de completitud

La sección de sucursales se considera completa cuando:

- existe al menos una sucursal activa
- todas las sucursales activas tienen domicilio estructurado completo
- una sucursal activa está marcada como casa central

No se infieren funciones ni direcciones a partir de nombres existentes.

## 6. Actividades económicas

## 6.1. Catálogo

### ActividadEconomica

Campos conceptuales:

- sistema o nomenclador
- código
- descripción
- vigencia desde
- vigencia hasta
- activa

Sistemas iniciales posibles:

- `ARCA_CLAE`
- `NAES`
- `PROVINCIAL`
- `OTRO`

No se asumirá que dos códigos iguales de nomencladores diferentes son
necesariamente equivalentes.

## 6.2. Relación con empresa

### EmpresaActividad

Campos conceptuales:

- empresa
- actividad
- principal
- activa
- orden de visualización
- vigencia desde
- vigencia hasta
- observaciones

Reglas:

- una empresa puede tener cualquier cantidad de actividades
- no existe un máximo artificial de catorce actividades
- debe existir como máximo una actividad principal activa
- antes de completar la configuración fiscal debe existir al menos una
  actividad activa
- la baja histórica no debe borrar la relación
- el cambio de actividad principal debe conservar trazabilidad

## 7. Ingresos Brutos

## 7.1. Separación de conceptos

No se utilizará un único campo `condicion_iibb` para representar todo.

Se distinguen:

### Régimen de inscripción

Valores conceptuales:

- `NO_INSCRIPTO`
- `LOCAL`
- `CONVENIO_MULTILATERAL`

### Tratamiento fiscal general

Valores conceptuales:

- `GRAVADO`
- `EXENTO`
- `NO_ALCANZADO`
- `MIXTO`

El tratamiento puede variar por actividad o jurisdicción. Por eso, el
valor general será informativo y no reemplazará reglas específicas.

## 7.2. Configuración general

### ConfiguracionIIBBEmpresa

Campos conceptuales:

- empresa
- régimen
- tratamiento general
- jurisdicción sede
- número de inscripción
- fecha de alta
- fecha de baja
- activa
- observaciones

## 7.3. Jurisdicciones

### EmpresaJurisdiccionIIBB

Campos conceptuales:

- configuración IIBB
- jurisdicción
- número de inscripción o cuenta
- sede
- activa
- fecha de alta
- fecha de baja
- tratamiento
- observaciones

Reglas:

- una configuración de Convenio Multilateral puede tener varias
  jurisdicciones
- debe existir como máximo una jurisdicción sede activa
- la jurisdicción sede debe pertenecer al conjunto de jurisdicciones
  activas
- los ceses deben conservarse históricamente

## 7.4. Catálogo jurisdiccional

Se propone un catálogo común:

### JurisdiccionFiscal

Campos conceptuales:

- código interno
- nombre
- código ISO cuando corresponda
- código de Comisión Arbitral cuando corresponda
- activa

Este catálogo podrá utilizarse tanto en domicilios como en IIBB.

## 8. Agentes de retención y percepción

### AgenteRecaudacionIIBB

Campos conceptuales:

- empresa
- jurisdicción
- tipo de agente
- número o código de inscripción
- régimen o código predeterminado
- sistema de presentación
- origen de presentación
- tipo de presentación
- fecha desde
- fecha hasta
- activo
- observaciones

Tipos iniciales:

- `RETENCION`
- `PERCEPCION`

Sistemas iniciales posibles:

- `SIPRIB`
- `SIRCAR`
- `OTRO`

Reglas:

- una empresa puede ser agente en una jurisdicción y no en otra
- puede ser agente de retención, percepción o ambos
- debe conservarse la vigencia histórica
- el sistema de presentación no se deduce solo del tipo de agente
- los códigos de régimen deben validarse contra la jurisdicción y vigencia
  cuando se implemente el motor tributario

## 9. Campos del software relevado que no se copiarán directamente

### Primer año IIBB

No se recomienda un booleano permanente.

Debe derivarse de:

- fecha de alta en IIBB
- período fiscal procesado
- reglas de la jurisdicción

### Incluir montos exentos en base imponible

No es un dato maestro universal de la empresa.

Debe pertenecer a una política de liquidación por:

- jurisdicción
- régimen
- período de vigencia

### Incluir montos no gravados en base imponible

Se aplica el mismo criterio anterior.

### Mínimo de base imponible

No se guardará como atributo fijo de `Empresa`.

Puede variar por:

- jurisdicción
- período fiscal
- actividad
- régimen

### Mínimo de impuesto determinado

Tampoco se guardará como atributo fijo de `Empresa`.

### Posee actividad especial

No se utilizará un booleano genérico.

La especialidad debe relacionarse con:

- actividad económica
- jurisdicción
- norma o tratamiento
- vigencia

## 10. Permisos

## 10.1. Datos del contribuyente

Permisos existentes:

- `empresas.ver`
- `empresas.editar`

Se utilizarán para identidad, perfil fiscal y domicilios básicos.

## 10.2. Actividades e impuestos

Se propone incorporar más adelante:

- `impuestos.ver`
- `impuestos.editar`

La condición IIBB, jurisdicciones y agentes no debe quedar protegida
únicamente por `parametros.editar`.

## 10.3. Portada integrada

La portada integrada actualmente se habilita mediante permisos de
parámetros.

Cuando se activen las nuevas secciones deberá aceptar acceso si el usuario
posee al menos uno de los permisos funcionales de configuración:

- empresas
- sucursales
- parámetros
- usuarios
- impuestos

Cada acción interna seguirá validando su permiso específico.

## 11. Interfaz objetivo

La portada de configuración evolucionará hacia:

1. Datos del contribuyente
2. Sucursales y domicilios
3. Actividades económicas
4. Ingresos Brutos
5. Parámetros operativos
6. Usuarios y accesos

Cada tarjeta deberá mostrar:

- resumen real
- estado completo, incompleto o no aplicable
- advertencias concretas
- enlace a su pantalla propia
- modo solo lectura cuando corresponda

No se mostrarán botones deshabilitados indefinidamente una vez que la
sección tenga implementación propia.

## 12. Estrategia de migración

Principios:

- no borrar datos existentes
- no renombrar columnas destructivamente sin necesidad
- no convertir provincia o domicilio de sucursal sin backup y validación
- crear campos inicialmente opcionales cuando existan empresas reales
- completar datos mediante pantalla o migración controlada
- agregar obligatoriedad solo después de cargar los datos existentes
- conservar fechas y estados históricos
- ejecutar una migración lógica por tarea

Datos actuales a preservar:

- CUIT
- razón social
- nombre de fantasía
- condición IVA
- estado activo
- sucursales y sus domicilios actuales
- accesos y roles
- parámetros operativos

## 13. Secuencia recomendada de implementación

### Etapa 1. Datos básicos del contribuyente

Alcance:

- nombre corto para listados
- naturaleza del contribuyente
- inicio de actividades
- mes de cierre predeterminado
- datos condicionales de persona humana
- pantalla propia
- permisos `empresas.ver` y `empresas.editar`

No incluye domicilios, actividades ni IIBB.

### Etapa 2. Sucursales y domicilios

Alcance:

- listado propio de sucursales
- alta y edición
- domicilio estructurado
- funciones múltiples del establecimiento
- exclusividad de funciones centrales y fiscales
- preservación del domicilio histórico
- resumen real en la portada

### Etapa 3. Actividades económicas

Alcance:

- catálogo
- relación dinámica
- actividad principal
- vigencias
- resumen en portada

### Etapa 4. Inscripción en Ingresos Brutos

Alcance:

- régimen
- tratamiento general
- jurisdicción sede
- jurisdicciones activas
- número de inscripción
- vigencias

### Etapa 5. Agentes y presentaciones

Alcance:

- retención
- percepción
- jurisdicción
- SIPRIB
- SIRCAR
- códigos y vigencias

### Etapa 6. Reglas de liquidación

Alcance futuro:

- inclusión de exentos
- inclusión de no gravados
- mínimos
- tratamientos especiales
- vigencia por período
- motor tributario

## 14. Próxima tarea de implementación

La próxima tarea técnica recomendada es:

`TAREA 0003 - Datos básicos del contribuyente`

Alcance cerrado:

- ampliar el perfil básico sin mezclar domicilios, actividades o IIBB
- crear pantalla propia de consulta y edición
- mantener compatibilidad con empresas existentes
- usar permisos de empresas
- integrar estado real en la portada
- agregar migración, formularios, vistas y pruebas

## 15. Fuentes oficiales consultadas

- ARCA, Registro Único Tributario: funcionalidades, actividades,
  jurisdicciones y tipos de domicilios.
- ARCA, alta, modificación o baja de domicilios, actividades e impuestos.
- Comisión Arbitral, Padrón Web y Registro Único Tributario para
  Convenio Multilateral.
- Comisión Arbitral, nomenclador NAES.
- Gobierno de Santa Fe, Impuesto sobre los Ingresos Brutos.
- Gobierno de Santa Fe, Padrón Web de Contribuyentes Locales.
- Gobierno de Santa Fe, SIRCAR para agentes alcanzados.
- Gobierno de Santa Fe, SIPRIB.
- Gobierno de Santa Fe, Padrón de Alícuotas de Retenciones y
  Percepciones.

## 16. Implementación de la etapa 1

La TAREA 0003 implementa los datos básicos del contribuyente.

Se incorpora:

- modelo `PerfilFiscalEmpresa` relacionado uno a uno con `Empresa`
- naturaleza del contribuyente
- fecha de inicio de actividades
- mes de cierre predeterminado
- apellido
- apellido materno
- nombres
- fecha de nacimiento
- pantalla propia de consulta y edición
- validación con permisos `empresas.ver` y `empresas.editar`
- resumen y estado de completitud en la portada integrada

Decisiones preservadas:

- `Empresa.nombre_fantasia` continúa como campo técnico y se presenta como
  `Nombre corto para listados`
- el cierre se almacena como mes y no como fecha fija
- los ejercicios existentes no se modifican
- los datos personales se aplican únicamente a personas humanas y
  sucesiones indivisas
- domicilios, actividades económicas e IIBB permanecen fuera de esta etapa
- los datos reales se cargan localmente y no se incluyen en migraciones ni
  pruebas versionadas

## 17. Implementación de la etapa 2

La TAREA 0004 implementa sucursales y domicilios estructurados.

Se incorpora:

- CRUD funcional sin borrado físico
- domicilio estructurado directamente en `Sucursal`
- conservación del campo histórico `domicilio`
- funciones múltiples por establecimiento
- restricciones para funciones exclusivas
- permisos específicos de consulta, creación y edición
- listado propio
- integración con la portada de configuración
- pruebas de aislamiento multiempresa

No se incorporan jurisdicciones de Ingresos Brutos ni se infieren
funciones sobre las sucursales existentes.

## 18. Implementacion del catalogo oficial CLAE

La TAREA 0005 incorpora la base tecnica previa a la gestion de actividades
por empresa.

Se implementa:

- catalogo local `ActividadEconomica`
- nomenclador `ARCA_CLAE`
- sincronizacion desde la pagina oficial vigente
- validacion de descargas parciales
- hash SHA-256 de la fuente
- historial de importaciones
- actualizacion idempotente
- desactivacion sin borrado de codigos ausentes

La asignacion de actividades a empresas y su tarjeta funcional se realiza
en la etapa siguiente.

## 19. Implementación de actividades económicas por empresa

La TAREA 0006 implementa la relación `EmpresaActividad` dentro de
Configuración de empresa.

Resultado:

- selección exclusiva desde el catálogo ARCA-CLAE activo
- actividad principal y secundarias
- vigencias y observaciones
- orden de visualización
- baja lógica
- una sola principal activa por empresa
- prevención de duplicados activos
- instantánea histórica de código, descripción, nomenclador y SHA-256
- servicios transaccionales
- auditoría de altas, cambios e inactivaciones
- permisos funcionales propios
- buscador por código o descripción
- integración con el estado de configuración base

La relación física con sucursales no se infiere. Las actividades pertenecen
a la empresa y las sucursales continúan representando establecimientos.

## 20. Implementación de Ingresos Brutos y jurisdicciones

La TAREA 0007 implementa:

- catálogo `JurisdiccionFiscal`
- 24 códigos oficiales COMARB del 901 al 924
- configuraciones históricas de IIBB por empresa
- régimen local, Convenio Multilateral o no inscripto
- tratamiento fiscal general
- números de inscripción
- fechas de alta y baja
- jurisdicciones activas e históricas
- una única jurisdicción sede activa
- snapshot histórico
- baja lógica
- servicios transaccionales
- auditoría
- permisos `iibb.*`
- tarjeta dentro de Configuración de empresa

Las jurisdicciones fiscales permanecen separadas de las sucursales físicas.

No se implementan liquidaciones, alícuotas ni declaraciones juradas.
