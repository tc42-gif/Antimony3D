import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import subprocess
import tempfile
import keyword
import pprint

from block_pack import load_block_defs, save_block_defs, CAT_COLORS, CODE_TEMPLATES, BLOCK_CATEGORIES, open_block_pack_editor
from scene_editor import build_scene_editor, entities, layers, selected_entity_idx, selected_layer_idx, refresh_canvas, canva
from code_editor import build_code_editor, scene_script, scene_objects, refresh_global_ws, refresh_objects_panel, code_obj_frame, get_script_text
from utils import fmt_block

# ----------------------------------------------------------------------
# Global root and status
# ----------------------------------------------------------------------
root = tk.Tk()
root.geometry('1200x700')
root.title('Ursina Scene Builder')

status_var = tk.StringVar()
status_var.set("Ready")
status_label = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

def set_status(msg, is_error=False, duration=3000):
    status_var.set(msg)
    if duration > 0:
        root.after(duration, lambda: status_var.set("Ready"))

# ----------------------------------------------------------------------
# Notebook
# ----------------------------------------------------------------------
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

scene_frame = build_scene_editor(notebook, set_status)
notebook.add(scene_frame, text="Scene Builder")

code_frame = tk.Frame(notebook)
notebook.add(code_frame, text="Code Editor")
build_code_editor(code_frame, entities, set_status)

# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
menubar = tk.Menu(root)
root.config(menu=menubar)

# File menu
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save Scene & Script", command=lambda: save_scene())
file_menu.add_command(label="Load Scene & Script", command=lambda: load_scene())
file_menu.add_separator()
file_menu.add_command(label="Export Scene (single .py)", command=lambda: export_scene_combined())
file_menu.add_command(label="Edit Block Pack", command=lambda: open_block_pack_editor(root, set_status))
file_menu.add_separator()
file_menu.add_command(label="Run Scene", command=lambda: run_scene())

# Help menu
help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=lambda: show_about())

def show_about():
    messagebox.showinfo("About Ursina Scene Builder",
                        "Ursina Scene Builder\n\n"
                        "A visual scene editor for Ursina engine.\n"
                        "Create scenes with entities, layers, and code blocks.\n"
                        "Export to a single Python script or run directly.\n\n"
                        "Version 1.0\n"
                        "© 2025")

