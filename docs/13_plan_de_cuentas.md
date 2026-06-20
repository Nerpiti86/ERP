# Diseño funcional y técnico mínimo del Plan de cuentas

```text
Estado: DISEÑO MÍNIMO APROBADO
Fecha: 2026-06-20
Implementación: PENDIENTE
```

Este documento consolida las decisiones aprobadas para la primera versión del
Plan de cuentas. Reemplaza las definiciones anteriores que quedaron superadas
durante el análisis.

El alcance se limita al maestro `CuentaContable`. No implementa todavía asientos,
libros, centros de costo, proyectos, moneda extranjera, ajuste por inflación ni
procesos de cierre.

## 1. Objetivo de la primera versión

La primera versión deberá permitir:

- mantener un Plan de cuentas por empresa
- representar una jerarquía contable ordenada de cinco niveles
- distinguir cuentas agrupadoras e imputables sin duplicar información
- habilitar o deshabilitar cuentas sin perder historia
- servir como base para los futuros asientos de apertura y de operaciones

El Plan de cuentas no almacenará saldos, movimientos ni acumulados.

## 2. Aplicación Django

Se creará una aplicación específica:

```text
apps.contabilidad
```

`CuentaContable` pertenecerá a `apps.contabilidad`.

La dirección de dependencia será:

```text
contabilidad → nucleo
```

`apps.contabilidad` podrá utilizar las entidades transversales de `apps.nucleo`,
como `Empresa`, usuarios, permisos y auditoría. `apps.nucleo` no dependerá de
`apps.contabilidad`.

## 3. Propiedad y alcance empresarial

- Cada empresa tendrá un único Plan de cuentas.
- El plan será compartido por todas las sucursales de la empresa.
- Permanecerá entre ejercicios fiscales y no se copiará cada año.
- No existirá una tabla cabecera `PlanDeCuentas`.
- El plan será el conjunto de registros `CuentaContable` de una empresa.
- La pantalla requerirá empresa activa, pero no sucursal activa.
- Todo acceso deberá filtrar y validar la empresa activa.

## 4. Modelo mínimo persistido

La primera versión almacenará únicamente:

```text
CuentaContable
├── id
├── empresa
├── parent
├── codigo
├── nombre
├── descripcion
├── tipo_contable
├── naturaleza
├── habilitada
├── creada_en
└── actualizada_en
```

Además existirán los campos técnicos internos requeridos por la biblioteca del
árbol.

No se almacenarán como campos editables:

```text
nivel
imputable
es_raiz
codigo_del_padre_esperado
saldo
debe
haber
saldo_inicial
```

Esos valores serán derivados cuando corresponda.

## 5. Definición inicial de campos

| Campo | Definición inicial | Regla principal |
|---|---|---|
| `empresa` | `ForeignKey` a `nucleo.Empresa` | Obligatoria y protegida |
| `parent` | `ForeignKey` autorreferenciada | Nula solamente para raíces |
| `codigo` | `CharField(max_length=13)` | Máscara fija y único por empresa |
| `nombre` | `CharField(max_length=150)` | Obligatorio |
| `descripcion` | `TextField` | Opcional |
| `tipo_contable` | `CharField` con opciones | Obligatorio |
| `naturaleza` | `CharField` con opciones | Obligatoria solo para imputables |
| `habilitada` | `BooleanField` | Verdadero inicialmente |
| `creada_en` | `DateTimeField` | Automático al crear |
| `actualizada_en` | `DateTimeField` | Automático al modificar |

El nombre técnico de la relación superior será `parent`, requerido por la
estrategia elegida de Treebeard.

La representación acordada será:

```text
Nombre Python: parent
Columna SQL: cuenta_padre_id
Nombre visible: Cuenta superior
Relación inversa: cuentas_hijas
```

## 6. Jerarquía y dependencia open source

Se utilizará `django-treebeard` mediante:

```python
treebeard.al_tree.AL_Node
```

La biblioteca resolverá la mecánica general del árbol. Las reglas contables
seguirán siendo responsabilidad del ERP.

El modelo declarará la autorrelación `parent` y utilizará:

```python
node_order_by = ["codigo"]
```

No habrá una tabla separada `RubroContable`.

Se impedirán:

- autorreferencias
- ciclos
- superiores de otra empresa
- superiores incompatibles con el código
- superiores incompatibles con el tipo contable
- cuentas imputables con descendientes

