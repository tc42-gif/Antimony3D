import tkinter as tk
from tkinter import ttk
from block_pack import CAT_COLORS, CODE_TEMPLATES, BLOCK_CATEGORIES
from utils import fmt_block, ResizableEntry
import json
import os

# ----------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------
scene_script = []
scene_objects = {"entities": [], "variables": [], "functions": []}
code_ws_frame = None
code_obj_frame = None
pal_inner = None
pal_canvas = None
jump_combo = None

# Drag state for block reordering
_drag_data = {"block": None, "orig_index": -1, "drag_widget": None}
# Drag state for palette drag‑and‑drop
_palette_drag = {"block_id": None, "drag_widget": None}

# ----------------------------------------------------------------------
# Rendering a block (top‑level or nested)
# ----------------------------------------------------------------------
def render_block(parent, block_data, refresh_func, is_nested=False, parent_idx=None, param_key=None, remove_callback=None):
    t = block_data["type"]
    tmpl_def = CODE_TEMPLATES.get(t, {})
    is_options = tmpl_def.get("is_options", False)

    cat_name = None
    for cn, bids in BLOCK_CATEGORIES:
        if t in bids:
            cat_name = cn
            break
    color = CAT_COLORS.get(cat_name, "#888")
    label_text = t.replace("_", " ").title()

    # Outer frame – packs with anchor to avoid full‑width stretching
    outer = tk.Frame(parent, bg="white")
    outer.pack(side="top", anchor="w", pady=2)
    outer.block_data = block_data  # for drag detection

    indent_level = block_data.get("indent", 0)
    if indent_level > 0:
        spacer = tk.Frame(outer, width=indent_level * 20, bg="white")
        spacer.pack(side="left", fill="y")

    bf = tk.Frame(outer, bd=3, relief="solid", bg=color)
    bf.pack(fill="x", expand=True)

    hdr = tk.Frame(bf, bg=color)
    hdr.pack(fill="x")

    # Drag handle (only for top‑level blocks)
    if not is_nested:
        drag_handle = tk.Label(hdr, text="⠿", bg=color, fg="white", cursor="fleur")
        drag_handle.pack(side="left", padx=2)
        drag_handle.bind("<ButtonPress-1>", lambda e, bd=block_data: start_drag_block(e, bd))
        drag_handle.bind("<B1-Motion>", lambda e, bd=block_data: drag_block(e, bd))
        drag_handle.bind("<ButtonRelease-1>", lambda e, bd=block_data: end_drag_block(e, bd))

    tk.Label(hdr, text=label_text, bg=color, fg="white", font=("TkDefaultFont", 11, "bold")).pack(side="left", padx=6, pady=2)

    if not is_nested:
        # Outdent/Indent buttons
        tk.Button(hdr, text="←", font=("TkDefaultFont", 8), width=2,
                  command=lambda: outdent_block(block_data, refresh_func)).pack(side="right", padx=1)
        tk.Button(hdr, text="→", font=("TkDefaultFont", 8), width=2,
                  command=lambda: indent_block(block_data, refresh_func)).pack(side="right", padx=1)
        # Delete button
        tk.Button(hdr, text="✕", font=("TkDefaultFont", 8), width=2, fg="red",
                  command=lambda: remove_global_block(block_data, refresh_func)).pack(side="right", padx=1)
    else:
        if remove_callback:
            tk.Button(hdr, text="✕", font=("TkDefaultFont", 8), width=2, fg="red",
                      command=remove_callback).pack(side="right", padx=1)
        else:
            tk.Button(hdr, text="✕", font=("TkDefaultFont", 8), width=2, fg="red",
                      command=lambda: remove_nested_block(parent_idx, param_key, refresh_func)).pack(side="right", padx=1)

    # Parameters rendering
    params = CODE_TEMPLATES[t].get("params", [])
    if params:
        pframe = tk.Frame(bf, bg="white")
        pframe.pack(fill="x", padx=6, pady=4)
        row_frame = None
        for i, pd in enumerate(params):
            if i % 3 == 0:
                row_frame = tk.Frame(pframe, bg="white")
                row_frame.pack(fill="x", pady=1)
            pkey = pd["name"]
            plabel = pd["label"]
            pdefault = pd["default"]
            ptype = pd.get("type", "entry")

            param_container = tk.Frame(row_frame, bg="white")
            param_container.pack(side="left", padx=2)

            tk.Label(param_container, text=plabel+":", bg="white", font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=2)

            val = block_data.get("params", {}).get(pkey, pdefault)

            if isinstance(val, dict) and "type" in val and val["type"] in CODE_TEMPLATES:
                nested_frame = tk.Frame(param_container, bg="white")
                nested_frame.pack(side="left", padx=2)
                def remove_this_nested(bd=block_data, key=pkey):
                    bd["params"][key] = fmt_block(bd["params"][key])
                    refresh_func()
                render_block(nested_frame, val, refresh_func, is_nested=True, remove_callback=remove_this_nested)
            else:
                if ptype == "text":
                    tw_frame, tw, fn_update_ln = make_line_numbered_text(param_container, height=4, width=30)
                    tw_frame.pack(side="left", fill="x", expand=True, padx=2)
                    tw.insert("1.0", str(val))
                    tw.bind("<Button-3>", lambda e, w=tw: insert_block_into_text_menu(e, w))
                    def save_text(*args, bd=block_data, key=pkey, w=tw):
                        bd["params"][key] = w.get("1.0", "end-1c")
                        refresh_func()
                    tw.bind("<KeyRelease>", lambda e, s=save_text, u=fn_update_ln: (u(), s()))
                    tw.bind("<Return>", lambda e: (tw.after(1, fn_update_ln), "break"))
                    fn_update_ln()
                else:
                    ef = tk.Frame(param_container, bg="white")
                    ef.pack(side="left", padx=1)
                    is_expanded = [False]
                    current_text = [str(val)]
                    var = tk.StringVar(value=str(val))
                    var.trace("w", lambda *a, bd=block_data, key=pkey, v=var: bd["params"].__setitem__(key, v.get()))
                    text_widget_ref = [None]

                    def rebuild_entry():
                        for w in ef.winfo_children():
                            w.destroy()
                        e = ResizableEntry(ef, textvariable=var, width=12)
                        e.pack(side="left")
                        # Fix focus issues
                        e.bind("<Escape>", lambda ev: e.master.focus_set())
                        e.bind("<FocusOut>", lambda ev: e.selection_clear())
                        bi = tk.Button(ef, text=">>", font=("TkDefaultFont", 8), width=2)
                        bi.pack(side="left", padx=1)
                        bi.bind("<Button-1>", lambda e2, bd=block_data, key=pkey: insert_block_menu(e2, bd, key, refresh_func))
                        be = tk.Button(ef, text="⤡", font=("TkDefaultFont", 8), width=2,
                                       command=lambda k=pkey: toggle_mode(k))
                        be.pack(side="left", padx=1)
                        text_widget_ref[0] = None

                    def rebuild_text():
                        for w in ef.winfo_children():
                            w.destroy()
                        tw_frame, tw, fn_up = make_line_numbered_text(ef, height=4, width=30)
                        tw_frame.pack(fill="x", expand=True)
                        tw.insert("1.0", current_text[0])
                        tw.bind("<Button-3>", lambda e2, w=tw: insert_block_into_text_menu(e2, w))
                        def st(*args, bd=block_data, key=pkey, w=tw):
                            txt = w.get("1.0", "end-1c")
                            bd["params"][key] = txt
                            current_text[0] = txt
                            var.set(txt)
                        tw.bind("<KeyRelease>", lambda e2, s=st, u=fn_up: (u(), s()))
                        tw.bind("<Return>", lambda e2: (tw.after(1, fn_up), "break"))
                        fn_up()
                        text_widget_ref[0] = tw
                        bc = tk.Button(ef, text="⤢", font=("TkDefaultFont", 8), width=2,
                                       command=lambda k=pkey: toggle_mode(k))
                        bc.pack(side="left")

                    def toggle_mode(key):
                        if is_expanded[0]:
                            if text_widget_ref[0]:
                                current_text[0] = text_widget_ref[0].get("1.0", "end-1c")
                                block_data["params"][key] = current_text[0]
                                var.set(current_text[0])
                            is_expanded[0] = False
                            rebuild_entry()
                        else:
                            current_text[0] = var.get()
                            is_expanded[0] = True
                            rebuild_text()
                    rebuild_entry()
    return outer

