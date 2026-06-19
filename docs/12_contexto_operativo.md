# Contexto operativo obligatorio

## 1. Objetivo

Toda operación futura del ERP debe ejecutarse dentro de un contexto explícito
y validado. El contexto evita mezclar datos entre empresas o sucursales aunque
un usuario altere una URL, un formulario o un identificador.

## 2. Tipos de pantalla

### Pantalla por empresa

Requiere:

- usuario autenticado
- empresa activa
- permiso funcional cuando corresponda

Ejemplos:

- configuración de empresa
- ejercicios fiscales
- parámetros generales
- reportes consolidados de empresa

Uso:

```python
@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("modulo.accion")
def vista(request):
    ...
```

### Pantalla operativa por sucursal

Requiere:

- usuario autenticado
- empresa activa
- sucursal activa perteneciente a esa empresa
- permiso funcional

Ejemplos:

- ventas
- compras
- stock
- caja
- cobros
- pagos
- movimientos operativos

Uso:

```python
@login_required
@contexto_operativo_requerido
@permiso_funcional_requerido("modulo.accion")
def vista(request):
    ...
```

## 3. Orden obligatorio de validación

```text
autenticación
→ contexto operativo
→ permiso funcional
→ pertenencia del objeto
→ operación
```

El permiso se evalúa después de resolver la empresa activa porque los roles
funcionales son por empresa.

## 4. Redirecciones

Cuando falta empresa:

```text
/empresa/seleccionar/?next=<ruta original>
```

Cuando existe empresa pero falta sucursal:

```text
/sucursal/seleccionar/?next=<ruta original>
```

El destino original se conserva mediante `next` y los selectores mantienen la
validación de URL interna segura ya implementada.

## 5. Aislamiento de consultas

Proteger una vista no alcanza. Cada queryset debe quedar acotado.

Por empresa:

```python
queryset = filtrar_queryset_por_empresa_activa(
    request,
    Tercero.objects.all(),
)
```

Por empresa y sucursal:

```python
queryset = filtrar_queryset_por_contexto_operativo(
    request,
    Movimiento.objects.all(),
)
```

Los nombres de campos pueden configurarse cuando el modelo use relaciones
indirectas.

## 6. Validación de objetos

Antes de ver, modificar, confirmar o anular un objeto recuperado por ID:

```python
validar_objeto_en_empresa_activa(request, objeto)
```

o:

```python
validar_objeto_en_contexto_operativo(request, objeto)
```

Una discrepancia responde con `PermissionDenied`. El diseño falla de forma
cerrada: sin contexto válido no devuelve datos ni permite operar.

## 7. Reglas para modelos futuros

Todo modelo operativo debe tener una pertenencia inequívoca:

- `empresa` obligatoria
- `sucursal` obligatoria cuando la operación ocurre en una sucursal
- índices acordes a las consultas por contexto
- validación de que la sucursal pertenece a la empresa
- creación desde `request.empresa_activa` y `request.sucursal_activa`
- no aceptar empresa o sucursal arbitrarias desde el navegador

Los formularios operativos no deben confiar en IDs ocultos enviados por el
cliente para determinar la empresa o sucursal.

## 8. Superusuarios

El superusuario puede seleccionar cualquier empresa y sucursal activas, pero
continúa sujeto al contexto seleccionado. Ser superusuario no autoriza a mezclar
objetos de otra empresa o sucursal dentro de una operación concreta.

## 9. Alcance de TAREA 49

Se implementan:

- `sucursal_activa_requerida`
- `contexto_operativo_requerido`
- filtrado de querysets por contexto
- validación de pertenencia de objetos
- pruebas de redirección, manipulación de sesión y aislamiento
- clasificación explícita de Configuración como pantalla por empresa

No se implementa todavía un módulo operativo concreto.

## 10. Próximo paso

```text
TAREA 50 — Diseñar maestro de terceros
```

A partir de ese módulo, todo desarrollo nuevo debe aplicar este contrato.