## 7. Máscara del código

El código tendrá obligatoriamente la máscara:

```text
9.9.99.99.999
```

Su validación formal será equivalente a:

```regex
^\d\.\d\.\d{2}\.\d{2}\.\d{3}$
```

El código será obligatorio y único por empresa:

```text
UNIQUE (empresa, codigo)
```

Los ceros representan niveles todavía no utilizados. No podrá existir un bloque
informado después de un bloque estructuralmente vacío.

Ejemplos válidos:

```text
1.0.00.00.000
1.1.00.00.000
1.1.01.00.000
1.1.01.01.000
1.1.01.01.001
```

Ejemplo inválido:

```text
1.0.01.00.000
```

## 8. Niveles

La estructura tendrá cinco niveles:

| Nivel | Ejemplo | Uso |
|---:|---|---|
| 1 | `1.0.00.00.000` | Rubro principal |
| 2 | `1.1.00.00.000` | Clasificación general |
| 3 | `1.1.01.00.000` | Grupo |
| 4 | `1.1.01.01.000` | Subgrupo |
| 5 | `1.1.01.01.001` | Cuenta imputable |

El nivel será derivado del último bloque distinto de cero. No se almacenará como
dato funcional editable.

## 9. Correspondencia entre código y superior

`parent` será la relación estructural persistida, pero deberá coincidir con el
superior derivado del código.

El código esperado del superior se obtiene poniendo en cero el último bloque
informado:

```text
1.1.01.01.001 → 1.1.01.01.000
1.1.01.01.000 → 1.1.01.00.000
1.1.01.00.000 → 1.1.00.00.000
1.1.00.00.000 → 1.0.00.00.000
```

Una raíz tendrá `parent = NULL`.

La creación o modificación será rechazada cuando el superior seleccionado no
coincida con el superior esperado por el código.

## 10. Orden

Como todos los segmentos tienen longitud fija, el orden textual de `codigo`
coincide con el orden contable esperado.

Ejemplo:

```text
1.1.01.03.001
1.1.01.03.002
1.1.01.03.003
1.1.01.04.001
```

No se agregará un campo de orden editable por el usuario.

## 11. Tipos contables

Los tipos iniciales serán:

```text
ACTIVO
PASIVO
PATRIMONIO_NETO
RESULTADO_POSITIVO
RESULTADO_NEGATIVO
ORDEN
```

Denominaciones visibles iniciales:

```text
ACTIVO              → Activo
PASIVO               → Pasivo
PATRIMONIO_NETO      → Patrimonio Neto
RESULTADO_POSITIVO   → Ingresos
RESULTADO_NEGATIVO   → Gastos y pérdidas
ORDEN                → Cuentas de orden
```

Las raíces operativas iniciales serán:

```text
1.0.00.00.000  ACTIVO
2.0.00.00.000  PASIVO
3.0.00.00.000  PATRIMONIO_NETO
4.0.00.00.000  RESULTADO_POSITIVO
5.0.00.00.000  RESULTADO_NEGATIVO
```

`ORDEN` queda disponible como clasificación opcional. Su código raíz definitivo
se establecerá cuando se incorpore efectivamente al plan.

Toda cuenta descendiente deberá conservar el tipo contable de su raíz.

## 12. Imputabilidad derivada

`imputable` no será un campo persistido ni editable.

La regla será:

```text
Último bloque = 000       → cuenta agrupadora
Último bloque = 001–999   → cuenta imputable
```

Ejemplos:

```text
1.1.01.01.000  Cajas en Moneda Nacional  → agrupadora
1.1.01.01.001  Caja ARS                   → imputable
```

Consecuencias:

- los niveles 1 a 4 serán agrupadores
- el nivel 5 será imputable
- una agrupadora nunca recibirá movimientos
- una imputable nunca tendrá descendientes
- solo una cuenta habilitada e imputable podrá utilizarse en futuros asientos

## 13. Naturaleza

Las naturalezas serán:

```text
DEUDORA
ACREEDORA
```

Reglas:

- una cuenta imputable deberá tener naturaleza
- una cuenta agrupadora tendrá `naturaleza = NULL`
- la naturaleza no se derivará rígidamente del tipo contable
- se admitirán cuentas regularizadoras con naturaleza contraria a la habitual
- una cuenta utilizada no podrá cambiar su naturaleza

