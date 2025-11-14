# Weekly Planner

A beautiful, modern web-based weekly planner app for managing tasks across all 7 days of the week. Built with Flask backend and a responsive HTML/CSS frontend.

## Features

- 📅 **7-day layout** (Monday through Sunday)
- ✨ **Modern UI** with smooth animations and gradients
- 📝 **Rich task management**: add, edit, delete, and check off tasks
- ⏰ **Time scheduling** with AM/PM support
- 📋 **Task descriptions** with inline editing
- 🎨 **Beautiful color-coded days** for visual appeal
- 📱 **Fully responsive** design (works on mobile & desktop)
- 💾 **Persistent storage** - all tasks saved in `tasks.json`
- 🔄 **Chronological sorting** - tasks auto-sort by time

## Requirements

- Python 3.8+
- Flask 2.3.3+

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Flask server

```bash
python3 app.py
```

### 3. Open in your browser

Navigate to: **http://localhost:5000**

## Usage

- **Add Task**: Enter task name, select day, optionally add time (HH:MM with AM/PM), then click "Add Task"
- **Complete Task**: Check the checkbox next to a task
- **Edit Task**: Click the ✏️ button to edit task details, time, or description
- **Delete Task**: Click the ✕ button to remove a task
- **Persistence**: All changes are automatically saved to `tasks.json`

## Project Structure

```
/Users/beahunt/Desktop/mini project/
├── app.py           # Flask backend & API endpoints
├── index.html       # Frontend UI (HTML/CSS/JavaScript)
├── edit.hyml        # Frotend UI (editing task boxes)
├── tasks.json       # Task storage (auto-created)
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Notes

- Tasks are automatically sorted chronologically by time
- Tasks without a time appear at the bottom
- All data persists between sessions via `tasks.json`
- Mobile-friendly responsive design

Enjoy your beautiful new planner! 📅✨
