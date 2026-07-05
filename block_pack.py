import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser, filedialog

BLOCK_PACK_FILE = "block_pack.json"
DEFAULT_BLOCK_PACK = {
    "CAT_COLORS": {
        "Variables": "#FF6B6B", "Logic": "#845EC2", "Loops": "#D65DB1",
        "Functions": "#00C9A7", "Math": "#FFC75F", "I/O": "#F9F871",
        "Comments": "#A0A0A0", "Special": "#888888", "Comparison": "#FF6B6B",
        "Logical": "#845EC2", "Lists": "#D65DB1", "More Math": "#FFC75F"
    },
    "CODE_TEMPLATES": {
        "set_var": {"template": "{name} = {value}", "indent_after": False, "params": [{"name":"name","label":"Name","default":"x","type":"entry"}, {"name":"value","label":"Value","default":"0","type":"entry"}]},
        "change_var": {"template": "{name} += {value}", "indent_after": False, "params": [{"name":"name","label":"Name","default":"x","type":"entry"}, {"name":"value","label":"By","default":"1","type":"entry"}]},
        "if_then": {"template": "if {condition}:", "indent_after": True, "params": [{"name":"condition","label":"Condition","default":"True","type":"entry"}]},
        "else_block": {"template": "else:", "indent_after": False, "params": []},
        "elif": {"template": "elif {condition}:", "indent_after": True, "params": [{"name":"condition","label":"Condition","default":"False","type":"entry"}]},
        "for_loop": {"template": "for {var} in {iter}:", "indent_after": True, "params": [{"name":"var","label":"Var","default":"i","type":"entry"}, {"name":"iter","label":"In","default":"range(10)","type":"entry"}]},
        "while_loop": {"template": "while {condition}:", "indent_after": True, "params": [{"name":"condition","label":"Condition","default":"True","type":"entry"}]},
        "break": {"template": "break", "indent_after": False, "params": []},
        "continue": {"template": "continue", "indent_after": False, "params": []},
        "def_fn": {"template": "def {name}({args}):", "indent_after": True, "params": [{"name":"name","label":"Name","default":"my_func","type":"entry"}, {"name":"args","label":"Args","default":"","type":"entry"}]},
        "call_fn": {"template": "{name}({args})", "indent_after": False, "params": [{"name":"name","label":"Name","default":"my_func","type":"entry"}, {"name":"args","label":"Args","default":"","type":"entry"}]},
        "return_fn": {"template": "return {value}", "indent_after": False, "params": [{"name":"value","label":"Value","default":"None","type":"entry"}]},
        "add": {"template": "{result} = {a} + {b}", "indent_after": False, "params": [{"name":"result","label":"Store","default":"r","type":"entry"}, {"name":"a","label":"A","default":"0","type":"entry"}, {"name":"b","label":"B","default":"0","type":"entry"}]},
        "sub": {"template": "{result} = {a} - {b}", "indent_after": False, "params": [{"name":"result","label":"Store","default":"r","type":"entry"}, {"name":"a","label":"A","default":"0","type":"entry"}, {"name":"b","label":"B","default":"0","type":"entry"}]},
        "mul": {"template": "{result} = {a} * {b}", "indent_after": False, "params": [{"name":"result","label":"Store","default":"r","type":"entry"}, {"name":"a","label":"A","default":"0","type":"entry"}, {"name":"b","label":"B","default":"0","type":"entry"}]},
        "div": {"template": "{result} = {a} / {b}", "indent_after": False, "params": [{"name":"result","label":"Store","default":"r","type":"entry"}, {"name":"a","label":"A","default":"0","type":"entry"}, {"name":"b","label":"B","default":"0","type":"entry"}]},
        "print": {"template": "print({value})", "indent_after": False, "params": [{"name":"value","label":"Value","default":"'hello'","type":"entry"}]},
        "comment": {"template": "# {text}", "indent_after": False, "params": [{"name":"text","label":"Text","default":"comment","type":"entry"}]},
        "compare": {"template": "{a} {op} {b}", "indent_after": False, "params": [{"name":"a","label":"A","default":"0","type":"entry"}, {"name":"op","label":"Op","default":"==","type":"entry"}, {"name":"b","label":"B","default":"0","type":"entry"}]},
        "and_op": {"template": "{a} and {b}", "indent_after": False, "params": [{"name":"a","label":"A","default":"True","type":"entry"}, {"name":"b","label":"B","default":"False","type":"entry"}]},
        "or_op": {"template": "{a} or {b}", "indent_after": False, "params": [{"name":"a","label":"A","default":"True","type":"entry"}, {"name":"b","label":"B","default":"False","type":"entry"}]},
        "not_op": {"template": "not {a}", "indent_after": False, "params": [{"name":"a","label":"A","default":"True","type":"entry"}]},
        "list_create": {"template": "{result} = [{items}]", "indent_after": False, "params": [{"name":"result","label":"Store","default":"my_list","type":"entry"}, {"name":"items","label":"Items","default":"","type":"entry"}]},
        "list_append": {"template": "{list_name}.append({item})", "indent_after": False, "params": [{"name":"list_name","label":"List","default":"my_list","type":"entry"}, {"name":"item","label":"Item","default":"0","type":"entry"}]},
        "indent": {"template": "{indent}", "indent_after": False, "params": []},
        "outdent": {"template": "{outdent}", "indent_after": False, "params": []},
        "blank": {"template": "{custom}", "indent_after": False, "params": [{"name":"custom","label":"Code","default":"pass","type":"entry"}]},
        "multiline": {
            "template": "# {content}",
            "indent_after": False,
            "params": [{"name":"content","label":"Multi‑line content","default":"","type":"text"}]
        }
    },
    "BLOCK_CATEGORIES": [
        ["Variables", ["set_var", "change_var"]],
        ["Logic", ["if_then", "else_block", "elif"]],
        ["Comparison", ["compare"]],
        ["Logical", ["and_op", "or_op", "not_op"]],
        ["Loops", ["for_loop", "while_loop", "break", "continue"]],
        ["Functions", ["def_fn", "call_fn", "return_fn"]],
        ["Math", ["add", "sub", "mul", "div"]],
        ["Lists", ["list_create", "list_append"]],
        ["I/O", ["print"]],
        ["Comments", ["comment"]],
        ["Special", ["indent", "outdent", "blank", "multiline"]]
    ]
}

