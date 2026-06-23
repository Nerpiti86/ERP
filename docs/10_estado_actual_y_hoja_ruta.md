# Estado actual y hoja de ruta del ERP

Fecha del corte: 20/06/2026.

Base verificada:

```text
Repositorio: Nerpiti86/ERP
Rama: main
Cierre funcional: TAREA 0006
Base de implementación: e91c21f1a08e03fa76e1be821352e847d907b84f
Tests: 243 OK
```

## 1. Resumen ejecutivo

El proyecto ya superó la etapa de preparación técnica.

Actualmente existe un núcleo Django/PostgreSQL funcional con:

- estructura empresarial
- períodos contables
- accesos por empresa y sucursal
- configuración
- auditoría
- eventos
- documentos adjuntos
- roles y permisos
- contexto activo de empresa y sucursal
- autenticación propia del ERP

Todavía no existe un circuito operativo completo de ventas, compras, tesorería o contabilidad dentro de este nuevo ERP.

La base transversal está cerrada para comenzar el diseño del primer módulo operativo.

## 2. Arquitectura vigente

```text
Windows
└── Django
    ├── app core
    ├── app nucleo
    ├── Django Templates
    ├── Bootstrap
    └── PostgreSQL local
```

Acceso remoto previsto:

```text
Navegador
→ Tailscale
→ aplicación Django
→ PostgreSQL local
```

PostgreSQL no se expone directamente.

## 3. Núcleo implementado

### Estructura organizativa

- Empresa
- Sucursal
- UsuarioEmpresa
- UsuarioSucursal

### Estructura contable temporal

- EjercicioFiscal
- PeriodoContable

### Configuración y trazabilidad

- ParametroSistema
- Auditoria
- EventoNegocio
- DocumentoAdjunto

### Seguridad funcional

- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa
- helper `usuario_tiene_permiso`

### Datos iniciales de seguridad

```text
Roles: 5
Permisos: 25
Relaciones rol-permiso: 64
```

Roles:

- ADMIN
- CONTADOR
- OPERADOR
- AUDITOR
- SOLO_LECTURA

## 4. Contexto de sesión implementado

### Empresa activa

- se guarda el ID en sesión
- se valida acceso activo
- se selecciona automáticamente si hay una sola
- permite selección manual si hay varias
- el superusuario puede usar cualquier empresa activa
- una selección inválida se limpia

### Sucursal activa

- depende de la empresa activa
- se guarda el ID en sesión
- exige acceso activo a empresa y sucursal
- se selecciona automáticamente si hay una sola
- rechaza sucursales de otra empresa
- cambiar de empresa limpia la sucursal anterior

## 5. Autenticación implementada

Rutas:

```text
/ingresar/
/salir/
```

Reglas:

- mantiene `auth.User` estándar
- solo usuarios activos pueden ingresar
- la portada requiere autenticación
- los selectores usan el login propio
- `next` acepta únicamente URLs internas
- el login limpia contextos anteriores
- el logout funciona solo por POST
- el logout elimina la sesión completa
- los enlaces al Admin se muestran únicamente a usuarios `staff`
- la portada ya no expone conteos globales

## 6. Estado de usuarios

Estado operativo local relevado el 19/06/2026:

```text
Usuarios reales: ADMIN y Laura
Empresas activas: Empresa Demo SA y ESREQUIS LAURA
```

Laura posee acceso activo a `ESREQUIS LAURA`, a su sucursal `Consultorio Pasco` y tiene asignado el rol funcional `OPERADOR`.

## 7. Tareas recientes cerradas

