# Índice de documentación del ERP

Estado del índice: 26/06/2026.

## Fuente documental vigente

La fotografía canónica del sistema se encuentra en:

```text
docs/22_estado_real_integral_erp.md
```

Los riesgos y deudas detectados se registran en:

```text
docs/23_riesgos_y_deuda_tecnica.md
```

## Inventario

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

## Jerarquía documental

En caso de contradicción:

1. `docs/03_contrato_operativo.md`;
2. documento normativo específico;
3. `docs/22_estado_real_integral_erp.md` para el estado implementado;
4. documento rector del módulo;
5. `docs/01_nucleo_erp.md`;
6. `README.md`;
7. cortes y resúmenes históricos.

El código, las migraciones y las pruebas de `main` prevalecen sobre cualquier descripción documental desactualizada.

## Estados

- **Normativo vigente:** establece reglas obligatorias.
- **Vigente:** describe una decisión o implementación actual.
- **Histórico:** conserva el contexto de un corte anterior.
- **Implementado parcialmente:** una parte existe y el resto está expresamente pendiente.
- **Diseño futuro:** no debe presentarse como funcionalidad disponible.

## Regla de actualización

Los documentos rectores deben actualizarse en la misma tarea que modifica su dominio. `docs/22_estado_real_integral_erp.md` se regenera únicamente en cortes integrales y nunca reemplaza el historial de decisiones.
