# Estado real integral del ERP

> Fotografía canónica generada por la TAREA 0016. Los cortes anteriores se conservan como historia y no reemplazan este estado.

## Identificación del corte

```text
Fecha: 26/06/2026
Repositorio: Nerpiti86/ERP
Rama: main
Base auditada antes del commit documental: 0f9712ff85cb38deb2a5442bcbed5b5598f8b959
Commit documental: el commit de main que contiene este archivo
Suite completa: 425 pruebas
Migraciones pendientes: 0
```

## Criterio de verdad

La fuente primaria es el código y las migraciones de `main`. Esta fotografía resume ese estado. Los documentos históricos siguen siendo útiles para reconstruir decisiones, pero sus cifras y próximos pasos no deben interpretarse como vigentes cuando contradicen este archivo.

## Arquitectura efectiva

- monolito modular Django;
- PostgreSQL como base principal;
- Django Templates y Bootstrap para la interfaz;
- autenticación basada en Django Auth;
- roles y permisos funcionales propios;
- contexto activo por empresa y, cuando corresponde, por sucursal;
- servicios transaccionales para cambios de dominio;
- auditoría de operaciones relevantes;
- trabajo sobre rama única `main` mediante tareas ejecutables `.txt`.

## Componentes transversales

```text
Settings: config.settings
ROOT_URLCONF: config.urls
AUTH_USER_MODEL: auth.User
Base de datos: django.db.backends.postgresql
Middlewares: 8
Context processors: 5
```

## Aplicaciones propias instaladas

| Aplicación | Modelos | Última hoja de migración | Pruebas ejecutadas | Componentes detectados |
|---|---|---|---|---|
| apps.contabilidad | 1 | 0001_initial | 40 | models, services, forms, views, urls, admin |
| apps.core | 0 | Sin migraciones | 45 | models, forms, views, urls, admin |
| apps.items | 5 | 0002_catalogos_iniciales | 67 | models, services, forms, views, urls, admin |
| apps.nucleo | 22 | 0015_puntos_venta | 221 | models, forms, views, urls, admin, context_processors |
| apps.terceros | 6 | 0002_catalogos_iniciales | 52 | models, services, forms, views, urls, admin |

## Estado funcional

### Implementado y operativo

- núcleo empresarial, accesos, contexto de empresa y sucursal, parámetros y auditoría;
- configuración fiscal de empresa, actividades económicas, Ingresos Brutos y puntos de venta;
- autenticación propia y autorización funcional por empresa;
- maestro de terceros con roles de cliente/proveedor, domicilios y contactos;
- maestro de productos y servicios con categorías, marcas, unidades, IVA e interfaz funcional.

### Implementado parcialmente

- el ERP posee permisos reservados y conceptos para módulos transaccionales futuros, pero eso no implica que esos circuitos estén disponibles;
- Django Admin continúa como backoffice técnico y no sustituye la interfaz funcional;
- la medición de cobertura de código no forma parte del contrato actual.

### No implementado como circuito operativo completo

- ventas
- compras
- stock
- tesoreria
- cuentas corrientes
- impuestos
- reportes

## Modelos y esquema

### `apps.contabilidad`

- Ruta: `apps/contabilidad`
- Pruebas ejecutadas para la app: `40`
- Métodos de prueba detectados estáticamente: `40`
- Plantillas detectadas: `2`
- Archivos estáticos detectados: `0`
- Comandos de gestión: `ninguno`

#### `contabilidad.CuentaContable`

- Tabla: `contabilidad_cuentacontable`
- Campos: `cuentas_hijas, id, empresa, parent, codigo, nombre, descripcion, tipo_contable, naturaleza, habilitada, creada_en, actualizada_en`
- Restricciones declaradas: `4` (`uniq_cuenta_empresa_codigo, uniq_cuenta_raiz_empresa_tipo, chk_cuenta_codigo_estructura, chk_cuenta_naturaleza_imputabilidad`)
- Índices declarados: `0`
### `apps.core`

- Ruta: `apps/core`
- Pruebas ejecutadas para la app: `45`
- Métodos de prueba detectados estáticamente: `45`
- Plantillas detectadas: `4`
- Archivos estáticos detectados: `0`
- Comandos de gestión: `ninguno`

No define modelos propios.
### `apps.items`

- Ruta: `apps/items`
- Pruebas ejecutadas para la app: `67`
- Métodos de prueba detectados estáticamente: `67`
- Plantillas detectadas: `5`
- Archivos estáticos detectados: `0`
- Comandos de gestión: `cargar_catalogos_items_iniciales`

#### `items.CategoriaItem`

- Tabla: `items_categoriaitem`
- Campos: `items, id, empresa, codigo, nombre, activo, creado_en, actualizado_en, descripcion`
- Restricciones declaradas: `1` (`uniq_categoria_item_empresa_codigo`)
- Índices declarados: `1` (`idx_categoria_item_emp_act`)

#### `items.Marca`

- Tabla: `items_marca`
- Campos: `items, id, empresa, codigo, nombre, activo, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`uniq_marca_empresa_codigo`)
- Índices declarados: `1` (`idx_marca_emp_act_nombre`)

#### `items.UnidadMedida`

- Tabla: `items_unidadmedida`
- Campos: `items, id, codigo, nombre, activo, sistema, creado_en, actualizado_en, simbolo, codigo_arca`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `items.AlicuotaIVA`

- Tabla: `items_alicuotaiva`
- Campos: `items, id, codigo, nombre, activo, sistema, creado_en, actualizado_en, porcentaje, codigo_arca`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `items.Item`

- Tabla: `items_item`
- Campos: `id, empresa, codigo, nombre, descripcion, tipo, categoria, marca, unidad_medida, se_compra, se_vende, controla_stock, tratamiento_iva, alicuota_iva, activo, observaciones, creado_en, actualizado_en`
- Restricciones declaradas: `4` (`uniq_item_empresa_codigo, chk_item_capacidad_operativa, chk_item_servicio_sin_stock, chk_item_tratamiento_iva`)
- Índices declarados: `2` (`idx_item_emp_act_nombre, idx_item_emp_tipo_activo`)
### `apps.nucleo`

- Ruta: `apps/nucleo`
- Pruebas ejecutadas para la app: `221`
- Métodos de prueba detectados estáticamente: `221`
- Plantillas detectadas: `12`
- Archivos estáticos detectados: `0`
- Comandos de gestión: `actualizar_catalogo_clae, cargar_roles_permisos_iniciales`

#### `nucleo.Empresa`

- Tabla: `nucleo_empresa`
- Campos: `perfil_fiscal, actividades_economicas, configuraciones_iibb, sucursales, puntos_venta, ejercicios_fiscales, parametros_sistema, auditorias, eventos_negocio, documentos_adjuntos, usuarios_roles, usuarios_asignados, terceros, categoriaitem, marca, items, cuentas_contables, id, cuit, razon_social, nombre_fantasia, condicion_iva, activa, creada_en, actualizada_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `nucleo.PerfilFiscalEmpresa`