# ----------------------------------------------------------------------
# Drag‑and‑drop for block reordering (top‑level)
# ----------------------------------------------------------------------
def start_drag_block(event, block_data):
    _drag_data["block"] = block_data
    _drag_data["orig_index"] = scene_script.index(block_data)
    # Create a floating window to follow mouse (optional)
    _drag_data["drag_widget"] = tk.Toplevel(event.widget.winfo_toplevel())
    _drag_data["drag_widget"].overrideredirect(True)
    _drag_data["drag_widget"].geometry(f"+{event.x_root}+{event.y_root}")
    lbl = tk.Label(_drag_data["drag_widget"], text=block_data["type"], bg="lightblue", relief="solid")
    lbl.pack()

def drag_block(event, block_data):
    if _drag_data["drag_widget"]:
        _drag_data["drag_widget"].geometry(f"+{event.x_root}+{event.y_root}")

def end_drag_block(event, block_data):
    if _drag_data["drag_widget"]:
        _drag_data["drag_widget"].destroy()
        _drag_data["drag_widget"] = None

    # Find the widget under the cursor
    widget = event.widget.winfo_containing(event.x_root, event.y_root)
    target_block = None
    if widget:
        # Traverse parents to find a frame with 'block_data' attribute
        while widget:
            if hasattr(widget, "block_data"):
                target_block = widget.block_data
                break
            widget = widget.master
    if target_block is not None and target_block != _drag_data["block"]:
        orig_idx = _drag_data["orig_index"]
        target_idx = scene_script.index(target_block)
        if orig_idx < target_idx:
            target_idx += 1  # because we remove first
        # Move block
        block = scene_script.pop(orig_idx)
        scene_script.insert(target_idx, block)
        refresh_global_ws()
    _drag_data["block"] = None
    _drag_data["orig_index"] = -1

