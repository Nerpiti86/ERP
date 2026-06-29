# Riesgos y deuda técnica del ERP

Fecha del relevamiento vigente: 2026-06-29.

Base auditada antes del commit documental:
`2e6094a4e6dd5b2cf4ee0710febbcca2a9e65e2e`.

Este registro documenta hallazgos. No autoriza a corregirlos dentro de una
tarea documental ni convierte cada observación en un defecto bloqueante.

| ID | Severidad | Módulo | Estado y evidencia | Impacto | Recomendación |
|---|---|---|---|---|---|
| R-001 | Media | `apps.terceros` | **RESUELTO — TAREA 0017.** Se eliminó la barra invertida aislada. | El riesgo sintáctico dejó de existir. | Conservar como antecedente. |
| R-002 | Baja | Seguridad funcional | Existen permisos reservados para dominios todavía no implementados. | Puede confundirse permiso con funcionalidad. | Mantener explícita la distinción. |
| R-003 | Media | Calidad | No se detectaron workflows de GitHub Actions en el corte anterior. | La validación depende de ejecución local. | Evaluar CI sin reemplazar validaciones locales. |
| R-004 | Baja | Documentación | **RESUELTO EN EL CORTE TAREA 0023.** Los documentos canónicos se sincronizaron con 35 modelos y 460 pruebas. | Se reduce el riesgo de leer cifras viejas como vigentes. | Actualizar documentos rectores junto con cada dominio. |
| R-005 | Baja | Pruebas | La suite no calcula cobertura de líneas o ramas. | Una suite verde no cuantifica zonas sin cobertura. | Definir una política solo si aporta valor operativo. |

## Regla de tratamiento

Cada corrección debe ejecutarse como una tarea independiente, con alcance
cerrado, pruebas específicas, suite completa y verificación remota. Los riesgos
resueltos se conservan con su estado para mantener trazabilidad.
