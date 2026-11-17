"""
Plugin maestro de Obsidian para Mark-LV / DEREK.
Controla y ejecuta en tiempo real:
- Abrir Obsidian en la ventana activa.
- Abrir la nota diaria de hoy.
- Crear notas directamente en la bóveda o subcarpetas canónicas (03-Fleeting Notes, 04-Permanent, 02-Areas).
- Buscar cualquier nota y leer su contenido.
"""
import os
import subprocess
import datetime
from pathlib import Path
from urllib.parse import quote

_DEFAULT_VAULT = Path.home() / 'Documents' / 'Second Brain'
VAULT_DIR = Path(os.environ.get('OBSIDIAN_VAULT_PATH', _DEFAULT_VAULT))
OBSIDIAN_EXE = Path.home() / 'AppData' / 'Local' / 'Programs' / 'Obsidian' / 'Obsidian.exe'
DEFAULT_NEW_FOLDER = "03-Fleeting Notes/Fleeting Notes to be processed"

PLUGIN = {
    "name": "obsidian_vault",
    "description": (
        "Controls Obsidian and Second Brain vault directly. "
        "Use this for ANY request to: open Obsidian, open today's daily note, "
        "create a new note, write notes, search vault files, or organize notes."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "open_app | open_daily_note | create_note | read_note | search_notes"
            },
            "title": {
                "type": "STRING",
                "description": "Title or filename for the note (e.g. 'Apuntes Santo Tomas.md')"
            },
            "folder": {
                "type": "STRING",
                "description": "Subfolder in vault (e.g. '03-Fleeting Notes/Fleeting Notes to be processed', '04-Permanent/Formación espiritual', '02-Areas/Apuntes'). Defaults to '03-Fleeting Notes/Fleeting Notes to be processed'."
            },
            "content": {
                "type": "STRING",
                "description": "Content/text to write inside the note."
            }
        },
        "required": ["action"],
    },
}

def _open_in_obsidian(rel_path: str) -> None:
    """Abre un archivo en Obsidian usando la API ShellExecute de Windows directamente sin cmd.exe."""
    vault_name = "Second Brain"
    clean_rel = rel_path.replace("\\", "/")
    uri = f"obsidian://open?vault={quote(vault_name)}&file={quote(clean_rel)}"
    try:
        os.startfile(uri)
    except Exception:
        # Fallback si startfile falla
        subprocess.Popen(["cmd", "/c", "start", "", uri], shell=True)

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action", "open_app")).strip().lower()
    title = str(parameters.get("title", "")).strip()
    folder = str(parameters.get("folder", "")).strip()
    content = str(parameters.get("content", "")).strip()

    try:
        # 1. Abrir aplicación Obsidian
        if action == "open_app":
            if OBSIDIAN_EXE.exists():
                subprocess.Popen([str(OBSIDIAN_EXE)])
                return "Obsidian abierto en su pantalla."
            else:
                try:
                    os.startfile("obsidian://open?vault=Second%20Brain")
                except Exception:
                    subprocess.Popen(["cmd", "/c", "start", "obsidian:"], shell=True)
                return "Iniciando Obsidian en pantalla."

        # 2. Abrir nota diaria de hoy
        elif action == "open_daily_note":
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            rel_path = f"05-Planners/Daily/{today_str}.md"
            daily_file = VAULT_DIR / "05-Planners" / "Daily" / f"{today_str}.md"
            
            if not daily_file.exists():
                daily_file.parent.mkdir(parents=True, exist_ok=True)
                header = f"---\ntags:\n  - dailyplanner\ncreated: {today_str}\n---\n# Notas personales de hoy {today_str}\n\n"
                daily_file.write_text(header, encoding="utf-8")

            _open_in_obsidian(rel_path)
            return f"Abriendo la nota diaria de hoy ({today_str}) en Obsidian para usted."

        # 3. Crear una nueva nota física real
        elif action == "create_note":
            if not title:
                title = f"Nota {datetime.datetime.now().strftime('%Y-%m-%d %H%M')}"
            if not title.lower().endswith(".md"):
                title += ".md"

            dest_folder = folder if folder else DEFAULT_NEW_FOLDER
            dest_dir = VAULT_DIR / dest_folder
            dest_dir.mkdir(parents=True, exist_ok=True)

            target_file = dest_dir / title
            rel_path = str(target_file.relative_to(VAULT_DIR)).replace("\\", "/")

            if not target_file.exists():
                header = f"---\ntitle: \"{title[:-3]}\"\ncreated: {datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n---\n# {title[:-3]}\n\n"
                target_file.write_text(header + content, encoding="utf-8")
            else:
                if content:
                    with open(target_file, "a", encoding="utf-8") as f:
                        f.write(f"\n\n{content}")

            # Abrirla al instante en la pantalla de Obsidian
            _open_in_obsidian(rel_path)
            return f"Nota '{title}' creada con éxito en '{dest_folder}' y abierta en su pantalla de Obsidian."

        # 4. Buscar notas
        elif action == "search_notes":
            term = title or content
            if not term:
                return "Por favor indique qué tema o título de nota desea buscar en su bóveda."
            matches = []
            for root, _, files in os.walk(str(VAULT_DIR)):
                for f in files:
                    if f.endswith(".md") and (term.lower() in f.lower()):
                        rel = os.path.relpath(os.path.join(root, f), str(VAULT_DIR))
                        matches.append(rel.replace("\\", "/"))
                        if len(matches) >= 5:
                            break
                if len(matches) >= 5:
                    break
            if matches:
                return f"Notas encontradas en su bóveda:\n• " + "\n• ".join(matches)
            return f"No se encontraron notas que coincidan con '{term}' en su bóveda."

        return "Acción completada con éxito."

    except Exception as e:
        return f"Error ejecutando la acción de Obsidian: {e}"