# ----------------------------------------------------------------------
# Drag from palette to workspace
# ----------------------------------------------------------------------
def start_palette_drag(event, block_id):
    _palette_drag["block_id"] = block_id
    _palette_drag["drag_widget"] = tk.Toplevel(event.widget.winfo_toplevel())
    _palette_drag["drag_widget"].overrideredirect(True)
    _palette_drag["drag_widget"].geometry(f"+{event.x_root}+{event.y_root}")
    lbl = tk.Label(_palette_drag["drag_widget"], text=block_id, bg="lightgreen", relief="solid")
    lbl.pack()

def drag_palette(event):
    if _palette_drag["drag_widget"]:
        _palette_drag["drag_widget"].geometry(f"+{event.x_root}+{event.y_root}")

def end_palette_drop(event):
    if _palette_drag["drag_widget"]:
        _palette_drag["drag_widget"].destroy()
        _palette_drag["drag_widget"] = None
    # Determine drop position
    widget = event.widget.winfo_containing(event.x_root, event.y_root)
    target_block = None
    if widget:
        while widget:
            if hasattr(widget, "block_data"):
                target_block = widget.block_data
                break
            widget = widget.master
    # Create a new block
    block_id = _palette_drag["block_id"]
    if block_id and block_id in CODE_TEMPLATES:
        default_params = {p["name"]: p["default"] for p in CODE_TEMPLATES[block_id]["params"]}
        new_block = {"type": block_id, "params": default_params, "indent": 0}
        if target_block is not None:
            idx = scene_script.index(target_block)
            scene_script.insert(idx + 1, new_block)
        else:
            scene_script.append(new_block)
        refresh_global_ws()
    _palette_drag["block_id"] = None

# ----------------------------------------------------------------------
# Insertion menus, nested block helpers
# ----------------------------------------------------------------------
def insert_block_menu(event, parent_block, param_key, refresh_func):
    menu = tk.Menu(event.widget, tearoff=0)
    for cat_name, block_ids in BLOCK_CATEGORIES:
        cat_menu = tk.Menu(menu, tearoff=0)
        for bid in block_ids:
            if bid in CODE_TEMPLATES:
                cat_menu.add_command(label=bid, command=lambda b=bid, pb=parent_block, pk=param_key: add_nested_block_to_param(b, pb, pk, refresh_func))
        menu.add_cascade(label=cat_name, menu=cat_menu)
    menu.tk_popup(event.x_root, event.y_root)

def add_nested_block_to_param(bid, parent_block, param_key, refresh_func):
    default_params = {p["name"]: p["default"] for p in CODE_TEMPLATES[bid]["params"]}
    parent_block["params"][param_key] = {
        "type": bid,
        "params": default_params
    }
    refresh_func()

