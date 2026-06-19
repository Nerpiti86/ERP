# DOCUMENTO 01 - NUCLEO ERP

## 1. Objetivo del modulo

El Nucleo ERP es la base funcional y tecnica del sistema.

Su objetivo es definir las entidades, reglas y servicios comunes que seran utilizados por todos los demas modulos del ERP.

Este modulo debe resolver:

- empresas
- sucursales
- usuarios
- roles
- permisos
- parametros del sistema
- ejercicios fiscales
- periodos contables
- auditoria
- eventos del sistema
- documentos base

---

## 2. Principio general

Todo dato operativo del ERP debe pertenecer a una empresa.

Por eso, la mayoria de las entidades principales del sistema deberan tener relacion directa o indirecta con empresa_id.

El ERP se disenara como multiempresa desde el inicio, aunque en la primera etapa se utilice una sola empresa.

---

## 3. Alcance inicial

El alcance inicial del Nucleo ERP incluye:

1. Alta y mantenimiento de empresas.
2. Alta y mantenimiento de sucursales.
3. Administracion de usuarios.
4. Administracion de roles.
5. Administracion de permisos.
6. Relacion entre usuarios, empresas y sucursales.
7. Parametros generales del sistema.
8. Ejercicios fiscales.
9. Periodos contables.
10. Auditoria basica.
11. Eventos de negocio.
12. Base para adjuntar documentos.

---

## 4. Tablas principales previstas

### 4.1. Empresas

Tabla prevista:

- empresas

Responsabilidad:

Guardar los datos principales de cada empresa administrada por el ERP.

Campos conceptuales:

- razon_social
- nombre_fantasia
- cuit
- condicion_iva
- ingresos_brutos
- actividad_principal
- domicilio_fiscal
- localidad
- provincia
- codigo_postal
- pais
- telefono
- email
- sitio_web
- logo
- moneda_funcional
- fecha_inicio_actividades
- punto_venta_default
- activa

Reglas:

- El CUIT debe ser unico.
- La empresa puede estar activa o inactiva.
- No se deberia borrar una empresa con movimientos.
- La moneda funcional inicial sera ARS.

---

### 4.2. Sucursales

Tabla prevista:

- sucursales

Responsabilidad:

Representar puntos fisicos, administrativos o comerciales de una empresa.

Campos conceptuales:

- empresa
- nombre
- domicilio
- localidad
- provincia
- punto_de_venta
- activa

Reglas:

- Una sucursal siempre pertenece a una empresa.
- Una empresa puede tener una o varias sucursales.
- El punto de venta se usara luego para facturacion y comprobantes.

---

### 4.3. Usuarios

Tabla prevista:

- usuarios

Responsabilidad:

Representar a las personas que pueden ingresar al ERP.

Campos conceptuales:

- nombre
- apellido
- email
- password_hash
- activo
- ultimo_login
- created_at
- updated_at

Reglas:

- Cada persona debe tener su propio usuario.
- No se permite usuario compartido.
- El email debe ser unico.
- Un usuario inactivo no puede ingresar.
- Las acciones importantes deben registrar usuario_id.

---

### 4.4. Roles

Tabla prevista:

- roles

Responsabilidad:

Agrupar permisos funcionales.

Roles iniciales sugeridos:

- ADMIN
- CONTADOR
- OPERADOR
- AUDITOR
- SOLO_LECTURA

Reglas:

- Un usuario puede tener uno o mas roles.
- Los roles no deberian hardcodearse en pantallas.
- Los permisos efectivos deben calcularse desde roles y permisos.

---

### 4.5. Permisos

Tabla prevista:

- permisos

Responsabilidad:

Definir acciones posibles dentro del sistema.

Ejemplos:

- empresas.ver
- empresas.crear
- empresas.editar
- empresas.desactivar
- usuarios.ver
- usuarios.crear
- usuarios.editar
- contabilidad.ver
- contabilidad.editar
- ventas.ver
- ventas.crear
- compras.ver
- compras.crear
- tesoreria.ver
- tesoreria.operar
- auditoria.ver

Reglas:

- Los permisos deben ser granulares.
- Los permisos se asignan a roles.
- Los usuarios reciben permisos a traves de sus roles.

---

