# Estado actual y hoja de ruta del ERP

Fecha del corte: 19/06/2026.

Base verificada:

```text
Repositorio: Nerpiti86/ERP
Rama: main
Último cierre funcional: TAREA 49
Mensaje: Definir contexto operativo obligatorio
Tests: 142 OK
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

## 8. Próxima tarea

```text
TAREA 50 — Diseñar maestro de terceros
Estado: PENDIENTE DE DISEÑO
```

Objetivo esperado:

- definir un maestro único para clientes y proveedores
- establecer identificación fiscal y datos de contacto
- permitir que un tercero sea cliente, proveedor o ambos
- aplicar empresa activa, permisos y auditoría desde el diseño
- preparar la base para ventas, compras y cuentas corrientes

## 9. Próximos pasos recomendados

### Inmediatos

1. Diseñar TAREA 50: maestro de terceros.
2. Definir el modelo funcional de clientes y proveedores.
3. Implementar altas, edición, consulta y baja lógica.
4. Aplicar el contrato de contexto y permisos desde el inicio.
5. Continuar luego con productos y servicios.

### Consistencia pendiente

- impedir ejercicios fiscales superpuestos
- impedir períodos contables superpuestos
- definir política final para superusuarios
- auditar cambios críticos de seguridad
- aplicar permisos a rutas y acciones

### Operación e infraestructura pendiente

- servidor WSGI para uso estable en Windows
- servicio de inicio automático
- acceso remoto por Tailscale
- configuración final de `ALLOWED_HOSTS`
- `DEBUG=False` para uso real
- backups automáticos de PostgreSQL
- recuperación probada de backups
- política de archivos en `media/`

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
