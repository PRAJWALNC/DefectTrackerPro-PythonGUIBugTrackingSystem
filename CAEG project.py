import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import turtle
import math
import json
import os

# ---------------- CONFIG ---------------- #
AXIS_LIMIT = 300     # coordinate permissible range -300..300
TICK_STEP = 30       # tick every 30 units on axes

# Zoom configuration
INITIAL_ZOOM = 1.0
ZOOM_STEP = 1.25     # multiply/divide zoom by this on +/-
MIN_ZOOM = 0.25      # maximum zoom out (smaller means more world shown)
MAX_ZOOM = 8.0       # maximum zoom in (larger means more zoomed)

# Visual sizes (base values)
CANVAS_SIZE = 900                 # canvas width & height in pixels (big)
TICK_LABEL_BASE_FONT = 12         # base font for tick labels (will scale with zoom)
AXIS_LABEL_BASE_FONT = 14         # base font for axis letters (will scale with zoom)
TICK_LENGTH_BASE = 6              # base tick half-length in coordinate units (will scale lightly)

# Limits for readable fonts
TICK_FONT_MIN = 8
TICK_FONT_MAX = 36
AXIS_FONT_MIN = 10
AXIS_FONT_MAX = 40

# ---------------- TK ROOT & LAYOUT ---------------- #
root = tk.Tk()
root.title("Coordinate Geometry Drawer (Zoom Font Adaptive)")
root.geometry("1200x820")
root.resizable(False, False)

left_frame = tk.Frame(root, width=400, padx=12, pady=12)
left_frame.pack(side="left", fill="y")
right_frame = tk.Frame(root, width=CANVAS_SIZE + 20, padx=6, pady=6)
right_frame.pack(side="right", fill="both", expand=True)

# ---------------- EMBEDDED TURTLE CANVAS ---------------- #
canvas = tk.Canvas(right_frame, width=CANVAS_SIZE, height=CANVAS_SIZE)
canvas.pack()

screen = turtle.TurtleScreen(canvas)
screen.tracer(0)  # manual updates for smoother redraws

# initial zoom
current_zoom = INITIAL_ZOOM

def set_screen_world():
    """Set world coordinates of the turtle screen according to current zoom."""
    view_range = AXIS_LIMIT / current_zoom
    screen.setworldcoordinates(-view_range, -view_range, view_range, view_range)

set_screen_world()

drawer = turtle.RawTurtle(screen)
drawer.hideturtle()
drawer.speed(0)

# ---------------- PROJECT STORAGE ---------------- #
project_data = []  # list of shape dicts in order drawn

# ---------------- COLOR OPTIONS ---------------- #
COLOR_DISPLAY = ["Black", "Blue", "Red", "Green", "Purple", "Orange", "Brown"]
def color_to_turtle(col_display):
    return col_display.lower()

# ---------------- AXES / REDRAW ---------------- #
def draw_axes():
    """Draw axes and ticks with fonts and sizes scaled by current_zoom for optimal visibility."""
    drawer.clear()
    drawer.penup()
    drawer.pensize(1)
    drawer.color("black")

    view_range = AXIS_LIMIT / current_zoom
    # tick length scales a bit with zoom so ticks remain visible
    tick_len = max(2, TICK_LENGTH_BASE * (0.9 + 0.1 * current_zoom))

    # calculate font sizes scaled with zoom, clamped
    tick_font_size = int(TICK_LABEL_BASE_FONT * current_zoom)
    tick_font_size = max(TICK_FONT_MIN, min(TICK_FONT_MAX, tick_font_size))
    axis_font_size = int(AXIS_LABEL_BASE_FONT * current_zoom)
    axis_font_size = max(AXIS_FONT_MIN, min(AXIS_FONT_MAX, axis_font_size))

    # draw X axis
    drawer.goto(-view_range, 0)
    drawer.pendown()
    drawer.goto(view_range, 0)
    drawer.penup()

    # draw Y axis
    drawer.goto(0, -view_range)
    drawer.pendown()
    drawer.goto(0, view_range)
    drawer.penup()

    # ticks and labels at multiples of TICK_STEP within visible range
    start_tick = int(math.floor(-view_range / TICK_STEP) * TICK_STEP)
    end_tick = int(math.ceil(view_range / TICK_STEP) * TICK_STEP)
    for i in range(start_tick, end_tick + 1, TICK_STEP):
        if i == 0:
            continue
        if -view_range <= i <= view_range:
            # X tick (vertical small line at x=i)
            drawer.goto(i, -tick_len)
            drawer.pendown()
            drawer.goto(i, tick_len)
            drawer.penup()
            # write x label slightly below axis (offset depends on tick_len and zoom)
            label_x_offset = TICK_STEP * 0.08
            drawer.goto(i - label_x_offset, -tick_len - (TICK_STEP * 0.08))
            drawer.write(str(i), font=("Arial", tick_font_size))

            # Y tick (horizontal small line at y=i)
            drawer.goto(-tick_len, i)
            drawer.pendown()
            drawer.goto(tick_len, i)
            drawer.penup()
            # write y label slightly right of axis
            drawer.goto(tick_len + (TICK_STEP * 0.04), i - (TICK_STEP * 0.04))
            drawer.write(str(i), font=("Arial", tick_font_size))

    # axis letters
    drawer.goto(view_range - (TICK_STEP * 0.3), - (TICK_STEP * 0.4))
    drawer.write("X", font=("Arial", axis_font_size, "bold"))
    drawer.goto((TICK_STEP * 0.3), view_range - (TICK_STEP * 0.5))
    drawer.write("Y", font=("Arial", axis_font_size, "bold"))

    drawer.penup()
    screen.update()

