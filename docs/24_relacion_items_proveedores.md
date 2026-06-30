# Relación entre ítems y proveedores

```text
Estado: IMPLEMENTADO
Diseño: TAREA 0024
Implementación: TAREA 0025
Fecha de implementación: 2026-06-29
Base auditada antes del commit funcional: c71ee89c22901543e7b4a2328efe3b13da30407c
Migración: 0003_item_proveedor
Pruebas de apps.items: 101
Suite completa: 494
Issue de origen: #3
```

## 1. Objetivo

Definir el contrato de la futura entidad `ItemProveedor`, destinada a registrar
qué terceros con rol proveedor pueden suministrar un ítem comprable y cuál es
el código utilizado por cada proveedor.

Esta relación amplía los maestros existentes sin crear todavía órdenes de
compra, precios, costos ni condiciones comerciales.

## 2. Decisiones definitivas

1. `ItemProveedor` pertenecerá a `apps.items`.
2. Referenciará `Tercero`, no `TerceroRol`.
3. Existirá una sola fila histórica por combinación de ítem y proveedor.
4. La baja será lógica; no habrá eliminación física desde la interfaz.
5. La reactivación reutilizará la misma fila.
6. `codigo_proveedor` será opcional.
7. El código informado será único por proveedor, sin distinguir mayúsculas.
8. La disponibilidad operativa será calculada y no se duplicará en una columna.
9. Se bloqueará cambiar `Item.se_compra` a `False` mientras existan relaciones
   activas.
10. Se reutilizarán los permisos `items.ver` e `items.editar`.

## 3. Ubicación y dependencias

La entidad se ubicará en:

```text
apps.items.models.ItemProveedor
```

La dirección de dependencia será:

```text
apps.items
  ├── apps.nucleo.Empresa
  └── apps.terceros.Tercero
```

`apps.terceros` no dependerá de `apps.items`. Un futuro módulo de compras podrá
depender de ambos sin generar una dependencia circular.

## 4. Modelo conceptual

```text
Empresa
├── Item
├── Tercero
│   └── TerceroRol(PROVEEDOR)
└── ItemProveedor
    ├── item
    └── proveedor
```

La relación apunta a `Tercero` porque la identidad del proveedor debe sobrevivir
a la inactivación y reactivación de episodios del rol `PROVEEDOR`.

El rol activo es una condición operativa, no la identidad referenciada.

## 5. Campos previstos

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `empresa` | FK a `Empresa`, `PROTECT` | obligatoria e inmutable |
| `item` | FK a `Item`, `PROTECT` | obligatorio e inmutable |
| `proveedor` | FK a `Tercero`, `PROTECT` | obligatorio e inmutable |
| `codigo_proveedor` | texto de hasta 80 caracteres | opcional y editable |
| `observaciones` | texto | opcional |
| `activo` | booleano | estado histórico de la relación |
| `fecha_alta` | fecha | obligatoria |
| `fecha_baja` | fecha nullable | solo para relaciones inactivas |
| `creado_en` | fecha y hora | técnica |
| `actualizado_en` | fecha y hora | técnica |

Nombres de relaciones inversas recomendados:

```text
Item.relaciones_proveedores
Tercero.relaciones_items_proveedor
```

No se incorporan campos de precio, moneda, prioridad ni plazo.

## 6. Identidad e inmutabilidad

La identidad histórica queda determinada por:

```text
empresa + item + proveedor
```

Una vez creada la fila, no podrán modificarse:

- empresa;
- ítem;
- proveedor.

El código del proveedor sí podrá corregirse. La auditoría conservará el valor
anterior y el nuevo.

## 7. Normalización del código del proveedor

`codigo_proveedor` será opcional porque una relación puede ser útil aunque el
proveedor no publique un código estable.

Cuando se informe:

1. se aplicará normalización Unicode NFKC;
2. se eliminarán espacios externos;
3. las secuencias internas de espacios se reducirán a uno;
4. se convertirá a mayúsculas;
5. se rechazarán saltos de línea y caracteres de control;
6. se conservarán signos habituales como guion, barra, punto o paréntesis.