- Tabla: `nucleo_perfilfiscalempresa`
- Campos: `id, empresa, naturaleza, fecha_inicio_actividades, mes_cierre_ejercicio_predeterminado, apellido, apellido_materno, nombres, fecha_nacimiento, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`chk_perfil_fiscal_mes_cierre`)
- Índices declarados: `0`

#### `nucleo.ActividadEconomica`

- Tabla: `nucleo_actividadeconomica`
- Campos: `asignaciones_empresa, id, nomenclador, codigo, descripcion, activa, fuente_url, fuente_sha256, primera_importacion_en, ultima_sincronizacion_en`
- Restricciones declaradas: `1` (`uniq_actividad_nomenclador_codigo`)
- Índices declarados: `1` (`idx_actividad_nom_act_cod`)

#### `nucleo.ImportacionCatalogoActividad`

- Tabla: `nucleo_importacioncatalogoactividad`
- Campos: `id, nomenclador, fuente_url, archivo_nombre, sha256, total_registros, creados, actualizados, reactivados, desactivados, importada_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `nucleo.EmpresaActividad`

- Tabla: `nucleo_empresaactividad`
- Campos: `puntos_venta_predeterminados, id, empresa, actividad, principal, activa, orden, vigencia_desde, vigencia_hasta, observaciones, nomenclador_registrado, codigo_registrado, descripcion_registrada, fuente_sha256_registrada, creada_en, actualizada_en`
- Restricciones declaradas: `4` (`uniq_emp_actividad_activa, uniq_emp_actividad_principal, chk_emp_act_principal_activa, chk_emp_act_vigencia`)
- Índices declarados: `1` (`idx_emp_act_estado`)

#### `nucleo.JurisdiccionFiscal`

- Tabla: `nucleo_jurisdiccionfiscal`
- Campos: `inscripciones_empresa, id, codigo, nombre, activa, orden, fuente_url, creada_en, actualizada_en`
- Restricciones declaradas: `0`
- Índices declarados: `1` (`idx_jur_fiscal_act_ord`)

#### `nucleo.ConfiguracionIIBBEmpresa`

- Tabla: `nucleo_configuracionesiibbempresa`
- Campos: `jurisdicciones, id, empresa, regimen, tratamiento_general, numero_inscripcion, fecha_alta, fecha_baja, activa, observaciones, creada_en, actualizada_en`
- Restricciones declaradas: `3` (`uniq_emp_config_iibb_activa, chk_config_iibb_fechas, chk_config_iibb_activa_sin_baja`)
- Índices declarados: `1` (`idx_config_iibb_emp_est`)

#### `nucleo.EmpresaJurisdiccionIIBB`

- Tabla: `nucleo_empresajurisdicioniibb`
- Campos: `puntos_venta_predeterminados, id, configuracion, jurisdiccion, numero_inscripcion, sede, tratamiento, fecha_alta, fecha_baja, activa, observaciones, codigo_registrado, nombre_registrado, fuente_url_registrada, creada_en, actualizada_en`
- Restricciones declaradas: `5` (`uniq_config_jur_iibb_activa, uniq_config_jur_iibb_sede, chk_jur_iibb_sede_activa, chk_jur_iibb_fechas, chk_jur_iibb_activa_sin_baja`)
- Índices declarados: `1` (`idx_jur_iibb_config_est`)

#### `nucleo.Sucursal`

- Tabla: `nucleo_sucursal`
- Campos: `puntos_venta, usuarios_asignados, id, empresa, codigo, nombre, domicilio, calle, numero, sector, torre, piso, departamento, barrio, localidad, codigo_postal, partido_departamento, provincia, pais, es_casa_central, es_domicilio_fiscal_nacional, es_domicilio_fiscal_provincial, es_domicilio_legal, es_principal_actividades, es_deposito, es_local_comercial, es_oficina_administrativa, otras_funciones, activa, creada_en, actualizada_en`
- Restricciones declaradas: `6` (`uniq_sucursal_empresa_codigo, uniq_suc_emp_casa_central, uniq_suc_emp_fiscal_nac, uniq_suc_emp_fiscal_prov, uniq_suc_emp_legal, uniq_suc_emp_principal_act`)
- Índices declarados: `0`

#### `nucleo.PuntoVenta`

- Tabla: `nucleo_puntoventa`
- Campos: `id, empresa, sucursal, numero, nombre_fantasia, sistema_emision, descripcion_sistema_arca, actividad_predeterminada, jurisdiccion_iibb_predeterminada, predeterminado, bloqueado, fecha_alta, fecha_baja, activo, observaciones, creado_en, actualizado_en`
- Restricciones declaradas: `6` (`uniq_pv_empresa_numero, uniq_pv_suc_default_activo, chk_pv_numero_rango, chk_pv_fechas, chk_pv_activo_sin_baja, chk_pv_default_activo`)
- Índices declarados: `2` (`idx_pv_emp_act_num, idx_pv_suc_act_def`)

#### `nucleo.EjercicioFiscal`

- Tabla: `nucleo_ejerciciofiscal`
- Campos: `periodos, id, empresa, codigo, nombre, fecha_inicio, fecha_cierre, estado, activo, creado_en, actualizado_en`
- Restricciones declaradas: `2` (`uniq_ejercicio_empresa_codigo, chk_ejercicio_fecha_cierre_gte_inicio`)
- Índices declarados: `0`

#### `nucleo.PeriodoContable`

- Tabla: `nucleo_periodocontable`
- Campos: `id, ejercicio, codigo, nombre, fecha_inicio, fecha_cierre, estado, activo, creado_en, actualizado_en`
- Restricciones declaradas: `2` (`uniq_periodo_ejercicio_codigo, chk_periodo_fecha_cierre_gte_inicio`)
- Índices declarados: `0`

#### `nucleo.ParametroSistema`

- Tabla: `nucleo_parametrosistema`
- Campos: `id, ambito, empresa, clave, valor, tipo_valor, descripcion, activo, creado_en, actualizado_en`
- Restricciones declaradas: `3` (`uniq_parametro_global_clave, uniq_parametro_empresa_clave, chk_parametro_ambito_empresa`)
- Índices declarados: `0`

#### `nucleo.Auditoria`

- Tabla: `nucleo_auditoria`
- Campos: `id, empresa, usuario, accion, tabla, registro_id, datos_anteriores, datos_nuevos, ip, user_agent, creado_en`
- Restricciones declaradas: `0`
- Índices declarados: `3` (`idx_auditoria_empresa_fecha, idx_auditoria_accion_fecha, idx_auditoria_tabla_registro`)

