# Parámetros de empresa: inicialización y configuración amigable

## 1. Objetivo

Definir una forma operativa y segura de administrar la configuración estándar de cada empresa sin exigir que el usuario conozca claves técnicas, ámbitos ni tipos internos de `ParametroSistema`.

La interfaz normal del ERP debe trabajar con campos funcionales.

El Django Admin conserva el formulario técnico como herramienta avanzada.

## 2. Alcance de TAREA 47

Se implementan:

- definición versionada de ocho parámetros estándar
- inicialización manual e idempotente por empresa activa
- reactivación de parámetros estándar inactivos sin modificar su valor
- preservación de valores existentes
- formulario funcional para editar la configuración
- validación de moneda, punto de venta y modo de numeración
- conversión de casillas booleanas a valores internos `si` y `no`
- acceso desde la navegación del ERP
- aislamiento estricto por empresa activa
- pruebas de servicio, formulario, vista y seguridad

No se crean migraciones porque no cambia la estructura de base de datos.

## 3. Ruta

```text
/nucleo/configuracion/
```

La inicialización se ejecuta mediante POST:

```text
/nucleo/configuracion/inicializar/
```

## 4. Parámetros estándar

| Campo funcional | Clave interna | Valor inicial | Tipo |
|---|---|---:|---|
| Moneda funcional | `moneda_funcional` | `ARS` | Texto |
| Permitir stock negativo | `permite_stock_negativo` | `no` | Booleano |
| Usar centros de costo | `usa_centros_costo` | `si` | Booleano |
| Usar proyectos | `usa_proyectos` | `no` | Booleano |
| Requerir aprobación de pagos | `requiere_aprobacion_pagos` | `no` | Booleano |
| Requerir aprobación de compras | `requiere_aprobacion_compras` | `no` | Booleano |
| Punto de venta predeterminado | `punto_venta_default` | `0001` | Texto |
| Numeración de comprobantes internos | `modo_numeracion_comprobantes` | `automatico` | Texto |

La numeración de comprobantes internos no configura todavía facturación electrónica ARCA/AFIP.

## 5. Inicialización

La operación se ejecuta de forma explícita desde la pantalla.

Reglas:

1. opera sobre `request.empresa_activa`
2. crea solamente parámetros faltantes
3. no duplica registros
4. no modifica valores existentes
5. reactiva parámetros estándar inactivos preservando su valor
6. no elimina ni modifica parámetros personalizados
7. informa creados, reactivados y existentes

La mera instalación de TAREA 47 no carga datos en empresas reales.

## 6. Edición funcional

Una vez completa la inicialización, la pantalla expone:

- moneda funcional
- punto de venta predeterminado
- modo de numeración
- cinco opciones booleanas mediante casillas

El usuario no edita directamente:

- ámbito
- empresa
- clave
- tipo de valor
- representación textual de booleanos
- descripción técnica
- estado activo

Al guardar, el servicio normaliza y valida los ocho registros estándar.

## 7. Seguridad inicial

Hasta aplicar permisos funcionales en TAREA 48:

- la vista exige autenticación
- la vista exige `user.is_staff`
- la empresa debe estar activa en la sesión
- una empresa se selecciona mediante el mecanismo ya validado
- no se acepta un ID de empresa enviado por formulario

Esto impide editar otra empresa alterando parámetros del navegador.

TAREA 48 reemplazará la restricción temporal de `is_staff` por el permiso funcional `parametros.editar`.

## 8. Validaciones

- moneda: tres letras, normalizada a mayúsculas
- punto de venta: cuatro dígitos, conservando ceros a la izquierda
- numeración: `automatico` o `manual`
- booleanos: almacenados como `si` o `no`
- todos los registros pasan `full_clean()`
- el guardado se ejecuta dentro de una transacción

## 9. Caso real de prueba

El relevamiento R01 detectó:

```text
Empresa: ESREQUIS LAURA
Parámetros estándar existentes: 0
```

Después de cerrar TAREA 47, el usuario `ADMIN` deberá:

1. seleccionar `ESREQUIS LAURA`
2. abrir Configuración
3. presionar Inicializar configuración
4. revisar los valores propuestos
5. guardar los cambios que correspondan

Esa acción manual será la prueba funcional sobre la base real.

## 10. Fuera de alcance

TAREA 47 no implementa:

- permisos funcionales aplicados a todas las vistas
- asignación de roles a Laura
- creación automática al dar de alta una empresa
- ejercicio fiscal o períodos contables
- facturación electrónica
- puntos de venta ARCA
- auditoría automática de cambios
- configuración por sucursal
- parámetros globales
- edición de parámetros personalizados