No se aplicará el validador restrictivo de los códigos internos del ERP porque
los códigos externos no están bajo control de la empresa.

Ejemplos:

```text
"  ab-12 / x  "  → "AB-12 / X"
"Comp.44-a"       → "COMP.44-A"
""                → ""
```

## 8. Restricciones de base de datos

La implementación futura deberá incluir:

### 8.1. Relación única

```text
UNIQUE(empresa, item, proveedor)
```

La restricción abarcará filas activas e inactivas para impedir duplicar la
historia. La reactivación utilizará la fila existente.

### 8.2. Código único dentro del proveedor

Cuando `codigo_proveedor` no esté vacío:

```text
UNIQUE(empresa, proveedor, LOWER(codigo_proveedor))
```

Esto impide que un proveedor identifique dos ítems distintos con el mismo
código, incluso con diferencias de mayúsculas.

El mismo código podrá existir en proveedores diferentes.

### 8.3. Fechas y estado

```text
fecha_baja IS NULL OR fecha_baja >= fecha_alta
activo = FALSE OR fecha_baja IS NULL
```

Las coincidencias de empresa entre la relación, el ítem y el tercero requieren
validación de modelo y servicios porque involucran otras tablas.

## 9. Requisitos para crear o reactivar

La empresa debe estar activa.

El ítem debe:

- existir en la empresa activa;
- estar activo;
- tener `se_compra=True`.

El proveedor debe:

- existir en la misma empresa;
- estar activo;
- poseer un `TerceroRol` activo con rol `PROVEEDOR`.

La ausencia de cualquiera de estas condiciones debe producir un error de
validación de dominio.

## 10. Disponibilidad operativa

`activo` representa la vigencia elegida para la relación. No garantiza por sí
solo que pueda utilizarse en una compra.

La disponibilidad se calculará como:

```text
relación activa
AND ítem activo
AND ítem se_compra
AND proveedor activo
AND rol PROVEEDOR activo
```

No se almacenará un segundo booleano de disponibilidad.

La interfaz deberá mostrar:

- estado histórico: activa o inactiva;
- disponibilidad operativa: disponible o no disponible;
- motivo cuando no esté disponible.

La consulta deberá evitar N+1 mediante `select_related`, `prefetch_related` o
`Exists`, según corresponda.

## 11. Ciclo de vida

### 11.1. Alta

- crea una relación activa;
- establece `fecha_alta`;
- deja `fecha_baja=None`;
- valida todos los requisitos operativos;
- audita un `INSERT`.

### 11.2. Edición

Solo permite modificar:

- código del proveedor;
- observaciones.

Empresa, ítem y proveedor permanecen inmutables.

La edición de una relación activa requerirá que siga operativamente disponible.
Cuando una dependencia esté inactiva, la acción permitida será inactivar la
relación o restablecer primero la dependencia.

### 11.3. Inactivación

- no elimina la fila;
- establece `activo=False`;
- asigna una fecha de baja válida;
- puede ejecutarse aunque el ítem, el tercero o el rol ya estén inactivos;
- audita un `UPDATE`.

### 11.4. Reactivación

- reutiliza la misma fila;
- valida nuevamente empresa, ítem, proveedor y rol;
- establece `activo=True`;
- limpia `fecha_baja`;
- audita un `UPDATE`.

### 11.5. Eliminación física

No se ofrecerá en la interfaz funcional. Las claves foráneas utilizarán
`PROTECT`.

## 12. Interacción con el ítem

### 12.1. Quitar capacidad de compra

`actualizar_item` deberá bloquear el cambio:

```text
se_compra=True → se_compra=False
```

cuando exista al menos una relación `ItemProveedor` activa.

El mensaje deberá indicar que primero deben inactivarse las relaciones con
proveedores.

La regla considera el estado histórico `activo` de la relación, aunque alguna
dependencia esté temporalmente inactiva.

### 12.2. Inactivar el ítem

La inactivación del ítem no eliminará ni modificará sus relaciones. Estas
quedarán no disponibles por cálculo y conservarán su historia.

### 12.3. Reactivar el ítem

