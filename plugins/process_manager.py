import psutil
import os
import time

PLUGIN = {
    "name": "process_manager",
    "description": (
        "Autonomous task, CPU load and process monitor. "
        "Call IMMEDIATELY when the user asks about CPU usage, why the computer is slow, "
        "what tasks are running, or asks to terminate a specific process."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "status (default summary of CPU, RAM and top processes) | top_cpu | top_ram | kill_process"
            },
            "process_name": {
                "type": "STRING",
                "description": "Process name or PID to kill (e.g. 'notepad', 'chrome', '14052')"
            },
            "limit": {
                "type": "NUMBER",
                "description": "Number of top processes to return (default 5)"
            }
        },
        "required": ["action"]
    }
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action", "status")).lower().strip()
    proc_query = str(parameters.get("process_name", "")).lower().strip()
    limit = int(parameters.get("limit") or 5)

    try:
        if action == "kill_process":
            if not proc_query:
                return "Por favor indique el nombre o PID del proceso a finalizar."
            killed = 0
            # If numeric PID
            if proc_query.isdigit():
                pid = int(proc_query)
                try:
                    p = psutil.Process(pid)
                    p_name = p.name()
                    p.terminate()
                    return f"Proceso {p_name} (PID {pid}) finalizado con exito."
                except Exception as e:
                    return f"Error al finalizar PID {pid}: {e}"

            for p in psutil.process_iter():
                try:
                    if proc_query in p.name().lower():
                        p.terminate()
                        killed += 1
                except Exception:
                    continue
            return f"Se han cerrado {killed} instancia(s) de '{proc_query}'."

        # Status / top_cpu / top_ram
        sys_cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()

        # Collect processes
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                info = p.info
                info['cpu'] = p.cpu_percent(interval=None)
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort based on action
        if action == "top_cpu":
            procs.sort(key=lambda x: (x.get('cpu') or 0.0), reverse=True)
            top_list = [f"- {x['name']} (PID {x['pid']}): CPU {x['cpu']:.1f}%" for x in procs[:limit]]
            res = f"Diagnostico de CPU ({sys_cpu}% total):\n" + "\n".join(top_list)
        elif action == "top_ram":
            procs.sort(key=lambda x: (x.get('memory_percent') or 0.0), reverse=True)
            top_list = [f"- {x['name']} (PID {x['pid']}): RAM {x['memory_percent']:.1f}%" for x in procs[:limit]]
            res = f"Diagnostico de Memoria RAM ({mem.percent}% en uso):\n" + "\n".join(top_list)
        else: # status
            # Top by RAM
            procs_by_ram = sorted(procs, key=lambda x: (x.get('memory_percent') or 0.0), reverse=True)[:limit]
            ram_lines = [f"  • {x['name']} (PID {x['pid']}): {x['memory_percent']:.1f}% RAM" for x in procs_by_ram]
            
            res = (
                f"Estado del sistema:\n"
                f"- Carga de CPU: {sys_cpu}%\n"
                f"- Memoria RAM: {mem.percent}% ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)\n"
                f"- Procesos con mayor consumo:\n" + "\n".join(ram_lines)
            )

        if player and hasattr(player, 'show_content'):
            player.show_content('TASK MONITOR', res)

        return res
    except Exception as e:
        return f"Error en el monitor de procesos: {e}"