def remove_nested_block(parent_idx, param_key, refresh_func):
    if 0 <= parent_idx < len(scene_script):
        parent_block = scene_script[parent_idx]
        nested_block = parent_block["params"][param_key]
        parent_block["params"][param_key] = fmt_block(nested_block)
        refresh_func()

# ----------------------------------------------------------------------
# Multi‑line text helpers
# ----------------------------------------------------------------------
def make_line_numbered_text(parent, height=4, width=30):
    tw_frame = tk.Frame(parent, bg="white")
    line_num = tk.Text(tw_frame, width=3, height=height, bg="#f0f0f0",
                       font=("TkDefaultFont", 9), state="disabled",
                       relief="flat", padx=2, highlightthickness=0, cursor="arrow")
    line_num.pack(side="left", fill="y")
    tw = tk.Text(tw_frame, height=height, width=width, font=("TkDefaultFont", 9),
                 undo=True, padx=2)
    tw.pack(side="left", fill="both", expand=True)
    def fn_update():
        lines = int(tw.index("end-1c").split(".")[0])
        line_num.config(state="normal")
        line_num.delete("1.0", tk.END)
        line_num.insert("1.0", "\n".join(str(i+1) for i in range(lines)))
        line_num.config(state="disabled")
    tw.bind("<KeyRelease>", lambda e: fn_update())
    tw.bind("<Return>", lambda e: (tw.after(1, fn_update), "break"))
    tw.bind("<Button-1>", lambda e: tw.after(1, fn_update))
    return tw_frame, tw, fn_update

def insert_block_into_text_menu(event, text_widget):
    menu = tk.Menu(event.widget, tearoff=0)
    for cat_name, block_ids in BLOCK_CATEGORIES:
        cat_menu = tk.Menu(menu, tearoff=0)
        for bid in block_ids:
            if bid in CODE_TEMPLATES:
                cat_menu.add_command(
                    label=bid,
                    command=lambda b=bid, tw=text_widget: insert_rendered_block_into_text(tw, b)
                )
        menu.add_cascade(label=cat_name, menu=cat_menu)
    menu.tk_popup(event.x_root, event.y_root)

def insert_rendered_block_into_text(text_widget, block_id):
    default_params = {p["name"]: p["default"] for p in CODE_TEMPLATES[block_id]["params"]}
    block = {"type": block_id, "params": default_params}
    rendered = fmt_block(block)
    try:
        cursor_pos = text_widget.index(tk.INSERT)
        text_widget.insert(cursor_pos, rendered)
    except:
        text_widget.insert(tk.END, rendered)

# ----------------------------------------------------------------------
# Top‑level block operations
# ----------------------------------------------------------------------
def find_block_index(block_data):
    try:
        return scene_script.index(block_data)
    except ValueError:
        return -1

def outdent_block(block_data, refresh_func):
    idx = find_block_index(block_data)
    if idx == -1:
        return
    new_indent = max(block_data.get("indent", 0) - 1, 0)
    if new_indent == block_data.get("indent", 0):
        return
    block_data["indent"] = new_indent
    refresh_func()

def indent_block(block_data, refresh_func):
    idx = find_block_index(block_data)
    if idx == -1:
        return
    block_data["indent"] = block_data.get("indent", 0) + 1
    refresh_func()

def remove_global_block(block_data, refresh_func):
    idx = find_block_index(block_data)
    if idx != -1:
        del scene_script[idx]
        refresh_func()

def add_global_block(block_id, refresh_func):
    indent = 0
    if scene_script:
        prev = scene_script[-1]
        prev_type = prev["type"]
        prev_indent_after = CODE_TEMPLATES.get(prev_type, {}).get("indent_after", False)
        if prev_indent_after:
            indent = prev.get("indent", 0) + 1
        else:
            indent = prev.get("indent", 0)
    scene_script.append({"type": block_id, "params": {}, "indent": indent})
    refresh_func()

def clear_global(refresh_func):
    scene_script.clear()
    refresh_func()

# ----------------------------------------------------------------------
# Workspace refresh
# ----------------------------------------------------------------------
def refresh_global_ws():
    global code_ws_frame
    if code_ws_frame is None:
        return
    for w in code_ws_frame.winfo_children():
        w.destroy()
    for block_data in scene_script:
        render_block(code_ws_frame, block_data, refresh_global_ws, is_nested=False)