| Tarea | Resultado | Commit |
|---|---|---|
| 37 | Auditoría básica | `bdf2ebbb1eb80e7df9babfe296ca27f1eccf6969` |
| 38 | Eventos de negocio | `e84bbca23998aefabdaed390b1e08ac150dd86a2` |
| 39 | Base de documentos adjuntos | `7dc9757b7bc82968a66e2031bcca73bb41cb0034` |
| 40 | Estrategia de roles y permisos | `696183f61f0c58c1e7ad09f471f3c4c2170679ec` |
| 41 | Evaluación de usuario custom | `5cf0a8f85f0fc6588a34153fe355d62263719e08` |
| 42 | Roles y permisos funcionales | `9c325358680f4199734e6784a67faa3584f7095d` |
| 43 | Roles y permisos iniciales | `f29d8ce03cdf53bae752d1cd09ccc51150b8a0a0` |
| 44 | Empresa activa por sesión | `2d1e6ee32498b13b6955d7cfaf6c364ddab10f8f` |
| 45 | Sucursal activa por sesión | `4e47a55b443085f4dda33bd8c2fe778f2a89d39d` |
| 46 | Autenticación propia del ERP | `8e35e36ec3565affba379378aa818ac4cab4d1ba` |
| 47 | Configuración amigable de parámetros por empresa | `9d798937895df04e4f50b89924abc25754ee86b4` |
| 48 | Permisos funcionales aplicados a vistas | `1e8b6199833f0a698fa7e914ccf433503fca099a` |
| 49 | Contexto operativo obligatorio | ver historial de `main` |

## 8. Estado actual de configuración fiscal

La configuración de empresa incorpora:

- datos básicos del contribuyente
- sucursales y domicilios estructurados
- catálogo oficial ARCA-CLAE
- actividades económicas por empresa
- parámetros operativos
- permisos funcionales por empresa

La configuración base se considera lista únicamente cuando también existe
una actividad económica principal activa.

## 9. Próximos pasos recomendados

### Inmediato

```text
TAREA 0007 — Ingresos Brutos y jurisdicciones
Estado: PENDIENTE DE DISEÑO
```

Objetivos esperados:

- régimen local o Convenio Multilateral
- tratamiento fiscal general
- jurisdicciones y números de inscripción
- fechas de alta y baja
- separación entre jurisdicción fiscal y sucursal física
- integración con Configuración de empresa

### Después

1. Usuarios y accesos desde interfaz funcional.
2. Maestro de terceros.
3. Productos y servicios.
4. Primer circuito transaccional.

## 10. Qué todavía no es el ERP

Todavía no están implementados como módulos operativos completos:

- ventas
- compras
- stock
- tesorería
- cuentas corrientes
- contabilidad operativa
- impuestos
- reportes funcionales

El núcleo actual es la base transversal necesaria para construirlos sin mezclar empresas, sucursales, usuarios ni permisos.

## 11. Criterio para avanzar

La secuencia recomendada es:

```text
autenticación
→ configuración amigable por empresa
→ permisos en vistas
→ contexto obligatorio
→ maestro de terceros
→ productos y servicios
→ primer circuito transaccional
```

Autenticación, permisos y contexto obligatorio ya están cerrados. El próximo paso es el primer diseño funcional operativo.

## 12. Actualización posterior al corte D01: TAREA 47

Se implementa la configuración amigable de parámetros por empresa.

Ruta:

```text
/nucleo/configuracion/
```

La pantalla:

- opera sobre la empresa activa
- inicializa ocho parámetros estándar de forma manual e idempotente
- preserva valores existentes
- reactiva parámetros estándar inactivos
- no modifica parámetros personalizados
- permite editar moneda, punto de venta, numeración y opciones operativas
- no expone claves, ámbitos ni tipos técnicos
- queda restringida temporalmente a usuarios staff

Caso real previsto:

```text
Empresa: ESREQUIS LAURA
Estado antes de la prueba: 0 parámetros
Acción posterior al cierre: inicializar manualmente desde la interfaz
```

La próxima tarea funcional pasa a ser TAREA 48: aplicar permisos funcionales a las vistas.


## 13. Actualización posterior: TAREA 48

Se aplica autorización funcional en backend a la configuración de
la empresa activa.

Resultado:

- `parametros.ver` habilita consulta en modo solo lectura.
- `parametros.editar` habilita inicialización y guardado.
- `OPERADOR` no posee acceso a configuración.
- `CONTADOR`, `AUDITOR` y `SOLO_LECTURA` pueden consultar.
- `ADMIN` puede consultar y editar.
- `staff` deja de ser una autorización funcional.
- la navegación refleja permisos efectivos.
- el acceso directo sin permiso devuelve una página 403 propia.

Escenario real preparado:

```text
ADMIN: acceso técnico total
Laura: rol OPERADOR en ESREQUIS LAURA
ESREQUIS LAURA: ocho parámetros estándar activos
```