def redraw_all():
    """Clear and redraw axes and all shapes in project_data in order."""
    set_screen_world()
    draw_axes()
    for item in project_data:
        typ = item.get("type")
        col = color_to_turtle(item.get("color", "Black"))
        try:
            if typ == "line":
                _draw_line(item["x1"], item["y1"], item["x2"], item["y2"], col)
            elif typ == "circle":
                _draw_circle(item["xc"], item["yc"], item["r"], col)
            elif typ == "polygon":
                _draw_polygon(item["cx"], item["cy"], item["sides"], item["side_length"], col)
        except Exception:
            # skip invalid entries but continue drawing others
            continue
    screen.update()

# ---------------- DRAW HELPERS ---------------- #
def move_to(x, y):
    drawer.penup()
    drawer.goto(x, y)
    drawer.pendown()

def _draw_line(x1, y1, x2, y2, color):
    drawer.color(color)
    move_to(x1, y1)
    drawer.goto(x2, y2)
    drawer.penup()

def _draw_circle(xc, yc, r, color):
    drawer.color(color)
    # move to top of circle for turtle.circle so center aligns
    move_to(xc, yc - r)
    drawer.setheading(0)
    drawer.pendown()
    drawer.circle(r)
    drawer.penup()

def _draw_polygon(cx, cy, sides, side_length, color):
    drawer.color(color)
    if sides < 3:
        return
    R = side_length / (2 * math.sin(math.pi / sides))
    vertices = []
    for k in range(sides):
        theta = 2 * math.pi * k / sides
        vx = cx + R * math.cos(theta)
        vy = cy + R * math.sin(theta)
        vertices.append((vx, vy))
    move_to(*vertices[0])
    drawer.pendown()
    for vx, vy in vertices[1:]:
        drawer.goto(vx, vy)
    drawer.goto(vertices[0])
    drawer.penup()

# ---------------- GUI LOGIC: shape operations ---------------- #
def in_range(x):
    return -AXIS_LIMIT <= x <= AXIS_LIMIT

def on_shape_change(*args):
    shape = shape_var.get()
    # disable all specific inputs first
    for w in (e_x2, e_y2, e_radius, e_sides, e_length):
        w.config(state="disabled")
    if shape == "Line":
        e_x2.config(state="normal")
        e_y2.config(state="normal")
    elif shape == "Circle":
        e_radius.config(state="normal")
    elif shape == "Polygon":
        e_sides.config(state="normal")
        e_length.config(state="normal")

