"""Flask backend for Weekly Planner app."""
import json
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__, template_folder='.', static_folder='.')

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")


def normalize_time(tstr):
    """Convert a time string to minutes since midnight."""
    if not tstr:
        return None
    s = tstr.strip()
    ampm = None
    lowered = s.lower()
    if lowered.endswith('am') or lowered.endswith('pm'):
        ampm = lowered[-2:]
        s = s[:-2].strip()
    
    # If we have AM/PM, parse as 12-hour format
    if ampm:
        try:
            dt = datetime.strptime(s + ampm.upper(), "%I:%M%p")
            return dt.hour * 60 + dt.minute
        except Exception:
            pass
    
    # Try 24-hour format
    try:
        dt = datetime.strptime(s, "%H:%M")
        return dt.hour * 60 + dt.minute
    except Exception:
        pass
    
    # Try 12-hour format without AM/PM (assume AM)
    try:
        dt = datetime.strptime(s, "%I:%M")
        return dt.hour * 60 + dt.minute
    except Exception:
        pass
    
    # Manual parsing as last resort
    try:
        parts = s.split(":")
        if len(parts) == 2:
            h = int(parts[0])
            m = int(parts[1])
            if ampm:
                if ampm == 'pm' and h != 12:
                    h = h + 12
                elif ampm == 'am' and h == 12:
                    h = 0
            if 0 <= h < 24 and 0 <= m < 60:
                return h * 60 + m
    except Exception:
        return None
    
    return None


def format_time(minutes):
    """Format minutes since midnight to HH:MM (24-hour format)."""
    if minutes is None:
        return ""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def format_time_with_ampm(minutes):
    """Format minutes since midnight to HH:MM AM/PM (12-hour format)."""
    if minutes is None:
        return ""
    h = minutes // 60
    m = minutes % 60
    ampm = "AM" if h < 12 else "PM"
    h_12 = h if h <= 12 else h - 12
    if h_12 == 0:
        h_12 = 12
    return f"{h_12:02d}:{m:02d} {ampm}"


def load_tasks():
    """Load tasks from JSON file."""
    if not os.path.exists(TASKS_FILE):
        return {day: [] for day in DAYS}
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result = {}
        for day in DAYS:
            items = data.get(day, [])
            result[day] = []
            for it in items:
                time_val = it.get('time')
                if isinstance(time_val, str):
                    time_val = normalize_time(time_val)
                result[day].append({
                    'text': it.get('text', ''),
                    'done': bool(it.get('done', False)),
                    'time': time_val,
                    'desc': it.get('desc', '')
                })
            # Sort by time
            result[day].sort(key=lambda t: (t['time'] is None, t['time'] if t['time'] is not None else 24*60, t['text'].lower()))
        return result
    except Exception as e:
        print(f'Failed to load tasks: {e}')
        return {day: [] for day in DAYS}


def save_tasks(tasks):
    """Save tasks to JSON file."""
    out = {}
    for day in DAYS:
        day_list = []
        for task in tasks[day]:
            day_list.append({
                'text': task.get('text', ''),
                'done': bool(task.get('done', False)),
                'time': format_time(task.get('time')) if task.get('time') is not None else '',
                'desc': task.get('desc', '')
            })
        out[day] = day_list
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
    except Exception as e:
        print(f'Failed to save tasks: {e}')


@app.route('/')
def index():
    """Render the main planner page server-side (no JavaScript required).

    Pass the tasks and days into the template so the UI is fully server-rendered.
    """
    tasks = load_tasks()
    return render_template('index.html', tasks=tasks, days=DAYS, format_time_with_ampm=format_time_with_ampm)


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks."""
    tasks = load_tasks()
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task."""
    data = request.json
    day = data.get('day')
    text = data.get('text', '').strip()
    time_str = data.get('time', '').strip()
    ampm = data.get('ampm', '').strip()
    
    if not text or day not in DAYS:
        return jsonify({'error': 'Invalid task data'}), 400
    
    if ampm and time_str:
        time_str = time_str + ampm
    minutes = normalize_time(time_str)
    
    tasks = load_tasks()
    tasks[day].append({
        'text': text,
        'done': False,
        'time': minutes,
        'desc': ''
    })
    # Re-sort
    tasks[day].sort(key=lambda t: (t['time'] is None, t['time'] if t['time'] is not None else 24*60, t['text'].lower()))
    save_tasks(tasks)
    return jsonify({'success': True})