# ----------------------------------------------------------------------
# Objects panel refresh
# ----------------------------------------------------------------------
def refresh_objects_panel(obj_frame, entities=None):
    if entities is not None:
        scene_objects["entities"] = entities
    else:
        entities = scene_objects.get("entities", [])

    for w in obj_frame.winfo_children():
        w.destroy()

    tk.Label(obj_frame, text="Entities", font=("TkDefaultFont", 9, "bold"), bg="#e0e0e0", anchor="w").pack(fill="x", padx=2, pady=1)
    for ent in entities:
        n = ent.get("Name", "?")
        f = tk.Frame(obj_frame, bg="#e8e8e8")
        f.pack(fill="x", padx=4)
        tk.Label(f, text="● " + n, bg="#e8e8e8", font=("TkDefaultFont", 8)).pack(side="left")

    vhdr = tk.Frame(obj_frame, bg="#e0e0e0")
    vhdr.pack(fill="x", padx=2, pady=1)
    tk.Label(vhdr, text="Variables", font=("TkDefaultFont", 9, "bold"), bg="#e0e0e0").pack(side="left")
    tk.Button(vhdr, text="+", font=("TkDefaultFont", 8), width=2,
              command=lambda: add_object_var(obj_frame)).pack(side="right")
    for v in scene_objects.get("variables", []):
        f = tk.Frame(obj_frame, bg="#e8e8e8")
        f.pack(fill="x", padx=4)
        tk.Label(f, text="   " + v["name"] + " = " + v["value"], bg="#e8e8e8", font=("TkDefaultFont", 8), anchor="w").pack(fill="x", side="left")

    fhdr = tk.Frame(obj_frame, bg="#e0e0e0")
    fhdr.pack(fill="x", padx=2, pady=1)
    tk.Label(fhdr, text="Functions", font=("TkDefaultFont", 9, "bold"), bg="#e0e0e0").pack(side="left")
    tk.Button(fhdr, text="+", font=("TkDefaultFont", 8), width=2,
              command=lambda: add_object_func(obj_frame)).pack(side="right")
    for f in scene_objects.get("functions", []):
        p_label = tk.Frame(obj_frame, bg="#e8e8e8")
        p_label.pack(fill="x", padx=4)
        tk.Label(p_label, text="   " + f["name"] + "(" + f.get("params", "") + ")", bg="#e8e8e8", font=("TkDefaultFont", 8), anchor="w").pack(fill="x", side="left")

def add_object_var(obj_frame):
    from tkinter import simpledialog
    root_window = obj_frame.winfo_toplevel()
    name = simpledialog.askstring("Add Variable", "Variable name:", parent=root_window)
    if not name:
        return
    value = simpledialog.askstring("Add Variable", f"Default value for '{name}':", parent=root_window, initialvalue="0")
    if value is None:
        value = "0"
    scene_objects.setdefault("variables", []).append({"name": name, "value": value})
    refresh_objects_panel(obj_frame)

def add_object_func(obj_frame):
    from tkinter import simpledialog
    root_window = obj_frame.winfo_toplevel()
    name = simpledialog.askstring("Add Function", "Function name:", parent=root_window)
    if not name:
        return
    params = simpledialog.askstring("Add Function", f"Parameters for '{name}' (comma-separated):", parent=root_window, initialvalue="")
    if params is None:
        params = ""
    scene_objects.setdefault("functions", []).append({"name": name, "params": params})
    refresh_objects_panel(obj_frame)

# ----------------------------------------------------------------------
# Get script text (for Copy Script)
# ----------------------------------------------------------------------
def get_script_text():
    lines = []
    for block in scene_script:
        t = block["type"]
        raw = fmt_block(block)
        indent_level = block.get("indent", 0)
        indent_str = "    " * indent_level
        lines.append(indent_str + raw)
    return "\n".join(lines)

def copy_script_to_clipboard(status_callback):
    script = get_script_text()
    import main
    main.root.clipboard_clear()
    main.root.clipboard_append(script)
    status_callback("Scene script copied to clipboard")