#### `nucleo.EventoNegocio`

- Tabla: `nucleo_eventonegocio`
- Campos: `id, empresa, tipo_evento, entidad_tipo, entidad_id, fecha_evento, usuario, payload_json, estado, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `3` (`idx_evento_empresa_fecha, idx_evento_tipo_fecha, idx_evento_entidad`)

#### `nucleo.DocumentoAdjunto`

- Tabla: `nucleo_documentoadjunto`
- Campos: `id, empresa, entidad_tipo, entidad_id, nombre_original, nombre_archivo, tipo_mime, ruta, tamanio_bytes, usuario, activo, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `3` (`idx_documento_empresa_fecha, idx_documento_entidad, idx_documento_activo_fecha`)

#### `nucleo.RolFuncional`

- Tabla: `nucleo_rolfuncional`
- Campos: `permisos_asignados, usuarios_empresa, id, codigo, nombre, descripcion, activo, sistema, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `nucleo.PermisoFuncional`

- Tabla: `nucleo_permisofuncional`
- Campos: `roles_asignados, id, codigo, modulo, accion, descripcion, activo, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `nucleo.RolPermiso`

- Tabla: `nucleo_rolpermiso`
- Campos: `id, rol, permiso, activo, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`uniq_rol_permiso`)
- Índices declarados: `0`

#### `nucleo.UsuarioRolEmpresa`

- Tabla: `nucleo_usuariorolempresa`
- Campos: `id, usuario, empresa, rol, activo, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`uniq_usuario_rol_empresa`)
- Índices declarados: `0`

#### `nucleo.UsuarioEmpresa`

- Tabla: `nucleo_usuarioempresa`
- Campos: `id, usuario, empresa, activo, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`uniq_usuario_empresa`)
- Índices declarados: `0`

#### `nucleo.UsuarioSucursal`

- Tabla: `nucleo_usuariosucursal`
- Campos: `id, usuario, sucursal, activo, creado_en, actualizado_en`
- Restricciones declaradas: `1` (`uniq_usuario_sucursal`)
- Índices declarados: `0`
### `apps.terceros`

- Ruta: `apps/terceros`
- Pruebas ejecutadas para la app: `52`
- Métodos de prueba detectados estáticamente: `52`
- Plantillas detectadas: `5`
- Archivos estáticos detectados: `0`
- Comandos de gestión: `ninguno`

#### `terceros.TipoDocumento`

- Tabla: `terceros_tipodocumento`
- Campos: `terceros, id, codigo, nombre, codigo_arca, requiere_numero, activo, sistema, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `terceros.CondicionIVA`

- Tabla: `terceros_condicioniva`
- Campos: `terceros, id, codigo, nombre, codigo_arca, activo, sistema, creado_en, actualizado_en`
- Restricciones declaradas: `0`
- Índices declarados: `0`

#### `terceros.Tercero`

- Tabla: `terceros_tercero`
- Campos: `roles, domicilios, contactos, id, empresa, codigo, tipo_persona, tipo_documento, numero_documento, denominacion, nombre_fantasia, condicion_iva, telefono, email, sitio_web, observaciones, fecha_alta, fecha_baja, activo, creado_en, actualizado_en`
- Restricciones declaradas: `4` (`uniq_tercero_empresa_codigo, uniq_tercero_empresa_documento, chk_tercero_fechas, chk_tercero_activo_sin_baja`)
- Índices declarados: `2` (`idx_tercero_emp_act_den, idx_tercero_emp_doc`)

#### `terceros.TerceroRol`

- Tabla: `terceros_tercerorol`
- Campos: `id, tercero, rol, fecha_alta, fecha_baja, activo, creado_en, actualizado_en`
- Restricciones declaradas: `3` (`uniq_tercero_rol_activo, chk_tercero_rol_fechas, chk_tercero_rol_activo_sin_baja`)
- Índices declarados: `0`

#### `terceros.DomicilioTercero`

- Tabla: `terceros_domiciliotercero`
- Campos: `id, tercero, tipo, nombre, calle, numero, sector, torre, piso, departamento, barrio, localidad, codigo_postal, partido_departamento, provincia, pais, principal, activo, fecha_alta, fecha_baja, observaciones, creado_en, actualizado_en`
- Restricciones declaradas: `4` (`uniq_dom_tercero_tipo_principal, chk_dom_principal_activo, chk_dom_tercero_fechas, chk_dom_tercero_activo_sin_baja`)
- Índices declarados: `1` (`idx_dom_tercero_act_tipo`)

#### `terceros.ContactoTercero`

- Tabla: `terceros_contactotercero`
- Campos: `id, tercero, nombre, cargo, area, telefono, email, principal, activo, fecha_alta, fecha_baja, observaciones, creado_en, actualizado_en`
- Restricciones declaradas: `4` (`uniq_contacto_tercero_principal, chk_contacto_principal_activo, chk_contacto_tercero_fechas, chk_contacto_activo_sin_baja`)
- Índices declarados: `1` (`idx_contacto_tercero_act`)

## Migraciones

| Aplicación | Migraciones en disco | Migraciones aplicadas | Hojas |
|---|---|---|---|
| apps.contabilidad | 1 | 1 | 0001_initial |
| apps.core | 0 | 0 | Sin hoja |
| apps.items | 2 | 2 | 0002_catalogos_iniciales |
| apps.nucleo | 15 | 15 | 0015_puntos_venta |
| apps.terceros | 2 | 2 | 0002_catalogos_iniciales |

Migraciones pendientes detectadas: `0`.

## Rutas registradas