# ----------------------------------------------------------------------
# File operations
# ----------------------------------------------------------------------
def save_scene():
    path = filedialog.asksaveasfilename(defaultextension=".aucf", filetypes=[("Ursina Scene files", "*.aucf")])
    if not path:
        return
    data = {
        "layers": layers,
        "entities": entities,
        "scene_script": scene_script,
        "scene_objects": scene_objects
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    set_status(f"Scene & Script saved to {os.path.basename(path)}")

def load_scene(path=None):
    global entities, layers, selected_entity_idx, selected_layer_idx, scene_script, scene_objects
    if path is None:
        path = filedialog.askopenfilename(filetypes=[("Ursina Scene files", "*.aucf")])
        if not path:
            return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entities.clear()
        entities.extend(data.get("entities", []))
        layers.clear()
        layers.extend(data.get("layers", []))
        scene_script.clear()
        scene_script.extend(data.get("scene_script", []))
        scene_objects.clear()
        scene_objects.update(data.get("scene_objects", {"variables": [], "functions": []}))

        selected_entity_idx = None
        selected_layer_idx = None

        from scene_editor import obj_lisbox, layer_lisbox, clear_editor
        obj_lisbox.delete(0, tk.END)
        for e in entities:
            obj_lisbox.insert(tk.END, e.get("Name", ""))
        layer_lisbox.delete(0, tk.END)
        for ly in layers:
            layer_lisbox.insert(tk.END, f"Layer y={ly}")
        clear_editor()
        refresh_canvas(set_status)
        refresh_global_ws()
        refresh_objects_panel(code_obj_frame, entities)
        set_status(f"Loaded {len(entities)} entities, {len(layers)} layers from {os.path.basename(path)}")
    except Exception as e:
        set_status(f"Error loading scene: {e}", is_error=True)

def export_scene_combined():
    path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
    if not path:
        return
    combined_code = generate_combined_script()
    with open(path, "w", encoding="utf-8") as f:
        f.write(combined_code)
    set_status(f"Exported combined script: {os.path.basename(path)}")

def generate_combined_script():
    # Prepare entity data (unchanged)
    entities_data = []
    for ent in entities:
        e = {
            "Name": ent.get("Name", ""),
            "model": ent.get("model", "cube"),
            "texture": ent.get("texture", ""),
            "color": ent.get("color", "color.white"),
            "scale": ent.get("scale", "(1, 1, 1)"),
            "position": f"({ent.get('x',0)}, {ent.get('y',0)}, {ent.get('z',0)})",
            "rotation": (ent.get("rotation_x",0), ent.get("rotation_y",0), ent.get("rotation_z",0)),
            "enabled": ent.get("enabled", "True"),
            "visible": ent.get("visible", "True"),
            "collider": ent.get("collider", "box"),
        }
        entities_data.append(e)

    data_str = pprint.pformat(entities_data, indent=2)

    # Generate scene script (unchanged)
    scene_code = generate_scene_code_only()

    # Build the complete script
    return f'''# Automatically generated combined Ursina scene
from ursina import *
import random
import keyword
app = Ursina()

# Entity data (for reference)
entities_data = {data_str}

# Create entities and assign to named variables when possible
for item in entities_data:
    ent = Entity(
        model=item.get('model', 'cube'),
        texture=item.get('texture', None) or None,
        color=eval(item['color']) if isinstance(item['color'], str) else color.white,
        scale=eval(item['scale']) if isinstance(item['scale'], str) else item['scale'],
        position=eval(item['position']) if isinstance(item['position'], str) else item['position'],
        rotation=eval(item['rotation']) if isinstance(item['rotation'], str) else item['rotation'],
        enabled=item.get('enabled', 'True') == 'True',
        visible=item.get('visible', 'True') == 'True',
        collider=item.get('collider', None) or None,
    )
    name = item.get('Name', '')
    if name and name.isidentifier() and not keyword.iskeyword(name):
        globals()[name] = ent

# Scene script
{scene_code}

app.run()
'''

def generate_scene_code_only():
    # (keep your existing implementation)
    if not scene_script:
        return "# (no scene script blocks)"
    lines = []
    for block in scene_script:
        t = block["type"]
        raw = fmt_block(block)
        indent_level = block.get("indent", 0)
        indent_str = "    " * indent_level
        if t == "on_update":
            lines.append("def update():")
            continue
        elif t == "on_key":
            k = block.get("params", {}).get("key", "space")
            lines.append("def input(key):")
            lines.append(f"    if key == '{k}':")
            continue
        elif t == "on_click":
            lines.append("def on_click():")
            continue
        lines.append(indent_str + raw)
    return "\n".join(lines)

def generate_scene_code_only():
    if not scene_script:
        return "# (no scene script blocks)"
    lines = []
    for block in scene_script:
        t = block["type"]
        raw = fmt_block(block)
        indent_level = block.get("indent", 0)
        indent_str = "    " * indent_level
        if t == "on_update":
            lines.append("def update():")
            continue
        elif t == "on_key":
            k = block.get("params", {}).get("key", "space")
            lines.append("def input(key):")
            lines.append(f"    if key == '{k}':")
            continue
        elif t == "on_click":
            lines.append("def on_click():")
            continue
        lines.append(indent_str + raw)
    return "\n".join(lines)

# ----------------------------------------------------------------------
# Run Scene
# ----------------------------------------------------------------------
def run_scene():
    script = generate_combined_script()
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(os.path.abspath(sys.executable))
        py_cmd = 'py'
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        py_cmd = 'python'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=script_dir) as f:
        f.write(script)
        temp_path = f.name
    try:
        proc = subprocess.Popen([py_cmd, temp_path], shell=True)
        set_status(f"Running scene from {temp_path}")
        def poll_and_clean():
            if proc.poll() is not None:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                set_status("Scene closed")
            else:
                root.after(1000, poll_and_clean)
        root.after(1000, poll_and_clean)
    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass
        set_status(f"Error running scene: {e}", is_error=True)

