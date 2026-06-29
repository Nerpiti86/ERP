# Índice de documentación del ERP

Estado del índice: 2026-06-29.

## Fuente documental vigente

La fotografía canónica del estado implementado se encuentra en:

```text
docs/22_estado_real_integral_erp.md
```

Los riesgos y deudas se registran en:

```text
docs/23_riesgos_y_deuda_tecnica.md
```

## Inventario

| Documento | Categoría | Estado |
|---|---|---|
| `00_decision_implementacion.md` | Arquitectura | Vigente |
| `01_nucleo_erp.md` | Documento rector acumulado | Vigente; bloque inicial sincronizado |
| `02_politica_operativa_logs.md` | Política operativa | Normativo vigente |
| `03_contrato_operativo.md` | Contrato operativo | Normativo prioritario |
| `04_roles_permisos.md` | Seguridad funcional | Vigente; matriz inicial sincronizada |
| `05_usuario_custom.md` | Decisión técnica | Vigente |
| `06_empresa_activa_sesion.md` | Implementación histórica | Implementado; referencia histórica |
| `07_sucursal_activa_sesion.md` | Implementación histórica | Implementado; referencia histórica |
| `08_autenticacion_erp.md` | Implementación histórica | Implementado; referencia histórica |
| `09_mecanica_trabajo_tareas_txt.md` | Mecánica de trabajo | Normativo vigente |
| `10_estado_actual_y_hoja_ruta.md` | Estado y evolución | Bloque inicial vigente; resto histórico |
| `11_parametros_empresa.md` | Documento de módulo | Implementado |
| `12_contexto_operativo.md` | Documento de módulo | Implementado |
| `13_configuracion_empresa_fiscal.md` | Documento de módulo | Implementado parcialmente según detalle |
| `13_plan_de_cuentas.md` | Documento de módulo | Maestro mínimo implementado; operación pendiente |
| `14_sucursales_domicilios.md` | Documento de módulo | Implementado |
| `15_catalogo_actividades_arca.md` | Documento de catálogo | Implementado |
| `16_actividades_economicas_empresa.md` | Documento de módulo | Implementado |
| `17_lecciones_aprendidas_y_estandar_implementacion.md` | Estándar y lecciones | Normativo vigente con historial |
| `18_ingresos_brutos_jurisdicciones.md` | Documento de módulo | Implementado |
| `19_puntos_venta.md` | Documento de módulo | Implementado |
| `20_maestro_terceros.md` | Documento rector de terceros | Implementado con grupos por rol |
| `21_maestro_productos_servicios.md` | Documento rector de ítems | Primera versión funcional implementada |
| `22_estado_real_integral_erp.md` | Estado integral canónico | Vigente al corte 2026-06-29 |
| `23_riesgos_y_deuda_tecnica.md` | Registro de riesgos | Vigente |
| `24_relacion_items_proveedores.md` | Diseño de relación comercial | Diseño aprobado; implementación pendiente |
| `25_doble_entrada_gestion_contabilidad.md` | Arquitectura de ejecución | Implementado |

`docs/24_relacion_items_proveedores.md` es un contrato de diseño. Su presencia
no implica que el modelo o la interfaz estén implementados.

## Jerarquía documental

En caso de contradicción:

1. `docs/03_contrato_operativo.md`;
2. documento normativo específico;
3. código, migraciones y pruebas de `main`;
4. `docs/22_estado_real_integral_erp.md`;
5. documento rector del módulo;
6. `docs/01_nucleo_erp.md`;
7. `README.md`;
8. cortes y resúmenes históricos.

## Estados

- **Normativo vigente:** establece reglas obligatorias.
- **Vigente:** describe una decisión o implementación actual.
- **Histórico:** conserva el contexto de un corte anterior.
- **Implementado parcialmente:** existe una parte y el resto está pendiente.
- **Diseño futuro:** no debe presentarse como funcionalidad disponible.

## Regla de actualización

Los documentos rectores deben actualizarse en la misma tarea que modifica su
dominio. `docs/22_estado_real_integral_erp.md` se actualiza en cortes integrales
verificados y no convierte propuestas futuras en decisiones aprobadas.