### 4.6. Usuarios por empresa

Tabla prevista:

- usuarios_empresas

Responsabilidad:

Definir a que empresas puede acceder cada usuario.

Campos conceptuales:

- usuario
- empresa
- activo

Reglas:

- Un usuario puede acceder a una o varias empresas.
- Un usuario no deberia ver datos de empresas no asignadas.

---

### 4.7. Usuarios por sucursal

Tabla prevista:

- usuarios_sucursales

Responsabilidad:

Definir a que sucursales puede acceder cada usuario.

Campos conceptuales:

- usuario
- sucursal
- activo

Reglas:

- Esta tabla permite limitar operaciones por sucursal.
- Si un usuario no tiene sucursales asignadas, se debera definir si accede a todas o a ninguna.

Decision inicial:

Por seguridad, si el usuario no tiene sucursales asignadas, no deberia operar sucursales salvo que sea administrador.

---

### 4.8. Parametros del sistema

Tabla prevista:

- parametros_sistema

Responsabilidad:

Guardar configuraciones modificables sin tocar codigo.

Ejemplos de parametros:

- moneda_funcional
- permite_stock_negativo
- usa_centros_costo
- usa_proyectos
- requiere_aprobacion_pagos
- requiere_aprobacion_compras
- tipo_cambio_default
- punto_venta_default
- modo_numeracion_comprobantes

Reglas:

- Los parametros pueden ser globales o por empresa.
- Los parametros deben tener clave unica por empresa.
- No deben usarse valores hardcodeados si pueden parametrizarse.

---

### 4.9. Ejercicios fiscales

Tabla prevista:

- ejercicios_fiscales

Responsabilidad:

Definir los ejercicios contables de cada empresa.

Campos conceptuales:

- empresa
- descripcion
- fecha_inicio
- fecha_cierre
- cerrado

Reglas:

- Una empresa puede tener varios ejercicios.
- No puede haber ejercicios superpuestos.
- Un ejercicio cerrado limita modificaciones contables.

---

### 4.10. Periodos contables

Tabla prevista:

- periodos_contables

Responsabilidad:

Dividir cada ejercicio en periodos operativos, normalmente mensuales.

Campos conceptuales:

- ejercicio
- numero
- descripcion
- fecha_inicio
- fecha_cierre
- cerrado

Reglas:

- Un periodo pertenece a un ejercicio.
- Un periodo cerrado no deberia permitir modificaciones libres.
- Las operaciones deben validar si el periodo esta abierto.

---

### 4.11. Auditoria

Tabla prevista:

- auditoria

Responsabilidad:

Registrar acciones importantes del sistema.

Campos conceptuales:

- empresa
- usuario
- accion
- tabla
- registro_id
- datos_anteriores
- datos_nuevos
- ip
- user_agent
- created_at

Acciones posibles:

- INSERT
- UPDATE
- DELETE
- LOGIN
- LOGOUT
- ANULAR
- CONFIRMAR
- CERRAR_PERIODO
- ABRIR_PERIODO

Reglas:

- Las acciones criticas deben auditarse.
- No se debe borrar auditoria desde pantallas comunes.
- La auditoria debe permitir reconstruir cambios importantes.

---

### 4.12. Eventos de negocio

Tabla prevista:

- eventos_negocio

Responsabilidad:

Registrar hechos relevantes que ocurren dentro del ERP.

Campos conceptuales:

- empresa
- tipo_evento
- entidad_tipo
- entidad_id
- fecha_evento
- usuario
- payload_json
- estado
- created_at

Ejemplos de eventos:

- EMPRESA_CREADA
- SUCURSAL_CREADA
- USUARIO_CREADO
- PERIODO_CERRADO
- FACTURA_VENTA_EMITIDA
- COBRO_CONFIRMADO
- PAGO_CONFIRMADO
- ASIENTO_GENERADO

Reglas:

- Un evento representa algo que ya ocurrio.
- Los eventos deben ser trazables.
- Los modulos futuros podran reaccionar a eventos.

---

### 4.13. Documentos

Tabla prevista:

- documentos

Responsabilidad:

Guardar referencias a archivos adjuntos del ERP.

Campos conceptuales:

