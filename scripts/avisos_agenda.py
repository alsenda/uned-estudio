"""Avisos de la agenda: notificaciones de Windows para eventos y tareas próximos.

Lo ejecuta el Programador de tareas cada 5 minutos (ver registrar-avisos-agenda.ps1), sin ventana,
con `pythonw`. Lee `agenda/events` y `agenda/todos` (los mismos ficheros que la sección Calendario).

    python scripts/avisos_agenda.py             # envía lo que toque ahora
    python scripts/avisos_agenda.py --simular   # solo imprime lo que enviaría
    python scripts/avisos_agenda.py --prueba    # lanza una notificación de prueba
    python scripts/avisos_agenda.py --simular --ahora=2026-10-06T17:40   # ver qué avisaría a esa hora

Cuándo avisa (por defecto, según el tipo; se puede cambiar por evento con `remind: [minutos...]`
en la cabecera del fichero, solo para eventos con hora):

  con hora   tutoria 30 min antes · reunion/estudio/otro 15 min · entrega 1 día y 1 h · examen 7 días, 1 día y 1 h
  sin hora   08:00 del día anterior (entregas, exámenes y tareas) · exámenes: también 7 días antes
  cada día  a las 08:00, un resumen único de todo lo de hoy (eventos con hora, de todo el día y tareas que vencen)

Un aviso solo se envía si su hora ya ha pasado hace poco (hasta 2 h tras la hora prevista, o 12 h
si es de todo el día) y el evento no ha empezado; así, si el PC estaba apagado, no llegan avisos
viejos. Lo ya enviado se anota en backend/data/avisos_enviados.json.
"""

import base64
import json
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from backend.app.agenda import store  # noqa: E402
from backend.app.config import DATA_DIR  # noqa: E402

ESTADO = DATA_DIR / "avisos_enviados.json"
CON_HORA = {"tutoria": [30], "reunion": [15], "estudio": [15], "otro": [15], "entrega": [1440, 60], "examen": [10080, 1440, 60]}
SIN_HORA_DIAS_ANTES = {"entrega": [0, 1], "examen": [0, 1, 7]}  # 08:00 de cada uno de esos días
HORA_AVISO_DIA = time(8, 0)
RETRASO_MAX = timedelta(hours=2)
RETRASO_MAX_DIA = timedelta(hours=12)
ASIGNATURAS = {"71031010": "Cálculo", "71031027": "Álgebra", "71031033": "Lógica", "7103104": "Computadores"}