# ----------------------------------------------------------------------
# Import add‑on pack
# ----------------------------------------------------------------------
def load_addon_pack(filepath, status_callback):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.get("CAT_COLORS", {}).items():
            CAT_COLORS[k] = v
        for k, v in data.get("CODE_TEMPLATES", {}).items():
            CODE_TEMPLATES[k] = v
        existing_cats = {c[0]: c for c in BLOCK_CATEGORIES}
        for cat_name, block_ids in data.get("BLOCK_CATEGORIES", []):
            if cat_name in existing_cats:
                for bid in block_ids:
                    if bid not in existing_cats[cat_name][1]:
                        existing_cats[cat_name][1].append(bid)
            else:
                BLOCK_CATEGORIES.append([cat_name, block_ids])
        status_callback(f"Loaded add-on: {os.path.basename(filepath)}")
        rebuild_palette()
        refresh_global_ws()
    except Exception as e:
        status_callback(f"Error loading add-on: {e}", is_error=True)

def import_addon(status_callback):
    from tkinter import filedialog
    path = filedialog.askopenfilename(filetypes=[("Block Pack files", "*.aubp")])
    if path:
        load_addon_pack(path, status_callback)

# ----------------------------------------------------------------------
# Rebuild palette (called after loading packs)
# ----------------------------------------------------------------------
def rebuild_palette():
    global pal_inner, jump_combo
    if pal_inner is None:
        return
    for w in pal_inner.winfo_children():
        w.destroy()
    for cat_name, block_ids in BLOCK_CATEGORIES:
        cf = tk.LabelFrame(pal_inner, text=cat_name, padx=4, pady=4, bg="#f0f0f0", font=("TkDefaultFont", 9, "bold"))
        cf.pack(fill="x", padx=4, pady=2)
        for bid in block_ids:
            if bid not in CODE_TEMPLATES:
                continue
            tmpl = CODE_TEMPLATES[bid]["template"]
            color = CAT_COLORS.get(cat_name, "#888")
            btn = tk.Button(cf, text=tmpl, bg=color, fg="white", font=("TkDefaultFont", 8, "bold"), padx=4, pady=3, anchor="w",
                            command=lambda b=bid: add_global_block(b, refresh_global_ws))
            # Enable drag from palette
            btn.bind("<ButtonPress-1>", lambda e, b=bid: start_palette_drag(e, b))
            btn.bind("<B1-Motion>", drag_palette)
            btn.bind("<ButtonRelease-1>", end_palette_drop)
            btn.pack(fill="x", pady=1)
    if jump_combo:
        jump_combo['values'] = [c[0] for c in BLOCK_CATEGORIES]

