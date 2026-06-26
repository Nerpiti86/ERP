from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
import webbrowser


HOST = "127.0.0.1"


@dataclass(frozen=True)
class ConfiguracionLanzador:
    nombre: str
    slug: str
    modo: str
    settings_module: str
    puerto: int
    ruta_inicial: str

    @property
    def url_base(self):
        return f"http://{HOST}:{self.puerto}"

    @property
    def url_estado(self):
        return f"{self.url_base}/_estado/"

    @property
    def url_inicial(self):
        return f"{self.url_base}{self.ruta_inicial}"


def _raiz_proyecto():
    raiz = Path(__file__).resolve().parent
    if not (raiz / "manage.py").is_file():
        raise RuntimeError("No se encontró manage.py junto al lanzador.")
    return raiz


def _python_virtual(raiz):
    candidatos = (
        raiz / ".venv" / "Scripts" / "python.exe",
        raiz / ".venv" / "bin" / "python",
    )
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    raise RuntimeError("No se encontró el intérprete de .venv.")


def _registrar(raiz, slug, mensaje):
    logs = raiz / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().astimezone().isoformat(timespec="seconds")
    with (logs / f"lanzador_{slug}.log").open(
        "a",
        encoding="utf-8",
    ) as archivo:
        archivo.write(f"[{marca}] {mensaje}\n")


def _mostrar_error(titulo, mensaje):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, mensaje, titulo, 0x10)
    except Exception:
        pass


def _consultar_modo(url_estado, timeout=0.8):
    solicitud = Request(url_estado, headers={"Accept": "application/json"})
    try:
        with urlopen(solicitud, timeout=timeout) as respuesta:
            contenido = respuesta.read().decode("utf-8")
    except (OSError, TimeoutError, URLError):
        return None

    try:
        datos = json.loads(contenido)
    except (TypeError, ValueError):
        return ""

    if datos.get("estado") != "ok":
        return ""
    return str(datos.get("aplicacion", ""))


def _puerto_en_uso(puerto):
    try:
        with socket.create_connection((HOST, puerto), timeout=0.4):
            return True
    except OSError:
        return False


def _iniciar_servidor(configuracion, raiz, python):
    logs = raiz / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    salida = (logs / f"servidor_{configuracion.slug}.log").open(
        "a",
        encoding="utf-8",
    )

    entorno = os.environ.copy()
    entorno["DJANGO_SETTINGS_MODULE"] = configuracion.settings_module
    entorno["PYTHONUNBUFFERED"] = "1"

    creationflags = 0
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | 0x00000008
        )

    try:
        return subprocess.Popen(
            [
                str(python),
                str(raiz / "manage.py"),
                "runserver",
                "--noreload",
                f"{HOST}:{configuracion.puerto}",
            ],
            cwd=raiz,
            env=entorno,
            stdin=subprocess.DEVNULL,
            stdout=salida,
            stderr=subprocess.STDOUT,
            close_fds=True,
            creationflags=creationflags,
        )
    finally:
        salida.close()


def abrir_aplicacion(configuracion):
    titulo = f"NeriSoft {configuracion.nombre}"
    try:
        raiz = _raiz_proyecto()
        python = _python_virtual(raiz)
        _registrar(
            raiz,
            configuracion.slug,
            f"Solicitud de apertura en {configuracion.url_inicial}.",
        )

        modo_actual = _consultar_modo(configuracion.url_estado)
        if modo_actual is not None:
            if modo_actual != configuracion.modo:
                raise RuntimeError(
                    f"El puerto {configuracion.puerto} pertenece a "
                    f"'{modo_actual or 'una aplicación desconocida'}'."
                )
        else:
            if _puerto_en_uso(configuracion.puerto):
                raise RuntimeError(
                    f"El puerto {configuracion.puerto} está ocupado por "
                    "otro proceso."
                )

            proceso = _iniciar_servidor(configuracion, raiz, python)
            _registrar(
                raiz,
                configuracion.slug,
                f"Servidor iniciado con PID {proceso.pid}.",
            )

            for _ in range(80):
                if proceso.poll() is not None:
                    raise RuntimeError(
                        "El servidor se cerró durante el inicio. "
                        f"Revisá logs/servidor_{configuracion.slug}.log."
                    )
                modo_actual = _consultar_modo(
                    configuracion.url_estado,
                    timeout=0.5,
                )
                if modo_actual is not None:
                    break
                time.sleep(0.25)
            else:
                raise RuntimeError(
                    "El servidor no respondió. "
                    f"Revisá logs/servidor_{configuracion.slug}.log."
                )

            if modo_actual != configuracion.modo:
                raise RuntimeError(
                    "El servidor respondió con una identidad incorrecta."
                )

        if not webbrowser.open_new_tab(configuracion.url_inicial):
            raise RuntimeError(
                "El servidor está activo, pero no se pudo abrir el navegador."
            )

        _registrar(
            raiz,
            configuracion.slug,
            "Aplicación abierta correctamente.",
        )
        return 0
    except Exception as error:
        mensaje = str(error)
        try:
            raiz = _raiz_proyecto()
            _registrar(raiz, configuracion.slug, f"ERROR: {mensaje}")
        except Exception:
            pass
        _mostrar_error(titulo, mensaje)
        return 1