Cuando el ítem vuelva a estar activo y conserve `se_compra=True`, sus relaciones
activas podrán volver a quedar disponibles si el proveedor y su rol también
están activos.

## 13. Interacción con el tercero y su rol

La inactivación del tercero o del rol `PROVEEDOR`:

- no se bloqueará;
- no eliminará ni inactivará automáticamente `ItemProveedor`;
- volverá no disponibles las relaciones activas;
- conservará el historial.

La reactivación posterior del tercero y del rol podrá restablecer
automáticamente la disponibilidad calculada.

No se agregarán referencias desde `TerceroRol` hacia `ItemProveedor`.

## 14. Servicios transaccionales

La implementación deberá concentrar las escrituras en:

```python
crear_item_proveedor(...)
actualizar_item_proveedor(...)
inactivar_item_proveedor(...)
reactivar_item_proveedor(...)
```

Los servicios deberán:

- usar `transaction.atomic`;
- bloquear con `select_for_update` la empresa, el ítem, el proveedor, el rol y la
  relación cuando corresponda;
- ejecutar `full_clean`;
- convertir conflictos de unicidad en errores de dominio comprensibles;
- generar auditoría dentro de la misma transacción;
- rechazar IDs manipulados de otras empresas.

Las vistas no escribirán modelos directamente.

## 15. Auditoría

Se reutilizará `apps.nucleo.models.Auditoria`.

Snapshots mínimos:

```text
empresa_id
item_id
proveedor_id
codigo_proveedor
activo
fecha_alta
fecha_baja
observaciones
disponibilidad calculada al momento de la operación
```

Acciones:

- alta: `Auditoria.Accion.INSERT`;
- edición: `Auditoria.Accion.UPDATE`;
- inactivación: `Auditoria.Accion.UPDATE`;
- reactivación: `Auditoria.Accion.UPDATE`.

No se crean nuevos tipos de evento en esta primera versión.

## 16. Permisos

Se reutilizan:

```text
items.ver
items.editar
```

`items.ver` permite:

- consultar proveedores del ítem;
- ver códigos, estado e indisponibilidad.

`items.editar` permite:

- crear;
- editar;
- inactivar;
- reactivar.

`items.crear` no autoriza por sí solo a administrar relaciones existentes.

No se crean permisos específicos hasta que exista una necesidad real de
delegación independiente.

## 17. Interfaz funcional

La administración se ubicará dentro del detalle del ítem, en una card
**Proveedores**.

Columnas:

- proveedor;
- grupo de proveedor;
- código del proveedor;
- estado histórico;
- disponibilidad;
- motivo de indisponibilidad;
- acciones.

Comportamiento:

- con `items.ver`, la sección es de consulta;
- con `items.editar`, aparecen las acciones;
- el selector muestra solo terceros activos de la empresa activa con rol
  `PROVEEDOR` activo;
- excluye proveedores que ya tengan una relación histórica con el ítem;
- en edición, ítem y proveedor aparecen como identidad no modificable;
- las acciones de inactivar y reactivar son `POST`;
- toda ruta vuelve a validar empresa, permisos y pertenencia.

Rutas previstas:

```text
/items/<item_id>/proveedores/nuevo/
/items/<item_id>/proveedores/<relacion_id>/editar/
/items/<item_id>/proveedores/<relacion_id>/inactivar/
/items/<item_id>/proveedores/<relacion_id>/reactivar/
```

Si el ítem no es comprable, la sección conserva el historial pero no permite
crear ni reactivar relaciones.

## 18. Administración técnica

El modelo podrá registrarse en Django Admin como backoffice técnico.

La administración habitual seguirá realizándose desde la ficha del ítem.

El Admin:

- no debe permitir eliminación física;
- debe mostrar empresa, ítem, proveedor, código y estado;
- debe tratar empresa, ítem y proveedor como inmutables después del alta.

## 19. Migración futura

La implementación persistente deberá crear una única migración nueva en
`apps.items`, con dependencia explícita de la migración vigente de terceros.

No se requiere migración de datos porque no existen relaciones históricas en el
sistema actual.

La tarea de diseño no crea ni aplica ninguna migración.

## 20. Pruebas obligatorias de implementación

