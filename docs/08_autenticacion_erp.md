# Autenticación propia del ERP

Estado: implementado al cierre de la Tarea 46.

## 1. Objetivo

Proporcionar ingreso y salida propios del ERP sin utilizar el login de Django Admin como interfaz habitual.

La autenticación continúa basada en:

```text
django.contrib.auth
auth.User
sesiones de Django
```

No se crea un segundo sistema de usuarios.

## 2. Rutas

```text
/ingresar/
/salir/
```

Nombres de URL:

```text
core:login
core:logout
```

## 3. Ingreso

El formulario solicita:

- usuario
- contraseña

La validación utiliza `AuthenticationForm` de Django mediante una subclase con presentación Bootstrap.

Reglas:

- solo usuarios existentes
- contraseña válida
- usuario activo
- error genérico ante credenciales incorrectas
- protección CSRF
- renovación de la sesión mediante `django.contrib.auth.login`

## 4. Redirección posterior

Luego del ingreso:

1. se limpia cualquier contexto operativo anterior
2. se respeta `next` únicamente si es una URL interna segura
3. con varias empresas se abre el selector de empresa
4. con una empresa se la selecciona
5. con varias sucursales se abre el selector de sucursal
6. en los demás casos se abre la portada

No se permiten redirecciones externas.

## 5. Salida

La salida:

- se ejecuta únicamente mediante POST
- exige usuario autenticado
- incluye protección CSRF
- usa `django.contrib.auth.logout`
- elimina la sesión completa
- elimina empresa y sucursal activas
- redirige al login propio

No se admite logout por GET.

## 6. Protección de vistas

La portada y los selectores requieren autenticación.

Configuración:

```text
LOGIN_URL = core:login
LOGIN_REDIRECT_URL = core:home
LOGOUT_REDIRECT_URL = core:login
```

El acceso anónimo a una vista protegida se redirige a:

```text
/ingresar/?next=...
```

## 7. Django Admin

El Admin continúa disponible como backoffice técnico.

Reglas visuales:

- solo usuarios `is_staff` ven enlaces hacia el Admin
- los usuarios normales operan desde las pantallas propias
- el Admin conserva su propio control de acceso

Ocultar enlaces no reemplaza la validación de permisos de Django Admin.

## 8. Portada

La portada deja de ser pública.

Las métricas se limitan al contexto del usuario:

- empresas disponibles
- sucursales disponibles de la empresa activa
- ejercicios fiscales de la empresa activa
- períodos contables de la empresa activa

No se muestran conteos globales a usuarios normales.

## 9. Sesión y contexto

Al iniciar sesión se elimina cualquier empresa o sucursal que pudiera existir de una sesión previa.

En requests posteriores, el middleware vuelve a resolver:

```text
request.empresa_activa
request.sucursal_activa
```

## 10. Seguridad inicial

Implementado:

- autenticación de Django
- usuario activo obligatorio
- CSRF en login y logout
- logout por POST
- validación de `next`
- sesión renovada al ingresar
- sesión eliminada al salir
- portada protegida
- enlaces de Admin restringidos visualmente a staff

## 11. Fuera de alcance

Esta tarea no implementa:

- recuperación de contraseña
- cambio de contraseña desde pantalla propia
- alta o edición de usuarios
- segundo factor
- bloqueo por cantidad de intentos
- auditoría automática de login y logout
- cierre forzado de otras sesiones
- permisos funcionales aplicados a cada vista
- endurecimiento HTTPS de producción
- migraciones o tablas nuevas

## 12. Próximo paso

```text
TAREA 47 — Aplicar permisos funcionales a las vistas del ERP
```
