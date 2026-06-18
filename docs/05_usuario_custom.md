# Evaluacion de usuario custom

Estado: definido documentalmente al cierre de la Tarea 41.

## 1. Objetivo

Evaluar si conviene cambiar el usuario base de Django antes de implementar roles y permisos funcionales propios del ERP.

## 2. Estado actual del proyecto

El proyecto no define `AUTH_USER_MODEL` en `config/settings.py`.

Por lo tanto, el usuario base actual es el usuario estandar de Django: `auth.User`.

Los modelos propios ya referencian usuarios mediante `settings.AUTH_USER_MODEL`.

Ejemplos actuales:

- Auditoria
- EventoNegocio
- DocumentoAdjunto
- UsuarioEmpresa
- UsuarioSucursal

Este criterio es correcto porque mantiene el codigo preparado para un eventual cambio futuro, aunque hoy se use `auth.User`.

## 3. Decision

No crear usuario custom en esta etapa.

Decision operativa:

```text
Mantener auth.User estandar de Django.
No cambiar AUTH_USER_MODEL.
Continuar usando settings.AUTH_USER_MODEL en modelos.
Continuar usando get_user_model() en codigo runtime y tests.
```

## 4. Motivos

### 4.1. El proyecto ya tiene migraciones aplicadas

Ya existen tablas y migraciones que dependen del usuario actual.

Cambiar `AUTH_USER_MODEL` despues de haber creado tablas puede ser complejo porque afecta claves foraneas, relaciones many-to-many y orden de migraciones.

### 4.2. No hay necesidad funcional fuerte todavia

Por ahora el ERP necesita:

- identificar usuario
- controlar si esta activo
- permitir superuser tecnico inicial
- relacionar usuario con empresas
- relacionar usuario con sucursales
- asignar roles funcionales por empresa

Todo eso puede resolverse con `auth.User` mas modelos propios.

### 4.3. La informacion funcional no debe mezclarse con autenticacion

La empresa activa, sucursal activa, roles, permisos y configuraciones funcionales pertenecen al ERP.

No necesitan estar dentro del modelo de usuario.

Deben vivir en modelos propios del nucleo.

## 5. Regla de arquitectura

El modelo de usuario debe quedar enfocado en autenticacion.

Los datos funcionales del ERP deben vivir en modelos separados.

Ejemplos:

- UsuarioEmpresa
- UsuarioSucursal
- UsuarioRolEmpresa
- futuro PerfilUsuario si hiciera falta

## 6. Reglas obligatorias de codigo

### 6.1. Modelos

En modelos, usar siempre:

```python
from django.conf import settings

usuario = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

No usar:

```python
from django.contrib.auth.models import User
```

### 6.2. Codigo runtime y tests

En codigo runtime y tests, usar:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
```

### 6.3. Settings

No agregar:

```python
AUTH_USER_MODEL = "..."
```

salvo decision tecnica futura explicita y con plan de migracion separado.

## 7. Cuando reconsiderar usuario custom

Reconsiderar usuario custom solo si aparece una necesidad fuerte como:

- login obligatorio por email sin username
- integracion centralizada de identidad externa
- campos autenticadores que deben vivir en el usuario
- reglas de autenticacion imposibles de expresar con `auth.User`
- decision de resetear migraciones y base antes de datos reales

## 8. Alternativa si se necesitan datos extra

Si se necesitan datos extra no autenticadores, crear un modelo separado.

Nombre posible:

```text
PerfilUsuario
```

Campos posibles:

- usuario
- nombre_mostrar
- telefono
- cargo
- preferencias_json
- activo
- creado_en
- actualizado_en

No se implementa en esta tarea.

## 9. Impacto sobre roles y permisos

La decision permite avanzar con la estrategia ya definida en `docs/04_roles_permisos.md`.

Modelos futuros:

- RolFuncional
- PermisoFuncional
- RolPermiso
- UsuarioRolEmpresa

Estos modelos deben referenciar usuarios mediante `settings.AUTH_USER_MODEL`.

## 10. Alcance fuera de esta tarea

No se implementa:

- usuario custom
- PerfilUsuario
- migraciones
- modelos nuevos
- cambios en settings
- cambios en login
- cambios en admin
- roles y permisos funcionales
- middleware
- pantallas

## 11. Secuencia recomendada

Tarea siguiente:

```text
TAREA 42 — Implementar roles y permisos funcionales
```

Luego:

```text
TAREA 43 — Cargar roles y permisos iniciales
```

## 12. Estado de cierre

Tarea 41 resuelve la decision de usuario custom.

La implementacion de roles y permisos funcionales queda desbloqueada.
