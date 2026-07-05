# scene_editor.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
from utils import ResizableEntry

# ----------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------
entities = []
selected_entity_idx = None
layers = []
selected_layer_idx = None
canva_scale = 15
offset_x = 0
offset_y = 0

snap_enabled = None
snap_val = None

canva = None
obj_lisbox = None
layer_lisbox = None
addety = None
editor_widgets = {}  # maps label -> widget (Entry or Combobox)
editor_buttons = {}  # maps label -> button (for Select/Pick)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def snap(val):
    if snap_enabled is not None and snap_enabled.get():
        s = snap_val.get() if snap_val is not None else 1.0
        if s > 0:
            return round(val / s) * s
    return val

def get_entity_color_hex(ent):
    parts = ent.get("color_hex", "4488ff").lstrip("#")
    if len(parts) == 3:
        parts = "".join(c*2 for c in parts)
    if len(parts) == 6:
        return "#" + parts
    return "#4488ff"

def canvas_to_world(cx, cy):
    wx = (cx - canva.winfo_width()/2 - offset_x) / canva_scale
    wz = (canva.winfo_height()/2 + offset_y - cy) / canva_scale
    return wx, wz

def world_to_canvas(wx, wz):
    cx = canva.winfo_width()/2 + offset_x + wx * canva_scale
    cy = canva.winfo_height()/2 + offset_y - wz * canva_scale
    return cx, cy

def make_default_entity(name, x=0, y=0, z=0, sx=1, sy=1, sz=1):
    return {
        "Name": name, "model": "cube", "texture": "", "color": "color.random_color()",
        "color_hex": "4488ff", "scale": f"({sx}, {sy}, {sz})", "position": f"({x}, {y}, {z})",
        "x": x, "y": y, "z": z, "scale_x": sx, "scale_y": sy, "scale_z": sz,
        "rotation_x": 0, "rotation_y": 0, "rotation_z": 0,
        "enabled": "True", "visible": "True", "collider": "box"
    }

# ----------------------------------------------------------------------
# Canvas drawing
# ----------------------------------------------------------------------
_entity_items = {}
_handle_items = {}