La próxima tarea funcional es TAREA 49: definir obligatoriedad del
contexto operativo.


## 14. Actualización posterior: TAREA 49

Se implementa el contrato de contexto operativo obligatorio.

Resultado:

- vistas por empresa con empresa activa obligatoria
- vistas operativas con empresa y sucursal activas
- redirecciones a selectores conservando `next`
- filtrado reutilizable de querysets por contexto
- validación de pertenencia de objetos recuperados por ID
- rechazo de sucursales pertenecientes a otra empresa
- pruebas de aislamiento y manipulación de sesión
- Configuración declarada como pantalla por empresa

El núcleo transversal queda listo para iniciar un módulo funcional.
La próxima tarea es TAREA 50: diseñar el maestro de terceros.

## 15. Actualización posterior: TAREA 0006

Se implementan actividades económicas por empresa sobre el catálogo oficial
ARCA-CLAE.

Resultado:

- modelo `EmpresaActividad`
- instantánea histórica de datos oficiales
- principal y secundarias
- vigencias, orden y observaciones
- baja lógica
- restricciones PostgreSQL
- servicios transaccionales
- auditoría
- permisos `actividades.*`
- búsqueda por código o descripción
- tarjeta en Configuración de empresa
- catálogo oficial y relaciones bloqueados para escritura manual en Admin

Suite verificada al cierre: `243` pruebas.

## 15. Corte documental D02

Base verificada antes del corte:

```text
Commit: 4842d374f43d696e625368bc625a19dfc5a3ead6
Última tarea funcional: TAREA 0006
Pruebas: 243 OK
Migraciones de núcleo: hasta 0012
Catálogo ARCA-CLAE: 958 actividades activas
```

Funcionalidad fiscal y empresarial incorporada después del corte anterior:

- datos básicos del contribuyente
- perfil fiscal de empresa
- sucursales y domicilios estructurados
- funciones exclusivas de establecimientos
- catálogo oficial ARCA-CLAE
- sincronización auditable del catálogo
- actividades económicas por empresa
- actividad principal y secundarias
- snapshot histórico
- permisos específicos
- auditoría de cambios
- integración en Configuración de empresa

Lecciones metodológicas consolidadas:

- revisar siempre el remoto real
- fijar el SHA contractual
- no usar anclas textuales frágiles
- validar el código generado por los scripts
- inicializar Django antes de importar modelos en Python directo
- retrasar migraciones hasta terminar validaciones previas
- crear continuaciones específicas
- preservar datos mediante backup y baja lógica
- verificar el commit directamente en GitHub

El estándar completo queda documentado en:

```text
docs/17_lecciones_aprendidas_y_estandar_implementacion.md
```

## 16. Actualización posterior: TAREA 0007

Se implementa la configuración de Ingresos Brutos y jurisdicciones fiscales.

Resultado:

- catálogo oficial de 24 jurisdicciones COMARB
- régimen local, Convenio Multilateral y no inscripto
- tratamiento fiscal general
- números de inscripción
- vigencias e historial
- jurisdicción sede
- restricciones PostgreSQL
- servicios transaccionales
- auditoría
- permisos `iibb.*`
- integración en Configuración de empresa
- separación entre jurisdicción fiscal y sucursal física

Suite verificada al cierre: `237` pruebas.

El recuento anterior de 277 fue corregido al volver a ejecutar la suite completa
sobre el commit de cierre de la TAREA 0007.

La tarea funcional siguiente se definirá mediante una decisión explícita
posterior. Los agentes de retención y percepción continúan pendientes y no
forman parte de la TAREA 0008.


## Actualización posterior: TAREA 0008

Se implementan puntos de venta por sucursal.

Resultado:

- modelo `PuntoVenta`
- relación obligatoria con empresa y sucursal
- varios puntos por sucursal
- número único por empresa entre 1 y 99998
- presentación con cinco posiciones
- sistema de emisión
- actividad e IIBB predeterminados opcionales
- un predeterminado activo por sucursal
- baja lógica sin reutilización de número
- servicios transaccionales
- auditoría
- permisos `puntos_venta.*`
- integración en Configuración de empresa
- preservación del parámetro anterior sin conversión automática