CREATE_NO_WINDOW = 0x08000000
TOAST_PS = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$t = $tpl.GetElementsByTagName('text')
$t.Item(0).AppendChild($tpl.CreateTextNode($env:AVISO_TITULO)) | Out-Null
$t.Item(1).AppendChild($tpl.CreateTextNode($env:AVISO_TEXTO)) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($tpl)
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
"""


def toast(titulo: str, texto: str) -> None:
    import os

    codigo = base64.b64encode(TOAST_PS.encode("utf-16-le")).decode()
    env = dict(os.environ, AVISO_TITULO=titulo, AVISO_TEXTO=texto)
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", codigo],
        env=env,
        creationflags=CREATE_NO_WINDOW,
        timeout=30,
        check=False,
    )


def hora_de(valor) -> time | None:
    """`time` puede llegar como '10:00' o, si YAML lo interpretó mal, como minutos (int)."""
    if valor in (None, ""):
        return None
    if isinstance(valor, int):
        return time(valor // 60 % 24, valor % 60)
    try:
        h, m = str(valor).split(":")[:2]
        return time(int(h), int(m))
    except ValueError:
        return None


def asignatura_corta(subject) -> str:
    for codigo, nombre in ASIGNATURAS.items():
        if str(subject or "").startswith(codigo):
            return nombre
    return ""


def lugar_corto(location) -> str:
    """'UNED Cádiz, Plaza San Antonio 2 — Aula 1.1' -> 'UNED Cádiz · Aula 1.1' (lo que cabe en el aviso)."""
    if not location:
        return ""
    sitio, _, detalle = str(location).partition("—")
    return " · ".join(p.strip() for p in (sitio.split(",")[0], detalle) if p.strip())


def cuando(delta: timedelta) -> str:
    minutos = round(delta.total_seconds() / 60)
    if minutos < 90:
        return f"En {max(minutos, 1)} min"
    if minutos < 24 * 60:
        return f"En {round(minutos / 60)} h"
    dias = round(minutos / 60 / 24)
    return "Mañana" if dias == 1 else f"En {dias} días"


def resumen_del_dia(ahora: datetime, eventos: list[dict]) -> dict | None:
    """Un solo aviso a las 08:00 con todo lo de hoy (eventos con hora ordenados, luego los de todo el día)."""
    hoy = ahora.date().isoformat()
    delhoy = [e for e in eventos if str(e.get("date")) == hoy]
    tareas = [t for t in store.list_todos(done=False) if str(t.get("due_date") or "") == hoy]
    if not (delhoy or tareas):
        return None
    if not (datetime.combine(ahora.date(), HORA_AVISO_DIA) <= ahora < datetime.combine(ahora.date(), time(20, 0))):
        return None
    con_hora = sorted((hora_de(e.get("time")), e["title"]) for e in delhoy if hora_de(e.get("time")))
    sin_hora = [e["title"] for e in delhoy if not hora_de(e.get("time"))]
    partes = [f"{h:%H:%M} {t}" for h, t in con_hora] + sin_hora + [f"Vence: {t['title']}" for t in tareas]
    texto = " · ".join(partes)
    if len(texto) > 190:
        texto = texto[:187] + "…"
    return {"clave": f"resumen|{hoy}", "titulo": f"Hoy en la UNED ({len(partes)})", "texto": texto,
            "fin": datetime.combine(ahora.date(), time(23, 59))}


def avisos_pendientes(ahora: datetime) -> list[dict]:
    pendientes = []
    eventos = store.list_events()
    # Un bloque de varios días seguidos con el mismo título (semana de exámenes) avisa con 7 días
    # de antelación solo el primer día; el resto de días avisa el día antes y el mismo día.
    dias_con_titulo = {(str(e.get("date")), e.get("title")) for e in eventos}

    resumen = resumen_del_dia(ahora, eventos)
    if resumen:
        pendientes.append(resumen)

    for ev in eventos:
        try:
            dia = date.fromisoformat(str(ev["date"]))
        except (KeyError, ValueError):
            continue
        tipo = ev.get("type") or "otro"
        hora = hora_de(ev.get("time"))
        extra = ev.get("subject")
        if hora:
            inicio = datetime.combine(dia, hora)
            offsets = ev.get("remind") or CON_HORA.get(tipo, [15])
            for minutos in offsets:
                disparo = inicio - timedelta(minutes=int(minutos))
                caduca = min(inicio + timedelta(minutes=5), disparo + RETRASO_MAX)
                if disparo <= ahora < caduca:
                    pendientes.append(
                        {"clave": f"{ev['id']}|{disparo:%Y-%m-%dT%H:%M}", "titulo": f"{cuando(inicio - ahora)} · {ev['title']}",
                         "texto": " · ".join(p for p in (f"{inicio:%H:%M}", asignatura_corta(extra), lugar_corto(ev.get("location"))) if p),
                         "fin": inicio}
                    )
        else:
            dia_anterior = ((dia - timedelta(days=1)).isoformat(), ev.get("title")) in dias_con_titulo
            for antes in SIN_HORA_DIAS_ANTES.get(tipo, [0]):
                if antes == 0 or (antes == 7 and dia_anterior):  # el mismo día lo cubre el resumen de las 08:00
                    continue
                disparo = datetime.combine(dia - timedelta(days=antes), HORA_AVISO_DIA)
                if disparo <= ahora < disparo + RETRASO_MAX_DIA and ahora.date() <= dia:
                    etiqueta = "Hoy" if antes == 0 else ("Mañana" if antes == 1 else f"En {antes} días")
                    pendientes.append(
                        {"clave": f"{ev['id']}|{disparo:%Y-%m-%dT%H:%M}", "titulo": f"{etiqueta} · {ev['title']}",
                         "texto": asignatura_corta(extra) or "Todo el día", "fin": datetime.combine(dia, time(23, 59))}
                    )

    for td in store.list_todos(done=False):
        if not td.get("due_date"):
            continue
        try:
            dia = date.fromisoformat(str(td["due_date"]))
        except ValueError:
            continue
        disparo = datetime.combine(dia - timedelta(days=1), HORA_AVISO_DIA)  # el mismo día, en el resumen
        if disparo <= ahora < disparo + RETRASO_MAX_DIA and ahora.date() <= dia:
            pendientes.append(
                {"clave": f"{td['id']}|{disparo:%Y-%m-%dT%H:%M}", "titulo": f"Mañana vence: {td['title']}",
                 "texto": asignatura_corta(td.get("subject")) or "Tarea", "fin": datetime.combine(dia, time(23, 59))}
            )
    return pendientes


def main() -> int:
    if "--prueba" in sys.argv:
        toast("UNED · prueba de avisos", "Si ves esto, las notificaciones de la agenda funcionan.")
        return 0

    ahora = datetime.now()
    for arg in sys.argv[1:]:
        if arg.startswith("--ahora="):  # solo para pruebas, junto con --simular
            ahora = datetime.fromisoformat(arg.split("=", 1)[1])
    enviados = {}
    if ESTADO.exists():
        try:
            enviados = json.loads(ESTADO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            enviados = {}

    nuevos = [a for a in avisos_pendientes(ahora) if a["clave"] not in enviados]
    simular = "--simular" in sys.argv
    for aviso in nuevos:
        print(("[simulado] " if simular else "") + f"{aviso['titulo']} — {aviso['texto']}")
        if not simular:
            toast(aviso["titulo"], aviso["texto"])
            enviados[aviso["clave"]] = ahora.isoformat(timespec="seconds")

    if not simular:
        limite = (ahora - timedelta(days=30)).isoformat()
        enviados = {k: v for k, v in enviados.items() if v >= limite}
        ESTADO.write_text(json.dumps(enviados, ensure_ascii=False, indent=1), encoding="utf-8")
    if simular and not nuevos:
        print("(nada que avisar ahora mismo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
