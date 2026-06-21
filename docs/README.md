# Índice de documentación del ERP

Estado del índice: 20/06/2026.

## Documentos de arquitectura y operación

| Documento | Contenido | Estado |
|---|---|---|
| `00_decision_implementacion.md` | Arquitectura, stack y forma de despliegue inicial | Vigente |
| `01_nucleo_erp.md` | Modelo funcional y técnico acumulado del núcleo | Vigente; actualización continua |
| `02_politica_operativa_logs.md` | Política de logs y backups locales | Vigente |
| `03_contrato_operativo.md` | Contrato obligatorio de trabajo sobre el repositorio | Vigente |
| `04_roles_permisos.md` | Estrategia e implementación de roles y permisos | Vigente |
| `05_usuario_custom.md` | Decisión de mantener `auth.User` estándar | Vigente |
| `06_empresa_activa_sesion.md` | Empresa activa y accesos por sesión | Implementado |
| `07_sucursal_activa_sesion.md` | Sucursal activa dentro de la empresa activa | Implementado |
| `08_autenticacion_erp.md` | Login, logout y protección inicial de vistas | Implementado |
| `09_mecanica_trabajo_tareas_txt.md` | Mecánica acordada de tareas ejecutables `.txt` | Vigente |
| `10_estado_actual_y_hoja_ruta.md` | Foto del estado actual y próximos pasos | Vigente; actualización por cortes |
| `11_parametros_empresa.md` | Inicialización y edición amigable de parámetros por empresa | Implementado |
| `12_contexto_operativo.md` | Contrato obligatorio de empresa y sucursal para operaciones | Implementado |
| `13_configuracion_empresa_fiscal.md` | Identidad, domicilios, actividades e IIBB de empresa | Implementado hasta IIBB; agentes pendiente |
| `14_sucursales_domicilios.md` | Gestión funcional de establecimientos, domicilios estructurados y funciones | Implementado |
| `15_catalogo_actividades_arca.md` | Catálogo local sincronizado con el nomenclador oficial ARCA CLAE | Implementado |
| `16_actividades_economicas_empresa.md` | Actividades principales y secundarias por empresa | Implementado |
| `17_lecciones_aprendidas_y_estandar_implementacion.md` | Lecciones consolidadas y estándar obligatorio para tareas futuras | Vigente |
| `18_ingresos_brutos_jurisdicciones.md` | Configuración de IIBB, jurisdicción sede e historial por empresa | Implementado |

## Jerarquía documental

En caso de contradicción:

1. `docs/03_contrato_operativo.md`
2. documento específico del módulo o decisión
3. `docs/01_nucleo_erp.md`
4. `README.md`
5. resúmenes históricos de tareas

Los scripts `.txt` entregados para ejecutar una tarea son instrucciones operativas de esa ejecución. No reemplazan los documentos rectores versionados.

## Estados utilizados

### Cerrado y verificado

La tarea:

- pasó todas las validaciones
- generó commit
- fue pusheada
- terminó con sincronización `0 0`
- fue verificada contra GitHub

### Preparado, pendiente de ejecución

Existe un script de trabajo fuera del repositorio, pero todavía:

- no se ejecutó o no se recibió su log final
- no tiene commit validado
- no debe considerarse funcionalidad disponible

### En ejecución o continuación

La tarea dejó cambios locales y debe retomarse mediante una continuación explícita.

### Pendiente de diseño

Existe en la hoja de ruta, pero todavía no se preparó una implementación.

## Regla de actualización

Este índice y `10_estado_actual_y_hoja_ruta.md` deben actualizarse en cortes documentales, no necesariamente después de cada cambio pequeño.

Los documentos específicos sí deben actualizarse dentro de la misma tarea que implementa su funcionalidad.