Suite verificada al cierre: `266` pruebas.


## Actualización: TAREA 0009 — Maestro base de terceros

Implementado:

- app `apps.terceros`
- identidad única por empresa
- roles de cliente y proveedor
- catálogos de documento y condición IVA
- domicilios y contactos múltiples
- principales automáticos
- baja lógica
- servicios transaccionales y auditoría
- permisos `terceros.*`
- aislamiento por empresa activa
- navegación desde Gestión

Suite específica: `48` pruebas.
Suite completa verificada: `354` pruebas.

Próximo bloque recomendado:

```text
TAREA 0011 — Productos y servicios
Estado: PENDIENTE DE DISEÑO
```


## Actualización: TAREA 0010 — Edición de terceros

Se corrige el flujo de edición del maestro de terceros.

Resultado:

- el formulario GET precarga todos los datos existentes
- `None` se interpreta correctamente como formulario no vinculado
- la vista separa explícitamente GET y POST
- el título identifica la edición de cliente/proveedor
- se muestra la razón social, código y documento del tercero
- distintivo visual `Modo edición`
- advertencia antes de modificar un registro existente
- acciones claras `Guardar cambios` y `Cancelar y volver`
- el alta conserva su presentación independiente
- no se agregan migraciones ni se modifican permisos

Suite específica de terceros: `52` pruebas.
Suite completa verificada: `358` pruebas.

Próximo bloque recomendado:

```text
TAREA 0011 — Productos y servicios
Estado: PENDIENTE DE DISEÑO
```

## Actualización: TAREA 0011 — Diseño base de productos y servicios

Se documenta el alcance inicial del maestro unificado de productos y servicios.

Resultado:

- documento específico `docs/21_maestro_productos_servicios.md`
- entidad conceptual única `Item`
- tipos `PRODUCTO` y `SERVICIO`
- compra y venta independientes
- stock permitido únicamente para productos
- ficha principal genérica
- categorías, marcas, unidades e IVA como catálogos relacionados
- variantes operativas como ítems independientes
- baja lógica, multiempresa, permisos y auditoría
- funciones avanzadas separadas en tareas posteriores

Estado:

```text
TAREA 0011 — DISEÑO DOCUMENTADO
Implementación técnica: PENDIENTE
```

Próximo bloque recomendado:

```text
TAREA 0012 — Implementar el núcleo del maestro de productos y servicios
```

## Actualización: TAREA 0012 — Núcleo persistente de productos y servicios

Se implementa la primera base técnica del maestro unificado.

Resultado:

- app `apps.items`
- categorías y marcas por empresa
- catálogos controlados de unidades de medida y alícuotas de IVA
- modelo `Item` para productos y servicios
- código único por empresa e identidad inmutable
- compra y venta independientes
- servicios sin control de stock
- coherencia entre tratamiento de IVA y alícuota
- restricciones PostgreSQL
- administración técnica de solo lectura
- pruebas específicas de modelos e invariantes

Estado:

```text
TAREA 0012 — NÚCLEO PERSISTENTE IMPLEMENTADO
Servicios, permisos e interfaz: PENDIENTES
```

Próximo bloque recomendado:

```text
TAREA 0013 — Servicios transaccionales, auditoría y permisos de ítems
```

## Actualización: TAREA 0013 — Servicios, auditoría y permisos de ítems

Se incorpora la capa transaccional del maestro de productos y servicios.

Resultado:

- servicios `crear_item`, `actualizar_item` e `inactivar_item`
- bloqueo de empresa, ítem y catálogos durante la operación
- aislamiento por empresa
- auditoría con snapshots anteriores y nuevos
- permisos `items.ver`, `items.crear` e `items.editar`
- matriz inicial ampliada a 40 permisos y 110 relaciones
- carga idempotente aplicada y verificada
- pruebas específicas de servicios y permisos

Estado:

```text
TAREA 0013 — SERVICIOS, AUDITORÍA Y PERMISOS IMPLEMENTADOS
Formularios, vistas y navegación: PENDIENTES
```

Próximo bloque recomendado:

```text
TAREA 0014 — Interfaz funcional del maestro de productos y servicios
```
