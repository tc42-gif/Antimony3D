import tkinter as tk

class ResizableEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.on_click, add="+")
        self.bind("<B1-Motion>", self.on_drag, add="+")
        self.bind("<ButtonRelease-1>", self.on_release, add="+")
        self.bind("<FocusOut>", self.on_focus_out, add="+")
        self._drag_start_x = None
        self._orig_width = None
        self._resizing = False

    def on_click(self, event):
        # If click is near the right edge (within 10 pixels), start resize
        if self.winfo_width() - event.x < 10:
            self._drag_start_x = event.x_root
            self._orig_width = self.winfo_width()
            self._resizing = True
            self.grab_set()          # capture all mouse events
        else:
            # Normal click: let default behavior handle focus and selection
            self._resizing = False

    def on_drag(self, event):
        if self._resizing and self._drag_start_x is not None:
            delta = event.x_root - self._drag_start_x
            new_width = max(20, self._orig_width + delta)
            self.config(width=int(new_width / 10))   # adjust step as needed
            self._drag_start_x = event.x_root
            self._orig_width = new_width

    def on_release(self, event):
        if self._resizing:
            self.grab_release()          # release mouse capture
            self._resizing = False
            self._drag_start_x = None
            self._orig_width = None
            # Clear focus and selection to avoid stuck selected state
            self.selection_clear()       # clear any selected text

    def on_focus_out(self, event):
        # Safety: if focus leaves for any reason, clear selection and release grab
        self.selection_clear()
        if self._resizing:
            self.grab_release()
            self._resizing = False
            self._drag_start_x = None
            self._orig_width = None

def fmt_block(block):
    from block_pack import CODE_TEMPLATES
    if not isinstance(block, dict) or "type" not in block:
        return str(block)
    t = block["type"]
    if t not in CODE_TEMPLATES:
        return "# unknown block"
    tmpl = CODE_TEMPLATES[t]["template"]
    param_defs = CODE_TEMPLATES[t]["params"]
    p = block.get("params", {})
    resolved = {}
    for pd in param_defs:
        key = pd["name"]
        val = p.get(key, pd["default"])
        if isinstance(val, dict) and "type" in val:
            resolved[key] = fmt_block(val)
        else:
            resolved[key] = val
    # For options blocks, the value is stored in "value" param
    if CODE_TEMPLATES[t].get("is_options"):
        resolved["value"] = p.get("value", CODE_TEMPLATES[t].get("options", [""])[0])
    try:
        return tmpl.format(**resolved)
    except:
        return f"# error rendering {t}"