### Modelo y restricciones

- normalización del código;
- relación única activa o inactiva;
- código opcional;
- código único por proveedor sin distinguir mayúsculas;
- mismo código permitido en proveedores diferentes;
- empresa, ítem y proveedor inmutables;
- fechas coherentes;
- `PROTECT` y ausencia de eliminación funcional.

### Servicios

- alta válida;
- rechazo de empresa inactiva;
- rechazo de ítem de otra empresa;
- rechazo de proveedor de otra empresa;
- rechazo de ítem inactivo;
- rechazo de ítem no comprable;
- rechazo de tercero inactivo;
- rechazo de tercero sin rol proveedor activo;
- edición de código y observaciones;
- inactivación;
- reactivación;
- rechazo de reactivación sin requisitos;
- auditoría antes/después;
- concurrencia y traducción de conflictos de unicidad.

### Interacción con maestros

- bloqueo de `se_compra=False` con relaciones activas;
- permiso para quitar `se_compra` después de inactivarlas;
- inactivación del ítem sin borrar relaciones;
- inactivación del tercero sin borrar relaciones;
- inactivación del rol sin borrar relaciones;
- disponibilidad recuperada al reactivar dependencias.

### Formularios y vistas

- selector limitado a proveedores válidos;
- exclusión de proveedores ya relacionados;
- validación contra IDs manipulados;
- consulta con `items.ver`;
- escritura solo con `items.editar`;
- aislamiento por empresa;
- rutas `POST` para cambios de estado;
- mensajes y redirecciones;
- detalle sin consultas N+1 relevantes.

### Regresión

- ausencia de migraciones no previstas;
- checks de Integrado, Gestión y Contabilidad;
- suite completa.

## 21. Fuera de alcance

No forman parte de `ItemProveedor`:

- proveedor preferido;
- múltiples códigos simultáneos para el mismo proveedor e ítem;
- precios y costos;
- monedas y tipos de cambio;
- descuentos;
- listas o acuerdos de precios;
- cantidades mínimas o múltiplos;
- unidades de compra y presentaciones;
- factores de conversión;
- plazos de entrega;
- condiciones de pago;
- órdenes de compra;
- recepciones;
- stock por proveedor;
- códigos de barras genéricos;
- múltiples identificadores externos.

Cada necesidad futura deberá tener contrato propio.

## 22. Criterios para la tarea de implementación

La implementación posterior será aceptable cuando:

- respete este modelo sin ampliar el alcance;
- cree modelo, migración, servicios, formularios, vistas y pruebas;
- preserve el aislamiento por empresa;
- proteja invariantes en base, modelo, servicios y formularios;
- no realice escrituras directas desde vistas;
- mantenga el repositorio sin migraciones pendientes;
- cierre con suite completa verde y verificación remota.

## 23. Estado final del diseño

```text
DISEÑO APROBADO
IMPLEMENTACIÓN COMPLETADA EN TAREA 0025
MIGRACIÓN APLICADA Y FUNCIONALIDAD OPERATIVA
```

<!-- BEGIN TAREA_0025_IMPLEMENTACION -->
## 24. Implementación verificada — TAREA 0025

```text
Modelo: apps.items.models.ItemProveedor
Tabla: items_itemproveedor
Migración: 0003_item_proveedor
Servicios: crear, actualizar, inactivar y reactivar
Interfaz: card Proveedores en el detalle del ítem
Pruebas apps.items: 95
Suite completa: 488
```

Se implementó el contrato sin incorporar precios, costos, monedas,
presentaciones ni condiciones comerciales.
<!-- END TAREA_0025_IMPLEMENTACION -->

<!-- BEGIN TAREA_0026_AJUSTE_VISUAL -->
## 25. Ajuste posterior a revisión visual — TAREA 0026

Una relación activa puede quedar no disponible cuando el ítem se inactiva. Se
incorpora la acción auditada **Reactivar ítem**.

El formulario también explica que primero deben inactivarse las relaciones
activas antes de quitar `se_compra`.

```text
Pruebas apps.items: 101
Suite completa: 494
```
<!-- END TAREA_0026_AJUSTE_VISUAL -->