Una agrupadora podrá contener descendientes con naturalezas diferentes.

## 14. Nombre y descripción

- `nombre` será obligatorio.
- `nombre` podrá repetirse dentro de la empresa.
- `descripcion` será opcional.
- Los textos eliminarán espacios sobrantes.
- No se forzarán mayúsculas.
- El código identificará la cuenta dentro de la empresa.
- Los cambios de nombre y descripción deberán conservar trazabilidad.

## 15. Estado operativo

El campo será `habilitada`, para evitar confusión con el tipo contable `ACTIVO`.

Estados visibles:

```text
HABILITADA
DESHABILITADA
```

Reglas:

- no habrá eliminación física desde la operación normal
- una cuenta deshabilitada conservará su historia
- una cuenta deshabilitada no podrá utilizarse en nuevas operaciones
- una agrupadora no podrá deshabilitarse mientras tenga descendientes habilitados
- la rehabilitación volverá a validar código, superior, empresa, tipo y naturaleza

## 16. Modificaciones estructurales

Una cuenta o rama nunca utilizada podrá cambiar de código o superior mediante una
operación transaccional controlada.

Si la rama tiene descendientes, la operación deberá actualizar de manera atómica:

- el código de la cuenta
- el superior
- los códigos de todos sus descendientes
- la posición del árbol administrada por Treebeard

Una cuenta se considerará utilizada cuando tenga movimientos o referencias desde
asientos, configuraciones u otros módulos del ERP.

Una cuenta o rama utilizada no podrá cambiar:

- código
- superior
- posición estructural
- tipo contable
- naturaleza

Para reemplazarla se deberá crear una nueva cuenta y deshabilitar la anterior,
conservando la historia.

## 17. Saldos y futura registración

`CuentaContable` no almacenará:

```text
saldo
saldo inicial
debe
haber
acumulados
```

Los saldos surgirán en el futuro de las líneas de asientos confirmados.

Las agrupadoras totalizarán los movimientos de sus descendientes. Los saldos de
apertura se representarán mediante asientos de apertura del ejercicio nuevo.

Con este maestro mínimo será posible construir posteriormente:

- asiento de apertura inicial
- asiento de apertura por arrastre
- asientos de operaciones
- Diario General
- Mayor por cuenta
- balance de sumas y saldos

## 18. Dependencias y licencias

El ERP será una aplicación privada, de uso propio, sin distribución ni
comercialización prevista.

Podrán evaluarse herramientas open source con licencias:

```text
MIT
BSD
Apache 2.0
LGPL
GPL
```

Toda dependencia deberá cumplir además:

- no exigir suscripción
- no exigir pagos por usuario o servidor
- no depender obligatoriamente de un SaaS
- poder instalarse localmente
- mantener los datos bajo control del usuario
- aportar valor técnico concreto
- ser compatible con la versión de Django utilizada

`django-treebeard` queda aprobado para el árbol del Plan de cuentas.

`django-ledger` ya no se descarta solamente por su licencia GPL, pero tampoco se
incorpora automáticamente. Su posible uso futuro dependerá de una evaluación de
encaje arquitectónico y funcional.

## 19. Fuera del alcance de la primera versión

Se postergan expresamente:

```text
funcion_contable
centros de costo
proyectos
moneda extranjera
cuentas automáticas
plantillas complejas
importaciones avanzadas
ConfiguracionCierreCuenta
ajuste por inflación
criterios de medición
valuaciones
refundición
cierre contable
```

Estos temas podrán agregarse mediante campos opcionales, tablas de configuración
o módulos separados cuando exista experiencia de uso y datos reales.

## 20. Pendientes de implementación

Antes de considerar completo el Plan de cuentas deberán desarrollarse:

- creación de `apps.contabilidad`
- incorporación de `django-treebeard`
- modelo `CuentaContable`
- migración inicial
- restricciones de base de datos
- servicios de creación y modificación
- validaciones del código y del superior
- permisos funcionales
- auditoría y eventos
- interfaz del árbol
- búsqueda y filtros
- pruebas automatizadas
- carga inicial del plan de la primera empresa

## 21. Próximo paso

El próximo trabajo será implementar exclusivamente el maestro básico:

```text
apps.contabilidad
└── CuentaContable
```

Los asientos contables se diseñarán e implementarán después de disponer del Plan
de cuentas funcionando y cargado con datos reales.