def draw_grid():
    if canva is None:
        return
    canva.delete("grid")
    w = canva.winfo_width()
    h = canva.winfo_height()
    if w < 10 or h < 10:
        return
    start_x = (w // 2 + offset_x) % canva_scale
    start_y = (h // 2 + offset_y) % canva_scale
    for i in range(int(start_x), w, canva_scale):
        canva.create_line(i, 0, i, h, fill="#C6C6C6", tags="grid")
    for j in range(int(start_y), h, canva_scale):
        canva.create_line(0, j, w, j, fill="#C6C6C6", tags="grid")

def draw_entities():
    canva.delete("entity")
    canva.delete("handle")
    _entity_items.clear()
    _handle_items.clear()
    if selected_layer_idx is None or selected_layer_idx >= len(layers):
        return
    layer_y = layers[selected_layer_idx]
    for idx, ent in enumerate(entities):
        ey = float(ent.get("y", 0))
        sy = float(ent.get("scale_y", 1) or 1)
        if not (ey == layer_y or (ey < layer_y < ey + sy)):
            continue
        ex = float(ent.get("x", 0))
        ez = float(ent.get("z", 0))
        sx = float(ent.get("scale_x", 1) or 1)
        sz = float(ent.get("scale_z", 1) or 1)
        cx, cy = world_to_canvas(ex, ez)
        cw = max(sx * canva_scale, 4)
        ch = max(sz * canva_scale, 4)
        color = get_entity_color_hex(ent)
        is_on_layer = (ey == layer_y)
        fill = color if is_on_layer else ""
        outline = "black" if is_on_layer else "gray"
        rect_args = {
            "fill": fill, "outline": outline,
            "tags": ("entity", f"e{idx}"),
            "width": 2 if idx == selected_entity_idx else 1
        }
        if not is_on_layer:
            rect_args["stipple"] = "gray25"
        item = canva.create_rectangle(cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2, **rect_args)
        _entity_items[idx] = item
        canva.create_text(cx, cy, text=ent.get("Name", f"E{idx}"),
                          font=("TkDefaultFont", 8), tags=("entity", f"e{idx}"))
    # Draw handles if selected
    if selected_entity_idx is not None and selected_entity_idx in _entity_items:
        draw_handles(selected_entity_idx)

def draw_handles(idx):
    ent = entities[idx]
    ex = float(ent.get("x", 0))
    ez = float(ent.get("z", 0))
    sx = float(ent.get("scale_x", 1) or 1)
    sz = float(ent.get("scale_z", 1) or 1)
    cx, cy = world_to_canvas(ex, ez)
    half_w = sx * canva_scale / 2
    half_h = sz * canva_scale / 2
    handle_positions = [
        (cx - half_w, cy - half_h), (cx, cy - half_h), (cx + half_w, cy - half_h),
        (cx - half_w, cy), (cx + half_w, cy),
        (cx - half_w, cy + half_h), (cx, cy + half_h), (cx + half_w, cy + half_h)
    ]
    handle_ids = []
    for px, py in handle_positions:
        item = canva.create_rectangle(px-3, py-3, px+3, py+3,
                                      fill="white", outline="black",
                                      tags=("handle", f"h{idx}"))
        handle_ids.append(item)
    _handle_items[idx] = handle_ids

def refresh_canvas(status_callback):
    draw_grid()
    draw_entities()
    if selected_entity_idx is not None:
        obj_lisbox.selection_clear(0, tk.END)
        obj_lisbox.selection_set(selected_entity_idx)
        obj_lisbox.activate(selected_entity_idx)

def get_entity_at(cx, cy):
    items = canva.find_overlapping(cx-1, cy-1, cx+1, cy+1)
    for item in items:
        tags = canva.gettags(item)
        for tag in tags:
            if tag.startswith("e"):
                idx = int(tag[1:])
                if float(entities[idx].get("y", 0)) == layers[selected_layer_idx]:
                    return idx
    return None

def get_handle_at(cx, cy):
    items = canva.find_overlapping(cx-2, cy-2, cx+2, cy+2)
    for item in items:
        tags = canva.gettags(item)
        if "handle" in tags:
            for tag in tags:
                if tag.startswith("h") and tag != "handle":
                    idx = int(tag[1:])
                    if idx in _handle_items:
                        hlist = _handle_items[idx]
                        if item in hlist:
                            hidx = hlist.index(item)
                            return idx, hidx
    return None, None

# ----------------------------------------------------------------------
# Canvas interaction state
# ----------------------------------------------------------------------
_drag_mode = None  # 'move', 'resize', 'select_rect', None
_drag_entity_idx = None
_drag_handle_idx = None
_drag_start_canvas = None
_drag_start_world = None
_drag_rect_start = None
_drag_rect_item = None

def on_canvas_click(event):
    global _drag_mode, _drag_entity_idx, _drag_handle_idx, _drag_start_canvas, _drag_start_world
    global _drag_rect_start, _drag_rect_item

    # Check for handle click
    hidx, hnum = get_handle_at(event.x, event.y)
    if hidx is not None:
        _drag_mode = 'resize'
        _drag_entity_idx = hidx
        _drag_handle_idx = hnum
        _drag_start_canvas = (event.x, event.y)
        ent = entities[hidx]
        _drag_start_world = (float(ent.get("x", 0)), float(ent.get("z", 0)),
                             float(ent.get("scale_x", 1)), float(ent.get("scale_z", 1)))
        return

    # Check for entity click
    idx = get_entity_at(event.x, event.y)
    if idx is not None:
        select_entity_by_idx(idx)
        _drag_mode = 'move'
        _drag_entity_idx = idx
        _drag_start_canvas = (event.x, event.y)
        _drag_start_world = (float(entities[idx].get("x", 0)), float(entities[idx].get("z", 0)))
        return

    # Click on empty canvas: deselect and start selection rectangle
    selected_entity_idx = None
    obj_lisbox.selection_clear(0, tk.END)
    clear_editor()
    _drag_mode = 'select_rect'
    _drag_rect_start = (event.x, event.y)
    _drag_rect_item = None

def on_canvas_drag(event):
    global _drag_mode, _drag_entity_idx, _drag_handle_idx
    global _drag_start_canvas, _drag_start_world
    global _drag_rect_start, _drag_rect_item

    if _drag_mode == 'move' and _drag_entity_idx is not None:
        ent = entities[_drag_entity_idx]
        dx = (event.x - _drag_start_canvas[0]) / canva_scale
        dz = - (event.y - _drag_start_canvas[1]) / canva_scale
        new_x = _drag_start_world[0] + dx
        new_z = _drag_start_world[1] + dz
        if snap_enabled.get():
            new_x = snap(new_x)
            new_z = snap(new_z)
        ent["x"] = round(new_x, 6)
        ent["z"] = round(new_z, 6)
        draw_entities()
    elif _drag_mode == 'resize' and _drag_entity_idx is not None:
        ent = entities[_drag_entity_idx]
        dx = (event.x - _drag_start_canvas[0]) / canva_scale
        dz = - (event.y - _drag_start_canvas[1]) / canva_scale
        init_sx, init_sz = _drag_start_world[2], _drag_start_world[3]
        hnum = _drag_handle_idx
        new_sx = init_sx
        new_sz = init_sz
        new_x = _drag_start_world[0]
        new_z = _drag_start_world[1]
        if hnum in (0, 3, 5):  # left side
            new_x = _drag_start_world[0] + dx
            new_sx = init_sx - dx
        elif hnum in (2, 4, 7):  # right side
            new_sx = init_sx + dx
        if hnum in (0, 1, 2):  # top side
            new_z = _drag_start_world[1] + dz
            new_sz = init_sz - dz
        elif hnum in (5, 6, 7):  # bottom side
            new_sz = init_sz + dz
        min_size = 0.2
        if snap_enabled.get():
            new_x = snap(new_x)
            new_z = snap(new_z)
            new_sx = max(min_size, snap(new_sx))
            new_sz = max(min_size, snap(new_sz))
        else:
            new_sx = max(min_size, new_sx)
            new_sz = max(min_size, new_sz)
        ent["x"] = round(new_x, 6)
        ent["z"] = round(new_z, 6)
        ent["scale_x"] = round(new_sx, 6)
        ent["scale_z"] = round(new_sz, 6)
        ent["scale"] = f"({ent['scale_x']}, {ent.get('scale_y', 1)}, {ent['scale_z']})"
        draw_entities()
    elif _drag_mode == 'select_rect':
        if _drag_rect_item:
            canva.delete(_drag_rect_item)
        x1, y1 = _drag_rect_start
        x2, y2 = event.x, event.y
        _drag_rect_item = canva.create_rectangle(x1, y1, x2, y2,
                                                 outline="blue", dash=(4,2),
                                                 tags="selection_box")

def on_canvas_release(event):
    global _drag_mode, _drag_entity_idx, _drag_handle_idx
    global _drag_rect_start, _drag_rect_item, _drag_start_world

    if _drag_mode == 'move' and _drag_entity_idx is not None:
        ent = entities[_drag_entity_idx]
        ent["position"] = f"({ent['x']}, {ent['y']}, {ent['z']})"
        if selected_entity_idx == _drag_entity_idx:
            for key in editor_widgets:
                if key in ent:
                    widget = editor_widgets[key]
                    if isinstance(widget, ttk.Combobox):
                        widget.set(str(ent[key]))
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, str(ent[key]))
        _drag_entity_idx = None
    elif _drag_mode == 'resize' and _drag_entity_idx is not None:
        ent = entities[_drag_entity_idx]
        ent["position"] = f"({ent['x']}, {ent['y']}, {ent['z']})"
        if selected_entity_idx == _drag_entity_idx:
            for key in editor_widgets:
                if key in ent:
                    widget = editor_widgets[key]
                    if isinstance(widget, ttk.Combobox):
                        widget.set(str(ent[key]))
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, str(ent[key]))
        _drag_entity_idx = None
    elif _drag_mode == 'select_rect':
        if _drag_rect_item:
            canva.delete(_drag_rect_item)
            _drag_rect_item = None
        if _drag_rect_start is None:
            _drag_mode = None
            return
        x1, y1 = _drag_rect_start
        x2, y2 = event.x, event.y
        _drag_rect_start = None
        if selected_layer_idx is None or selected_layer_idx >= len(layers):
            _drag_mode = None
            return
        layer_y = layers[selected_layer_idx]
        wx1, wz1 = canvas_to_world(x1, y1)
        wx2, wz2 = canvas_to_world(x2, y2)
        # If click (small drag), create single entity
        if abs(x2 - x1) < 5 and abs(y2 - y1) < 5:
            cx = snap(wx1)
            cz = snap(wz1)
            idx = len(entities)
            ent = make_default_entity(f"Entity {idx}", cx, layer_y, cz, 1.0, 1.0, 1.0)
            entities.append(ent)
            obj_lisbox.insert(tk.END, ent["Name"])
            select_entity_by_idx(idx)
            refresh_canvas(None)
            _drag_mode = None
            return
        # Otherwise create entity sized by rectangle
        cx = (wx1 + wx2) / 2
        cz = (wz1 + wz2) / 2
        sx = abs(wx2 - wx1)
        sz = abs(wz2 - wz1)
        if sx < 0.2:
            sx = 1.0
        if sz < 0.2:
            sz = 1.0
        cx = snap(cx)
        cz = snap(cz)
        sx = snap(sx)
        sz = snap(sz)
        idx = len(entities)
        ent = make_default_entity(f"Entity {idx}", cx, layer_y, cz, sx, 1.0, sz)
        entities.append(ent)
        obj_lisbox.insert(tk.END, ent["Name"])
        select_entity_by_idx(idx)
        refresh_canvas(None)
    _drag_mode = None