| Ruta | Nombre | Callback |
|---|---|---|
| admin/ | index | django.contrib.admin.sites.index |
| admin/login/ | login | django.contrib.admin.sites.login |
| admin/logout/ | logout | django.contrib.admin.sites.logout |
| admin/password_change/ | password_change | django.contrib.admin.sites.password_change |
| admin/password_change/done/ | password_change_done | django.contrib.admin.sites.password_change_done |
| admin/autocomplete/ | autocomplete | django.contrib.admin.sites.autocomplete_view |
| admin/jsi18n/ | jsi18n | django.contrib.admin.sites.i18n_javascript |
| admin/r/<path:content_type_id>/<path:object_id>/ | view_on_site | django.contrib.contenttypes.views.shortcut |
| admin/nucleo/actividadeconomica/ | nucleo_actividadeconomica_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/actividadeconomica/add/ | nucleo_actividadeconomica_add | django.contrib.admin.options.add_view |
| admin/nucleo/actividadeconomica/<path:object_id>/history/ | nucleo_actividadeconomica_history | django.contrib.admin.options.history_view |
| admin/nucleo/actividadeconomica/<path:object_id>/delete/ | nucleo_actividadeconomica_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/actividadeconomica/<path:object_id>/change/ | nucleo_actividadeconomica_change | django.contrib.admin.options.change_view |
| admin/nucleo/actividadeconomica/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/importacioncatalogoactividad/ | nucleo_importacioncatalogoactividad_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/importacioncatalogoactividad/add/ | nucleo_importacioncatalogoactividad_add | django.contrib.admin.options.add_view |
| admin/nucleo/importacioncatalogoactividad/<path:object_id>/history/ | nucleo_importacioncatalogoactividad_history | django.contrib.admin.options.history_view |
| admin/nucleo/importacioncatalogoactividad/<path:object_id>/delete/ | nucleo_importacioncatalogoactividad_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/importacioncatalogoactividad/<path:object_id>/change/ | nucleo_importacioncatalogoactividad_change | django.contrib.admin.options.change_view |
| admin/nucleo/importacioncatalogoactividad/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/empresaactividad/ | nucleo_empresaactividad_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/empresaactividad/add/ | nucleo_empresaactividad_add | django.contrib.admin.options.add_view |
| admin/nucleo/empresaactividad/<path:object_id>/history/ | nucleo_empresaactividad_history | django.contrib.admin.options.history_view |
| admin/nucleo/empresaactividad/<path:object_id>/delete/ | nucleo_empresaactividad_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/empresaactividad/<path:object_id>/change/ | nucleo_empresaactividad_change | django.contrib.admin.options.change_view |
| admin/nucleo/empresaactividad/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/jurisdiccionfiscal/ | nucleo_jurisdiccionfiscal_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/jurisdiccionfiscal/add/ | nucleo_jurisdiccionfiscal_add | django.contrib.admin.options.add_view |
| admin/nucleo/jurisdiccionfiscal/<path:object_id>/history/ | nucleo_jurisdiccionfiscal_history | django.contrib.admin.options.history_view |
| admin/nucleo/jurisdiccionfiscal/<path:object_id>/delete/ | nucleo_jurisdiccionfiscal_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/jurisdiccionfiscal/<path:object_id>/change/ | nucleo_jurisdiccionfiscal_change | django.contrib.admin.options.change_view |
| admin/nucleo/jurisdiccionfiscal/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/configuracioniibbempresa/ | nucleo_configuracioniibbempresa_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/configuracioniibbempresa/add/ | nucleo_configuracioniibbempresa_add | django.contrib.admin.options.add_view |
| admin/nucleo/configuracioniibbempresa/<path:object_id>/history/ | nucleo_configuracioniibbempresa_history | django.contrib.admin.options.history_view |
| admin/nucleo/configuracioniibbempresa/<path:object_id>/delete/ | nucleo_configuracioniibbempresa_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/configuracioniibbempresa/<path:object_id>/change/ | nucleo_configuracioniibbempresa_change | django.contrib.admin.options.change_view |
| admin/nucleo/configuracioniibbempresa/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/empresajurisdiccioniibb/ | nucleo_empresajurisdiccioniibb_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/empresajurisdiccioniibb/add/ | nucleo_empresajurisdiccioniibb_add | django.contrib.admin.options.add_view |
| admin/nucleo/empresajurisdiccioniibb/<path:object_id>/history/ | nucleo_empresajurisdiccioniibb_history | django.contrib.admin.options.history_view |
| admin/nucleo/empresajurisdiccioniibb/<path:object_id>/delete/ | nucleo_empresajurisdiccioniibb_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/empresajurisdiccioniibb/<path:object_id>/change/ | nucleo_empresajurisdiccioniibb_change | django.contrib.admin.options.change_view |
| admin/nucleo/empresajurisdiccioniibb/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/puntoventa/ | nucleo_puntoventa_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/puntoventa/add/ | nucleo_puntoventa_add | django.contrib.admin.options.add_view |
| admin/nucleo/puntoventa/<path:object_id>/history/ | nucleo_puntoventa_history | django.contrib.admin.options.history_view |
| admin/nucleo/puntoventa/<path:object_id>/delete/ | nucleo_puntoventa_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/puntoventa/<path:object_id>/change/ | nucleo_puntoventa_change | django.contrib.admin.options.change_view |
| admin/nucleo/puntoventa/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/empresa/ | nucleo_empresa_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/empresa/add/ | nucleo_empresa_add | django.contrib.admin.options.add_view |
| admin/nucleo/empresa/<path:object_id>/history/ | nucleo_empresa_history | django.contrib.admin.options.history_view |
| admin/nucleo/empresa/<path:object_id>/delete/ | nucleo_empresa_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/empresa/<path:object_id>/change/ | nucleo_empresa_change | django.contrib.admin.options.change_view |
| admin/nucleo/empresa/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/sucursal/ | nucleo_sucursal_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/sucursal/add/ | nucleo_sucursal_add | django.contrib.admin.options.add_view |
| admin/nucleo/sucursal/<path:object_id>/history/ | nucleo_sucursal_history | django.contrib.admin.options.history_view |
| admin/nucleo/sucursal/<path:object_id>/delete/ | nucleo_sucursal_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/sucursal/<path:object_id>/change/ | nucleo_sucursal_change | django.contrib.admin.options.change_view |
| admin/nucleo/sucursal/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/ejerciciofiscal/ | nucleo_ejerciciofiscal_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/ejerciciofiscal/add/ | nucleo_ejerciciofiscal_add | django.contrib.admin.options.add_view |
| admin/nucleo/ejerciciofiscal/<path:object_id>/history/ | nucleo_ejerciciofiscal_history | django.contrib.admin.options.history_view |
| admin/nucleo/ejerciciofiscal/<path:object_id>/delete/ | nucleo_ejerciciofiscal_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/ejerciciofiscal/<path:object_id>/change/ | nucleo_ejerciciofiscal_change | django.contrib.admin.options.change_view |
| admin/nucleo/ejerciciofiscal/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/periodocontable/ | nucleo_periodocontable_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/periodocontable/add/ | nucleo_periodocontable_add | django.contrib.admin.options.add_view |
| admin/nucleo/periodocontable/<path:object_id>/history/ | nucleo_periodocontable_history | django.contrib.admin.options.history_view |
| admin/nucleo/periodocontable/<path:object_id>/delete/ | nucleo_periodocontable_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/periodocontable/<path:object_id>/change/ | nucleo_periodocontable_change | django.contrib.admin.options.change_view |
| admin/nucleo/periodocontable/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/parametrosistema/ | nucleo_parametrosistema_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/parametrosistema/add/ | nucleo_parametrosistema_add | django.contrib.admin.options.add_view |
| admin/nucleo/parametrosistema/<path:object_id>/history/ | nucleo_parametrosistema_history | django.contrib.admin.options.history_view |
| admin/nucleo/parametrosistema/<path:object_id>/delete/ | nucleo_parametrosistema_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/parametrosistema/<path:object_id>/change/ | nucleo_parametrosistema_change | django.contrib.admin.options.change_view |
| admin/nucleo/parametrosistema/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/auditoria/ | nucleo_auditoria_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/auditoria/add/ | nucleo_auditoria_add | django.contrib.admin.options.add_view |
| admin/nucleo/auditoria/<path:object_id>/history/ | nucleo_auditoria_history | django.contrib.admin.options.history_view |
| admin/nucleo/auditoria/<path:object_id>/delete/ | nucleo_auditoria_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/auditoria/<path:object_id>/change/ | nucleo_auditoria_change | django.contrib.admin.options.change_view |
| admin/nucleo/auditoria/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/eventonegocio/ | nucleo_eventonegocio_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/eventonegocio/add/ | nucleo_eventonegocio_add | django.contrib.admin.options.add_view |
| admin/nucleo/eventonegocio/<path:object_id>/history/ | nucleo_eventonegocio_history | django.contrib.admin.options.history_view |
| admin/nucleo/eventonegocio/<path:object_id>/delete/ | nucleo_eventonegocio_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/eventonegocio/<path:object_id>/change/ | nucleo_eventonegocio_change | django.contrib.admin.options.change_view |
| admin/nucleo/eventonegocio/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/documentoadjunto/ | nucleo_documentoadjunto_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/documentoadjunto/add/ | nucleo_documentoadjunto_add | django.contrib.admin.options.add_view |
| admin/nucleo/documentoadjunto/<path:object_id>/history/ | nucleo_documentoadjunto_history | django.contrib.admin.options.history_view |
| admin/nucleo/documentoadjunto/<path:object_id>/delete/ | nucleo_documentoadjunto_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/documentoadjunto/<path:object_id>/change/ | nucleo_documentoadjunto_change | django.contrib.admin.options.change_view |
| admin/nucleo/documentoadjunto/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/rolfuncional/ | nucleo_rolfuncional_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/rolfuncional/add/ | nucleo_rolfuncional_add | django.contrib.admin.options.add_view |
| admin/nucleo/rolfuncional/<path:object_id>/history/ | nucleo_rolfuncional_history | django.contrib.admin.options.history_view |
| admin/nucleo/rolfuncional/<path:object_id>/delete/ | nucleo_rolfuncional_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/rolfuncional/<path:object_id>/change/ | nucleo_rolfuncional_change | django.contrib.admin.options.change_view |
| admin/nucleo/rolfuncional/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/permisofuncional/ | nucleo_permisofuncional_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/permisofuncional/add/ | nucleo_permisofuncional_add | django.contrib.admin.options.add_view |
| admin/nucleo/permisofuncional/<path:object_id>/history/ | nucleo_permisofuncional_history | django.contrib.admin.options.history_view |
| admin/nucleo/permisofuncional/<path:object_id>/delete/ | nucleo_permisofuncional_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/permisofuncional/<path:object_id>/change/ | nucleo_permisofuncional_change | django.contrib.admin.options.change_view |
| admin/nucleo/permisofuncional/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/rolpermiso/ | nucleo_rolpermiso_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/rolpermiso/add/ | nucleo_rolpermiso_add | django.contrib.admin.options.add_view |
| admin/nucleo/rolpermiso/<path:object_id>/history/ | nucleo_rolpermiso_history | django.contrib.admin.options.history_view |
| admin/nucleo/rolpermiso/<path:object_id>/delete/ | nucleo_rolpermiso_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/rolpermiso/<path:object_id>/change/ | nucleo_rolpermiso_change | django.contrib.admin.options.change_view |
| admin/nucleo/rolpermiso/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/usuariorolempresa/ | nucleo_usuariorolempresa_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/usuariorolempresa/add/ | nucleo_usuariorolempresa_add | django.contrib.admin.options.add_view |
| admin/nucleo/usuariorolempresa/<path:object_id>/history/ | nucleo_usuariorolempresa_history | django.contrib.admin.options.history_view |
| admin/nucleo/usuariorolempresa/<path:object_id>/delete/ | nucleo_usuariorolempresa_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/usuariorolempresa/<path:object_id>/change/ | nucleo_usuariorolempresa_change | django.contrib.admin.options.change_view |
| admin/nucleo/usuariorolempresa/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/usuarioempresa/ | nucleo_usuarioempresa_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/usuarioempresa/add/ | nucleo_usuarioempresa_add | django.contrib.admin.options.add_view |
| admin/nucleo/usuarioempresa/<path:object_id>/history/ | nucleo_usuarioempresa_history | django.contrib.admin.options.history_view |
| admin/nucleo/usuarioempresa/<path:object_id>/delete/ | nucleo_usuarioempresa_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/usuarioempresa/<path:object_id>/change/ | nucleo_usuarioempresa_change | django.contrib.admin.options.change_view |
| admin/nucleo/usuarioempresa/<path:object_id>/ | — | django.views.generic.base.view |
| admin/nucleo/usuariosucursal/ | nucleo_usuariosucursal_changelist | django.contrib.admin.options.changelist_view |
| admin/nucleo/usuariosucursal/add/ | nucleo_usuariosucursal_add | django.contrib.admin.options.add_view |
| admin/nucleo/usuariosucursal/<path:object_id>/history/ | nucleo_usuariosucursal_history | django.contrib.admin.options.history_view |
| admin/nucleo/usuariosucursal/<path:object_id>/delete/ | nucleo_usuariosucursal_delete | django.contrib.admin.options.delete_view |
| admin/nucleo/usuariosucursal/<path:object_id>/change/ | nucleo_usuariosucursal_change | django.contrib.admin.options.change_view |
| admin/nucleo/usuariosucursal/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/tipodocumento/ | terceros_tipodocumento_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/tipodocumento/add/ | terceros_tipodocumento_add | django.contrib.admin.options.add_view |
| admin/terceros/tipodocumento/<path:object_id>/history/ | terceros_tipodocumento_history | django.contrib.admin.options.history_view |
| admin/terceros/tipodocumento/<path:object_id>/delete/ | terceros_tipodocumento_delete | django.contrib.admin.options.delete_view |
| admin/terceros/tipodocumento/<path:object_id>/change/ | terceros_tipodocumento_change | django.contrib.admin.options.change_view |
| admin/terceros/tipodocumento/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/condicioniva/ | terceros_condicioniva_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/condicioniva/add/ | terceros_condicioniva_add | django.contrib.admin.options.add_view |
| admin/terceros/condicioniva/<path:object_id>/history/ | terceros_condicioniva_history | django.contrib.admin.options.history_view |
| admin/terceros/condicioniva/<path:object_id>/delete/ | terceros_condicioniva_delete | django.contrib.admin.options.delete_view |
| admin/terceros/condicioniva/<path:object_id>/change/ | terceros_condicioniva_change | django.contrib.admin.options.change_view |
| admin/terceros/condicioniva/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/tercero/ | terceros_tercero_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/tercero/add/ | terceros_tercero_add | django.contrib.admin.options.add_view |
| admin/terceros/tercero/<path:object_id>/history/ | terceros_tercero_history | django.contrib.admin.options.history_view |
| admin/terceros/tercero/<path:object_id>/delete/ | terceros_tercero_delete | django.contrib.admin.options.delete_view |
| admin/terceros/tercero/<path:object_id>/change/ | terceros_tercero_change | django.contrib.admin.options.change_view |
| admin/terceros/tercero/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/tercerorol/ | terceros_tercerorol_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/tercerorol/add/ | terceros_tercerorol_add | django.contrib.admin.options.add_view |
| admin/terceros/tercerorol/<path:object_id>/history/ | terceros_tercerorol_history | django.contrib.admin.options.history_view |
| admin/terceros/tercerorol/<path:object_id>/delete/ | terceros_tercerorol_delete | django.contrib.admin.options.delete_view |
| admin/terceros/tercerorol/<path:object_id>/change/ | terceros_tercerorol_change | django.contrib.admin.options.change_view |
| admin/terceros/tercerorol/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/domiciliotercero/ | terceros_domiciliotercero_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/domiciliotercero/add/ | terceros_domiciliotercero_add | django.contrib.admin.options.add_view |
| admin/terceros/domiciliotercero/<path:object_id>/history/ | terceros_domiciliotercero_history | django.contrib.admin.options.history_view |
| admin/terceros/domiciliotercero/<path:object_id>/delete/ | terceros_domiciliotercero_delete | django.contrib.admin.options.delete_view |
| admin/terceros/domiciliotercero/<path:object_id>/change/ | terceros_domiciliotercero_change | django.contrib.admin.options.change_view |
| admin/terceros/domiciliotercero/<path:object_id>/ | — | django.views.generic.base.view |
| admin/terceros/contactotercero/ | terceros_contactotercero_changelist | django.contrib.admin.options.changelist_view |
| admin/terceros/contactotercero/add/ | terceros_contactotercero_add | django.contrib.admin.options.add_view |
| admin/terceros/contactotercero/<path:object_id>/history/ | terceros_contactotercero_history | django.contrib.admin.options.history_view |
| admin/terceros/contactotercero/<path:object_id>/delete/ | terceros_contactotercero_delete | django.contrib.admin.options.delete_view |
| admin/terceros/contactotercero/<path:object_id>/change/ | terceros_contactotercero_change | django.contrib.admin.options.change_view |
| admin/terceros/contactotercero/<path:object_id>/ | — | django.views.generic.base.view |
| admin/items/categoriaitem/ | items_categoriaitem_changelist | django.contrib.admin.options.changelist_view |
| admin/items/categoriaitem/add/ | items_categoriaitem_add | django.contrib.admin.options.add_view |
| admin/items/categoriaitem/<path:object_id>/history/ | items_categoriaitem_history | django.contrib.admin.options.history_view |
| admin/items/categoriaitem/<path:object_id>/delete/ | items_categoriaitem_delete | django.contrib.admin.options.delete_view |
| admin/items/categoriaitem/<path:object_id>/change/ | items_categoriaitem_change | django.contrib.admin.options.change_view |
| admin/items/categoriaitem/<path:object_id>/ | — | django.views.generic.base.view |
| admin/items/marca/ | items_marca_changelist | django.contrib.admin.options.changelist_view |
| admin/items/marca/add/ | items_marca_add | django.contrib.admin.options.add_view |
| admin/items/marca/<path:object_id>/history/ | items_marca_history | django.contrib.admin.options.history_view |
| admin/items/marca/<path:object_id>/delete/ | items_marca_delete | django.contrib.admin.options.delete_view |
| admin/items/marca/<path:object_id>/change/ | items_marca_change | django.contrib.admin.options.change_view |
| admin/items/marca/<path:object_id>/ | — | django.views.generic.base.view |
| admin/items/unidadmedida/ | items_unidadmedida_changelist | django.contrib.admin.options.changelist_view |
| admin/items/unidadmedida/add/ | items_unidadmedida_add | django.contrib.admin.options.add_view |
| admin/items/unidadmedida/<path:object_id>/history/ | items_unidadmedida_history | django.contrib.admin.options.history_view |
| admin/items/unidadmedida/<path:object_id>/delete/ | items_unidadmedida_delete | django.contrib.admin.options.delete_view |
| admin/items/unidadmedida/<path:object_id>/change/ | items_unidadmedida_change | django.contrib.admin.options.change_view |
| admin/items/unidadmedida/<path:object_id>/ | — | django.views.generic.base.view |
| admin/items/alicuotaiva/ | items_alicuotaiva_changelist | django.contrib.admin.options.changelist_view |
| admin/items/alicuotaiva/add/ | items_alicuotaiva_add | django.contrib.admin.options.add_view |
| admin/items/alicuotaiva/<path:object_id>/history/ | items_alicuotaiva_history | django.contrib.admin.options.history_view |
| admin/items/alicuotaiva/<path:object_id>/delete/ | items_alicuotaiva_delete | django.contrib.admin.options.delete_view |
| admin/items/alicuotaiva/<path:object_id>/change/ | items_alicuotaiva_change | django.contrib.admin.options.change_view |
| admin/items/alicuotaiva/<path:object_id>/ | — | django.views.generic.base.view |
| admin/items/item/ | items_item_changelist | django.contrib.admin.options.changelist_view |
| admin/items/item/add/ | items_item_add | django.contrib.admin.options.add_view |
| admin/items/item/<path:object_id>/history/ | items_item_history | django.contrib.admin.options.history_view |
| admin/items/item/<path:object_id>/delete/ | items_item_delete | django.contrib.admin.options.delete_view |
| admin/items/item/<path:object_id>/change/ | items_item_change | django.contrib.admin.options.change_view |
| admin/items/item/<path:object_id>/ | — | django.views.generic.base.view |
| admin/contabilidad/cuentacontable/ | contabilidad_cuentacontable_changelist | django.contrib.admin.options.changelist_view |
| admin/contabilidad/cuentacontable/add/ | contabilidad_cuentacontable_add | django.contrib.admin.options.add_view |
| admin/contabilidad/cuentacontable/<path:object_id>/history/ | contabilidad_cuentacontable_history | django.contrib.admin.options.history_view |
| admin/contabilidad/cuentacontable/<path:object_id>/delete/ | contabilidad_cuentacontable_delete | django.contrib.admin.options.delete_view |
| admin/contabilidad/cuentacontable/<path:object_id>/change/ | contabilidad_cuentacontable_change | django.contrib.admin.options.change_view |
| admin/contabilidad/cuentacontable/<path:object_id>/ | — | django.views.generic.base.view |
| admin/auth/group/ | auth_group_changelist | django.contrib.admin.options.changelist_view |
| admin/auth/group/add/ | auth_group_add | django.contrib.admin.options.add_view |
| admin/auth/group/<path:object_id>/history/ | auth_group_history | django.contrib.admin.options.history_view |
| admin/auth/group/<path:object_id>/delete/ | auth_group_delete | django.contrib.admin.options.delete_view |
| admin/auth/group/<path:object_id>/change/ | auth_group_change | django.contrib.admin.options.change_view |
| admin/auth/group/<path:object_id>/ | — | django.views.generic.base.view |
| admin/auth/user/<id>/password/ | auth_user_password_change | django.contrib.auth.admin.user_change_password |
| admin/auth/user/ | auth_user_changelist | django.contrib.admin.options.changelist_view |
| admin/auth/user/add/ | auth_user_add | django.contrib.auth.admin.add_view |
| admin/auth/user/<path:object_id>/history/ | auth_user_history | django.contrib.admin.options.history_view |
| admin/auth/user/<path:object_id>/delete/ | auth_user_delete | django.contrib.admin.options.delete_view |
| admin/auth/user/<path:object_id>/change/ | auth_user_change | django.contrib.admin.options.change_view |
| admin/auth/user/<path:object_id>/ | — | django.views.generic.base.view |
| admin/^(?P<app_label>nucleo\|terceros\|items\|contabilidad\|auth)/$ | app_list | django.contrib.admin.sites.app_index |
| admin/(?P<url>.*)$ | — | django.contrib.admin.sites.catch_all_view |
| nucleo/configuracion/ | configuracion_empresa | apps.nucleo.views.configuracion_empresa |
| nucleo/configuracion/datos-contribuyente/ | datos_contribuyente | apps.nucleo.views.datos_contribuyente |
| nucleo/configuracion/sucursales/ | sucursales | apps.nucleo.views.sucursales |
| nucleo/configuracion/sucursales/nueva/ | sucursal_crear | apps.nucleo.views.sucursal_crear |
| nucleo/configuracion/sucursales/<int:sucursal_id>/editar/ | sucursal_editar | apps.nucleo.views.sucursal_editar |
| nucleo/configuracion/puntos-venta/ | puntos_venta | apps.nucleo.views.puntos_venta |
| nucleo/configuracion/puntos-venta/nuevo/ | punto_venta_crear | apps.nucleo.views.punto_venta_crear |
| nucleo/configuracion/puntos-venta/<int:punto_venta_id>/editar/ | punto_venta_editar | apps.nucleo.views.punto_venta_editar |
| nucleo/configuracion/puntos-venta/<int:punto_venta_id>/inactivar/ | punto_venta_inactivar | apps.nucleo.views.punto_venta_inactivar |
| nucleo/configuracion/actividades/ | actividades_empresa | apps.nucleo.views.actividades_empresa |
| nucleo/configuracion/actividades/nueva/ | actividad_empresa_crear | apps.nucleo.views.actividad_empresa_crear |
| nucleo/configuracion/actividades/<int:empresa_actividad_id>/editar/ | actividad_empresa_editar | apps.nucleo.views.actividad_empresa_editar |
| nucleo/configuracion/actividades/<int:empresa_actividad_id>/inactivar/ | actividad_empresa_inactivar | apps.nucleo.views.actividad_empresa_inactivar |
| nucleo/configuracion/actividades/catalogo/buscar/ | catalogo_actividades_buscar | apps.nucleo.views.catalogo_actividades_buscar |
| nucleo/configuracion/ingresos-brutos/ | ingresos_brutos | apps.nucleo.views.ingresos_brutos |
| nucleo/configuracion/ingresos-brutos/nueva/ | configuracion_iibb_crear | apps.nucleo.views.configuracion_iibb_crear |
| nucleo/configuracion/ingresos-brutos/<int:configuracion_id>/editar/ | configuracion_iibb_editar | apps.nucleo.views.configuracion_iibb_editar |
| nucleo/configuracion/ingresos-brutos/<int:configuracion_id>/inactivar/ | configuracion_iibb_inactivar | apps.nucleo.views.configuracion_iibb_inactivar |
| nucleo/configuracion/ingresos-brutos/<int:configuracion_id>/jurisdicciones/nueva/ | jurisdiccion_iibb_crear | apps.nucleo.views.jurisdiccion_iibb_crear |
| nucleo/configuracion/ingresos-brutos/jurisdicciones/<int:relacion_id>/editar/ | jurisdiccion_iibb_editar | apps.nucleo.views.jurisdiccion_iibb_editar |
| nucleo/configuracion/ingresos-brutos/jurisdicciones/<int:relacion_id>/inactivar/ | jurisdiccion_iibb_inactivar | apps.nucleo.views.jurisdiccion_iibb_inactivar |
| nucleo/configuracion/parametros/ | parametros_operativos | apps.nucleo.views.parametros_operativos |
| nucleo/configuracion/parametros/inicializar/ | inicializar_configuracion_empresa | apps.nucleo.views.inicializar_configuracion_empresa |
| terceros/ | tercero_list | apps.terceros.views.tercero_list |
| terceros/nuevo/ | tercero_create | apps.terceros.views.tercero_create |
| terceros/<int:tercero_id>/ | tercero_detail | apps.terceros.views.tercero_detail |
| terceros/<int:tercero_id>/editar/ | tercero_edit | apps.terceros.views.tercero_edit |
| terceros/<int:tercero_id>/inactivar/ | tercero_deactivate | apps.terceros.views.tercero_deactivate |
| terceros/<int:tercero_id>/domicilios/nuevo/ | domicilio_create | apps.terceros.views.domicilio_create |
| terceros/domicilios/<int:domicilio_id>/editar/ | domicilio_edit | apps.terceros.views.domicilio_edit |
| terceros/domicilios/<int:domicilio_id>/inactivar/ | domicilio_deactivate | apps.terceros.views.domicilio_deactivate |
| terceros/<int:tercero_id>/contactos/nuevo/ | contacto_create | apps.terceros.views.contacto_create |
| terceros/contactos/<int:contacto_id>/editar/ | contacto_edit | apps.terceros.views.contacto_edit |
| terceros/contactos/<int:contacto_id>/inactivar/ | contacto_deactivate | apps.terceros.views.contacto_deactivate |
| items/ | item_list | apps.items.views.item_list |
| items/nuevo/ | item_create | apps.items.views.item_create |
| items/categorias/ | categoria_list | apps.items.views.categoria_list |
| items/categorias/nueva/ | categoria_create | apps.items.views.categoria_create |
| items/categorias/<int:categoria_id>/editar/ | categoria_edit | apps.items.views.categoria_edit |
| items/categorias/<int:categoria_id>/inactivar/ | categoria_deactivate | apps.items.views.categoria_deactivate |
| items/marcas/ | marca_list | apps.items.views.marca_list |
| items/marcas/nueva/ | marca_create | apps.items.views.marca_create |
| items/marcas/<int:marca_id>/editar/ | marca_edit | apps.items.views.marca_edit |
| items/marcas/<int:marca_id>/inactivar/ | marca_deactivate | apps.items.views.marca_deactivate |
| items/<int:item_id>/ | item_detail | apps.items.views.item_detail |
| items/<int:item_id>/editar/ | item_edit | apps.items.views.item_edit |
| items/<int:item_id>/inactivar/ | item_deactivate | apps.items.views.item_deactivate |
| contabilidad/plan-de-cuentas/ | plan_cuentas | apps.contabilidad.views.plan_cuentas |
| contabilidad/plan-de-cuentas/nueva/ | crear_cuenta | apps.contabilidad.views.crear_cuenta |
| ingresar/ | login | apps.core.views.iniciar_sesion |
| salir/ | logout | apps.core.views.cerrar_sesion |
| / | home | apps.core.views.home |
| empresa/seleccionar/ | seleccionar_empresa | apps.core.views.seleccionar_empresa |
| sucursal/seleccionar/ | seleccionar_sucursal | apps.core.views.seleccionar_sucursal |

