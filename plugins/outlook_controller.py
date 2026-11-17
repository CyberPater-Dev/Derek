import os
import datetime
from pathlib import Path

PLUGIN = {
    "name": "outlook_controller",
    "description": (
        "Control total de Microsoft Outlook. Permite leer correos no leídos, recientes, enviar correos, "
        "consultar la agenda/calendario en tiempo real (reuniones de hoy, próxima junta) "
        "y sincronizar automáticamente los eventos del día dentro de la nota diaria de Obsidian (05-Planners/Daily)."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "get_calendar | next_meeting | sync_calendar_to_obsidian | get_unread | get_recent | send_email | open_outlook"
            },
            "count": {
                "type": "NUMBER",
                "description": "Cantidad de elementos a consultar (default 5)"
            },
            "target_date": {
                "type": "STRING",
                "description": "Fecha a consultar en formato 'YYYY-MM-DD' o 'today' (default: today)"
            },
            "to": {
                "type": "STRING",
                "description": "Destinatario de correo"
            },
            "subject": {
                "type": "STRING",
                "description": "Asunto de correo"
            },
            "body": {
                "type": "STRING",
                "description": "Cuerpo del correo"
            }
        },
        "required": ["action"]
    }
}

_DEFAULT_VAULT = Path.home() / "Documents" / "Second Brain"
VAULT_PATH = Path(os.environ.get("OBSIDIAN_VAULT_PATH", _DEFAULT_VAULT))
VAULT_DAILY_DIR = VAULT_PATH / "05-Planners" / "Daily"

def _get_app():
    import win32com.client
    try:
        return win32com.client.GetActiveObject("Outlook.Application")
    except Exception:
        return win32com.client.Dispatch("Outlook.Application")

def _make_naive(dt):
    if dt is not None and getattr(dt, "tzinfo", None) is not None:
        return dt.replace(tzinfo=None)
    return dt

def _fetch_calendar_events(target_date: datetime.date) -> list[dict]:
    app = _get_app()
    ns = app.GetNamespace("MAPI")
    cal = ns.GetDefaultFolder(9)  # olFolderCalendar
    items = cal.Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")

    start_str = target_date.strftime("%m/%d/%Y 00:00")
    end_date = target_date + datetime.timedelta(days=1)
    end_str = end_date.strftime("%m/%d/%Y 00:00")

    filter_str = f"[Start] >= '{start_str}' AND [Start] < '{end_str}'"
    restricted = items.Restrict(filter_str)

    events = []
    for item in restricted:
        try:
            start_dt = _make_naive(item.Start)
            end_dt = _make_naive(item.End)
            subject = getattr(item, "Subject", "Sin título") or "Sin título"
            location = getattr(item, "Location", "") or ""
            events.append({
                "start": start_dt,
                "end": end_dt,
                "start_str": start_dt.strftime("%H:%M"),
                "end_str": end_dt.strftime("%H:%M"),
                "subject": subject.strip(),
                "location": location.strip()
            })
        except Exception:
            continue

    events.sort(key=lambda x: x["start"])
    return events