# ----------------------------------------------------------------------
# Selection and UI helpers
# ----------------------------------------------------------------------
def select_entity_by_idx(idx):
    global selected_entity_idx
    if idx is None or idx < 0 or idx >= len(entities):
        selected_entity_idx = None
        return
    selected_entity_idx = idx
    ent = entities[idx]
    obj_lisbox.selection_clear(0, tk.END)
    obj_lisbox.selection_set(idx)
    obj_lisbox.activate(idx)
    refresh_y_combobox()
    for key, widget in editor_widgets.items():
        if key in ent:
            if isinstance(widget, ttk.Combobox):
                widget.set(str(ent[key]))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(ent[key]))
    refresh_canvas(None)

def clear_editor():
    for widget in editor_widgets.values():
        if isinstance(widget, ttk.Combobox):
            widget.set('')
        else:
            widget.delete(0, tk.END)

def refresh_y_combobox():
    w = editor_widgets.get("y")
    if w and isinstance(w, ttk.Combobox):
        w['values'] = [str(y) for y in layers]

# ----------------------------------------------------------------------
# Build UI
# ----------------------------------------------------------------------
def build_scene_editor(parent, status_callback):
    global canva, obj_lisbox, layer_lisbox, addety, editor_widgets, editor_buttons
    global snap_enabled, snap_val

    snap_enabled = tk.BooleanVar(value=False)
    snap_val = tk.DoubleVar(value=1.0)

    scene_frame = tk.Frame(parent)

    # Canvas
    canvas_frame = tk.Frame(scene_frame)
    canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canva = tk.Canvas(canvas_frame, background='white', highlightthickness=0)
    canva.pack(fill=tk.BOTH, expand=True)

    # Pan with middle mouse
    pan_start_x = 0
    pan_start_y = 0
    def start_pan_custom(event):
        nonlocal pan_start_x, pan_start_y
        pan_start_x = event.x
        pan_start_y = event.y
        canva.config(cursor="fleur")
    def drag_pan_custom(event):
        nonlocal pan_start_x, pan_start_y
        global offset_x, offset_y
        dx = event.x - pan_start_x
        dy = event.y - pan_start_y
        offset_x += dx
        offset_y += dy
        pan_start_x = event.x
        pan_start_y = event.y
        refresh_canvas(status_callback)
    def end_pan(event):
        canva.config(cursor="")
    canva.bind("<Button-2>", start_pan_custom)
    canva.bind("<B2-Motion>", drag_pan_custom)
    canva.bind("<ButtonRelease-2>", end_pan)

    # Entity interaction
    canva.bind("<Button-1>", on_canvas_click)
    canva.bind("<B1-Motion>", on_canvas_drag)
    canva.bind("<ButtonRelease-1>", on_canvas_release)
    canva.bind("<Configure>", lambda e: refresh_canvas(status_callback))

    # Right panel
    right_panel = tk.Frame(scene_frame, padx=5, pady=5)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # ---- Entities: listbox (left) + fields (right) ----
    tk.Label(right_panel, text="Entities", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
    entities_body = tk.Frame(right_panel)
    entities_body.pack(fill=tk.BOTH, expand=True)

    obj_lisbox = tk.Listbox(entities_body, width=20)
    obj_lisbox.pack(side=tk.LEFT, fill=tk.Y)
    def on_entity_listbox_select():
        sel = obj_lisbox.curselection()
        if sel:
            select_entity_by_idx(sel[0])
    obj_lisbox.bind("<<ListboxSelect>>", lambda e: on_entity_listbox_select())

    editor = tk.Frame(entities_body)
    editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))

    field_specs = [
        ("Name", "entry", []),
        ("model", "combobox", ['cube', 'sphere', 'plane', 'quad', 'circle', 'capsule', 'cylinder', 'torus', '']),
        ("texture", "combobox", ['brick', 'grass', 'circle', 'sky_default', 'white_cube', 'shore', 'vignette', 'vertical_gradient', 'ursina_logo', '']),
        ("color", "combobox", ['color.white', 'color.red', 'color.blue', 'color.green', 'color.yellow', 'color.orange', 'color.purple', 'color.cyan', 'color.magenta', 'color.lime', 'color.azure', 'color.violet', 'color.pink', 'color.brown', 'color.gray', 'color.black']),
        ("scale", "entry", []),
        ("x", "entry", []),
        ("y", "combobox", []),
        ("z", "entry", []),
        ("enabled", "combobox", ['True', 'False']),
        ("visible", "combobox", ['True', 'False']),
        ("collider", "combobox", ['box', 'sphere', 'capsule', 'mesh', 'None']),
        ("rotation_x", "entry", []),
        ("rotation_y", "entry", []),
        ("rotation_z", "entry", []),
    ]

    editor_widgets = {}
    editor_buttons = {}
    for i, (label, kind, options) in enumerate(field_specs):
        tk.Label(editor, text=label).grid(row=i, column=0, sticky="e", padx=2)
        if kind == "entry":
            widget = tk.Entry(editor, width=12)
        else:
            widget = ttk.Combobox(editor, values=options, width=10)
            widget.set(options[0] if options else "")
        widget.grid(row=i, column=1, padx=2, pady=1, sticky="w")
        editor_widgets[label] = widget

        if label == "model":
            btn = tk.Button(editor, text="Select", command=lambda l=label: select_file(l))
            btn.grid(row=i, column=2, padx=2)
            editor_buttons[label] = btn
        elif label == "texture":
            btn = tk.Button(editor, text="Select", command=lambda l=label: select_file(l))
            btn.grid(row=i, column=2, padx=2)
            editor_buttons[label] = btn
        elif label == "color":
            btn = tk.Button(editor, text="Pick", command=lambda l=label: pick_color(l))
            btn.grid(row=i, column=2, padx=2)
            editor_buttons[label] = btn

    def select_file(label):
        path = filedialog.askopenfilename(title=f"Select {label} file")
        if path:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            try:
                rel = os.path.relpath(path, script_dir)
                val = rel if not rel.startswith("..") else path
            except:
                val = path
            widget = editor_widgets[label]
            if isinstance(widget, ttk.Combobox):
                widget.set(val)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, val)

    def pick_color(label):
        color_code = colorchooser.askcolor(title="Pick color")
        if color_code:
            hex_color = color_code[1]
            widget = editor_widgets[label]
            value = f"color.hex('{hex_color}')"
            if isinstance(widget, ttk.Combobox):
                widget.set(value)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, value)

    # Buttons for save/delete
    btn_frame = tk.Frame(right_panel)
    btn_frame.pack(fill=tk.X, pady=4)
    tk.Button(btn_frame, text="Save Entity", command=lambda: save_entity()).pack(side=tk.LEFT, padx=2)
    tk.Button(btn_frame, text="Delete Entity", command=lambda: delete_entity()).pack(side=tk.LEFT, padx=2)

    # ---- Bottom: Layers + Snap (compact) ----
    bottom_bar = tk.Frame(right_panel)
    bottom_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(4,0))

    tk.Label(bottom_bar, text="Layers", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
    layer_lisbox = tk.Listbox(bottom_bar, height=3)
    layer_lisbox.pack(fill=tk.X)
    def on_layer_select():
        global selected_layer_idx, selected_entity_idx
        sel = layer_lisbox.curselection()
        if sel:
            selected_layer_idx = sel[0]
            selected_entity_idx = None
            obj_lisbox.selection_clear(0, tk.END)
            clear_editor()
            refresh_canvas(status_callback)
    layer_lisbox.bind("<<ListboxSelect>>", lambda e: on_layer_select())
    layrow = tk.Frame(bottom_bar)
    layrow.pack(fill=tk.X)
    tk.Label(layrow, text="y=").pack(side=tk.LEFT)
    addety = tk.Entry(layrow, width=6)
    addety.pack(side=tk.LEFT, padx=2)
    tk.Button(layrow, text="Add", font=("TkDefaultFont", 8),
              command=lambda: add_layer()).pack(side=tk.LEFT, padx=1)
    tk.Button(layrow, text="Del", font=("TkDefaultFont", 8),
              command=lambda: delete_layer()).pack(side=tk.LEFT, padx=1)
    snaprow = tk.Frame(bottom_bar)
    snaprow.pack(fill=tk.X, pady=3)
    tk.Checkbutton(snaprow, text="Snap", font=("TkDefaultFont", 9),
                   variable=snap_enabled).pack(side=tk.LEFT)
    tk.Entry(snaprow, textvariable=snap_val, width=5).pack(side=tk.LEFT, padx=2)
    tk.Label(snaprow, text="grid", font=("TkDefaultFont", 9)).pack(side=tk.LEFT)

    # Key binding for delete
    def on_key(event):
        if event.keysym == "Delete":
            delete_entity()
    scene_frame.bind("<Key>", on_key)
    scene_frame.focus_set()

    # ------------------------------------------------------------------
    # Inner functions for entity/layer operations
    # ------------------------------------------------------------------
    def save_entity():
        global selected_entity_idx
        name = editor_widgets["Name"].get().strip()
        if not name:
            status_callback("Error: Name is required", is_error=True)
            return
        try:
            x = snap(float(editor_widgets["x"].get() or 0))
            z = snap(float(editor_widgets["z"].get() or 0))
            rot_x = float(editor_widgets["rotation_x"].get() or 0)
            rot_y = float(editor_widgets["rotation_y"].get() or 0)
            rot_z = float(editor_widgets["rotation_z"].get() or 0)
        except ValueError:
            status_callback("Error: invalid number", is_error=True)
            return
        scale_str = editor_widgets["scale"].get().strip()
        if scale_str:
            try:
                parts = scale_str.strip("()").split(",")
                sx, sy, sz = snap(float(parts[0])), float(parts[1]), snap(float(parts[2]))
            except:
                sx, sy, sz = 1, 1, 1
        else:
            sx, sy, sz = 1, 1, 1

        y_str = editor_widgets["y"].get().strip()
        if selected_entity_idx is not None:
            ent = entities[selected_entity_idx]
            py = snap(float(y_str)) if y_str else float(ent.get("y", 0))
        else:
            if selected_layer_idx is None:
                status_callback("Error: select a layer first", is_error=True)
                return
            py = snap(float(y_str)) if y_str else layers[selected_layer_idx]
            selected_entity_idx = len(entities)
            ent = make_default_entity(name)
            entities.append(ent)

        ent.update({
            "Name": name,
            "x": x, "z": z, "y": py,
            "scale": f"({sx}, {sy}, {sz})",
            "scale_x": sx, "scale_y": sy, "scale_z": sz,
            "position": f"({x}, {py}, {z})",
            "rotation_x": rot_x, "rotation_y": rot_y, "rotation_z": rot_z,
            "model": editor_widgets["model"].get().strip(),
            "texture": editor_widgets["texture"].get().strip(),
            "color": editor_widgets["color"].get().strip(),
            "enabled": editor_widgets["enabled"].get().strip(),
            "visible": editor_widgets["visible"].get().strip(),
            "collider": editor_widgets["collider"].get().strip()
        })

        obj_lisbox.delete(0, tk.END)
        for e in entities:
            obj_lisbox.insert(tk.END, e.get("Name", ""))
        obj_lisbox.selection_set(selected_entity_idx)
        status_callback(f"Entity '{name}' saved")
        refresh_canvas(status_callback)

    def delete_entity():
        global selected_entity_idx
        if selected_entity_idx is None:
            status_callback("Error: no entity selected", is_error=True)
            return
        name = entities[selected_entity_idx].get("Name", "?")
        del entities[selected_entity_idx]
        obj_lisbox.delete(selected_entity_idx)
        selected_entity_idx = None
        clear_editor()
        status_callback(f"Entity '{name}' deleted")
        refresh_canvas(status_callback)

    def add_layer():
        y_val = addety.get().strip()
        if not y_val:
            status_callback("Error: enter a y value", is_error=True)
            return
        try:
            y_float = float(y_val)
        except ValueError:
            status_callback("Error: invalid y value", is_error=True)
            return
        if y_float in layers:
            status_callback(f"Error: layer y={y_float} exists", is_error=True)
            return
        layers.append(y_float)
        layer_lisbox.insert(tk.END, f"Layer y={y_float}")
        addety.delete(0, tk.END)
        refresh_y_combobox()
        status_callback(f"Layer y={y_float} added")

    def delete_layer():
        sel = layer_lisbox.curselection()
        if not sel:
            status_callback("Error: no layer selected", is_error=True)
            return
        idx = sel[0]
        y = layers.pop(idx)
        layer_lisbox.delete(idx)
        global selected_layer_idx
        if selected_layer_idx == idx:
            selected_layer_idx = None
        elif selected_layer_idx is not None and selected_layer_idx > idx:
            selected_layer_idx -= 1
        refresh_y_combobox()
        status_callback(f"Layer y={y} deleted")
        refresh_canvas(status_callback)

    # Initial refresh
    refresh_y_combobox()
    refresh_canvas(status_callback)
    return scene_frame