import time
import threading
import datetime
import winsound

ALARM_JOBS = []

PLUGIN = {
    "name": "alarm_timer",
    "description": "Set alarms and countdown timers. Use for requests like alarm at 7:30, timer for 10 minutes, temporizador, or despertador.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "set_timer, set_alarm, list_alarms, or cancel_all"},
            "minutes": {"type": "NUMBER", "description": "Minutes for countdown timer"},
            "time": {"type": "STRING", "description": "Time for alarm (HH:MM)"},
            "label": {"type": "STRING", "description": "Label for alarm"}
        },
        "required": ["action"]
    }
}

def _alarm_buzzer(label, player=None):
    for _ in range(5):
        try:
            winsound.Beep(1200, 350)
            winsound.Beep(1600, 450)
            time.sleep(0.2)
        except Exception:
            pass
    if player and hasattr(player, 'write_log'):
        player.write_log('ALARM: ' + str(label))

def _timer_worker(delay_sec, label, player=None):
    time.sleep(delay_sec)
    _alarm_buzzer(label, player)

def run(parameters, player=None, session_memory=None):
    action = str(parameters.get('action', 'set_timer')).lower().strip()
    minutes = parameters.get('minutes')
    time_str = str(parameters.get('time', '')).strip()
    label = str(parameters.get('label', 'Alarma')).strip()

    try:
        if action == 'set_timer':
            if not minutes or float(minutes) <= 0:
                return 'Please specify duration in minutes, Father.'
            mins = float(minutes)
            delay = mins * 60.0
            t = threading.Thread(target=_timer_worker, args=(delay, label, player), daemon=True)
            t.start()
            ALARM_JOBS.append({'type': 'timer', 'label': label, 'ends_at': time.time() + delay})
            if player and hasattr(player, 'write_log'):
                player.write_log('TIMER SET: ' + str(mins) + 'm (' + label + ')')
            return 'Timer set for ' + str(mins) + ' minutes (' + label + '), Father. I will ring when done.'

        elif action == 'set_alarm':
            if not time_str:
                return 'Please specify a time for the alarm, Father.'
            now = datetime.datetime.now()
            clean = time_str.lower().replace('am','').replace('pm','').strip()
            parts = clean.split(':')
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            if 'pm' in time_str.lower() and h < 12:
                h += 12
            if 'am' in time_str.lower() and h == 12:
                h = 0
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            delay = (target - now).total_seconds()
            t = threading.Thread(target=_timer_worker, args=(delay, label, player), daemon=True)
            t.start()
            ALARM_JOBS.append({'type': 'alarm', 'label': label, 'target': target.strftime('%H:%M')})
            return 'Alarm set for ' + target.strftime('%I:%M %p') + ' (' + label + '), Father.'

        elif action == 'list_alarms':
            if not ALARM_JOBS:
                return 'No active alarms or timers right now, Father.'
            return str(len(ALARM_JOBS)) + ' active alarms registered, Father.'

        elif action == 'cancel_all':
            ALARM_JOBS.clear()
            return 'All active alarms and timers have been cleared, Father.'

        return 'Action completed, Father.'
    except Exception as e:
        return 'Could not set alarm: ' + str(e)