def load_block_defs():
    if not os.path.exists(BLOCK_PACK_FILE):
        with open(BLOCK_PACK_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_BLOCK_PACK, f, indent=2)
    with open(BLOCK_PACK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in DEFAULT_BLOCK_PACK:
        if key not in data:
            data[key] = DEFAULT_BLOCK_PACK[key]
    for bid, tmpl in data["CODE_TEMPLATES"].items():
        if "indent_after" not in tmpl:
            tmpl["indent_after"] = False
        if "is_options" not in tmpl:
            tmpl["is_options"] = False
        if "options" not in tmpl:
            tmpl["options"] = []
        if "params" in tmpl and isinstance(tmpl["params"], list):
            new_params = []
            for p in tmpl["params"]:
                if isinstance(p, list) and len(p) >= 3:
                    new_params.append({"name": p[0], "label": p[1], "default": p[2], "type": "entry"})
                elif isinstance(p, dict):
                    new_params.append(p)
            tmpl["params"] = new_params
    return data

def save_block_defs(data, filepath=None):
    if filepath is None:
        filepath = BLOCK_PACK_FILE
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

block_data = load_block_defs()
CAT_COLORS = block_data["CAT_COLORS"]
CODE_TEMPLATES = block_data["CODE_TEMPLATES"]
BLOCK_CATEGORIES = block_data["BLOCK_CATEGORIES"]
CONTROL_FLOW_TYPES = {"if_then", "elif", "for_loop", "while_loop", "def_fn"}

# ------------------------------------------------------------
# Block Pack Editor
# ------------------------------------------------------------
def open_block_pack_editor(root, status_callback, load_file=None):
    win = tk.Toplevel(root)
    win.title("Block Pack Editor")
    win.geometry("950x700")
    win.transient(root)
    win.grab_set()

    data = load_block_defs()
    cat_colors = data["CAT_COLORS"]
    code_templates = data["CODE_TEMPLATES"]
    block_categories = data["BLOCK_CATEGORIES"]

    current_file = load_file
    if load_file and os.path.exists(load_file):
        try:
            with open(load_file, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            code_templates.clear()
            block_categories.clear()
            cat_colors.clear()
            for k, v in new_data.get("CAT_COLORS", {}).items():
                cat_colors[k] = v
            for k, v in new_data.get("CODE_TEMPLATES", {}).items():
                code_templates[k] = v
            for cat, bids in new_data.get("BLOCK_CATEGORIES", []):
                block_categories.append([cat, list(bids)])
            current_file = load_file
            status_callback(f"Loaded pack from {os.path.basename(load_file)}")
        except Exception as e:
            status_callback(f"Error loading pack: {e}", is_error=True)

    # ---------- Toolbar ----------
    toolbar = tk.Frame(win)
    toolbar.pack(fill="x", padx=5, pady=5)
    tk.Button(toolbar, text="New Pack", command=lambda: new_pack()).pack(side="left", padx=2)
    tk.Button(toolbar, text="Load Pack", command=lambda: load_pack()).pack(side="left", padx=2)
    tk.Button(toolbar, text="Save Pack", command=lambda: save_pack()).pack(side="left", padx=2)
    tk.Button(toolbar, text="Save As...", command=lambda: save_pack_as()).pack(side="left", padx=2)

    # ---------- Listbox ----------
    list_frame = tk.Frame(win)
    list_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    tk.Label(list_frame, text="Block IDs", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
    lb = tk.Listbox(list_frame, width=30)
    lb.exportselection = False
    lb.pack(fill="both", expand=True)
    for bid in code_templates:
        lb.insert(tk.END, bid)

    # ---------- Edit panel widgets ----------
    edit_frame = tk.Frame(win, padx=5, pady=5)
    edit_frame.pack(side="right", fill="both", expand=True)

    # Row 0: Block ID
    tk.Label(edit_frame, text="Block ID:", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="e")
    id_var = tk.StringVar()
    tk.Entry(edit_frame, textvariable=id_var, width=20).grid(row=0, column=1, padx=5)

    # Row 1: Template
    tk.Label(edit_frame, text="Template:", font=("TkDefaultFont", 9, "bold")).grid(row=1, column=0, sticky="e")
    tmpl_var = tk.StringVar()
    tmpl_entry = tk.Entry(edit_frame, textvariable=tmpl_var, width=40)
    tmpl_entry.grid(row=1, column=1, padx=5)

    # Row 2: Category
    tk.Label(edit_frame, text="Category:", font=("TkDefaultFont", 9, "bold")).grid(row=2, column=0, sticky="e")
    cat_var = tk.StringVar()
    tk.Entry(edit_frame, textvariable=cat_var, width=20).grid(row=2, column=1, padx=5)

    # Row 3: Color
    tk.Label(edit_frame, text="Color:", font=("TkDefaultFont", 9, "bold")).grid(row=3, column=0, sticky="e")
    color_var = tk.StringVar()
    tk.Entry(edit_frame, textvariable=color_var, width=20).grid(row=3, column=1, padx=5)
    tk.Button(edit_frame, text="Pick", command=lambda: pick_color()).grid(row=3, column=2)

    # Row 4: Indent after
    tk.Label(edit_frame, text="Indent after:", font=("TkDefaultFont", 9, "bold")).grid(row=4, column=0, sticky="e")
    indent_after_var = tk.BooleanVar(value=False)
    tk.Checkbutton(edit_frame, variable=indent_after_var).grid(row=4, column=1, sticky="w")

    # Row 5: Is Options Block (checkbox created later)
    tk.Label(edit_frame, text="Is Options Block:", font=("TkDefaultFont", 9, "bold")).grid(row=5, column=0, sticky="e")
    is_options_var = tk.BooleanVar(value=False)

    # Row 6: Options list (frame – initially hidden)
    options_frame = tk.Frame(edit_frame)
    options_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=5)
    options_frame.grid_remove()  # hide initially
    tk.Label(options_frame, text="Options:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
    options_listbox = tk.Listbox(options_frame, width=50, height=4)
    options_listbox.pack(side="left", fill="x", expand=True)
    opt_btn_frame = tk.Frame(options_frame)
    opt_btn_frame.pack(side="left", padx=5)

    # Row 7: Parameters
    tk.Label(edit_frame, text="Parameters (name,label,default)", font=("TkDefaultFont", 9, "bold")).grid(row=7, column=0, columnspan=3, sticky="w", pady=(10,0))
    param_listbox = tk.Listbox(edit_frame, width=60, height=6)
    param_listbox.grid(row=8, column=0, columnspan=3, pady=5)
    param_btn_frame = tk.Frame(edit_frame)
    param_btn_frame.grid(row=9, column=0, columnspan=3, pady=5)

    # ---------- Define all helper functions (must be before buttons that use them) ----------
    def pick_color():
        color_code = colorchooser.askcolor(title="Choose color", color=color_var.get(), parent=win)
        if color_code:
            color_var.set(color_code[1])

    def toggle_options_mode():
        if is_options_var.get():
            tmpl_entry.config(state="disabled")
            tmpl_var.set("{value}")
            param_listbox.config(state="disabled")
            options_frame.grid()   # show
        else:
            tmpl_entry.config(state="normal")
            param_listbox.config(state="normal")
            options_frame.grid_remove()  # hide

    def add_option():
        opt = simpledialog.askstring("Add Option", "Enter option value:", parent=win)
        if opt:
            options_listbox.insert(tk.END, opt)

    def remove_option():
        sel = options_listbox.curselection()
        if sel:
            options_listbox.delete(sel[0])

    def refresh_param_list():
        param_listbox.delete(0, tk.END)
        selected = lb.curselection()
        if selected and not is_options_var.get():
            bid = lb.get(selected[0])
            if bid in code_templates:
                for p in code_templates[bid].get("params", []):
                    param_listbox.insert(tk.END, f"{p['name']},{p['label']},{p['default']}")

    def add_param():
        selected = lb.curselection()
        if not selected or is_options_var.get():
            return
        bid = lb.get(selected[0])
        name = simpledialog.askstring("Add Parameter", "Parameter name (key):", parent=win)
        if not name:
            return
        label = simpledialog.askstring("Add Parameter", f"Label for '{name}':", parent=win)
        if label is None:
            return
        default = simpledialog.askstring("Add Parameter", f"Default value for '{name}':", parent=win)
        if default is None:
            default = ""
        code_templates[bid]["params"].append({"name": name, "label": label, "default": default, "type": "entry"})
        refresh_param_list()

    def remove_param():
        selected = lb.curselection()
        if not selected or is_options_var.get():
            return
        bid = lb.get(selected[0])
        idx = param_listbox.curselection()
        if idx:
            del code_templates[bid]["params"][idx[0]]
            refresh_param_list()

    def on_select(event):
        selected = lb.curselection()
        if not selected:
            return
        bid = lb.get(selected[0])
        id_var.set(bid)
        tmpl_var.set(code_templates[bid].get("template", ""))
        indent_after_var.set(code_templates[bid].get("indent_after", False))
        is_options_var.set(code_templates[bid].get("is_options", False))
        toggle_options_mode()
        if is_options_var.get():
            options_listbox.delete(0, tk.END)
            for opt in code_templates[bid].get("options", []):
                options_listbox.insert(tk.END, opt)
        for cat, bids in block_categories:
            if bid in bids:
                cat_var.set(cat)
                break
        else:
            cat_var.set("")
        color_var.set(cat_colors.get(cat_var.get(), "#888888"))
        refresh_param_list()

    def save_current():
        new_bid = id_var.get().strip()
        if not new_bid:
            status_callback("Error: Block ID cannot be empty", is_error=True)
            return
        is_options = is_options_var.get()
        if is_options:
            options = [options_listbox.get(i) for i in range(options_listbox.size())]
            if not options:
                status_callback("Error: Options block must have at least one option", is_error=True)
                return
            code_templates[new_bid] = {
                "template": "{value}",
                "indent_after": indent_after_var.get(),
                "is_options": True,
                "options": options,
                "params": []
            }
        else:
            new_template = tmpl_var.get().strip()
            if not new_template:
                new_template = "{custom}"
            if new_bid in code_templates:
                existing = code_templates[new_bid]
                params = existing.get("params", [])
            else:
                params = []
            code_templates[new_bid] = {
                "template": new_template,
                "indent_after": indent_after_var.get(),
                "is_options": False,
                "options": [],
                "params": params
            }
        new_cat = cat_var.get().strip()
        if new_cat:
            for cat, bids in block_categories:
                if new_bid in bids and cat != new_cat:
                    bids.remove(new_bid)
                    break
            found = False
            for cat, bids in block_categories:
                if cat == new_cat:
                    if new_bid not in bids:
                        bids.append(new_bid)
                    found = True
                    break
            if not found:
                block_categories.append([new_cat, [new_bid]])
            cat_colors[new_cat] = color_var.get()
        # Refresh listbox
        lb.delete(0, tk.END)
        for bid in code_templates:
            lb.insert(tk.END, bid)
        for i, bid in enumerate(code_templates):
            if bid == new_bid:
                lb.selection_set(i)
                lb.activate(i)
                on_select(None)
                break
        status_callback(f"Block '{new_bid}' saved")

    def delete_block():
        selected = lb.curselection()
        if not selected:
            status_callback("Error: No block selected", is_error=True)
            return
        bid = lb.get(selected[0])
        del code_templates[bid]
        for cat, bids in block_categories:
            if bid in bids:
                bids.remove(bid)
                break
        lb.delete(selected[0])
        clear_edit_fields()
        status_callback(f"Block '{bid}' deleted")

    def clear_edit_fields():
        id_var.set("")
        tmpl_var.set("")
        cat_var.set("")
        color_var.set("")
        indent_after_var.set(False)
        is_options_var.set(False)
        options_listbox.delete(0, tk.END)
        param_listbox.delete(0, tk.END)
        toggle_options_mode()

    def new_block():
        new_id = simpledialog.askstring("New Block", "Enter new block ID:", parent=win)
        if not new_id or new_id in code_templates:
            status_callback("Error: invalid or duplicate ID", is_error=True)
            return
        code_templates[new_id] = {"template": "{custom}", "indent_after": False, "is_options": False, "options": [], "params": []}
        cat_name = simpledialog.askstring("New Block", "Enter category name:", initialvalue="Custom", parent=win)
        if cat_name:
            if cat_name not in [c for c,_ in block_categories]:
                block_categories.append([cat_name, []])
            for cat, bids in block_categories:
                if cat == cat_name:
                    bids.append(new_id)
                    break
            if cat_name not in cat_colors:
                cat_colors[cat_name] = "#AAAAAA"
        lb.delete(0, tk.END)
        for bid in code_templates:
            lb.insert(tk.END, bid)
        for i, bid in enumerate(code_templates):
            if bid == new_id:
                lb.selection_set(i)
                lb.activate(i)
                on_select(None)
                break
        status_callback(f"Block '{new_id}' created. Edit and click Save Block.")

    def new_pack():
        nonlocal current_file
        if messagebox.askyesno("New Pack", "This will clear all current data. Continue?", parent=win):
            code_templates.clear()
            block_categories.clear()
            cat_colors.clear()
            for k, v in DEFAULT_BLOCK_PACK["CAT_COLORS"].items():
                cat_colors[k] = v
            for cat, bids in DEFAULT_BLOCK_PACK["BLOCK_CATEGORIES"]:
                block_categories.append([cat, list(bids)])
            for bid, tmpl in DEFAULT_BLOCK_PACK["CODE_TEMPLATES"].items():
                code_templates[bid] = tmpl.copy()
            current_file = None
            lb.delete(0, tk.END)
            for bid in code_templates:
                lb.insert(tk.END, bid)
            clear_edit_fields()
            status_callback("New pack created")

    def load_pack():
        nonlocal current_file
        path = filedialog.askopenfilename(filetypes=[("Block Pack files", "*.aubp")], parent=win)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            code_templates.clear()
            block_categories.clear()
            cat_colors.clear()
            for k, v in new_data.get("CAT_COLORS", {}).items():
                cat_colors[k] = v
            for k, v in new_data.get("CODE_TEMPLATES", {}).items():
                code_templates[k] = v
            for cat, bids in new_data.get("BLOCK_CATEGORIES", []):
                block_categories.append([cat, list(bids)])
            current_file = path
            lb.delete(0, tk.END)
            for bid in code_templates:
                lb.insert(tk.END, bid)
            clear_edit_fields()
            status_callback(f"Loaded pack from {os.path.basename(path)}")
        except Exception as e:
            status_callback(f"Error loading pack: {e}", is_error=True)

    def save_pack():
        nonlocal current_file
        if current_file:
            data = {"CAT_COLORS": cat_colors, "CODE_TEMPLATES": code_templates, "BLOCK_CATEGORIES": block_categories}
            try:
                with open(current_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                status_callback(f"Pack saved to {os.path.basename(current_file)}")
            except Exception as e:
                status_callback(f"Error saving pack: {e}", is_error=True)
        else:
            save_pack_as()

    def save_pack_as():
        nonlocal current_file
        path = filedialog.asksaveasfilename(defaultextension=".aubp", filetypes=[("Block Pack files", "*.aubp")], parent=win)
        if not path:
            return
        data = {"CAT_COLORS": cat_colors, "CODE_TEMPLATES": code_templates, "BLOCK_CATEGORIES": block_categories}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            current_file = path
            status_callback(f"Pack saved as {os.path.basename(path)}")
        except Exception as e:
            status_callback(f"Error saving pack: {e}", is_error=True)

    # ---------- Now create the buttons (all commands are defined) ----------
    # Options buttons
    tk.Button(opt_btn_frame, text="Add", command=add_option).pack(fill="x")
    tk.Button(opt_btn_frame, text="Remove", command=remove_option).pack(fill="x")

    # Parameter buttons
    tk.Button(param_btn_frame, text="Add Param", command=add_param).pack(side="left", padx=5)
    tk.Button(param_btn_frame, text="Remove Param", command=remove_param).pack(side="left", padx=5)

    # Is Options checkbox (now that toggle_options_mode exists)
    chk_options = tk.Checkbutton(edit_frame, variable=is_options_var, command=toggle_options_mode)
    chk_options.grid(row=5, column=1, sticky="w")

    # Save/Delete/New block buttons
    tk.Button(edit_frame, text="Save Block", command=save_current).grid(row=10, column=0, padx=5, pady=5)
    tk.Button(edit_frame, text="Delete Block", command=delete_block).grid(row=10, column=1, padx=5, pady=5)
    tk.Button(edit_frame, text="New Block", command=new_block).grid(row=10, column=2, padx=5, pady=5)

    # Save to default
    def save_default():
        data = {"CAT_COLORS": cat_colors, "CODE_TEMPLATES": code_templates, "BLOCK_CATEGORIES": block_categories}
        save_block_defs(data)
        global CAT_COLORS, CODE_TEMPLATES, BLOCK_CATEGORIES
        CAT_COLORS = data["CAT_COLORS"]
        CODE_TEMPLATES = data["CODE_TEMPLATES"]
        BLOCK_CATEGORIES = data["BLOCK_CATEGORIES"]
        status_callback("Default block pack saved. Restart the app to use new definitions.")

    tk.Button(edit_frame, text="Save to Default & Reload", command=save_default).grid(row=11, column=0, columnspan=3, pady=10)

    # Bind listbox selection
    lb.bind("<<ListboxSelect>>", on_select)

    # Initial UI state
    toggle_options_mode()  # ensure options frame is hidden