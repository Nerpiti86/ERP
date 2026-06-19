# Diseño funcional del Plan de cuentas

```text
Estado: DISEÑO APROBADO
Fecha: 2026-06-19
Implementación: PENDIENTE
```

Este documento consolida las decisiones aprobadas para el maestro de cuentas y
separa, como anexo, las definiciones preliminares del cierre contable. No crea
modelos, migraciones, vistas ni procesos.

## 1. Alcance y propiedad

- Cada empresa tendrá un único Plan de cuentas.
- El plan será compartido por todas sus sucursales.
- Permanecerá entre ejercicios fiscales y no se copiará cada año.
- No existirá una tabla cabecera `PlanDeCuentas`.
- El plan será el conjunto de registros `CuentaContable` de la empresa.
- Será una pantalla por empresa: requerirá empresa activa, no sucursal activa.

## 2. Modelo conceptual

```text
CuentaContable
├── empresa
├── cuenta_padre
├── codigo
├── nombre
├── descripcion
├── tipo_contable
├── naturaleza
├── imputable
├── funcion_contable
├── habilitada
├── creada_en
└── actualizada_en
```

Los tipos de campo, longitudes, índices y restricciones exactas se definirán en
el diseño técnico.

## 3. Jerarquía

- `cuenta_padre` será la fuente técnica de verdad del árbol.
- La jerarquía será flexible y sin cantidad fija de niveles.
- No habrá tabla separada `RubroContable` ni columnas rígidas por nivel.
- Se impedirán autorreferencias, ciclos, padres de otra empresa y movimientos
  debajo de un descendiente propio.

## 4. Clasificación contable

Toda cuenta tendrá un `tipo_contable`:

```text
ACTIVO
PASIVO
PATRIMONIO_NETO
RESULTADO
ORDEN
```

Una hija deberá conservar el tipo contable de su superior.

Las naturalezas serán:

```text
DEUDORA
ACREEDORA
```

La naturaleza será obligatoria solamente para cuentas imputables. Las
agrupadoras tendrán `naturaleza = NULL`, porque pueden reunir descendientes con
naturalezas diferentes.

## 5. Agrupadoras e imputables

```text
imputable = False  → agrupadora
imputable = True   → cuenta de movimiento
```

Reglas:

- solo una cuenta habilitada, imputable y sin hijas recibirá registraciones
- una imputable no podrá tener descendientes
- una cuenta con hijas será agrupadora
- una agrupadora podrá existir temporalmente sin hijas
- una agrupadora nunca recibirá movimientos directamente

## 6. Código contable

El código será obligatorio y único por empresa:

```text
UNIQUE (empresa, codigo)
```

Contendrá exclusivamente números y puntos. Admitirá ceros a la izquierda en
los segmentos. No admitirá espacios, puntos consecutivos ni puntos al inicio o
al final.

```regex
^\d+(?:\.\d+)*$
```

Ejemplo aprobado:

```text
1.1.01.01.001 - CAJA
```

El código de una hija deberá extender el código completo de su superior:

```text
codigo_hija = codigo_padre + "." + segmento_numerico
```

La cantidad de dígitos por segmento será flexible. `cuenta_padre` seguirá siendo
la relación técnica, pero el código deberá ser coherente con ella.

## 7. Nombre y descripción

- `nombre` será obligatorio y podrá repetirse.
- `descripcion` será opcional.
- El nombre tendrá una longitud funcional máxima de 150 caracteres.
- Los textos eliminarán espacios sobrantes sin forzar mayúsculas.
- El código, no el nombre, identificará funcionalmente a la cuenta.
- Los cambios de nombre y descripción deberán quedar auditados.

## 8. Renumeración y reubicación

Una cuenta o rama nunca utilizada podrá renumerarse o cambiar de superior. Si
tiene descendientes, toda la rama deberá actualizarse en una operación atómica.

Una cuenta se considera utilizada cuando tiene movimientos o referencias desde
asientos, configuraciones, cuentas automáticas, terceros, productos, cajas,
bancos, impuestos, documentos u otros procesos.

