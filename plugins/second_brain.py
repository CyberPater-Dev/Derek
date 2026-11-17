import os
import glob
import datetime
from pathlib import Path

_DEFAULT_VAULT = Path.home() / 'Documents' / 'Second Brain'
VAULT_PATH = str(os.environ.get('OBSIDIAN_VAULT_PATH', _DEFAULT_VAULT))

PLUGIN = {
    "name": "second_brain",
    "description": (
        "Accede, busca o agrega tareas a la bóveda Obsidian Second Brain del usuario. "
        "Use esta herramienta para consultar el plan diario, notas de Derecho Canónico, teología, "
        "formación espiritual, Santo Tomás de Aquino, o agregar tareas a sus notas."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "get_daily_planner | search_notes | add_task"
            },
            "query": {
                "type": "STRING",
                "description": "Tema a buscar o descripción de la tarea a agregar."
            }
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action", "get_daily_planner")).strip().lower()
    query = str(parameters.get("query", "")).strip()

    try:
        if action == "get_daily_planner":
            daily_dir = os.path.join(VAULT_PATH, "05-Planners", "Daily")
            if not os.path.exists(daily_dir):
                return "no encontré el directorio de planners diarios en su Second Brain."
            
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            today_file = os.path.join(daily_dir, f"{today_str}.md")
            
            target_file = today_file if os.path.exists(today_file) else None
            if not target_file:
                files = glob.glob(os.path.join(daily_dir, "*.md"))
                if files:
                    target_file = max(files, key=os.path.getmtime)
            
            if target_file:
                with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                fname = os.path.basename(target_file)
                # Extraer tareas y agenda
                lines = [l.strip() for l in content.splitlines() if l.strip().startswith("- [ ]") or l.strip().startswith("•")]
                summary = "\n".join(lines[:8]) if lines else content[:350]
                return f"En su planner diario ({fname}):\n{summary}"
            return "No se encontraron notas de planner diario en su bóveda."

        elif action == "add_task":
            if not query:
                return "por favor especifique qué tarea desea que agregue a su planner."
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            daily_dir = os.path.join(VAULT_PATH, "05-Planners", "Daily")
            os.makedirs(daily_dir, exist_ok=True)
            daily_file = os.path.join(daily_dir, f"{today_str}.md")
            
            if not os.path.exists(daily_file):
                header = f"---\ntags:\n  - dailyplanner\ncreated: {today_str}\n---\n# Notas personales de hoy {today_str}\n\n"
                with open(daily_file, "w", encoding="utf-8") as f:
                    f.write(header)

            new_item = f"\n- [ ] {query} *(Registrado por Derek: {datetime.datetime.now().strftime('%H:%M')})*\n"
            with open(daily_file, "a", encoding="utf-8") as f:
                f.write(new_item)
            return f"Tarea '{query}' registrada exitosamente en su planner de hoy ({today_str})."

        elif action == "search_notes":
            if not query:
                return "Por favor indique qué tema o nota desea buscar en su bóveda."
            matches = []
            for root, _, files in os.walk(VAULT_PATH):
                for f in files:
                    if f.endswith(".md"):
                        path = os.path.join(root, f)
                        try:
                            with open(path, "r", encoding="utf-8", errors="ignore") as fc:
                                txt = fc.read()
                                if query.lower() in f.lower() or query.lower() in txt.lower():
                                    snippet = txt[:250].replace("\n", " ").strip()
                                    matches.append(f"• **{f[:-3]}**: {snippet}...")
                                    if len(matches) >= 3:
                                        break
                        except Exception:
                            pass
                if len(matches) >= 3:
                    break
            if matches:
                return f"Notas encontradas en su bóveda sobre '{query}':\n" + "\n".join(matches)
            return f"No encontré notas relacionadas con '{query}' en su bóveda."

        return "Acción completada con éxito."

    except Exception as e:
        return f"Error accediendo a Second Brain: {e}"
