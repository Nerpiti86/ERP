# Estado real integral del ERP

> Fotografía canónica generada por la TAREA 0023 a partir del repositorio local,
> la base migrada y las pruebas. El historial previo permanece disponible en
> Git y en los documentos acumulativos.

## 1. Identificación del corte

```text
Fecha: 2026-06-29
Repositorio: Nerpiti86/ERP
Rama: main
Base auditada antes del commit documental: 2e6094a4e6dd5b2cf4ee0710febbcca2a9e65e2e
Python: 3.13.9
Django: 5.2.15
Base de datos: django.db.backends.postgresql
Apps propias: 5
Modelos propios: 35
Tablas propias detectadas: 35
Migraciones propias aplicadas: 21
Roles funcionales activos: 5
Permisos funcionales activos: 40
Relaciones rol-permiso activas: 110
Suite completa: 460 pruebas
Migraciones pendientes: 0
```

## 2. Criterio de verdad

La fuente primaria es el código, las migraciones, la base local y las pruebas
de `main`. Los documentos históricos explican decisiones, pero sus cifras y
próximos pasos no reemplazan este corte.

## 3. Arquitectura efectiva

- monolito modular Django;
- PostgreSQL como base principal;
- Django Templates y Bootstrap;
- autenticación sobre Django Auth;
- roles y permisos funcionales por empresa;
- contexto activo de empresa y sucursal;
- servicios transaccionales y auditoría;
- rama única `main`;
- tareas ejecutables `.txt` con validación, commit y push condicionados.

## 4. Superficies de ejecución

| Superficie | Settings | URLconf | Puerto habitual | Rutas detectadas |
|---|---|---|---:|---:|
| Integrado | `config.settings` | `config.urls` | 8000 | 289 |
| Gestión | `config.settings_gestion` | `config.urls_gestion` | 8001 | 288 |
| Contabilidad | `config.settings_contabilidad` | `config.urls_contabilidad` | 8002 | 258 |

Gestión publica núcleo, terceros e ítems, pero no el dominio contable.
Contabilidad publica núcleo y Plan de cuentas, pero no terceros ni ítems.
Las tres superficies comparten usuarios, empresas, modelos, migraciones y base.

## 5. Aplicaciones propias

| Aplicación | Modelos | Última migración aplicada | Pruebas de app | Plantillas |
|---|---:|---|---:|---:|
| `apps.contabilidad` | 1 | `0001_initial` | 40 | 2 |
| `apps.core` | 0 | `Sin migraciones` | 60 | 6 |
| `apps.items` | 5 | `0002_catalogos_iniciales` | 67 | 5 |
| `apps.nucleo` | 22 | `0015_puntos_venta` | 221 | 12 |
| `apps.terceros` | 7 | `0003_grupos_terceros` | 72 | 7 |

## 6. Inventario de modelos

| Modelo | Tabla | Campos directos | Restricciones | Índices |
|---|---|---:|---:|---:|
| `contabilidad.CuentaContable` | `contabilidad_cuentacontable` | 11 | 4 | 0 |
| `items.AlicuotaIVA` | `items_alicuotaiva` | 9 | 0 | 0 |
| `items.CategoriaItem` | `items_categoriaitem` | 8 | 1 | 1 |
| `items.Item` | `items_item` | 18 | 4 | 2 |
| `items.Marca` | `items_marca` | 7 | 1 | 1 |
| `items.UnidadMedida` | `items_unidadmedida` | 9 | 0 | 0 |
| `nucleo.ActividadEconomica` | `nucleo_actividadeconomica` | 9 | 1 | 1 |
| `nucleo.Auditoria` | `nucleo_auditoria` | 11 | 0 | 3 |
| `nucleo.ConfiguracionIIBBEmpresa` | `nucleo_configuracionesiibbempresa` | 11 | 3 | 1 |
| `nucleo.DocumentoAdjunto` | `nucleo_documentoadjunto` | 13 | 0 | 3 |
| `nucleo.EjercicioFiscal` | `nucleo_ejerciciofiscal` | 10 | 2 | 0 |
| `nucleo.Empresa` | `nucleo_empresa` | 8 | 0 | 0 |
| `nucleo.EmpresaActividad` | `nucleo_empresaactividad` | 15 | 4 | 1 |
| `nucleo.EmpresaJurisdiccionIIBB` | `nucleo_empresajurisdicioniibb` | 15 | 5 | 1 |
| `nucleo.EventoNegocio` | `nucleo_eventonegocio` | 11 | 0 | 3 |
| `nucleo.ImportacionCatalogoActividad` | `nucleo_importacioncatalogoactividad` | 11 | 0 | 0 |
| `nucleo.JurisdiccionFiscal` | `nucleo_jurisdiccionfiscal` | 8 | 0 | 1 |
| `nucleo.ParametroSistema` | `nucleo_parametrosistema` | 10 | 3 | 0 |
| `nucleo.PerfilFiscalEmpresa` | `nucleo_perfilfiscalempresa` | 11 | 1 | 0 |
| `nucleo.PeriodoContable` | `nucleo_periodocontable` | 10 | 2 | 0 |
| `nucleo.PermisoFuncional` | `nucleo_permisofuncional` | 8 | 0 | 0 |
| `nucleo.PuntoVenta` | `nucleo_puntoventa` | 17 | 6 | 2 |
| `nucleo.RolFuncional` | `nucleo_rolfuncional` | 8 | 0 | 0 |
| `nucleo.RolPermiso` | `nucleo_rolpermiso` | 6 | 1 | 0 |
| `nucleo.Sucursal` | `nucleo_sucursal` | 29 | 6 | 0 |
| `nucleo.UsuarioEmpresa` | `nucleo_usuarioempresa` | 6 | 1 | 0 |
| `nucleo.UsuarioRolEmpresa` | `nucleo_usuariorolempresa` | 7 | 1 | 0 |
| `nucleo.UsuarioSucursal` | `nucleo_usuariosucursal` | 6 | 1 | 0 |
| `terceros.CondicionIVA` | `terceros_condicioniva` | 8 | 0 | 0 |
| `terceros.ContactoTercero` | `terceros_contactotercero` | 14 | 4 | 1 |
| `terceros.DomicilioTercero` | `terceros_domiciliotercero` | 23 | 4 | 1 |
| `terceros.GrupoTercero` | `terceros_grupotercero` | 9 | 2 | 1 |
| `terceros.Tercero` | `terceros_tercero` | 18 | 4 | 2 |
| `terceros.TerceroRol` | `terceros_tercerorol` | 9 | 3 | 0 |
| `terceros.TipoDocumento` | `terceros_tipodocumento` | 9 | 0 | 0 |