# ----------------------------------------------------------------------
# Build the Code Editor UI
# ----------------------------------------------------------------------
def build_code_editor(parent, entities, status_callback):
    global code_ws_frame, code_obj_frame, pal_inner, pal_canvas, jump_combo

    # Objects panel (left)
    obj_outer = tk.Frame(parent, width=175, bg="#e8e8e8")
    obj_outer.pack(side="left", fill="y")
    obj_outer.pack_propagate(False)
    tk.Label(obj_outer, text="Objects", font=("TkDefaultFont", 11, "bold"), bg="#e0e0e0").pack(fill="x", padx=2, pady=1)
    obj_canvas = tk.Canvas(obj_outer, bg="#e8e8e8", highlightthickness=0)
    obj_scroll = tk.Scrollbar(obj_outer, orient="vertical", command=obj_canvas.yview)
    obj_frame = tk.Frame(obj_canvas, bg="#e8e8e8")
    obj_frame.bind("<Configure>", lambda e: obj_canvas.configure(scrollregion=obj_canvas.bbox("all")))
    obj_canvas.create_window((0, 0), window=obj_frame, anchor="nw")
    obj_canvas.configure(yscrollcommand=obj_scroll.set)
    obj_canvas.pack(side="left", fill="both", expand=True)
    obj_scroll.pack(side="right", fill="y")
    code_obj_frame = obj_frame

    # Block palette (middle)
    pal_outer = tk.Frame(parent, width=210, bg="#f0f0f0")
    pal_outer.pack(side="left", fill="y")
    pal_outer.pack_propagate(False)
    tk.Label(pal_outer, text="Block Palette", font=("TkDefaultFont", 12, "bold"), bg="#f0f0f0").pack(pady=4)

    jump_frame = tk.Frame(pal_outer, bg="#f0f0f0")
    jump_frame.pack(fill="x", padx=4, pady=4)
    tk.Label(jump_frame, text="Jump to:", bg="#f0f0f0").pack(side="left")
    jump_combo = ttk.Combobox(jump_frame, values=[c[0] for c in BLOCK_CATEGORIES], state="readonly", width=15)
    jump_combo.pack(side="left", padx=2)
    def on_jump_select(event):
        selected_cat = jump_combo.get()
        for widget in pal_inner.winfo_children():
            if isinstance(widget, tk.LabelFrame) and widget.cget("text") == selected_cat:
                y = widget.winfo_y()
                pal_canvas.yview_moveto(y / max(1, pal_inner.winfo_reqheight()))
                break
    jump_combo.bind("<<ComboboxSelected>>", on_jump_select)

    pal_canvas = tk.Canvas(pal_outer, bg="#f0f0f0", highlightthickness=0)
    pal_scroll = tk.Scrollbar(pal_outer, orient="vertical", command=pal_canvas.yview)
    pal_scroll.pack(side="right", fill="y")
    pal_canvas.pack(side="left", fill="both", expand=True)
    pal_inner = tk.Frame(pal_canvas, bg="#f0f0f0")
    pal_inner.bind("<Configure>", lambda e: pal_canvas.configure(scrollregion=pal_canvas.bbox("all")))
    pal_canvas.create_window((0, 0), window=pal_inner, anchor="nw")
    pal_canvas.configure(yscrollcommand=pal_scroll.set)
    rebuild_palette()

    # Workspace (right) with horizontal and vertical scroll
    right = tk.Frame(parent)
    right.pack(side="right", fill="both", expand=True)

    toolbar = tk.Frame(right)
    toolbar.pack(fill="x")
    tk.Button(toolbar, text="Copy Script", font=("TkDefaultFont", 9),
              command=lambda: copy_script_to_clipboard(status_callback)).pack(side="left", padx=5, pady=3)
    tk.Button(toolbar, text="Import Pack", font=("TkDefaultFont", 9),
              command=lambda: import_addon(status_callback)).pack(side="left", padx=5, pady=3)
    tk.Button(toolbar, text="Clear All", font=("TkDefaultFont", 9),
              command=lambda: clear_global(refresh_global_ws)).pack(side="left", padx=5, pady=3)

    ws_container = tk.Frame(right)
    ws_container.pack(fill="both", expand=True)

    ws_canvas = tk.Canvas(ws_container, bg="white", highlightthickness=0)
    ws_scroll_y = tk.Scrollbar(ws_container, orient="vertical", command=ws_canvas.yview)
    ws_scroll_x = tk.Scrollbar(ws_container, orient="horizontal", command=ws_canvas.xview)

    ws_frame = tk.Frame(ws_canvas, bg="white")
    ws_frame.bind("<Configure>", lambda e: ws_canvas.configure(scrollregion=ws_canvas.bbox("all")))
    ws_canvas.create_window((0, 0), window=ws_frame, anchor="nw")
    ws_canvas.configure(yscrollcommand=ws_scroll_y.set, xscrollcommand=ws_scroll_x.set)

    ws_canvas.pack(side="top", fill="both", expand=True)
    ws_scroll_y.pack(side="right", fill="y")
    ws_scroll_x.pack(side="bottom", fill="x")

    # Click on canvas to clear focus
    ws_canvas.bind("<Button-1>", lambda e: ws_canvas.focus_set())

    # Mouse wheel scrolling
    def on_mousewheel(event):
        ws_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def on_shift_mousewheel(event):
        ws_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    ws_canvas.bind("<MouseWheel>", on_mousewheel)
    ws_canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
    ws_frame.bind("<MouseWheel>", on_mousewheel)
    ws_frame.bind("<Shift-MouseWheel>", on_shift_mousewheel)

    # Middle-click drag pan
    ws_canvas.bind("<Button-2>", lambda e: ws_canvas.scan_mark(e.x, e.y))
    ws_canvas.bind("<B2-Motion>", lambda e: ws_canvas.scan_dragto(e.x, e.y, gain=1))
    ws_frame.bind("<Button-2>", lambda e: ws_canvas.scan_mark(e.x, e.y))
    ws_frame.bind("<B2-Motion>", lambda e: ws_canvas.scan_dragto(e.x, e.y, gain=1))

    code_ws_frame = ws_frame

    refresh_objects_panel(code_obj_frame, entities)
    refresh_global_ws()

    return right