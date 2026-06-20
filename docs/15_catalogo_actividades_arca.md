# Catalogo oficial de actividades ARCA CLAE

Estado: implementado por la TAREA 0005.

## 1. Objetivo

Mantener una copia local, auditable y actualizable del Clasificador de
Actividades Economicas de ARCA, CLAE Formulario 883.

El catalogo local sera la unica fuente permitida para vincular actividades
economicas con empresas en la siguiente etapa.

## 2. Fuente oficial

Fuente operativa:

`https://serviciosweb.afip.gob.ar/genericos/nomencladorActividades/index.aspx`

La pagina oficial permite consultar actividades por rubro, codigo o palabra
clave y ofrece la descarga del archivo completo.

La Resolucion General 3537 aprobo el CLAE Formulario 883.

La Resolucion General 5607 de noviembre de 2024 intento ampliar el
clasificador de 951 a 966 actividades, pero fue abrogada por la Resolucion
General 5612, vigente desde el 10/12/2024.

Por ese motivo, el ERP no incorpora manualmente los codigos de la norma
abrogada. Sincroniza el contenido que ARCA publica efectivamente en el
nomenclador oficial vigente.

## 3. Estrategia

No se consulta ARCA cada vez que un usuario abre un formulario.

Se mantiene un catalogo local porque:

- permite trabajar aunque ARCA no responda
- evita lentitud en cada seleccion
- conserva la descripcion usada historicamente
- permite detectar altas, cambios y bajas
- evita que el usuario escriba codigos libres

## 4. Modelos

### ActividadEconomica

Contiene:

- nomenclador
- codigo de seis digitos
- descripcion oficial
- estado activo
- URL de la fuente
- hash SHA-256 de la descarga
- fecha de primera importacion
- fecha de ultima sincronizacion

La combinacion nomenclador y codigo es unica.

### ImportacionCatalogoActividad

Registra cada sincronizacion exitosa:

- fuente
- nombre del archivo
- SHA-256
- total de registros
- creados
- actualizados
- reactivados
- desactivados
- fecha de importacion

## 5. Actualizacion

Comando:

`python manage.py actualizar_catalogo_clae --archivo ARCHIVO_HTML`

El archivo debe ser una copia descargada desde la fuente oficial.

El comando:

1. Verifica tamano minimo.
2. Extrae codigos de seis digitos y descripciones.
3. Exige una cantidad minima de registros.
4. Comprueba codigos testigo conocidos.
5. Crea o actualiza actividades.
6. Reactiva codigos que reaparecen.
7. Desactiva codigos ausentes.
8. Nunca elimina registros.
9. Registra una auditoria de importacion.

## 6. Seguridad

Una descarga parcial no debe reemplazar el catalogo.

La importacion exige por defecto al menos 900 actividades y la presencia de
los codigos testigo:

- 259993
- 259999
- 464330
- 477330
- 620100

Estos codigos no definen una version juridica. Funcionan como controles de
integridad de la descarga.

## 7. Historial

Cuando ARCA retira un codigo, el ERP lo marca inactivo.

No se elimina porque futuras relaciones historicas de empresas deben seguir
mostrando el codigo y la descripcion utilizados en su momento.

## 8. Proxima etapa

La siguiente tarea incorporara:

- `EmpresaActividad`
- actividad principal y secundarias
- fechas de vigencia
- tarjeta dentro de Configuracion de empresa
- listado, alta, edicion e inactivacion
- seleccion exclusiva desde `ActividadEconomica`