## Roles y permisos

Definición inicial vigente:

```text
Roles: 5
Permisos: 40
Relaciones rol-permiso: 110
```

| Rol | Permisos en la matriz inicial |
|---|---|
| ADMIN | 40 |
| CONTADOR | 25 |
| OPERADOR | 16 |
| AUDITOR | 16 |
| SOLO_LECTURA | 13 |

Permisos encontrados en el código operativo: `24`.

Permisos definidos pero no encontrados como consumo operativo directo: `16`. Se consideran reservados o pendientes de integración, no funcionalidades implementadas.

## Pruebas

Suite completa ejecutada por esta tarea: `425` pruebas.

| Aplicación | Pruebas ejecutadas por app | Métodos detectados estáticamente | Archivos de prueba |
|---|---|---|---|
| apps.contabilidad | 40 | 40 | 6 |
| apps.core | 45 | 45 | 2 |
| apps.items | 67 | 67 | 6 |
| apps.nucleo | 221 | 221 | 11 |
| apps.terceros | 52 | 52 | 4 |

La cuenta estática se registra como control auxiliar. La cifra contractual es la obtenida por el runner de Django.

## Documentación

| Documento | Título | Categoría | Estado |
|---|---|---|---|
| 00_decision_implementacion.md | DOCUMENTO 00 - DECISION DE IMPLEMENTACION DEL ERP | Arquitectura | Vigente |
| 01_nucleo_erp.md | DOCUMENTO 01 - NUCLEO ERP | Documento rector acumulado | Vigente; consultar junto con el estado integral |
| 02_politica_operativa_logs.md | DOCUMENTO 02 - POLITICA OPERATIVA DE LOGS | Política operativa | Normativo vigente |
| 03_contrato_operativo.md | DOCUMENTO 03 - CONTRATO OPERATIVO DEL PROYECTO ERP | Contrato operativo | Normativo prioritario |
| 04_roles_permisos.md | Estrategia de roles y permisos propios | Seguridad, roles y permisos | Vigente; contiene evolución histórica y corte actual |
| 05_usuario_custom.md | Evaluacion de usuario custom | Decisión técnica | Vigente |
| 06_empresa_activa_sesion.md | Empresa activa para la sesión | Implementación histórica | Implementado; referencia histórica |
| 07_sucursal_activa_sesion.md | Sucursal activa para la sesión | Implementación histórica | Implementado; referencia histórica |
| 08_autenticacion_erp.md | Autenticación propia del ERP | Implementación histórica | Implementado; referencia histórica |
| 09_mecanica_trabajo_tareas_txt.md | Mecánica de trabajo mediante tareas ejecutables TXT | Mecánica de trabajo | Normativo vigente |
| 10_estado_actual_y_hoja_ruta.md | Estado actual y hoja de ruta del ERP | Estado y hoja de ruta | Histórico acumulado; el bloque inicial marcado es el estado vigente |
| 11_parametros_empresa.md | Parámetros de empresa: inicialización y configuración amigable | Documento de módulo | Implementado |
| 12_contexto_operativo.md | Contexto operativo obligatorio | Documento de módulo | Implementado |
| 13_configuracion_empresa_fiscal.md | Configuración fiscal y registral de empresa | Documento de módulo | Implementado parcialmente según detalle |
| 13_plan_de_cuentas.md | Diseño funcional y técnico mínimo del Plan de cuentas | Documento de módulo | Implementado parcialmente según detalle |
| 14_sucursales_domicilios.md | Sucursales y domicilios estructurados | Documento de módulo | Implementado |
| 15_catalogo_actividades_arca.md | Catalogo oficial de actividades ARCA CLAE | Documento de catálogo | Implementado |
| 16_actividades_economicas_empresa.md | Actividades económicas por empresa | Documento de módulo | Implementado |
| 17_lecciones_aprendidas_y_estandar_implementacion.md | Lecciones aprendidas y estándar de implementación del ERP | Estándar y lecciones | Normativo vigente con historial |
| 18_ingresos_brutos_jurisdicciones.md | Ingresos Brutos y jurisdicciones por empresa | Documento de módulo | Implementado |
| 19_puntos_venta.md | Puntos de venta por sucursal | Documento de módulo | Implementado |
| 20_maestro_terceros.md | Maestro base de terceros | Documento rector de terceros | Primera versión funcional implementada |
| 21_maestro_productos_servicios.md | Maestro de productos y servicios | Documento rector de ítems | Primera versión funcional implementada |
| README.md | Índice de documentación del ERP | Referencia documental | Revisar según su contenido |
| 22_estado_real_integral_erp.md | Estado real integral del ERP | Estado integral canónico | Vigente |
| 23_riesgos_y_deuda_tecnica.md | Riesgos y deuda técnica | Registro de riesgos | Vigente |

Referencias documentales locales inexistentes detectadas: `0`.

## Riesgos y deuda técnica

Se registran `5` hallazgos en `docs/23_riesgos_y_deuda_tecnica.md`. Esta tarea no los corrige porque su alcance es exclusivamente documental.

## Próxima secuencia

1. resolver en tareas independientes los hallazgos que se clasifiquen como bloqueantes;
2. diseñar e implementar la relación entre ítems y proveedores;
3. abordar identificadores externos;
4. definir presentaciones y conversiones cuando exista una política de cantidades y precisión.

La numeración posterior se ajustará según los hallazgos efectivamente priorizados.
