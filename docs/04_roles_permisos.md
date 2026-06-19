# Estrategia de roles y permisos propios

Estado: definido documentalmente al cierre de la Tarea 40.

## 1. Objetivo

Definir una estrategia propia de roles y permisos funcionales para el ERP sin acoplarla prematuramente a pantallas, Django Admin ni a un cambio de usuario custom.

La implementacion de tablas y validaciones queda para una tarea posterior.

## 2. Decision base

Se usara Django Auth como base tecnica inicial.

Los modelos propios deben seguir referenciando usuarios mediante `settings.AUTH_USER_MODEL`.

No se cambia `AUTH_USER_MODEL` en esta tarea.

Antes de implementar tablas definitivas de seguridad propia se debe ejecutar una tarea separada para evaluar si conviene mantener `auth.User` o crear usuario custom.

## 3. Principios

1. Los permisos son funcionales, no esteticos.
2. La interfaz puede ocultar botones, pero la seguridad real se valida en backend.
3. Los roles agrupan permisos.
4. Los usuarios reciben roles por empresa.
5. Un mismo usuario puede tener roles distintos en empresas distintas.
6. Los roles no deben hardcodearse en pantallas.
7. Los permisos efectivos se calculan desde roles activos y permisos activos.
8. Los superusuarios deben poder operar tecnicamente para evitar bloqueos administrativos iniciales.
9. La estrategia debe admitir sucursales en una etapa posterior, sin obligarlo en la primera implementacion.

## 4. Roles iniciales sugeridos

Roles funcionales iniciales:

- ADMIN
- CONTADOR
- OPERADOR
- AUDITOR
- SOLO_LECTURA

Descripcion inicial:

- ADMIN: administracion funcional amplia dentro de una empresa.
- CONTADOR: acceso contable, fiscal y de reportes.
- OPERADOR: carga y operacion diaria.
- AUDITOR: consulta de auditoria, eventos y reportes.
- SOLO_LECTURA: consulta sin modificacion.

Estos roles son datos configurables, no constantes hardcodeadas en vistas.

## 5. Convencion de permisos

Formato:

```text
modulo.accion
```

Ejemplos iniciales:

```text
empresas.ver
empresas.crear
empresas.editar
empresas.desactivar
sucursales.ver
sucursales.crear
sucursales.editar
usuarios.ver
usuarios.crear
usuarios.editar
parametros.ver
parametros.editar
auditoria.ver
eventos.ver
documentos.ver
documentos.adjuntar
documentos.desactivar
contabilidad.ver
contabilidad.editar
ventas.ver
ventas.crear
compras.ver
compras.crear
tesoreria.ver
tesoreria.operar
```

## 6. Modelos futuros propuestos

### 6.1. RolFuncional

Responsabilidad:

Guardar roles funcionales del ERP.

Campos sugeridos:

- codigo
- nombre
- descripcion
- activo
- sistema
- creado_en
- actualizado_en

Reglas:

- `codigo` unico.
- `codigo` normalizado en mayusculas.
- No hardcodear codigos en pantallas.
- Roles de sistema pueden bloquear eliminacion.

### 6.2. PermisoFuncional

Responsabilidad:

Guardar permisos funcionales disponibles.

Campos sugeridos:

- codigo
- modulo
- accion
- descripcion
- activo
- creado_en
- actualizado_en

Reglas:

- `codigo` unico.
- `codigo` en formato `modulo.accion`.
- `modulo` y `accion` en minusculas.
- Permisos inactivos no deben otorgar acceso efectivo.

### 6.3. RolPermiso

Responsabilidad:

Relacionar roles con permisos.

Campos sugeridos:

- rol
- permiso
- activo
- creado_en
- actualizado_en

Reglas:

- Un rol no debe tener el mismo permiso duplicado.
- Solo permisos activos deben considerarse efectivos.

### 6.4. UsuarioRolEmpresa

Responsabilidad:

Asignar roles a usuarios dentro de una empresa.

Campos sugeridos:

- usuario
- empresa
- rol
- activo
- creado_en
- actualizado_en

Reglas:

- Un usuario puede tener varios roles en una empresa.
- Un usuario puede tener roles distintos por empresa.
- Solo asignaciones activas otorgan permisos.
- El usuario debe tener acceso activo a la empresa antes de recibir rol en esa empresa.

## 7. Sucursal

No se implementa alcance por sucursal en la primera version de roles.

La estrategia debe permitir agregar luego:

- UsuarioRolSucursal
- permisos por sucursal
- restricciones operativas por sucursal activa

Decision inicial:

Primero empresa. Luego sucursal.

## 8. Permisos efectivos

Funcion conceptual futura:

```text
usuario_tiene_permiso(usuario, empresa, codigo_permiso) -> bool
```

Reglas:

1. Si el usuario esta inactivo, no tiene permiso.
2. Si la empresa esta inactiva, no tiene permiso.
3. Si el usuario no tiene acceso activo a la empresa, no tiene permiso.
4. Si el usuario es superuser, puede considerarse permitido para administracion tecnica inicial.
5. Si el usuario tiene un rol activo en la empresa y ese rol tiene el permiso activo, tiene permiso.
6. Caso contrario, no tiene permiso.

## 9. Auditoria y eventos

Cambios relevantes en seguridad deben auditarse.

Ejemplos:

- rol creado
- rol editado
- permiso creado
- permiso asignado a rol
- rol asignado a usuario
- rol desactivado
- permiso desactivado

Eventos de negocio posibles:

- ROL_CREADO
- PERMISO_CREADO
- ROL_ASIGNADO_USUARIO
- PERMISO_ASIGNADO_ROL