## 7. Migraciones

- `apps.contabilidad`: 1 aplicadas; última `0001_initial`.
- `apps.core`: 0 aplicadas; última `Sin migraciones`.
- `apps.items`: 2 aplicadas; última `0002_catalogos_iniciales`.
- `apps.nucleo`: 15 aplicadas; última `0015_puntos_venta`.
- `apps.terceros`: 3 aplicadas; última `0003_grupos_terceros`.

`makemigrations --check --dry-run` no detecta cambios y `migrate --plan` no
informa operaciones pendientes.

## 8. Seguridad funcional

```text
Roles activos: 5
Permisos activos: 40
Relaciones rol-permiso activas: 110
```

| Rol | Permisos activos |
|---|---:|
| ADMIN | 40 |
| AUDITOR | 16 |
| CONTADOR | 25 |
| OPERADOR | 16 |
| SOLO_LECTURA | 13 |

Los permisos reservados para módulos futuros no implican que esos módulos
estén implementados.

## 9. Estado funcional

### Implementado

- núcleo empresarial, accesos y contexto operativo;
- configuración fiscal y registral;
- sucursales y domicilios;
- catálogo ARCA-CLAE y actividades por empresa;
- Ingresos Brutos y jurisdicciones;
- puntos de venta;
- parámetros por empresa;
- seguridad funcional y auditoría;
- Plan de cuentas mínimo;
- maestro de terceros con grupos de clientes y proveedores;
- maestro de productos y servicios;
- listados y filtros unificados;
- doble entrada local Gestión/Contabilidad;
- housekeeping visual global de cards y badges.

### Implementado parcialmente

- Plan de cuentas: listado, filtros y alta; faltan edición funcional, baja lógica
  y carga inicial asistida;
- Django Admin: backoffice técnico, no sustituto de la interfaz funcional;
- permisos de dominios futuros: definidos como reserva, no como circuitos.

### No implementado como circuito completo

- ventas;
- compras;
- stock;
- tesorería;
- cuentas corrientes;
- asientos y procesos contables;
- impuestos transaccionales;
- reportes operativos.

## 10. Pruebas

| Aplicación | Pruebas verificadas |
|---|---:|
| `apps.contabilidad` | 40 |
| `apps.core` | 60 |
| `apps.items` | 67 |
| `apps.nucleo` | 221 |
| `apps.terceros` | 72 |

La cifra contractual de la suite completa es `460` y se valida con el
runner de Django después de generar esta documentación.

## 11. Documentación vigente

- contrato operativo: `docs/03_contrato_operativo.md`;
- índice y jerarquía: `docs/README.md`;
- estado integral: `docs/22_estado_real_integral_erp.md`;
- riesgos: `docs/23_riesgos_y_deuda_tecnica.md`;
- terceros: `docs/20_maestro_terceros.md`;
- ítems: `docs/21_maestro_productos_servicios.md`;
- doble entrada: `docs/25_doble_entrada_gestion_contabilidad.md`.

## 12. Riesgos y deuda

Los hallazgos vigentes se mantienen en
`docs/23_riesgos_y_deuda_tecnica.md`. La sincronización documental no corrige
automáticamente riesgos de código ni aprueba nuevas funcionalidades.

## 13. Decisión posterior al corte

No se aprueba una próxima funcionalidad dentro de esta tarea.

El issue #3 sobre `ItemProveedor` continúa abierto como propuesta de diseño.
Antes de crear modelos o migraciones debe existir un contrato funcional y
técnico aprobado en una tarea independiente.
