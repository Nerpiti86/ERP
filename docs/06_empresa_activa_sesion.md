# Empresa activa para la sesión

Estado: implementado al cierre de la Tarea 44.

## 1. Objetivo

Definir una única empresa de trabajo activa por sesión web.

La empresa activa constituye el contexto funcional que usarán los módulos del ERP para filtrar y validar operaciones futuras.

## 2. Almacenamiento

La sesión guarda únicamente el identificador de la empresa:

```text
nucleo_empresa_activa_id
```

No se guarda el objeto completo ni información duplicada de la empresa.

## 3. Reglas de acceso

### Usuario normal

Puede seleccionar únicamente empresas que cumplan todas estas condiciones:

- empresa activa
- relación `UsuarioEmpresa` existente
- relación `UsuarioEmpresa` activa
- usuario autenticado y activo

### Superusuario

Puede seleccionar cualquier empresa activa.

El superusuario continúa siendo un acceso técnico inicial.

## 4. Selección automática

Si el usuario tiene exactamente una empresa disponible y todavía no hay empresa activa, el sistema la selecciona automáticamente.

Si tiene más de una empresa disponible, debe elegir una.

## 5. Selección manual

Ruta inicial:

```text
/empresa/seleccionar/
```

La selección manual:

- requiere usuario autenticado
- valida nuevamente el acceso en backend
- rechaza empresas no autorizadas
- guarda el ID en la sesión
- permite regresar a una URL interna segura mediante `next`

Mientras no exista login propio del ERP, el acceso no autenticado se redirige al login técnico de Django Admin.

## 6. Invalidación automática

En cada request autenticado se vuelve a validar la empresa guardada.

La selección se elimina si:

- la empresa fue desactivada
- se desactivó o eliminó el acceso `UsuarioEmpresa`
- el usuario dejó de estar activo
- el ID almacenado ya no existe
- el usuario ya no tiene autorización

## 7. Middleware

Middleware agregado:

```text
apps.nucleo.middleware.EmpresaActivaMiddleware
```

Atributos disponibles en cada request:

```text
request.empresa_activa
request.empresas_disponibles
```

El middleware se ejecuta después de:

```text
django.contrib.auth.middleware.AuthenticationMiddleware
```

## 8. Plantillas

Context processor agregado:

```text
apps.nucleo.context_processors.empresa_activa
```

Variables globales:

```text
empresa_activa
empresas_disponibles
```

La barra superior muestra la empresa activa y permite cambiarla.

## 9. Seguridad

Ocultar empresas en la interfaz no constituye control de acceso.

La vista de selección valida el acceso nuevamente en backend antes de escribir la sesión.

Los módulos futuros deberán usar `request.empresa_activa` y validar que cada objeto operado pertenezca a esa empresa.

## 10. Fuera de alcance

Esta tarea no implementa:

- login propio del ERP
- empresa activa obligatoria para todas las vistas
- filtrado de todos los modelos por empresa
- permisos de pantalla
- auditoría del cambio de empresa
- persistencia de la última empresa fuera de la sesión
- migraciones o tablas nuevas

## 11. Próximo paso

```text
TAREA 46 — Definir autenticación propia del ERP
```


## 12. Integración con sucursal activa

Al cierre de la Tarea 45, cambiar de empresa elimina la sucursal anterior.

La sucursal activa se documenta en:

```text
docs/07_sucursal_activa_sesion.md
```

