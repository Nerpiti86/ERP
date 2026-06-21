# Ingresos Brutos y jurisdicciones por empresa

Estado: implementado por la TAREA 0007.

## 1. Objetivo

Administrar la situación registral de cada empresa frente al Impuesto sobre
los Ingresos Brutos sin mezclar:

- régimen de inscripción
- tratamiento fiscal general
- número de inscripción
- jurisdicción sede
- jurisdicciones activas
- vigencias
- sucursales físicas
- futuros cálculos tributarios

Esta etapa no liquida impuesto ni genera declaraciones juradas.

## 2. Fuentes oficiales

La Resolución General CA 3/2026 aprueba el ordenamiento jurídico electrónico
vigente de las normas de la Comisión Arbitral.

La página oficial actual de jurisdicciones y la tabla normativa consolidada
identifican 24 jurisdicciones. Los códigos COMARB tienen tres posiciones y
se extienden desde `901` hasta `924`.

Fuentes:

```text
https://www.ca.gob.ar/ordenamiento-juridico
https://www.ca.gob.ar/descargas/normativa/legislacion/Ordenamiento_RG-2026-3_v3.pdf
https://www.ca.gob.ar/datos-jurisdicciones
https://www.ca.gob.ar/resoluciones-comarb/download/441-2024/8513-rg-17-ordenamiento-resoluciones-generales-2025
```

El ordenamiento normativo también diferencia:

- jurisdicción con actividad económica
- jurisdicción sede
- período de inicio
- período de cese

## 3. Catálogo JurisdiccionFiscal

Campos:

- código COMARB
- nombre
- estado activo
- orden
- URL de fuente
- fechas técnicas

La migración `0014_cargar_jurisdicciones_fiscales` incorpora 24 registros:

```text
901 Ciudad Autónoma de Buenos Aires
902 Buenos Aires
...
921 Santa Fe
...
924 Tucumán
```

El catálogo es de solo lectura en Django Admin.

## 4. ConfiguracionIIBBEmpresa

Una empresa puede conservar configuraciones históricas, pero solo puede
tener una configuración activa.

Regímenes:

- `NO_INSCRIPTO`
- `LOCAL`
- `CONVENIO_MULTILATERAL`

Tratamientos generales:

- `GRAVADO`
- `EXENTO`
- `NO_ALCANZADO`
- `MIXTO`

Campos principales:

- empresa
- régimen
- tratamiento general
- número de inscripción
- fecha de alta
- fecha de baja
- activa
- observaciones

## 5. EmpresaJurisdiccionIIBB

Representa la presencia registral de una empresa en una jurisdicción.

Campos:

- configuración
- jurisdicción
- número de inscripción o cuenta jurisdiccional
- sede
- tratamiento
- fecha de alta
- fecha de baja
- activa
- observaciones
- instantánea del código, nombre y fuente

## 6. Reglas

### Configuración

- una sola configuración activa por empresa
- `NO_INSCRIPTO` no admite jurisdicciones activas
- `LOCAL` admite una sola jurisdicción activa
- `CONVENIO_MULTILATERAL` admite una o más
- una configuración inscripta requiere número y fecha de alta
- la fecha de baja no puede preceder a la de alta
- la baja es lógica

### Jurisdicciones

- una jurisdicción no puede estar duplicada activamente
- como máximo una jurisdicción sede activa
- la sede debe estar activa
- una jurisdicción activa requiere fecha de alta
- al cambiar la sede se desmarca la anterior en una transacción
- al inactivar la sede se promueve otra jurisdicción activa cuando existe
- los ceses se conservan históricamente

Las reglas principales se validan en aplicación y PostgreSQL.

## 7. Servicios transaccionales

Las operaciones se concentran en:

- `crear_configuracion_iibb`
- `actualizar_configuracion_iibb`
- `inactivar_configuracion_iibb`
- `crear_jurisdiccion_iibb`
- `actualizar_jurisdiccion_iibb`
- `inactivar_jurisdiccion_iibb`

Los servicios:

- validan empresa activa
- bloquean registros relevantes
- aplican cambios atómicos
- conservan instantáneas
- registran auditoría

## 8. Permisos

Permisos funcionales:

```text
iibb.ver
iibb.crear
iibb.editar
```

Matriz inicial:

- `ADMIN`: ver, crear y editar
- `CONTADOR`: ver, crear y editar
- `AUDITOR`: ver
- `SOLO_LECTURA`: ver
- `OPERADOR`: sin acceso

## 9. Interfaz

Rutas principales:

```text
/nucleo/configuracion/ingresos-brutos/
/nucleo/configuracion/ingresos-brutos/nueva/
/nucleo/configuracion/ingresos-brutos/<id>/editar/
/nucleo/configuracion/ingresos-brutos/<id>/inactivar/
```

Rutas jurisdiccionales:

```text
/nucleo/configuracion/ingresos-brutos/<id>/jurisdicciones/nueva/
/nucleo/configuracion/ingresos-brutos/jurisdicciones/<id>/editar/
/nucleo/configuracion/ingresos-brutos/jurisdicciones/<id>/inactivar/
```

La portada de Configuración de empresa muestra:

- régimen vigente
- número de inscripción
- jurisdicción sede
- cantidad de jurisdicciones activas
- estado de completitud

## 10. Estado de completitud

`NO_INSCRIPTO` se considera completo cuando no tiene jurisdicciones activas.

`LOCAL` se considera completo cuando:

- tiene número y fecha de alta
- tiene una jurisdicción activa
- esa jurisdicción es sede

`CONVENIO_MULTILATERAL` se considera completo cuando:

- tiene número y fecha de alta
- tiene al menos una jurisdicción activa
- tiene exactamente una sede activa

Este estado participa del cálculo de configuración base de la empresa.

## 11. Fuera de alcance

La TAREA 0007 no implementa:

- liquidaciones mensuales
- CM03, CM04 o CM05
- coeficientes unificados
- alícuotas por actividad
- retenciones o percepciones sufridas
- padrón de alícuotas
- agentes de recaudación
- generación de declaraciones juradas
- presentaciones SIFERE

Estas funciones requieren reglas tributarias por período y jurisdicción.

## 12. Pruebas

La implementación incorpora pruebas de:

- catálogo oficial
- constraints
- vigencias
- snapshots
- servicios y transacciones
- cambios de sede
- bajas lógicas
- auditoría
- formularios
- permisos
- aislamiento multiempresa
- vistas
- Django Admin de solo lectura

Suite completa verificada al cierre: `237` pruebas.

El recuento fue confirmado nuevamente al inicio de la TAREA 0008 sobre el
commit de cierre de la TAREA 0007.