- empresa
- entidad_tipo
- entidad_id
- nombre
- tipo_mime
- ruta
- tamanio_bytes
- usuario
- created_at

Reglas:

- Los archivos fisicos se guardaran inicialmente en media/.
- La base de datos guardara la referencia, no necesariamente el archivo binario.
- Cada documento debe estar asociado a una entidad del sistema.

---

## 5. Pantallas iniciales del Nucleo ERP

Pantallas previstas:

1. Login.
2. Panel inicial.
3. Listado de empresas.
4. Alta y edicion de empresa.
5. Listado de sucursales.
6. Alta y edicion de sucursal.
7. Listado de usuarios.
8. Alta y edicion de usuario.
9. Roles y permisos.
10. Parametros del sistema.
11. Ejercicios fiscales.
12. Periodos contables.
13. Consulta de auditoria.
14. Consulta de eventos.

---

## 6. Reglas generales del Nucleo ERP

1. No se debe operar sin usuario autenticado.
2. No se debe operar sin empresa activa.
3. No se debe operar sobre periodos cerrados salvo permiso especial.
4. No se deben borrar registros con movimientos asociados.
5. Toda accion critica debe auditarse.
6. Los permisos deben validarse en backend.
7. La interfaz no reemplaza la seguridad del backend.
8. PostgreSQL no debe exponerse directamente a la red.
9. El acceso remoto inicial sera por Tailscale.
10. Cada usuario remoto debe tener usuario propio dentro del ERP.

---

## 7. Dependencias con otros modulos

El Nucleo ERP sera dependencia de todos los modulos futuros.

Modulos que dependen del Nucleo ERP:

- terceros
- contabilidad
- productos
- stock
- ventas
- compras
- tesoreria
- impuestos
- documentos
- reporting

---

## 8. Prioridad

Prioridad: maxima.

Este modulo debe construirse antes de ventas, compras, stock, tesoreria o contabilidad avanzada.

---

## 9. Decision final

El Nucleo ERP sera el primer modulo funcional despues de la base tecnica.

Su implementacion debe dejar preparada la estructura para que todos los modulos futuros compartan empresa, usuario, permisos, periodos, auditoria y eventos.

---

## 10. Estado real actual al cierre de Tarea 34

Al cierre de la Tarea 34, el modulo `apps.nucleo` ya existe y tiene modelos reales, migraciones aplicadas, tests y administracion inicial mediante Django Admin.

### 10.1. Modelos implementados

Modelos actuales del nucleo:

- Empresa
- Sucursal
- EjercicioFiscal
- PeriodoContable
- UsuarioEmpresa
- UsuarioSucursal
- ParametroSistema
- Auditoria
- EventoNegocio
- DocumentoAdjunto
- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa

### 10.2. Tablas reales creadas en PostgreSQL

Tablas actuales del nucleo:

- nucleo_empresa
- nucleo_sucursal
- nucleo_ejerciciofiscal
- nucleo_periodocontable
- nucleo_usuarioempresa
- nucleo_usuariosucursal
- nucleo_parametrosistema
- nucleo_auditoria
- nucleo_eventonegocio
- nucleo_documentoadjunto
- nucleo_rolfuncional
- nucleo_permisofuncional
- nucleo_rolpermiso
- nucleo_usuariorolempresa

### 10.3. Migraciones relevantes

Migraciones principales aplicadas:

```text
0001_initial
0002_ejerciciofiscal_periodocontable_and_more
0003_usuarioempresa_usuariosucursal
0004_parametrosistema
0005_auditoria
0006_eventonegocio
0007_documentoadjunto
0008_roles_permisos_funcionales
```

### 10.4. Estado local de datos demo

Datos demo locales cargados en PostgreSQL:

```text
Empresa Demo SA
CUIT: 30712345678
Sucursal: Casa central
Codigo sucursal: CASA
Ejercicio fiscal: 2026
Periodo contable: 2026-01
Usuario: ADMIN
```

Relaciones de acceso cargadas localmente:

```text
ADMIN -> Empresa Demo SA
ADMIN -> Empresa Demo SA - Casa central
```

Estos datos son locales y no forman parte del repositorio.

### 10.5. ParametroSistema

El modelo `ParametroSistema` permite guardar configuraciones modificables sin tocar codigo.

