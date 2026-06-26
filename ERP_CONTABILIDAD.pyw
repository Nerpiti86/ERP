from launcher_erp import ConfiguracionLanzador, abrir_aplicacion


CONFIGURACION = ConfiguracionLanzador(
    nombre="Contabilidad",
    slug="contabilidad",
    modo="contabilidad",
    settings_module="config.settings_contabilidad",
    puerto=8002,
    ruta_inicial="/contabilidad/",
)


if __name__ == "__main__":
    raise SystemExit(abrir_aplicacion(CONFIGURACION))