No se implementan en esta tarea.

## 10. Django Admin

Django Admin sigue siendo backoffice tecnico inicial.

No es la interfaz final del ERP.

Los modelos de roles y permisos futuros pueden registrarse en admin para carga inicial y verificacion tecnica.

## 11. Fuera de alcance de Tarea 40

No se implementa:

- modelos
- migraciones
- middleware
- decoradores
- validadores backend
- pantallas
- carga inicial de roles
- carga inicial de permisos
- usuario custom
- reglas por sucursal
- permisos sobre objetos individuales

## 12. Secuencia recomendada

Tarea siguiente:

```text
TAREA 48 — Aplicar permisos funcionales a las vistas del ERP
```

## 13. Estado de cierre

Tarea 40 deja definida la estrategia.

La decision de usuario custom queda resuelta en `docs/05_usuario_custom.md`. La implementacion de roles y permisos funcionales puede avanzar en una tarea posterior.


## 14. Implementacion inicial

Al cierre de la Tarea 42 se implementan los modelos definidos en esta estrategia:

- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa

Tambien se agrega el helper backend:

```text
usuario_tiene_permiso(usuario, empresa, codigo_permiso) -> bool
```

La implementacion inicial no carga datos por defecto.

Los roles y permisos iniciales se cargaran en una tarea separada.


## 15. Carga inicial implementada

Al cierre de la Tarea 43 se agrega una carga idempotente mediante:

```text
python manage.py cargar_roles_permisos_iniciales
```

Matriz inicial:

- ADMIN: 25 permisos
- CONTADOR: 10 permisos
- OPERADOR: 10 permisos
- AUDITOR: 11 permisos
- SOLO_LECTURA: 8 permisos

Total:

- 5 roles
- 25 permisos
- 64 relaciones rol-permiso

Los roles iniciales quedan marcados como roles de sistema.

La carga no elimina extensiones posteriores ni asigna roles a usuarios concretos.


## 16. Empresa activa para evaluar permisos

Al cierre de la Tarea 44 la sesion dispone de una empresa activa validada.

Los modulos futuros podran evaluar permisos con:

```text
usuario_tiene_permiso(
    request.user,
    request.empresa_activa,
    codigo_permiso,
)
```

La empresa activa no reemplaza la validacion de pertenencia de cada objeto operado.

La siguiente etapa define la sucursal activa.


## 17. Sucursal activa como contexto operativo

Al cierre de la Tarea 45 la sesion dispone de una sucursal activa validada dentro de la empresa activa.

La evaluacion inicial de roles y permisos continúa siendo por empresa:

```text
usuario_tiene_permiso(
    request.user,
    request.empresa_activa,
    codigo_permiso,
)
```

La sucursal activa se utilizará para acotar operaciones y objetos cuando corresponda.

No se implementan todavía roles ni permisos específicos por sucursal.


## 18. Autenticacion propia del ERP

Al cierre de la Tarea 46, las vistas propias utilizan sesiones autenticadas de Django.

La autenticacion confirma identidad y estado activo del usuario.

La autorizacion funcional continúa siendo una capa separada y deberá resolverse mediante:

```text
usuario_tiene_permiso(
    request.user,
    request.empresa_activa,
    codigo_permiso,
)
```

Ser usuario autenticado no implica tener permiso funcional para operar.

## 19. Configuración de parámetros antes de aplicar permisos

Al cierre de la Tarea 47 se agrega una primera pantalla funcional propia del núcleo:

```text
/nucleo/configuracion/
```

La pantalla administra los ocho parámetros estándar de `request.empresa_activa`.

Como medida transitoria, antes de generalizar la autorización funcional:

- exige autenticación
- exige `user.is_staff`
- no acepta una empresa enviada por formulario
- no muestra el acceso a usuarios no staff

La siguiente tarea reemplazará esta restricción temporal por la evaluación backend del permiso:

```text
parametros.editar
```

Tarea siguiente:

```text
TAREA 48 — Aplicar permisos funcionales a las vistas del ERP
```


## 20. Aplicación inicial en vistas

Al cierre de TAREA 48 los permisos dejan de ser únicamente modelos
y pasan a proteger una vista funcional real.

Configuración de empresa:

- `parametros.ver`: acceso de consulta.
- `parametros.editar`: inicialización y modificación.
- edición implica acceso a la pantalla aunque no exista
  `parametros.ver` en el mismo rol.
- un usuario `staff` sin permiso funcional recibe HTTP 403.
- un superusuario activo mantiene acceso total.

Se agregan decoradores reutilizables:

```text
empresa_activa_requerida
permiso_funcional_requerido
permiso_funcional_alguno_requerido
```

La navegación utiliza decisiones derivadas del mismo backend.
Ocultar un enlace no sustituye la autorización de la vista.

Próxima tarea:

```text
TAREA 49 — Definir obligatoriedad del contexto operativo
```


## 21. Relación entre contexto y permiso

Desde TAREA 49 el orden obligatorio para vistas funcionales es:

```text
login_required
→ contexto_operativo_requerido
→ permiso_funcional_requerido
→ vista
```

El contexto debe resolverse antes del permiso porque los roles son
asignados por empresa. El permiso no reemplaza el aislamiento de
datos: cada queryset y cada objeto deben validarse contra empresa y
sucursal activas.

Una pantalla por empresa usa:

```python
@contexto_operativo_requerido(requiere_sucursal=False)
```

Una pantalla operativa usa:

```python
@contexto_operativo_requerido
```

Próxima tarea:

```text
TAREA 50 — Diseñar maestro de terceros
```