Ambitos implementados:

- GLOBAL
- EMPRESA

Tipos de valor implementados:

- TEXTO
- ENTERO
- DECIMAL
- BOOLEANO
- JSON

Reglas implementadas:

- Un parametro GLOBAL no debe tener empresa.
- Un parametro EMPRESA debe tener empresa.
- La clave se normaliza a minusculas.
- La clave global es unica.
- La clave por empresa es unica.
- Se validan valores enteros, decimales, booleanos y JSON segun `tipo_valor`.

### 10.6. Uso actual del Django Admin

El Django Admin se usa como backoffice tecnico inicial para:

- cargar datos
- validar modelos
- probar relaciones
- administrar configuraciones iniciales
- detectar errores antes de crear pantallas propias

El Django Admin no sera la interfaz final del ERP.

Las pantallas propias del nucleo se construiran luego con:

- Django Templates
- Bootstrap
- HTMX cuando corresponda

### 10.7. Validacion reciente

Ultima validacion funcional documentada:

```text
52 tests OK
manage.py check OK
compileall OK
makemigrations --check --dry-run: No changes detected
push OK
```

### 10.8. Pendientes inmediatos del nucleo

Pendientes inmediatos:

1. Definir seleccion de empresa activa para la sesion.
2. Definir seleccion de sucursal activa para la sesion.
3. Crear pantallas propias del nucleo.

Pendientes de reglas de consistencia:

1. Evitar ejercicios fiscales superpuestos por empresa.
2. Evitar periodos contables superpuestos dentro de un ejercicio.
3. Definir comportamiento final para superusuarios versus usuarios normales.


### 10.9. Auditoria basica

Al cierre de la Tarea 37 se implementa auditoria basica en el nucleo.

Modelo agregado:

- Auditoria

Tabla real:

- nucleo_auditoria

Alcance inicial:

- empresa opcional
- usuario opcional
- accion
- tabla
- registro_id
- datos_anteriores en JSON
- datos_nuevos en JSON
- ip
- user_agent
- fecha/hora de creacion

Acciones iniciales:

- INSERT
- UPDATE
- DELETE
- LOGIN
- LOGOUT
- ANULAR
- CONFIRMAR
- CERRAR_PERIODO
- ABRIR_PERIODO

Criterio inicial:

La auditoria queda disponible como modelo base y consulta tecnica desde Django Admin.

No se implementa todavia middleware global ni auditoria automatica de todas las pantallas.


### 10.10. Eventos de negocio

Al cierre de la Tarea 38 se implementa la base de eventos de negocio en el nucleo.

Modelo agregado:

- EventoNegocio

Tabla real:

- nucleo_eventonegocio

Alcance inicial:

- empresa opcional
- usuario opcional
- tipo_evento
- entidad_tipo
- entidad_id
- fecha_evento
- payload_json
- estado
- creado_en
- actualizado_en

Estados iniciales:

- PENDIENTE
- PROCESADO
- ERROR
- IGNORADO

Criterio inicial:

Un evento de negocio representa un hecho funcional que ya ocurrio dentro del ERP.

La estructura queda disponible como base para que modulos futuros registren hechos relevantes.

No se implementan todavia colas, listeners, signals automaticos ni procesamiento asincronico de eventos.


### 10.11. Documentos adjuntos

Al cierre de la Tarea 39 se implementa la base de documentos adjuntos en el nucleo.

Modelo agregado:

- DocumentoAdjunto

Tabla real:

- nucleo_documentoadjunto

Alcance inicial:

- empresa
- entidad_tipo
- entidad_id
- nombre_original
- nombre_archivo
- tipo_mime
- ruta
- tamanio_bytes
- usuario opcional
- activo
- creado_en
- actualizado_en

Criterio inicial:

La base de datos guarda referencias a archivos adjuntos, no el binario del archivo.

Los archivos fisicos se guardaran inicialmente bajo media/.

Cada documento queda asociado a una entidad del sistema mediante entidad_tipo y entidad_id.

No se implementan todavia carga desde pantalla, descarga, visor, borrado fisico, OCR, antivirus ni versionado de archivos.


### 10.12. Estrategia de roles y permisos propios

Al cierre de la Tarea 40 se define la estrategia documental de roles y permisos propios.

