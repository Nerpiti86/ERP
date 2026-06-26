# Riesgos y deuda técnica del ERP

Fecha del relevamiento: 26/06/2026.

Base auditada: `0f9712ff85cb38deb2a5442bcbed5b5598f8b959`.

Este registro documenta hallazgos. No autoriza a corregirlos dentro de una tarea documental ni convierte automáticamente cada observación en un defecto bloqueante.

| ID | Severidad | Módulo | Evidencia | Impacto | Recomendación |
|---|---|---|---|---|---|
| R-001 | Media | apps.terceros | El archivo comenzaba con una barra invertida aislada antes de `import re`. | La construcción sintáctica era frágil y podía afectar herramientas de análisis o futuras ediciones. | **RESUELTO — TAREA 0017:** se eliminó exclusivamente la primera línea anómala y se validó el módulo con pruebas específicas y suite completa. |
| R-002 | Baja | Seguridad funcional | 16 permisos iniciales no aparecen consumidos por el código actual. Módulos: auditoria, compras, documentos, empresas, eventos, tesoreria, usuarios, ventas. | La matriz contiene permisos reservados para módulos todavía no implementados. | Mantenerlos identificados como reservados; no presentarlos como funcionalidad disponible. |
| R-003 | Media | Calidad | No se detectaron workflows de GitHub Actions versionados. | La validación depende de la ejecución local y del contrato operativo. | Evaluar CI en una tarea futura sin reemplazar las validaciones locales. |
| R-004 | Baja | Documentación | Los documentos acumulativos conservan cortes históricos con cifras antiguas. | Una lectura fuera de contexto puede confundir estado histórico con estado vigente. | Usar docs/22_estado_real_integral_erp.md como fotografía canónica y respetar la jerarquía de docs/README.md. |
| R-005 | Baja | Pruebas | La tarea verifica cantidad y resultado de pruebas, pero no calcula cobertura de líneas o ramas. | Una suite verde no cuantifica áreas de código sin cobertura. | Definir una política de cobertura en una tarea separada si se considera necesaria. |

## Regla de tratamiento

Cada corrección debe ejecutarse como una tarea independiente, con alcance cerrado, pruebas específicas, suite completa y verificación remota. Los riesgos históricos resueltos deben conservarse con su estado y referencia al commit de solución.