Una cuenta o rama utilizada no podrá cambiar código, padre ni posición. Para
reemplazarla se deberá crear una nueva, trasladar las configuraciones aplicables
y deshabilitar la anterior, conservando la historia.

## 9. Estado operativo

El campo será `habilitada`, para no confundirlo con el tipo `ACTIVO`.

```text
HABILITADA
DESHABILITADA
```

No habrá eliminación física desde la operación normal.

Una cuenta deshabilitada conservará movimientos y referencias históricas, pero
no podrá utilizarse en nuevos asientos ni configuraciones. Una agrupadora no
podrá deshabilitarse mientras tenga descendientes habilitados.

La rehabilitación exigirá nuevamente código válido y único, superior habilitada,
tipo coherente y cumplimiento de las reglas de imputabilidad.

## 10. Función contable

Una cuenta imputable podrá tener una `funcion_contable` opcional para que el ERP
reconozca su uso sin depender del código o del nombre.

Ejemplos conceptuales:

```text
CAJA
BANCO
CREDITOS_POR_VENTAS
PROVEEDORES
VENTAS
COSTO_DE_VENTAS
IVA_CREDITO_FISCAL
IVA_DEBITO_FISCAL
```

- Las agrupadoras no tendrán función contable.
- Varias cuentas podrán compartir una función, por ejemplo varios bancos.
- La función no seleccionará automáticamente una cuenta concreta.
- El catálogo será controlado por el ERP, no texto libre.
- El catálogo definitivo queda pendiente.

## 11. Saldos

`CuentaContable` no almacenará saldo, saldo inicial, debe, haber ni acumulados.
Los saldos surgirán de líneas de asientos confirmados según empresa, sucursal,
ejercicio, período y fechas.

Las agrupadoras totalizarán a sus descendientes. Los saldos iniciales se
representarán mediante asientos de apertura. Cualquier caché o acumulado futuro
será derivado y reconstruible.

## 12. Cuentas raíz

Cada empresa podrá tener como máximo una raíz por tipo contable.

```text
1 ACTIVO
2 PASIVO
3 PATRIMONIO NETO
4 RESULTADOS
5 CUENTAS DE ORDEN
```

Una raíz tendrá:

```text
cuenta_padre = NULL
imputable = False
naturaleza = NULL
funcion_contable = NULL
```

Su código tendrá un único segmento. Para operar deberán existir y estar
habilitadas las raíces Activo, Pasivo, Patrimonio Neto y Resultado. Orden será
opcional.

Una raíz no podrá ser imputable, recibir movimientos, recibir superior, duplicar
un tipo raíz ni cambiar de tipo con descendientes.

# Configuración de cierre por cuenta

## 13. Separación de responsabilidades

Se separarán:

```text
CuentaContable
→ ConfiguracionCierreCuenta
→ ejecución concreta del cierre
```

La cuenta contiene la estructura estable. La configuración contiene políticas
con vigencia temporal. La ejecución contiene importes, parámetros, cálculos,
borradores y asientos propuestos de un ejercicio.

Un cambio de política no sobrescribirá la historia: cerrará la vigencia anterior
y creará una nueva.

## 14. Ajuste por inflación

No se utilizará un booleano `ajusta_por_inflacion`. Se distinguirán:

```text
clasificacion_inflacion
metodo_reexpresion
```

Clasificaciones conceptuales:

```text
MONETARIA
NO_MONETARIA
PATRIMONIO_NETO
RESULTADO
CUENTA_ORDEN
```

Métodos conceptuales:

```text
YA_EN_MONEDA_CIERRE
POR_FECHA_ORIGEN
POR_MOVIMIENTOS
POR_COMPONENTE_SUBYACENTE
SEGUN_SUBMODULO
CALCULO_DEL_SISTEMA
NO_PARTICIPA
```

La clasificación no determinará por sí sola el cálculo. Una partida no monetaria
ya medida a valor corriente de cierre no deberá reexpresarse nuevamente.

## 15. Medición al cierre

La configuración declarará:

```text
criterio_medicion_cierre
origen_medicion
```

Criterios conceptuales iniciales:

```text
SIN_MEDICION_ESPECIFICA
VALOR_NOMINAL
TIPO_CAMBIO_CIERRE
COSTO_AMORTIZADO
COSTO_REEXPRESADO
VALOR_NETO_REALIZACION
VALOR_RAZONABLE
VALOR_RECUPERABLE
SEGUN_SUBMODULO
INGRESO_MANUAL
```

Orígenes conceptuales iniciales:

```text
NO_APLICA
MANUAL
MONEDA_EXTRANJERA
CREDITOS_Y_DEUDAS
BIENES_DE_CAMBIO
BIENES_DE_USO
INVERSIONES
IMPUESTOS
OTRO_SUBMODULO
```

La cuenta no guardará cotizaciones, stock, vidas útiles, valores de mercado,
importes de ajuste, coeficientes ni asientos. Esos datos pertenecerán a los
submódulos y a la ejecución del cierre.

```text
saldo contable previo
→ valor medido al cierre
→ diferencia
→ asiento propuesto
```

No existirá una única contrapartida genérica para todos los ajustes.

# Anexo: ciclo contable

## 16. Apertura y operaciones

La apertura es un asiento del ejercicio nuevo, no una etapa persistente del
cierre.

```text
APERTURA_INICIAL
APERTURA_POR_ARRASTRE
```

Las operaciones son las registraciones diarias ordinarias: ventas, compras,
tesorería, stock, sueldos, impuestos y asientos manuales. Tampoco son una etapa
del cierre.

## 17. Preparación del cierre

El orden aprobado es:

```text
1. AJUSTES DE VALUACIÓN
2. AJUSTE POR INFLACIÓN
3. REFUNDICIÓN
4. CIERRE
```

Cada paso tendrá:

```text
BORRADOR DEL PASO
└── ASIENTO PROPUESTO
```

Los borradores y propuestas no afectarán Diario, Mayor, saldos oficiales ni
numeración definitiva. Podrán recalcularse, corregirse, descartarse y regenerarse
sin asientos de reversión antes de la confirmación final.

Los pasos posteriores trabajarán con saldos proyectados:

```text
asientos confirmados
+ propuestas de pasos anteriores
= base proyectada del paso siguiente
```

Si cambian las operaciones o un borrador anterior, los pasos posteriores quedarán
desactualizados y deberán recalcularse.

Los asientos definitivos se crearán recién en la confirmación final. El mecanismo
técnico de confirmación atómica, numeración, bloqueo y reapertura queda pendiente.

# Dependencias y licencias

## 18. Política

No se incorporarán componentes que exijan licencias pagas, suscripciones,
pagos por usuario, pagos por servidor o servicios SaaS obligatorios.

Se priorizarán licencias permisivas como MIT, BSD y Apache 2.0.

`django-ledger` queda descartado como dependencia por su licencia GPL-3.0-or-later
y el riesgo de copyleft para una distribución cerrada. Puede utilizarse como
referencia conceptual.

`django-treebeard` fue identificado como posible herramienta para el árbol, pero
su incorporación todavía no fue aprobada.

# Pendientes

## 19. Plan de cuentas

- ubicación técnica del modelo
- campos Django definitivos
- índices y restricciones de base
- servicios de validación
- permisos funcionales
- auditoría completa y eventos
- interfaz del árbol
- búsqueda y ordenamiento
- importación y exportación
- creación asistida de raíces
- plantillas iniciales
- catálogo definitivo de funciones
- decisión sobre `django-treebeard`
- pruebas automatizadas

## 20. Cierre contable

- catálogos definitivos de inflación y medición
- reglas de contrapartida
- modelos de borradores y propuestas
- validar si un paso puede generar más de un asiento propuesto
- versiones de cálculo
- confirmación final atómica
- numeración definitiva
- bloqueo de operaciones
- reapertura extraordinaria
- permisos y auditoría

## 21. Próximo paso

El siguiente diseño debe volver al alcance del maestro:

```text
Auditoría, permisos y restricciones técnicas de CuentaContable
```

El motor completo de cierre deberá desarrollarse en una tarea y documento
separados.