def validate_and_add_shape():
    shape = shape_var.get()
    color_display = color_var.get() or "Black"
    color = color_to_turtle(color_display)

    # Validate point1 / center
    try:
        x1 = float(e_x1.get()); y1 = float(e_y1.get())
    except Exception:
        messagebox.showerror("Input Error", "Enter numeric values for Point1 / Center (x,y).")
        return
    if not (in_range(x1) and in_range(y1)):
        messagebox.showerror("Range Error", f"Point1 must be within -{AXIS_LIMIT}..{AXIS_LIMIT}.")
        return

    if shape == "Line":
        try:
            x2 = float(e_x2.get()); y2 = float(e_y2.get())
        except Exception:
            messagebox.showerror("Input Error", "Enter numeric values for Point2 (x2,y2).")
            return
        if not (in_range(x2) and in_range(y2)):
            messagebox.showerror("Range Error", f"Point2 must be within -{AXIS_LIMIT}..{AXIS_LIMIT}.")
            return
        _draw_line(x1, y1, x2, y2, color)
        project_data.append({"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color_display})

    elif shape == "Circle":
        try:
            r = float(e_radius.get())
        except Exception:
            messagebox.showerror("Input Error", "Enter numeric value for radius.")
            return
        if r <= 0:
            messagebox.showerror("Input Error", "Radius must be positive.")
            return
        if not (in_range(x1 - r) and in_range(x1 + r) and in_range(y1 - r) and in_range(y1 + r)):
            if not messagebox.askyesno("Outside Range", "Circle will extend outside visible range. Draw anyway?"):
                return
        _draw_circle(x1, y1, r, color)
        project_data.append({"type": "circle", "xc": x1, "yc": y1, "r": r, "color": color_display})

    elif shape == "Polygon":
        try:
            sides = int(e_sides.get())
            side_len = float(e_length.get())
        except Exception:
            messagebox.showerror("Input Error", "Enter numeric values for sides and side length.")
            return
        if sides < 3:
            messagebox.showerror("Input Error", "Polygon must have at least 3 sides.")
            return
        if side_len <= 0:
            messagebox.showerror("Input Error", "Side length must be positive.")
            return
        R = side_len / (2 * math.sin(math.pi / sides))
        if not (in_range(x1 - R) and in_range(x1 + R) and in_range(y1 - R) and in_range(y1 + R)):
            if not messagebox.askyesno("Outside Range", "Polygon will extend outside visible range. Draw anyway?"):
                return
        _draw_polygon(x1, y1, sides, side_len, color)
        project_data.append({
            "type": "polygon", "cx": x1, "cy": y1,
            "sides": sides, "side_length": side_len, "color": color_display
        })
    else:
        messagebox.showerror("Select Shape", "Please select a shape.")
        return

    screen.update()

def undo_last_shape():
    if not project_data:
        messagebox.showinfo("Undo", "No shapes to undo.")
        return
    project_data.pop()
    redraw_all()

def clear_canvas():
    project_data.clear()
    redraw_all()

# ---------------- Save / Load ---------------- #
def save_project():
    if not project_data:
        messagebox.showwarning("Save", "No shapes to save.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if not path:
        return
    try:
        with open(path, "w") as f:
            json.dump(project_data, f, indent=4)
        messagebox.showinfo("Saved", f"Project saved to:\n{path}")
    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save:\n{e}")

def load_project():
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not path:
        return
    if not os.path.isfile(path):
        messagebox.showerror("Load Error", "Selected file does not exist.")
        return
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            messagebox.showerror("Load Error", "Invalid project file format.")
            return
        project_data.clear()
        for item in data:
            if not isinstance(item, dict):
                continue
            typ = item.get("type")
            if typ == "line" and {"x1","y1","x2","y2","color"} <= set(item.keys()):
                project_data.append(item)
            elif typ == "circle" and {"xc","yc","r","color"} <= set(item.keys()):
                project_data.append(item)
            elif typ == "polygon" and {"cx","cy","sides","side_length","color"} <= set(item.keys()):
                project_data.append(item)
            else:
                continue
        redraw_all()
        messagebox.showinfo("Loaded", f"Project loaded from:\n{path}")
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to load project:\n{e}")

# ---------------- Zoom Controls ---------------- #
def zoom_in():
    global current_zoom
    new_zoom = current_zoom * ZOOM_STEP
    if new_zoom > MAX_ZOOM:
        messagebox.showinfo("Zoom", "Maximum zoom reached.")
        return
    current_zoom = new_zoom
    redraw_all()

def zoom_out():
    global current_zoom
    new_zoom = current_zoom / ZOOM_STEP
    if new_zoom < MIN_ZOOM:
        messagebox.showinfo("Zoom", "Maximum zoom out reached.")
        return
    current_zoom = new_zoom
    redraw_all()

def reset_zoom():
    global current_zoom
    current_zoom = INITIAL_ZOOM
    redraw_all()

# ---------------- Exit ---------------- #
def exit_app():
    root.destroy()
    try:
        screen.bye()
    except Exception:
        pass

# ---------------- BUILD GUI CONTROLS ---------------- #
tk.Label(left_frame, text="Shape Selector", font=("Arial", 12, "bold")).pack(pady=(4,6))
shape_var = tk.StringVar(value="Line")
shape_box = ttk.Combobox(left_frame, textvariable=shape_var,
                         values=["Line", "Circle", "Polygon"], state="readonly", width=18)
shape_box.pack()
shape_var.trace_add("write", on_shape_change)

tk.Label(left_frame, text="Point 1 / Centre (x, y):", font=("Arial", 10)).pack(pady=(12, 0))
f1 = tk.Frame(left_frame); f1.pack(pady=4)
e_x1 = tk.Entry(f1, width=12); e_y1 = tk.Entry(f1, width=12)
e_x1.pack(side="left", padx=6); e_y1.pack(side="left", padx=6)

tk.Label(left_frame, text="Point 2 (x2, y2) — Line only:", font=("Arial", 10)).pack(pady=(8, 0))
f2 = tk.Frame(left_frame); f2.pack(pady=4)
e_x2 = tk.Entry(f2, width=12); e_y2 = tk.Entry(f2, width=12)
e_x2.pack(side="left", padx=6); e_y2.pack(side="left", padx=6)

tk.Label(left_frame, text="Radius (Circle):", font=("Arial", 10)).pack(pady=(8, 0))
e_radius = tk.Entry(left_frame, width=16)
e_radius.pack(pady=4)

tk.Label(left_frame, text="Polygon: Number of sides & Side length:", font=("Arial", 10)).pack(pady=(8,0))
f3 = tk.Frame(left_frame); f3.pack(pady=4)
e_sides = tk.Entry(f3, width=12); e_length = tk.Entry(f3, width=12)
e_sides.pack(side="left", padx=6); e_length.pack(side="left", padx=6)

# Color chooser (display capitalized names)
tk.Label(left_frame, text="Choose Color:", font=("Arial", 10)).pack(pady=(12, 2))
color_var = tk.StringVar(value="Black")
color_box = ttk.Combobox(left_frame, textvariable=color_var,
                         values=COLOR_DISPLAY, state="readonly", width=16)
color_box.pack()

# Buttons: Draw, Undo, Clear, Save, Load, Zoom +/-, Reset Zoom, Exit
btn_draw = ttk.Button(left_frame, text="Draw", command=validate_and_add_shape)
btn_draw.pack(pady=(14, 6), fill="x")
btn_undo = ttk.Button(left_frame, text="Undo Last Shape", command=undo_last_shape)
btn_undo.pack(pady=6, fill="x")
btn_clear = ttk.Button(left_frame, text="Clear (Remove All)", command=clear_canvas)
btn_clear.pack(pady=6, fill="x")
btn_save = ttk.Button(left_frame, text="Save Project", command=save_project)
btn_save.pack(pady=6, fill="x")
btn_load = ttk.Button(left_frame, text="Load Project", command=load_project)
btn_load.pack(pady=6, fill="x")

# Zoom controls group
zoom_frame = tk.Frame(left_frame)
zoom_frame.pack(pady=(12, 6), fill="x")
tk.Label(zoom_frame, text="Zoom:", font=("Arial", 10)).pack(side="left", padx=(2,8))
btn_zoom_in = ttk.Button(zoom_frame, text="+", width=4, command=zoom_in)
btn_zoom_in.pack(side="left", padx=4)
btn_zoom_out = ttk.Button(zoom_frame, text="-", width=4, command=zoom_out)
btn_zoom_out.pack(side="left", padx=4)
btn_zoom_reset = ttk.Button(zoom_frame, text="Reset", command=reset_zoom)
btn_zoom_reset.pack(side="left", padx=8)

btn_exit = ttk.Button(left_frame, text="Exit", command=exit_app)
btn_exit.pack(pady=6, fill="x")

note = tk.Label(left_frame, text=f"Coordinates range: -{AXIS_LIMIT} to {AXIS_LIMIT}\nTicks shown every {TICK_STEP} units.",
                fg="gray", justify="left")
note.pack(side="bottom", pady=8)

# initialize display and widget states
on_shape_change()
redraw_all()

# ensure graceful exit on window close
root.protocol("WM_DELETE_WINDOW", exit_app)
root.mainloop()