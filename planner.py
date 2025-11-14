import tkinter as tk
from tkinter import ttk
import json
import os
import tkinter.font as tkfont

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")

class PlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weekly Planner")
        self.geometry("1000x600")
        self.minsize(800, 400)

        self.tasks = {day: [] for day in DAYS}  # list of dicts: {text, done}
        self.task_vars = {day: [] for day in DAYS}  # list of BooleanVar for each Checkbutton

        self._build_ui()
        self._load_tasks()

        # Save on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Top input area
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        prompt_label = ttk.Label(top_frame, text="Add")
        prompt_label.pack(side=tk.LEFT)

        self.task_entry = ttk.Entry(top_frame)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))
        self.task_entry.focus()

        to_label = ttk.Label(top_frame, text="to")
        to_label.pack(side=tk.LEFT)

        self.day_var = tk.StringVar(value=DAYS[0])
        self.day_combo = ttk.Combobox(top_frame, textvariable=self.day_var, values=DAYS, state="readonly", width=10)
        self.day_combo.pack(side=tk.LEFT, padx=(6, 6))

        add_btn = ttk.Button(top_frame, text="Add", command=self._add_task_from_input)
        add_btn.pack(side=tk.LEFT)

        # Main area with 7 columns
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Use a canvas with a horizontal scrollbar in case window too narrow
        canvas = tk.Canvas(main_frame)
        h_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(canvas)
        # Put the content_frame in the canvas
        canvas.create_window((0,0), window=content_frame, anchor='nw')

        # Build day columns
        self.day_frames = {}
        for col, day in enumerate(DAYS):
            col_frame = ttk.Frame(content_frame, relief=tk.RIDGE, borderwidth=1)
            col_frame.grid(row=0, column=col, sticky='nsew', padx=4, pady=4)
            label = ttk.Label(col_frame, text=day, font=(None, 12, 'bold'))
            label.pack(anchor='n', pady=(6,4))

            tasks_container = ttk.Frame(col_frame)
            tasks_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))

            # Make tasks_container scrollable vertically if many tasks
            canvas_v = tk.Canvas(tasks_container, height=400)
            vscroll = ttk.Scrollbar(tasks_container, orient=tk.VERTICAL, command=canvas_v.yview)
            canvas_v.configure(yscrollcommand=vscroll.set)
            vscroll.pack(side=tk.RIGHT, fill=tk.Y)
            canvas_v.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            inner = ttk.Frame(canvas_v)
            canvas_v.create_window((0,0), window=inner, anchor='nw')

            # Keep references
            self.day_frames[day] = inner

            # make column expand evenly
            content_frame.columnconfigure(col, weight=1)

            # Update scrollregion when needed
            inner.bind('<Configure>', lambda e, c=canvas_v: c.configure(scrollregion=c.bbox('all')))

        # Update canvas scrollregion when content_frame changes
        content_frame.bind('<Configure>', lambda e, c=canvas: c.configure(scrollregion=c.bbox('all')))

        # Bind Enter to add
        self.bind('<Return>', lambda e: self._add_task_from_input())

    def _add_task_from_input(self):
        text = self.task_entry.get().strip()
        day = self.day_var.get()
        if not text:
            return
        self._add_task(day, text, done=False)
        self.task_entry.delete(0, tk.END)
        self.task_entry.focus()
        self._save_tasks()

    def _add_task(self, day, text, done=False):
        # Create BooleanVar and Checkbutton
        var = tk.BooleanVar(value=done)
        cb = ttk.Checkbutton(self.day_frames[day], text=text, variable=var, command=self._save_tasks)
        # For clearer layout, pack at top
        cb.pack(anchor='w', pady=2)

        # If done, visually show using a strikethrough font
        base_font = tkfont.nametofont(cb.cget('font'))
        strike_font = tkfont.Font(base=base_font, slant=base_font.cget('slant'))

        def update_visual():
            if var.get():
                # apply overstrike
                strike_font.configure(overstrike=1)
                cb.configure(style='Done.TCheckbutton')
                cb.configure(font=strike_font)
            else:
                strike_font.configure(overstrike=0)
                cb.configure(font=base_font)

        var.trace_add('write', lambda *args: update_visual())
        update_visual()

        # store
        self.task_vars[day].append((var, cb, text))
        self.tasks[day].append({'text': text, 'done': bool(var.get())})

    def _load_tasks(self):
        if not os.path.exists(TASKS_FILE):
            return
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for day in DAYS:
                items = data.get(day, [])
                # clear any existing UI tasks
                self.tasks[day] = []
                self.task_vars[day] = []
                for it in items:
                    text = it.get('text','')
                    done = bool(it.get('done', False))
                    self._add_task(day, text, done=done)
        except Exception as e:
            print("Failed to load tasks:", e)

    def _save_tasks(self):
        # Reconstruct tasks from task_vars to get latest done states
        out = {}
        for day in DAYS:
            day_list = []
            for (var, cb, text) in self.task_vars.get(day, []):
                day_list.append({'text': text, 'done': bool(var.get())})
            out[day] = day_list
        try:
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(out, f, indent=2)
        except Exception as e:
            print("Failed to save tasks:", e)

    def _on_close(self):
        self._save_tasks()
        self.destroy()

if __name__ == '__main__':
    app = PlannerApp()
    app.mainloop()