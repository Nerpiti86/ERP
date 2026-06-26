# Maestro de productos y servicios

Estado: primera versión funcional implementada con núcleo, servicios, permisos, catálogos e interfaz ERP.

## 1. Objetivo

Definir un maestro único, genérico y comprensible para registrar los productos
y servicios administrados por cada empresa del ERP.

El maestro debe resolver primero la operación habitual. Las funciones avanzadas
se incorporarán en tareas separadas únicamente cuando exista un caso de uso
concreto.

## 2. Principio general

La entidad central se denomina `Item` y pertenece obligatoriamente a una
empresa.

Cada ítem tiene un tipo obligatorio:

- `PRODUCTO`
- `SERVICIO`

El tipo identifica qué es el ítem. Las capacidades indican cómo participa en
la operación:

- se compra
- se vende
- controla stock

Compra y venta son independientes. No se deducen automáticamente desde el
tipo.

## 3. Ficha principal

La primera versión del maestro tendrá los siguientes datos conceptuales:

- empresa
- código interno
- nombre
- descripción ampliada opcional
- tipo: producto o servicio
- categoría opcional
- marca opcional
- unidad de medida base
- se compra
- se vende
- controla stock
- tratamiento y alícuota predeterminados de IVA
- activo
- observaciones
- fechas técnicas de creación y actualización

## 4. Reglas obligatorias

### 4.1. Código interno

El código interno será:

- obligatorio
- único por empresa
- normalizado a mayúsculas
- inmutable después del alta
- no reutilizable aunque el ítem quede inactivo

La generación automática de códigos podrá agregarse posteriormente como una
configuración por empresa. La primera implementación puede exigir ingreso
manual sin alterar esta regla de identidad.

### 4.2. Compra, venta y stock

- un producto puede comprarse, venderse o realizar ambas operaciones
- un producto puede controlar stock o no hacerlo
- un servicio puede comprarse, venderse o realizar ambas operaciones
- un servicio nunca controla stock
- todo ítem debe participar al menos en compra o venta

### 4.3. Variantes

Una variante se registra como otro ítem cuando necesita identidad operativa
propia, por ejemplo:

- código interno diferente
- precio diferente
- stock independiente
- código de barras propio
- identificación separada en compras o ventas

La primera versión no generará combinaciones automáticas de atributos ni usará
un modelo obligatorio de producto padre.

### 4.4. Baja lógica

Los ítems no se eliminan como operación habitual. Se inactivan conservando su
identidad y sus referencias históricas.

La reactivación deberá ser una acción controlada y auditada cuando se incorpore.

## 5. Catálogos relacionados

### 5.1. Categorías

La categoría será un catálogo por empresa, reutilizable y con baja lógica.

La primera versión utilizará una clasificación simple. Las múltiples
jerarquías y los atributos heredados quedan fuera del primer bloque técnico.

### 5.2. Marcas

La marca será un catálogo opcional por empresa, reutilizable y con baja lógica.

No será obligatoria para productos ni servicios.

### 5.3. Unidades de medida

La unidad base no será texto libre. Se seleccionará desde un catálogo local
controlado de unidades de medida.

La fuente oficial ARCA, su carga inicial y su mecanismo de actualización se
definirán e implementarán en una tarea específica antes de habilitar el alta
funcional completa de ítems.

### 5.4. IVA

El tratamiento predeterminado será:

- gravado
- exento
- no gravado

Cuando sea gravado, la alícuota será obligatoria y se seleccionará desde un
catálogo fiscal controlado. No se almacenará como texto libre.

## 6. Información relacionada prevista

El maestro debe poder ampliarse mediante relaciones separadas para:

- códigos de barras y otros identificadores externos
- presentaciones y factores respecto de la unidad base
- proveedores y códigos utilizados por cada proveedor
- listas de precios y vigencias
- imágenes y documentos

Estas relaciones no forman parte del primer modelo mínimo salvo que una tarea
técnica posterior las incluya expresamente.

## 7. Multiempresa, permisos y auditoría

Toda consulta y modificación debe aislarse por empresa activa.

Permisos funcionales previstos:

- `items.ver`
- `items.crear`
- `items.editar`

Los permisos se validarán en backend. Ocultar acciones en la interfaz no
reemplaza la autorización.

Las altas, modificaciones e inactivaciones se ejecutarán mediante servicios
transaccionales y generarán auditoría siguiendo el patrón existente del maestro
de terceros.

## 8. Protección de invariantes

Las reglas críticas deberán estar protegidas en más de una capa cuando
corresponda:

- restricciones PostgreSQL
- validación del modelo
- servicios transaccionales
- formularios
- pruebas automatizadas

Como mínimo deberán protegerse:

- unicidad de código por empresa
- inmutabilidad de empresa y código
- imposibilidad de stock para servicios
- pertenencia empresarial de los catálogos relacionados
- baja lógica

## 9. Primera implementación técnica

El primer bloque técnico se limitará a:

- crear la app del maestro
- crear los catálogos base necesarios
- crear el modelo `Item`
- crear migraciones
- crear servicios de alta, edición e inactivación
- crear permisos funcionales
- crear administración técnica
- crear listado, detalle, alta y edición en la interfaz ERP
- integrar la navegación
- agregar pruebas de modelos, servicios, permisos, vistas y aislamiento

No se intentará implementar en un solo commit proveedores, precios, monedas,
FX, presentaciones, stock, lotes, series, fabricación ni atributos dinámicos.

## 10. Fuera del alcance inicial

Quedan para tareas posteriores:

- movimientos y existencias de stock
- depósitos y reservas
- lotes, series y vencimientos
- fabricación y listas de materiales
- kits avanzados
- suscripciones
- atributos configurables
- múltiples jerarquías de clasificación
- ofertas y costos de proveedores
- listas de precios
- monedas y tipos de cambio
- actualizaciones masivas
- facturación y snapshots de documentos

## 11. Pruebas esperadas

La implementación deberá cubrir como mínimo:

- unicidad de código dentro de una empresa
- posibilidad de repetir código en empresas diferentes
- código y empresa inmutables
- servicio sin stock
- producto con y sin stock
- compra y venta independientes
- rechazo de ítems sin ninguna capacidad operativa
- catálogos pertenecientes a la misma empresa
- inactivación sin eliminación física
- aislamiento por empresa activa
- permisos de consulta, creación y edición
- auditoría de altas, cambios e inactivaciones

## 12. Criterio de evolución

El maestro se ampliará por bloques pequeños y auditables. Una necesidad futura
no se modelará anticipadamente si no afecta la integridad de la primera versión.

La prioridad es mantener un maestro normal, útil y entendible sin impedir su
evolución.

## 13. Implementación: TAREA 0012 — Núcleo persistente

Se incorpora la primera base técnica del maestro:

- app `apps.items`
- catálogos `CategoriaItem`, `Marca`, `UnidadMedida` y `AlicuotaIVA`
- modelo central `Item`
- restricciones de unicidad y coherencia operativa en PostgreSQL
- validación de pertenencia empresarial e inmutabilidad de identidad
- administración técnica de solo lectura
- pruebas específicas de modelos e invariantes

Todavía no se habilita la operación funcional desde la interfaz. Permanecen
pendientes los servicios transaccionales, la auditoría, los permisos, los
formularios, las vistas, la navegación y la carga controlada de catálogos
fiscales y unidades de medida.

## 14. Implementación: TAREA 0013 — Servicios, auditoría y permisos

Se incorpora la capa transaccional del modelo `Item`:

- alta con validación y bloqueo de empresa y catálogos
- edición de ítems activos dentro de la empresa correspondiente
- inactivación lógica
- snapshots de auditoría antes y después de cada cambio
- captura de usuario, IP y agente de usuario cuando existe request
- permisos `items.ver`, `items.crear` e `items.editar`
- carga idempotente de la matriz ampliada de roles y permisos
- pruebas de servicios, aislamiento, auditoría y permisos

La identidad compuesta por empresa y código continúa siendo inmutable. La
operación funcional mediante formularios, vistas y navegación permanece
pendiente para la siguiente tarea.

## 15. Implementación: TAREA 0014 — Catálogos iniciales

Se incorpora el snapshot local necesario para que el formulario de ítems pueda
operar con valores controlados:

- 46 unidades de medida de la tabla oficial ARCA
- alícuotas IVA 0%, 2,5%, 5%, 10,5%, 21% y 27%
- códigos ARCA asociados
- migración de datos
- comando idempotente `cargar_catalogos_items_iniciales`
- verificación de consistencia sin eliminar extensiones locales

Fuentes consultadas el 23/06/2026:

- tabla oficial de unidades de medida:
  `https://www.afip.gov.ar/fe/documentos/FormatoEnvioFacturadorPlus/fp_formato_archivo_tablas.html`
- método oficial de parámetros IVA:
  `https://servicios1.afip.gov.ar/wsfev1/service.asmx?op=FEParamGetTiposIva`

Este bloque es un snapshot controlado. Una futura integración con los
webservices de ARCA podrá sincronizar vigencias y modificaciones sin cambiar la
identidad interna de los registros ya utilizados.

## 16. Implementación: TAREA 0015 — Interfaz funcional

Se habilita la operación desde la interfaz propia del ERP:

- listado, filtros y resumen de productos y servicios
- alta, detalle, edición e inactivación lógica de ítems
- mantenimiento de categorías por empresa
- mantenimiento de marcas por empresa
- códigos internos inmutables
- selección controlada de unidades y alícuotas
- comportamiento guiado para servicios, stock e IVA
- navegación en `Gestión → Maestros`
- permisos backend `items.ver`, `items.crear` e `items.editar`
- aislamiento por empresa activa
- auditoría de categorías, marcas e ítems
- bloqueo de inactivación de categorías o marcas usadas por ítems activos
- pruebas de formularios, servicios, vistas, permisos y aislamiento

El Django Admin continúa como backoffice técnico de consulta. La operación
habitual se realiza desde `/items/`.
