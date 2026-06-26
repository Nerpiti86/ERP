# Doble entrada local: Gestión y Contabilidad

## Decisión

El ERP continúa siendo un monolito modular con una sola base PostgreSQL, un
solo repositorio y un solo historial de migraciones.

Se agregan dos superficies locales:

```text
ERP_GESTION.pyw      → http://127.0.0.1:8001/
ERP_CONTABILIDAD.pyw → http://127.0.0.1:8002/
```

## Componentes compartidos

- usuarios y autenticación;
- empresas y sucursales;
- modelos y migraciones;
- permisos funcionales;
- configuración de núcleo;
- auditoría;
- base PostgreSQL;
- entorno virtual.

## Modo Gestión

Utiliza `config.settings_gestion` y `config.urls_gestion`.

Publica autenticación, núcleo, terceros, ítems y administración técnica.
No publica `/contabilidad/`.

## Modo Contabilidad

Utiliza `config.settings_contabilidad` y `config.urls_contabilidad`.

Publica autenticación, núcleo, contabilidad y administración técnica.
No publica `/terceros/` ni `/items/`.

## Identidad, portada y navegación

Cada superficie presenta una identidad inequívoca en la marca superior y al
comienzo del título del navegador.

Gestión posee una portada con accesos reales a terceros, ítems, categorías y
marcas. Contabilidad posee una portada con acceso al Plan de cuentas. Cada menú
publica únicamente las opciones de su dominio.

El modo integrado conserva los menús agrupados y la portada general del núcleo.
Ambos lanzadores abren `/`.

## Sesiones

Las cookies de sesión y CSRF tienen nombres diferentes, por lo que ambas
aplicaciones pueden abrirse simultáneamente.

## Lanzadores

`launcher_erp.py` localiza el proyecto y `.venv`, consulta `/_estado/`, valida
la identidad del servidor, rechaza puertos ocupados, inicia Django sin consola,
registra actividad en `logs/` y abre el navegador.

## Modo integrado

El arranque tradicional sigue disponible:

```bash
.venv/Scripts/python.exe manage.py runserver
```

## Seguridad

La separación por URLconf complementa, pero no reemplaza, los permisos backend,
la autenticación y el aislamiento por empresa.

## Pendiente

- accesos directos de Windows;
- empaquetado `.exe`;
- servidor local endurecido para instalaciones productivas.