Documento rector agregado:

- docs/04_roles_permisos.md

Decision principal:

- Usar Django Auth como base tecnica inicial.
- Mantener `settings.AUTH_USER_MODEL` como referencia en modelos propios.
- No cambiar `AUTH_USER_MODEL` en esta tarea.
- Evaluar usuario custom en una tarea separada antes de implementar tablas de seguridad propias.
- Implementar permisos funcionales propios del ERP, independientes de la interfaz.
- Resolver permisos efectivos desde roles asignados por empresa.
- Validar permisos en backend, no solo en la interfaz.

Modelos futuros propuestos:

- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa

Esta tarea no crea tablas, migraciones, middleware, pantallas ni validadores de permisos.


### 10.13. Evaluacion de usuario custom

Al cierre de la Tarea 41 se evalua la conveniencia de crear un usuario custom.

Documento rector agregado:

- docs/05_usuario_custom.md

Decision principal:

- No cambiar `AUTH_USER_MODEL` en esta etapa.
- Mantener `auth.User` estandar de Django como usuario base.
- Continuar usando `settings.AUTH_USER_MODEL` en ForeignKey y `get_user_model()` en codigo runtime.
- No referenciar `django.contrib.auth.models.User` directamente en modelos propios.
- Usar modelos propios del ERP para empresa, sucursal, roles, permisos y datos funcionales.
- Crear un perfil de usuario propio solo si aparece informacion no autenticadora que lo justifique.

Motivo:

El proyecto ya tiene migraciones aplicadas y varias relaciones a usuario mediante `settings.AUTH_USER_MODEL`.

Cambiar a usuario custom despues de crear tablas puede afectar claves foraneas, relaciones y migraciones.

La estrategia queda desbloqueada para implementar roles y permisos funcionales propios.


### 10.14. Roles y permisos funcionales

Al cierre de la Tarea 42 se implementa la base de roles y permisos funcionales.

Modelos agregados:

- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa

Tablas reales:

- nucleo_rolfuncional
- nucleo_permisofuncional
- nucleo_rolpermiso
- nucleo_usuariorolempresa

Helper agregado:

- apps/nucleo/permisos.py
- usuario_tiene_permiso(usuario, empresa, codigo_permiso)

Alcance inicial:

- roles funcionales configurables
- permisos funcionales configurables
- permisos asignados a roles
- roles asignados a usuarios por empresa
- calculo backend de permiso efectivo

Reglas iniciales:

- Los roles usan codigo en mayusculas.
- Los permisos usan codigo `modulo.accion` en minusculas.
- Un usuario debe tener acceso activo a una empresa antes de recibir rol funcional en esa empresa.
- Los permisos efectivos se calculan desde roles activos, permisos activos y asignaciones activas.
- Un superusuario activo puede operar tecnicamente sobre una empresa activa.

No se cargan todavia roles ni permisos iniciales.

No se implementan todavia middleware, decoradores, pantallas ni restricciones de UI.


### 10.15. Roles y permisos iniciales

Al cierre de la Tarea 43 se versiona y ejecuta una carga inicial idempotente.

Comando agregado:

```text
python manage.py cargar_roles_permisos_iniciales
```

Definiciones versionadas:

- apps/nucleo/roles_iniciales.py

Roles iniciales:

- ADMIN
- CONTADOR
- OPERADOR
- AUDITOR
- SOLO_LECTURA

Cantidad inicial:

- 5 roles
- 25 permisos
- 64 relaciones rol-permiso

Criterio de asignacion:

- ADMIN recibe todos los permisos iniciales.
- CONTADOR recibe acceso contable, documental y consultas operativas.
- OPERADOR recibe permisos de carga operativa.
- AUDITOR recibe consultas ampliadas de auditoria y eventos.
- SOLO_LECTURA recibe consultas generales sin escritura.

La carga:

- crea los datos faltantes
- actualiza definiciones iniciales
- reactiva relaciones iniciales inactivas
- puede ejecutarse mas de una vez sin duplicar datos
- no elimina roles, permisos ni relaciones adicionales creadas por el usuario

La tarea no asigna roles a usuarios concretos.

No se crea migracion porque los roles y permisos son datos configurables, no estructura de base de datos.