# ----------------------------------------------------------------------
# Auto-load packages
# ----------------------------------------------------------------------
def auto_load_packages():
    pkg_dir = "packages"
    if not os.path.exists(pkg_dir):
        os.makedirs(pkg_dir)
        # Create default option packs
        create_default_packs(pkg_dir)
        return
    from code_editor import load_addon_pack
    for filename in os.listdir(pkg_dir):
        if filename.endswith(".aubp"):
            load_addon_pack(os.path.join(pkg_dir, filename), set_status)

def create_default_packs(pkg_dir):
    # options_bool.aubp
    bool_data = {
        "CAT_COLORS": {"Options": "#AAAAAA"},
        "CODE_TEMPLATES": {
            "True": {"template": "{value}", "indent_after": False, "is_options": True, "options": ["True", "False"], "params": []},
            "None": {"template": "{value}", "indent_after": False, "is_options": True, "options": ["None"], "params": []}
        },
        "BLOCK_CATEGORIES": [["Options", ["True", "None"]]]
    }
    with open(os.path.join(pkg_dir, "options_bool.aubp"), "w") as f:
        json.dump(bool_data, f, indent=2)

    # options_model.aubp
    model_data = {
        "CAT_COLORS": {"Options": "#AAAAAA"},
        "CODE_TEMPLATES": {
            "model": {"template": "{value}", "indent_after": False, "is_options": True,
                      "options": ["'cube'", "'sphere'", "'plane'", "'quad'", "'circle'", "'capsule'", "'cylinder'", "'torus'", "''"],
                      "params": []}
        },
        "BLOCK_CATEGORIES": [["Options", ["model"]]]
    }
    with open(os.path.join(pkg_dir, "options_model.aubp"), "w") as f:
        json.dump(model_data, f, indent=2)

    # options_texture.aubp
    texture_data = {
        "CAT_COLORS": {"Options": "#AAAAAA"},
        "CODE_TEMPLATES": {
            "texture": {"template": "{value}", "indent_after": False, "is_options": True,
                        "options": ["'brick'", "'grass'", "'circle'", "'sky_default'", "'white_cube'", "'shore'", "'vignette'", "'vertical_gradient'", "'ursina_logo'", "''"],
                        "params": []}
        },
        "BLOCK_CATEGORIES": [["Options", ["texture"]]]
    }
    with open(os.path.join(pkg_dir, "options_texture.aubp"), "w") as f:
        json.dump(texture_data, f, indent=2)

    # options_collider.aubp
    collider_data = {
        "CAT_COLORS": {"Options": "#AAAAAA"},
        "CODE_TEMPLATES": {
            "collider": {"template": "{value}", "indent_after": False, "is_options": True,
                         "options": ["'box'", "'sphere'", "'capsule'", "'mesh'", "None"],
                         "params": []}
        },
        "BLOCK_CATEGORIES": [["Options", ["collider"]]]
    }
    with open(os.path.join(pkg_dir, "options_collider.aubp"), "w") as f:
        json.dump(collider_data, f, indent=2)

# ----------------------------------------------------------------------
# Handle command-line arguments (Open With)
# ----------------------------------------------------------------------
if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg.endswith('.aucf'):
        if os.path.exists(arg):
            load_scene(arg)
    elif arg.endswith('.aubp'):
        if os.path.exists(arg):
            open_block_pack_editor(root, set_status, load_file=arg)

# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------
auto_load_packages()
root.mainloop()