@app.route('/add', methods=['POST'])
def add_task_form():
    """Add a task from an HTML form (no JS)."""
    day = request.form.get('day')
    text = (request.form.get('text') or '').strip()
    time_str = (request.form.get('time') or '').strip()
    ampm = (request.form.get('ampm') or '').strip()
    if not text or day not in DAYS:
        return ("Invalid data", 400)
    if ampm and time_str:
        time_str = time_str + ampm
    minutes = normalize_time(time_str)
    tasks = load_tasks()
    tasks[day].append({'text': text, 'done': False, 'time': minutes, 'desc': ''})
    tasks[day].sort(key=lambda t: (t['time'] is None, t['time'] if t['time'] is not None else 24*60, t['text'].lower()))
    save_tasks(tasks)
    return render_template('index.html', tasks=tasks, days=DAYS, format_time_with_ampm=format_time_with_ampm)


@app.route('/api/tasks/<day>/<int:task_index>', methods=['PUT'])
def update_task(day, task_index):
    """Update a task."""
    if day not in DAYS:
        return jsonify({'error': 'Invalid day'}), 400
    
    data = request.json
    tasks = load_tasks()
    
    if task_index < 0 or task_index >= len(tasks[day]):
        return jsonify({'error': 'Invalid task index'}), 400
    
    # Update fields
    if 'done' in data:
        tasks[day][task_index]['done'] = bool(data['done'])
    if 'text' in data:
        tasks[day][task_index]['text'] = data['text'].strip()
    if 'time' in data:
        time_str = data['time'].strip()
        if time_str:
            tasks[day][task_index]['time'] = normalize_time(time_str)
        else:
            tasks[day][task_index]['time'] = None
    if 'desc' in data:
        tasks[day][task_index]['desc'] = data['desc'].strip()
    
    # Re-sort
    tasks[day].sort(key=lambda t: (t['time'] is None, t['time'] if t['time'] is not None else 24*60, t['text'].lower()))
    save_tasks(tasks)
    return jsonify({'success': True})


@app.route('/api/tasks/<day>/<int:task_index>', methods=['DELETE'])
def delete_task(day, task_index):
    """Delete a task."""
    if day not in DAYS:
        return jsonify({'error': 'Invalid day'}), 400
    
    tasks = load_tasks()
    if task_index < 0 or task_index >= len(tasks[day]):
        return jsonify({'error': 'Invalid task index'}), 400
    
    tasks[day].pop(task_index)
    save_tasks(tasks)
    return jsonify({'success': True})


@app.route('/edit/<day>/<int:task_index>', methods=['GET'])
def edit_page(day, task_index):
    tasks = load_tasks()
    if day not in DAYS or task_index < 0 or task_index >= len(tasks[day]):
        return ("Not found", 404)
    task = tasks[day][task_index]
    return render_template('edit.html', day=day, index=task_index, task=task, days=DAYS, format_time_with_ampm=format_time_with_ampm)


@app.route('/update/<day>/<int:task_index>', methods=['POST'])
def update_task_form(day, task_index):
    tasks = load_tasks()
    if day not in DAYS or task_index < 0 or task_index >= len(tasks[day]):
        return ("Not found", 404)
    text = (request.form.get('text') or '').strip()
    time_str = (request.form.get('time') or '').strip()
    desc = (request.form.get('desc') or '').strip()
    done = request.form.get('done') == 'on'
    if not text:
        return ("Task cannot be empty", 400)
    tasks[day][task_index]['text'] = text
    tasks[day][task_index]['time'] = normalize_time(time_str) if time_str else None
    tasks[day][task_index]['desc'] = desc
    tasks[day][task_index]['done'] = done
    # Re-sort
    tasks[day].sort(key=lambda t: (t['time'] is None, t['time'] if t['time'] is not None else 24*60, t['text'].lower()))
    save_tasks(tasks)
    return render_template('index.html', tasks=tasks, days=DAYS, format_time_with_ampm=format_time_with_ampm)


@app.route('/delete/<day>/<int:task_index>', methods=['POST'])
def delete_task_form(day, task_index):
    tasks = load_tasks()
    if day not in DAYS or task_index < 0 or task_index >= len(tasks[day]):
        return ("Not found", 404)
    tasks[day].pop(task_index)
    save_tasks(tasks)
    return render_template('index.html', tasks=tasks, days=DAYS, format_time_with_ampm=format_time_with_ampm)


@app.route('/toggle/<day>/<int:task_index>', methods=['POST'])
def toggle_task_done(day, task_index):
    """Toggle the done status of a task."""
    tasks = load_tasks()
    if day not in DAYS or task_index < 0 or task_index >= len(tasks[day]):
        return ("Not found", 404)
    tasks[day][task_index]['done'] = not tasks[day][task_index]['done']
    save_tasks(tasks)
    return render_template('index.html', tasks=tasks, days=DAYS, format_time_with_ampm=format_time_with_ampm)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
