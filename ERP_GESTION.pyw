from launcher_erp import ConfiguracionLanzador, abrir_aplicacion


CONFIGURACION = ConfiguracionLanzador(
    nombre="Gestión",
    slug="gestion",
    modo="gestion",
    settings_module="config.settings_gestion",
    puerto=8001,
    ruta_inicial="/",
)


if __name__ == "__main__":
    raise SystemExit(abrir_aplicacion(CONFIGURACION))