def _sync_events_to_obsidian(target_date: datetime.date, events: list[dict]) -> str:
    VAULT_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date.strftime('%Y-%m-%d')}.md"
    file_path = VAULT_DAILY_DIR / filename

    agenda_lines = ["## 📆 Agenda del Día (Outlook)"]
    if not events:
        agenda_lines.append("- *(No hay reuniones programadas para este día)*")
    else:
        for ev in events:
            loc_str = f" — *Lugar:* {ev['location']}" if ev['location'] else ""
            agenda_lines.append(f"- [ ] **{ev['start_str']} - {ev['end_str']}** {ev['subject']}{loc_str}")
    agenda_block = "\n".join(agenda_lines) + "\n"

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        header_tag = "## 📆 Agenda del Día (Outlook)"
        if header_tag in content:
            import re
            pattern = r"## 📆 Agenda del Día \(Outlook\).*?(?=\n## |\n# |\Z)"
            new_content = re.sub(pattern, agenda_block.strip(), content, flags=re.DOTALL)
        else:
            if "## 📅 Daily Questions" in content:
                new_content = content.replace("## 📅 Daily Questions", f"{agenda_block}\n## 📅 Daily Questions")
            else:
                new_content = content + f"\n\n{agenda_block}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Agenda sincronizada con éxito en {filename}"
    else:
        header = f"""---
tags:
  - dailyplanner
created: {target_date.strftime('%Y-%m-%d')}
modified: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# Notas personales de hoy {target_date.strftime('%Y-%m-%d')}

{agenda_block}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header)
        return f"Nota creada y agenda sincronizada en {filename}"

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action", "get_calendar")).lower().strip()
    count = int(parameters.get("count") or 5)
    to = str(parameters.get("to", "")).strip()
    subject = str(parameters.get("subject", "")).strip()
    body = str(parameters.get("body", "")).strip()
    t_date_raw = str(parameters.get("target_date", "today")).strip().lower()

    if t_date_raw in ("today", "hoy", ""):
        target_date = datetime.date.today()
    elif t_date_raw in ("tomorrow", "mañana"):
        target_date = datetime.date.today() + datetime.timedelta(days=1)
    else:
        try:
            target_date = datetime.datetime.strptime(t_date_raw, "%Y-%m-%d").date()
        except Exception:
            target_date = datetime.date.today()

    try:
        if action == "open_outlook":
            import subprocess
            subprocess.Popen([r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"])
            return "Outlook iniciado en pantalla."

        # ── ACCIONES DE CALENDARIO ──────────────────────────────────────────
        if action in ("get_calendar", "get_today_schedule"):
            events = _fetch_calendar_events(target_date)
            date_str = target_date.strftime("%Y-%m-%d")
            if not events:
                return f"No tiene eventos ni reuniones programadas en Outlook para {date_str}."

            out_lines = [f"Agenda de Outlook para {date_str} ({len(events)} eventos):"]
            for ev in events:
                loc = f" ({ev['location']})" if ev["location"] else ""
                out_lines.append(f"• {ev['start_str']} - {ev['end_str']}: {ev['subject']}{loc}")
            
            res = "\n".join(out_lines)
            if player and hasattr(player, "show_content"):
                player.show_content("OUTLOOK CALENDAR", res)
            return res

        elif action == "next_meeting":
            now = datetime.datetime.now()
            today_events = _fetch_calendar_events(now.date())
            upcoming = [e for e in today_events if e["end"] > now]
            if not upcoming:
                return "No tiene más reuniones pendientes para el resto del día de hoy."
            
            next_ev = upcoming[0]
            loc = f" en {next_ev['location']}" if next_ev['location'] else ""
            res = f"Su próxima cita es: '{next_ev['subject']}' de {next_ev['start_str']} a {next_ev['end_str']}{loc}."
            if player and hasattr(player, "show_content"):
                player.show_content("PRÓXIMA REUNIÓN", res)
            return res

        elif action == "sync_calendar_to_obsidian":
            events = _fetch_calendar_events(target_date)
            status = _sync_events_to_obsidian(target_date, events)
            return f"{status} ({len(events)} evento(s) de Outlook registrados)."

        # ── ACCIONES DE CORREO ──────────────────────────────────────────────
        app = _get_app()
        namespace = app.GetNamespace("MAPI")
        inbox = namespace.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        if action == "get_unread":
            unread = messages.Restrict("[Unread] = true")
            results = []
            idx = 0
            for msg in unread:
                if idx >= count:
                    break
                try:
                    sender = getattr(msg, "SenderName", "Desconocido")
                    s = getattr(msg, "Subject", "Sin asunto")
                    results.append(f"- {sender}: {s}")
                    idx += 1
                except Exception:
                    continue
            if not results:
                return "No hay correos no leídos en Outlook."
            return f"{len(results)} correo(s) sin leer:\n" + "\n".join(results)

        elif action == "get_recent":
            results = []
            idx = 0
            for msg in messages:
                if idx >= count:
                    break
                try:
                    sender = getattr(msg, "SenderName", "Desconocido")
                    s = getattr(msg, "Subject", "Sin asunto")
                    results.append(f"- {sender}: {s}")
                    idx += 1
                except Exception:
                    continue
            if not results:
                return "La bandeja de entrada está vacía."
            return f"{len(results)} correo(s) recientes:\n" + "\n".join(results)

        elif action == "send_email":
            if not to:
                return "Por favor especifique la dirección de correo destinataria."
            mail = app.CreateItem(0)
            mail.To = to
            mail.Subject = subject or "Sin asunto"
            mail.Body = body or ""
            mail.Send()
            return f"Correo enviado a {to}."

        return "Acción completada con éxito."
    except Exception as e:
        return f"Error en Outlook: {e}"
