"""Lanzador todo-en-uno: prepara lo que falte y abre la web de estudio.

Lo usan Iniciar.bat (Windows) e iniciar.sh (Mac/Linux); también vale `python iniciar.py`.
Solo usa la librería estándar de Python, así que funciona antes de instalar nada.

    python iniciar.py              # prepara todo, arranca y abre el navegador
    python iniciar.py --sin-ia     # sin Ollama (no hay buscador con IA, el resto funciona)
    python iniciar.py --no-abrir   # no abre el navegador
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
MOTOR = ROOT / "estudio-profundo" / "backend"
LOGS = ROOT / "backend" / "data" / "logs"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODELOS = [
    os.environ.get("UNED_EMBED_MODEL", "nomic-embed-text"),
    os.environ.get("UNED_LLM_MODEL", "qwen2.5:7b-instruct"),
]
URL_WEB = "http://localhost:8000"


def paso(texto: str) -> None:
    print(f"\n==> {texto}", flush=True)


def ejecutar(args: list, **kw) -> int:
    return subprocess.run([str(a) for a in args], **kw).returncode


def responde(url: str, segundos: int = 1) -> bool:
    try:
        urllib.request.urlopen(url, timeout=segundos)
        return True
    except Exception:
        return False


def esperar(url: str, segundos: int = 60) -> bool:
    for _ in range(segundos):
        if responde(url, 2):
            return True
        time.sleep(1)
    return False


def preparar_entorno() -> None:
    paso("Preparando el programa (la primera vez tarda unos minutos)")
    if not PY.exists():
        print("Creando entorno de Python...")
        if ejecutar([sys.executable, "-m", "venv", VENV]) != 0:
            sys.exit("No se pudo crear el entorno de Python. ¿Instalaste Python 3.12 o superior?")
    reqs = ROOT / "backend" / "requirements.txt"
    marca = VENV / ".requirements.sha"
    huella = hashlib.sha256(reqs.read_bytes()).hexdigest()
    if marca.exists() and marca.read_text() == huella:
        print("Dependencias al día.")
        return
    print("Instalando dependencias: puede tardar 5-10 minutos y parecer parado. No cierres la ventana...")
    ejecutar([PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    if ejecutar([PY, "-m", "pip", "install", "--quiet", "-r", reqs]) != 0:
        sys.exit("Falló la instalación de dependencias. ¿Tienes conexión a internet?")
    marca.write_text(huella)


def arrancar_ollama() -> bool:
    paso("Comprobando Ollama (la IA que responde a tus preguntas)")
    if responde(f"{OLLAMA}/api/tags"):
        print("Ollama ya está en marcha.")
        return True
    exe = shutil.which("ollama")
    if not exe and os.name == "nt":
        candidato = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Ollama/ollama.exe"
        exe = str(candidato) if candidato.exists() else None
    if not exe:
        print("AVISO: Ollama no está instalado. Descárgalo de https://ollama.com y vuelve a abrir este programa.")
        print("       Mientras tanto la web funciona, pero sin el buscador con IA.")
        return False
    print("Arrancando Ollama...")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    if not esperar(f"{OLLAMA}/api/tags", 30):
        print("AVISO: Ollama no responde. Ábrelo a mano y vuelve a lanzar este programa.")
        return False
    return True


def descargar_modelos() -> bool:
    import json

    instalados = json.load(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=10))["models"]
    nombres = {m["name"] for m in instalados} | {m["name"].removesuffix(":latest") for m in instalados}
    faltan = [m for m in MODELOS if m not in nombres]
    if faltan:
        paso(f"Descargando modelos de IA: {', '.join(faltan)} (unos 5 GB la primera vez, ¡paciencia!)")
    for modelo in faltan:
        if ejecutar([shutil.which("ollama") or "ollama", "pull", modelo]) != 0:
            print(f"AVISO: no se pudo descargar {modelo}. El buscador con IA no funcionará.")
            return False
    return True


def indexar_documentos() -> None:
    paso("Indexando los documentos para el buscador (solo tarda mucho la primera vez)")
    if ejecutar([PY, "-m", "backend.app.rag.ingest"], cwd=ROOT) != 0:
        print("AVISO: no se pudo indexar. Se reintentará la próxima vez.")


def cargar_contenido_de_estudio() -> None:
    paso("Cargando las fichas y preguntas de repaso")
    if ejecutar([PY, "scripts/seed.py"], cwd=MOTOR) != 0:
        print("AVISO: no se pudo cargar el contenido de repaso.")


def lanzar(nombre: str, args: list, cwd: Path, health: str, procesos: list) -> None:
    if responde(health):
        print(f"{nombre}: ya estaba en marcha.")
        return
    LOGS.mkdir(parents=True, exist_ok=True)
    log = open(LOGS / f"{nombre}.log", "ab")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    procesos.append(subprocess.Popen([str(a) for a in args], cwd=cwd, stdout=log, stderr=log, creationflags=flags))
    if esperar(health):
        print(f"{nombre}: listo.")
    else:
        print(f"AVISO: {nombre} no responde. Mira el registro en {LOGS / (nombre + '.log')}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sin_ia = "--sin-ia" in sys.argv
    if sys.version_info < (3, 11):
        sys.exit("Hace falta Python 3.11 o superior (https://www.python.org/downloads/).")
    preparar_entorno()
    if not sin_ia and arrancar_ollama() and descargar_modelos():
        indexar_documentos()
    cargar_contenido_de_estudio()

    paso("Arrancando la web")
    procesos: list = []
    lanzar("app", [PY, "-m", "uvicorn", "backend.app.main:app", "--port", "8000"], ROOT,
           f"{URL_WEB}/api/rag/status", procesos)
    lanzar("motor-estudio", [PY, "-m", "uvicorn", "app.main:app", "--port", "8011"], MOTOR,
           "http://localhost:8011/api/health", procesos)

    print(f"\n✔ Todo listo: {URL_WEB}")
    print("  NO cierres esta ventana mientras estudias. Para apagar todo, ciérrala o pulsa Ctrl+C.")
    if "--no-abrir" not in sys.argv:
        webbrowser.open(URL_WEB)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procesos:
            p.terminate()


if __name__ == "__main__":
    main()
