"""\nThe Electric Kool-Aid User Meeting Gallery Maker  (v2.1)
=========================================================

Crops, resizes and compresses up to 20 meeting photos to 1080x1080 px,
then writes an image-credits.txt with photographer credits and optional

Usage:
    py the-electric-kool-aid-user-meeting-gallery-maker.py

Requires Python 3.12+.  Only hard dependency beyond stdlib is Pillow.
The anthropic package is optional (needed only for alt-text generation).

v1.5 changes:
  - Wider window (1200px), 7-column grid — all 20 images visible at once.
  - Drag-and-drop card reordering within the grid.
  - Per-image quality override dialog when a processed image exceeds the
    warning size threshold.

v1.4 changes:
  - Crop result now delivered via callback before popup.destroy(), so the
    value is never lost to Tkinter widget teardown.
  - Re-opening the crop popup restores the previous crop position.
  - Card thumbnail updates to show the cropped area with a green border.

v1.2 fixes:
  - Images copied into memory on load; file handles released immediately.
  - WebP output converts RGBA -> RGB (fixes Errno 22 on Windows).
"""

import io
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

__version__    = "2.6"
APP_TITLE      = f"The Electric Kool-Aid User Meeting Gallery Maker  v{__version__}"
WINDOW_SIZE    = "1200x820"
GRID_COLS      = 7

SETTINGS_PATH  = Path.home() / ".umip_settings.json"
OUTPUT_FOLDER  = "processed"
OUTPUT_SIZE    = (1080, 1080)
MAX_IMAGES     = 20
TARGET_SIZE_KB = 160
WARN_SIZE_KB   = 220

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


# ---------------------------------------------------------------------------
# Pillow
# ---------------------------------------------------------------------------

try:
    from PIL import Image, ImageTk, ExifTags
except ImportError:
    print("Pillow is required.  Run:  pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Optional Anthropic
# ---------------------------------------------------------------------------

try:
    import anthropic as _anthropic_lib
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text())
    except Exception:
        return {}


def _save_settings(patch: dict):
    try:
        data = _load_settings()
        data.update(patch)
        SETTINGS_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("\u2019", "").replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_filename(slug: str, index: int, ext: str) -> str:
    return f"user-meeting-image_{slug}_{index:03d}{ext}"


def fix_exif_orientation(img: Image.Image) -> Image.Image:
    try:
        exif = img._getexif()
        if exif is None:
            return img
        orient_tag = next(
            (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None)
        if orient_tag is None:
            return img
        ops = {
            2: (Image.FLIP_LEFT_RIGHT, None),
            3: (None, 180),
            4: (Image.FLIP_TOP_BOTTOM, None),
            5: (Image.FLIP_LEFT_RIGHT, -90),
            6: (None, -90),
            7: (Image.FLIP_LEFT_RIGHT, 90),
            8: (None, 90),
        }
        orientation = exif.get(orient_tag)
        if orientation in ops:
            flip_op, angle = ops[orientation]
            if flip_op is not None:
                img = img.transpose(flip_op)
            if angle is not None:
                img = img.rotate(angle, expand=True)
    except Exception:
        pass
    return img


def default_crop_box(img: Image.Image):
    w, h  = img.size
    half  = min(w, h) // 2
    return (w // 2 - half, h // 2 - half, w // 2 + half, h // 2 + half)


def save_image(img: Image.Image, path: Path, fmt: str, quality: int):
    """Save img to path in fmt at quality. Always converts to RGB first."""
    rgb = img.convert("RGB")
    if fmt == "WEBP":
        rgb.save(path, format="WEBP", quality=quality, method=4)
    else:
        rgb.save(path, format="JPEG", quality=quality, optimize=True)


def estimate_kb(img: Image.Image, fmt: str, quality: int) -> int:
    buf = io.BytesIO()
    save_image(img, buf, fmt, quality)
    return len(buf.getvalue()) // 1024




# ---------------------------------------------------------------------------
# Crop popup
# ---------------------------------------------------------------------------

class CropPopup(tk.Toplevel):
    """
    Modal crop adjuster.
    Drag to reposition • scroll-wheel / buttons to resize.
    Calls on_confirm((l, t, r, b)) before destroying itself.
    Pass existing_box to restore a previously confirmed crop on re-open.
    """
    CANVAS_W = 620
    CANVAS_H = 520

    def __init__(self, parent, img: Image.Image, index: int,
                 on_confirm=None, existing_box=None):
        super().__init__(parent)
        self.title(f"Adjust crop -- image {index:03d}")
        self.resizable(False, False)
        self.grab_set()
        self._on_confirm  = on_confirm
        self._result_box  = [None]   # mutable; survives widget teardown
        self._orig        = img
        ow, oh            = img.size
        self._min_half    = min(ow, oh) * 0.05
        self._max_half    = min(ow, oh) / 2

        if existing_box is not None:
            l, t, r, b  = existing_box
            self._half  = (r - l) / 2.0
            self._cx    = l + self._half
            self._cy    = t + self._half
        else:
            cs          = min(self.CANVAS_W, self.CANVAS_H)
            scale       = min(self.CANVAS_W / ow, self.CANVAS_H / oh)
            self._half  = min(min(ow, oh) / 2, cs / (2 * scale))
            self._cx    = ow / 2.0
            self._cy    = oh / 2.0

        self._drag_start  = None
        self._scale       = 1.0
        self._ox = self._oy = 0
        self._build_ui()
        self._redraw()
        self.wait_window()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self,
                  text="Drag the white square to reposition  |  "
                       "Scroll wheel or +/- to resize",
                  foreground="gray50", font=("", 9)).pack(**pad)

        self._canvas = tk.Canvas(self, width=self.CANVAS_W, height=self.CANVAS_H,
                                  bg="#808080", highlightthickness=1,
                                  highlightbackground="#aaa", cursor="fleur")
        self._canvas.pack(padx=8, pady=4)
        self._canvas.bind("<ButtonPress-1>",  self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<MouseWheel>",      self._on_scroll)
        self._canvas.bind("<Button-4>",        self._on_scroll)
        self._canvas.bind("<Button-5>",        self._on_scroll)

        zoom_row = ttk.Frame(self)
        zoom_row.pack(**pad)
        ttk.Button(zoom_row, text="- Zoom out",
                   command=lambda: self._zoom(1.08)).pack(side="left", padx=4)
        ttk.Button(zoom_row, text="+ Zoom in",
                   command=lambda: self._zoom(0.92)).pack(side="left", padx=4)
        self._size_lbl = ttk.Label(zoom_row, foreground="gray50", font=("", 9))
        self._size_lbl.pack(side="left", padx=12)

        btn_row = ttk.Frame(self)
        btn_row.pack(pady=8)
        ttk.Button(btn_row, text="Confirm crop",
                   command=self._confirm).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel",
                   command=self.destroy).pack(side="left", padx=6)

    def _redraw(self):
        cw, ch = self.CANVAS_W, self.CANVAS_H
        ow, oh = self._orig.size
        scale  = min(cw / ow, ch / oh)
        dw, dh = int(ow * scale), int(oh * scale)
        ox     = (cw - dw) // 2
        oy     = (ch - dh) // 2

        thumb = self._orig.resize((dw, dh), Image.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(thumb)
        self._canvas.delete("all")
        self._canvas.create_rectangle(0, 0, cw, ch, fill="#555555", outline="")
        self._canvas.create_image(ox, oy, anchor="nw", image=self._tkimg)

        sx = ox + (self._cx - self._half) * scale
        sy = oy + (self._cy - self._half) * scale
        ex = ox + (self._cx + self._half) * scale
        ey = oy + (self._cy + self._half) * scale

        # Dim outside — drawn before the border so border is always on top
        for coords in [(0, 0, cw, sy), (0, ey, cw, ch),
                       (0, sy, sx, ey), (ex, sy, cw, ey)]:
            self._canvas.create_rectangle(*coords, fill="#000000",
                                           stipple="gray50", outline="")

        # Crop border — drawn last, always on top
        self._canvas.create_rectangle(sx, sy, ex, ey, outline="white", width=2)
        for t in (1/3, 2/3):
            self._canvas.create_line(sx + (ex-sx)*t, sy, sx + (ex-sx)*t, ey,
                                      fill="white", stipple="gray50")
            self._canvas.create_line(sx, sy + (ey-sy)*t, ex, sy + (ey-sy)*t,
                                      fill="white", stipple="gray50")

        self._scale   = scale
        self._ox, self._oy = ox, oy
        side = int(self._half * 2)
        self._size_lbl.configure(
            text=f"Crop area: {side} x {side} px  ->  output: 1080 x 1080 px")

    def _clamp(self):
        ow, oh = self._orig.size
        self._half = max(self._min_half, min(self._max_half, self._half))
        self._cx   = max(self._half, min(ow - self._half, self._cx))
        self._cy   = max(self._half, min(oh - self._half, self._cy))

    def _zoom(self, factor):
        self._half *= factor
        self._clamp()
        self._redraw()

    def _on_press(self, e):
        self._drag_start = (e.x, e.y, self._cx, self._cy)

    def _on_drag(self, e):
        if not self._drag_start:
            return
        x0, y0, cx0, cy0 = self._drag_start
        self._cx = cx0 + (e.x - x0) / self._scale
        self._cy = cy0 + (e.y - y0) / self._scale
        self._clamp()
        self._redraw()

    def _on_release(self, _):
        self._drag_start = None

    def _on_scroll(self, e):
        self._zoom(0.92 if (e.num == 4 or (hasattr(e, "delta") and e.delta > 0))
                   else 1.08)

    def _confirm(self):
        ow, oh = self._orig.size
        box = (max(0, int(self._cx - self._half)),
               max(0, int(self._cy - self._half)),
               min(ow, int(self._cx + self._half)),
               min(oh, int(self._cy + self._half)))
        # Call callback and store BEFORE destroy() wipes the widget
        if self._on_confirm:
            self._on_confirm(box)
        self._result_box[0] = box
        self.destroy()


# ---------------------------------------------------------------------------
# Per-image quality override dialog (called from processing thread)
# ---------------------------------------------------------------------------

class QualityOverrideDialog(tk.Toplevel):
    """
    Shown when a processed image exceeds WARN_SIZE_KB.
    Runs on the main thread via app.after(); the processing thread blocks
    on a threading.Event until the user dismisses it.
    """

    def __init__(self, parent, fname: str, kb: int, fmt: str,
                 img: Image.Image, initial_quality: int, event: threading.Event,
                 result: dict):
        super().__init__(parent)
        self.title("Image too large")
        self.resizable(False, False)
        self.grab_set()
        self._fmt     = fmt
        self._img     = img
        self._event   = event
        self._result  = result   # result["quality"] written before event.set()
        self._initial = initial_quality

        pad = {"padx": 12, "pady": 6}

        ttk.Label(self,
                  text=f"{fname}\ncame out at {kb} KB  (target: <{TARGET_SIZE_KB} KB,"
                       f"  warning: >{WARN_SIZE_KB} KB).\n"
                       f"Adjust quality below and re-estimate, or just accept it.",
                  justify="left").pack(**pad)

        q_row = ttk.Frame(self)
        q_row.pack(fill="x", **pad)
        ttk.Label(q_row, text="Quality:").pack(side="left")
        self._q_var = tk.IntVar(value=initial_quality)
        ttk.Scale(q_row, from_=40, to=100, variable=self._q_var,
                  orient="horizontal", length=200,
                  command=lambda _: self._q_lbl.configure(
                      text=str(self._q_var.get()))).pack(side="left", padx=4)
        self._q_lbl = ttk.Label(q_row, text=str(initial_quality), width=3)
        self._q_lbl.pack(side="left", padx=4)

        ttk.Button(q_row, text="Estimate size",
                   command=self._estimate).pack(side="left", padx=8)
        self._est_lbl = ttk.Label(q_row, text="", foreground="gray50",
                                   font=("", 9))
        self._est_lbl.pack(side="left")

        btn_row = ttk.Frame(self)
        btn_row.pack(pady=8)
        ttk.Button(btn_row, text="Save with this quality",
                   command=self._accept).pack(side="left", padx=6)
        ttk.Button(btn_row, text=f"Keep original ({kb} KB)",
                   command=self._keep).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", self._keep)

    def _estimate(self):
        kb = estimate_kb(self._img, self._fmt, self._q_var.get())
        colour = "red" if kb > WARN_SIZE_KB else ("orange" if kb > TARGET_SIZE_KB
                                                    else "green")
        self._est_lbl.configure(text=f"≈ {kb} KB", foreground=colour)

    def _accept(self):
        self._result["quality"] = self._q_var.get()
        self._result["action"]  = "resave"
        self._event.set()
        self.destroy()

    def _keep(self):
        self._result["quality"] = self._initial
        self._result["action"]  = "keep"
        self._event.set()
        self.destroy()


# ---------------------------------------------------------------------------
# Image card
# ---------------------------------------------------------------------------

THUMB_SIZE = 130


class ImageCard(ttk.Frame):
    """One card per image: drag handle, thumbnail, crop state, photographer."""

    def __init__(self, parent, path: Path, index: int, app: "App"):
        super().__init__(parent, relief="groove", borderwidth=1)
        self._path     = path
        self._index    = index
        self._app      = app
        self._crop_box = None

        with Image.open(path) as raw:
            raw.load()
            self._orig = fix_exif_orientation(raw).copy()

        # ── drag handle ──────────────────────────────────────────────────────
        handle = ttk.Label(self, text="⠿  drag to reorder",
                           foreground="gray60", font=("", 7), cursor="fleur")
        handle.pack(fill="x", padx=4, pady=(3, 0))
        handle.bind("<ButtonPress-1>",   self._drag_start)
        handle.bind("<B1-Motion>",        self._drag_motion)
        handle.bind("<ButtonRelease-1>",  self._drag_end)

        # ── thumbnail ────────────────────────────────────────────────────────
        thumb = self._orig.copy()
        thumb.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        self._tkthumb = ImageTk.PhotoImage(thumb)

        self._canvas = tk.Canvas(self, width=THUMB_SIZE, height=THUMB_SIZE,
                                  bg="#d9d9d9", highlightthickness=0,
                                  cursor="hand2")
        self._canvas.create_image(THUMB_SIZE // 2, THUMB_SIZE // 2,
                                   anchor="center", image=self._tkthumb)
        self._canvas.pack(padx=6, pady=(2, 2))
        self._canvas.bind("<Button-1>", self._open_crop)

        # ── labels / button ──────────────────────────────────────────────────
        self._idx_var  = tk.StringVar(value=f"#{index:03d}")
        ttk.Label(self, textvariable=self._idx_var,
                  font=("", 8, "bold")).pack()

        ttk.Label(self, text=path.name, foreground="gray30",
                  font=("", 8), wraplength=THUMB_SIZE).pack()

        self._crop_var = tk.StringVar(value="default crop")
        ttk.Label(self, textvariable=self._crop_var,
                  foreground="gray50", font=("", 7)).pack()

        ttk.Button(self, text="Adjust crop...",
                   command=self._open_crop).pack(pady=(2, 3))

        ttk.Label(self, text="Photographer:", font=("", 7)).pack()
        self._photo_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._photo_var,
                  width=14, font=("", 8)).pack(pady=(0, 4))

    # ── crop ─────────────────────────────────────────────────────────────────

    def _open_crop(self, _event=None):
        def on_confirm(box):
            self._crop_box = box
            self._update_thumb_from_crop()

        CropPopup(self._app, self._orig, self._index,
                  on_confirm=on_confirm, existing_box=self._crop_box)

    def _update_thumb_from_crop(self):
        box     = self._crop_box if self._crop_box else default_crop_box(self._orig)
        cropped = self._orig.crop(box)
        cropped.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        self._tkthumb = ImageTk.PhotoImage(cropped)
        self._canvas.delete("all")
        self._canvas.create_image(THUMB_SIZE // 2, THUMB_SIZE // 2,
                                   anchor="center", image=self._tkthumb)
        if self._crop_box:
            self._canvas.configure(highlightthickness=3,
                                    highlightbackground="#008800")
            self._crop_var.set("crop adjusted")
        else:
            self._canvas.configure(highlightthickness=0)
            self._crop_var.set("default crop")

    # ── drag-to-reorder ───────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._drag_x = e.x_root
        self._drag_y = e.y_root

    def _drag_motion(self, e):
        # Ask the app to check if we've moved over a different card
        self._app.drag_over(self, e.x_root, e.y_root)

    def _drag_end(self, e):
        self._app.drag_end(self, e.x_root, e.y_root)

    # ── public API ────────────────────────────────────────────────────────────

    def set_index(self, n: int):
        self._index = n
        self._idx_var.set(f"#{n:03d}")

    def get_crop_box(self):
        return self._crop_box if self._crop_box else default_crop_box(self._orig)

    def get_photographer(self) -> str:
        per = self._photo_var.get().strip()
        return per if per else self._app.global_photographer_var.get().strip()


    @property
    def orig(self) -> Image.Image:
        return self._orig

    @property
    def path(self) -> Path:
        return self._path


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.resizable(True, True)

        self._settings            = _load_settings()
        self._cards: list[ImageCard] = []
        self._cancel_requested    = False
        self._last_output_dir: Path | None = None
        self._drag_source: ImageCard | None = None

        self._job_start    = 0.0
        self._timer_running = False
        self._build_ui()
        self._load_settings_into_ui()
        # Shut down gracefully when the window closes
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.destroy()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}

        # Input folder
        f = ttk.LabelFrame(self, text="Input folder")
        f.pack(fill="x", **pad)
        self._folder_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._folder_var).pack(
            side="left", fill="x", expand=True, padx=5, pady=4)
        ttk.Button(f, text="Browse...", command=self._browse_folder,
                   width=10).pack(side="right", padx=(0, 5), pady=4)

        # Meeting details + format on one row to save vertical space
        details_fmt = ttk.Frame(self)
        details_fmt.pack(fill="x", **pad)

        f = ttk.LabelFrame(details_fmt, text="Meeting details")
        f.pack(side="left", fill="x", expand=True, padx=(0, 5))

        row1 = ttk.Frame(f)
        row1.pack(fill="x", padx=8, pady=3)
        ttk.Label(row1, text="Meeting name:").pack(side="left")
        self._meeting_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._meeting_var,
                  width=20).pack(side="left", padx=(4, 12))
        ttk.Label(row1, text="Slug:", foreground="gray50",
                  font=("", 9)).pack(side="left")
        self._slug_var = tk.StringVar(value="")
        ttk.Label(row1, textvariable=self._slug_var,
                  foreground="gray50", font=("", 9)).pack(side="left", padx=4)
        self._meeting_var.trace_add("write", self._on_meeting_change)

        row2 = ttk.Frame(f)
        row2.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(row2, text="Default photographer:").pack(side="left")
        self.global_photographer_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.global_photographer_var,
                  width=24).pack(side="left", padx=(4, 8))
        ttk.Label(row2, text="(override per image below)",
                  foreground="gray50", font=("", 9)).pack(side="left")

        f = ttk.LabelFrame(details_fmt, text="Format & quality")
        f.pack(side="left", fill="y")

        fmt_row = ttk.Frame(f)
        fmt_row.pack(fill="x", padx=8, pady=3)
        ttk.Label(fmt_row, text="Format:").pack(side="left")
        self._fmt_var = tk.StringVar(value="WEBP")
        ttk.Radiobutton(fmt_row, text="WebP",
                        variable=self._fmt_var, value="WEBP").pack(
            side="left", padx=(4, 6))
        ttk.Radiobutton(fmt_row, text="JPEG",
                        variable=self._fmt_var, value="JPEG").pack(side="left")

        q_row = ttk.Frame(f)
        q_row.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(q_row, text="Quality:").pack(side="left")
        self._quality_var = tk.IntVar(value=82)
        ttk.Scale(q_row, from_=40, to=100, variable=self._quality_var,
                  orient="horizontal", length=120,
                  command=lambda _: self._on_quality_change()).pack(
            side="left", padx=(4, 0))
        self._quality_lbl = ttk.Label(q_row, text="82", width=3)
        self._quality_lbl.pack(side="left", padx=2)
        ttk.Label(q_row, text=f"Aim <{TARGET_SIZE_KB}  Warn >{WARN_SIZE_KB} KB",
                  foreground="gray50", font=("", 8)).pack(side="left", padx=6)

        # Image grid — fixed height canvas with scrollbar so controls below
        # are always visible regardless of window size.
        # Height sized for 3 full card rows (~175px each) + padding.
        self._grid_lf = ttk.LabelFrame(
            self,
            text="Images  —  click thumbnail or 'Adjust crop...' to set crop  "
                 "|  drag the ⠿ handle to reorder")
        self._grid_lf.pack(fill="both", expand=True, **pad)

        grid_canvas = tk.Canvas(self._grid_lf, highlightthickness=0)
        vsb = ttk.Scrollbar(self._grid_lf, orient="vertical",
                             command=grid_canvas.yview)
        grid_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        grid_canvas.pack(side="left", fill="both", expand=True)

        self._grid_frame = ttk.Frame(grid_canvas)
        self._grid_win   = grid_canvas.create_window(
            (0, 0), window=self._grid_frame, anchor="nw")

        self._grid_frame.bind(
            "<Configure>",
            lambda e: grid_canvas.configure(
                scrollregion=grid_canvas.bbox("all")))
        grid_canvas.bind(
            "<Configure>",
            lambda e: grid_canvas.itemconfig(self._grid_win, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            grid_canvas.bind(
                seq, lambda e, c=grid_canvas: self._scroll_grid(e, c))

        self._placeholder = ttk.Label(
            self._grid_frame, text="Select a folder to load images.",
            foreground="gray50")
        self._placeholder.grid(row=0, column=0, padx=20, pady=20)

        # Buttons + progress — always visible at bottom
        btn_row = ttk.Frame(self)
        btn_row.pack(pady=4)
        self._run_btn = ttk.Button(btn_row, text="Process all",
                                    command=self._run, state="disabled")
        self._run_btn.pack(side="left", padx=5)
        self._cancel_btn = ttk.Button(btn_row, text="Cancel",
                                       command=self._cancel, state="disabled")
        self._cancel_btn.pack(side="left", padx=5)
        self._open_btn = ttk.Button(btn_row, text="Open output folder",
                                     command=self._open_output,
                                     state="disabled", width=20)
        self._open_btn.pack(side="left", padx=5)

        self._progress = ttk.Progressbar(self, mode="determinate", length=500)
        self._progress.pack(pady=(0, 3))
        self._progress.pack_forget()

        # Log
        log_lf = ttk.LabelFrame(self, text="Log")
        log_lf.pack(fill="x", expand=False, **pad)
        log_tb = ttk.Frame(log_lf)
        log_tb.pack(fill="x", padx=5, pady=(3, 0))
        ttk.Button(log_tb, text="Copy log",
                   command=self._copy_log, width=12).pack(side="right")
        # Fixed height — does not grow when the window is maximised.
        self._log_widget = scrolledtext.ScrolledText(
            log_lf, height=5, font=("Consolas", 9), state="disabled")
        self._log_widget.pack(fill="x", expand=False, padx=5, pady=4)

        # Status bar
        self._status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self._status_var,
                  anchor="w", relief="sunken").pack(side="bottom", fill="x")

    # ── settings ──────────────────────────────────────────────────────────────

    def _load_settings_into_ui(self):
        s = self._settings
        if v := s.get("last_folder"):   self._folder_var.set(v)
        if v := s.get("meeting"):       self._meeting_var.set(v)
        if v := s.get("photographer"):  self.global_photographer_var.set(v)
        if v := s.get("format"):        self._fmt_var.set(v)
        if v := s.get("quality"):
            self._quality_var.set(v)
            self._quality_lbl.configure(text=str(v))
        self._on_meeting_change()

    def _persist_settings(self):
        _save_settings({
            "last_folder":  self._folder_var.get(),
            "meeting":      self._meeting_var.get(),
            "photographer": self.global_photographer_var.get(),
            "format":       self._fmt_var.get(),
            "quality":      self._quality_var.get(),
        })

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _on_meeting_change(self, *_):
        raw  = self._meeting_var.get()
        slug = slugify(raw) if raw.strip() else ""
        self._slug_var.set(slug or "(enter meeting name)")

    def _on_quality_change(self):
        self._quality_lbl.configure(text=str(self._quality_var.get()))


    # ── browse / load ─────────────────────────────────────────────────────────

    def _browse_folder(self):
        initial = self._folder_var.get() or str(Path.home())
        d = filedialog.askdirectory(initialdir=initial,
                                     title="Select folder containing images")
        if not d:
            return
        self._folder_var.set(d)
        _save_settings({"last_folder": d})
        self._load_folder(Path(d))

    def _load_folder(self, folder: Path):
        images = sorted(
            p for p in folder.iterdir()
            if p.suffix.lower() in IMG_EXTS
            and p.parent.name.lower() != OUTPUT_FOLDER
        )
        if not images:
            messagebox.showwarning("No images",
                                   "No supported image files found in that folder.")
            return
        if len(images) > MAX_IMAGES:
            messagebox.showinfo(
                "Too many images",
                f"Found {len(images)} images.  "
                f"Only the first {MAX_IMAGES} will be loaded.")
            images = images[:MAX_IMAGES]

        self._clear_grid()
        for i, path in enumerate(images):
            try:
                card = ImageCard(self._grid_frame, path, i + 1, self)
            except Exception as exc:
                self._log(f"Could not load {path.name}: {exc}")
                continue
            self._cards.append(card)

        self._regrid()
        self._run_btn.configure(state="normal")
        n = len(self._cards)
        self._status(f"{n} image(s) loaded.")
        self._log(f"Loaded {n} image(s) from {folder}")

    def _clear_grid(self):
        for card in self._cards:
            card.destroy()
        self._cards.clear()
        if self._placeholder.winfo_exists():
            self._placeholder.grid_remove()

    def _regrid(self):
        """Place all cards in their current list order into the grid."""
        for card in self._cards:
            card.grid_forget()
        for i, card in enumerate(self._cards):
            card.grid(row=i // GRID_COLS, column=i % GRID_COLS,
                      padx=3, pady=3, sticky="n")
            card.set_index(i + 1)

    # ── grid scroll ───────────────────────────────────────────────────────────

    def _scroll_grid(self, e, canvas: tk.Canvas):
        if e.num == 4:
            canvas.yview_scroll(-1, "units")
        elif e.num == 5:
            canvas.yview_scroll(1, "units")
        else:
            canvas.yview_scroll(int(-1 * e.delta / 120), "units")

    # ── drag reorder ──────────────────────────────────────────────────────────

    def drag_over(self, source: ImageCard, x_root: int, y_root: int):
        """Called continuously while dragging; swap cards if hovering over another."""
        target = self._card_under_pointer(x_root, y_root)
        if target is None or target is source:
            return
        si = self._cards.index(source)
        ti = self._cards.index(target)
        self._cards[si], self._cards[ti] = self._cards[ti], self._cards[si]
        self._regrid()

    def drag_end(self, source: ImageCard, x_root: int, y_root: int):
        self._regrid()   # Final tidy

    def _card_under_pointer(self, x_root: int, y_root: int):
        """Return the ImageCard whose bounding box contains (x_root, y_root)."""
        for card in self._cards:
            try:
                cx = card.winfo_rootx()
                cy = card.winfo_rooty()
                cw = card.winfo_width()
                ch = card.winfo_height()
                if cx <= x_root <= cx + cw and cy <= y_root <= cy + ch:
                    return card
            except Exception:
                pass
        return None

    # ── run / cancel ──────────────────────────────────────────────────────────

    def _run(self):
        if not self._meeting_var.get().strip():
            messagebox.showwarning("Meeting name required",
                                   "Please enter a meeting name.")
            return
        if not self._cards:
            messagebox.showwarning("No images", "No images loaded.")
            return
        self._persist_settings()
        self._cancel_requested = False
        self._run_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._open_btn.configure(state="disabled")
        self.after(0, lambda: self._progress.pack(pady=(0, 3)))
        self._progress.configure(value=0)
        self._job_start = __import__("time").monotonic()
        self._timer_running = True
        self.after(1000, self._tick_timer)
        threading.Thread(target=self._process_thread, daemon=True).start()

    def _cancel(self):
        self._cancel_requested = True
        self._timer_running = False
        self._cancel_btn.configure(state="disabled")
        self._status("Cancellation requested...")

    def _tick_timer(self):
        """Update status bar with elapsed time every second while processing."""
        if not getattr(self, "_timer_running", False):
            return
        elapsed = int(__import__("time").monotonic() - self._job_start)
        m, s = divmod(elapsed, 60)
        # Append elapsed to whatever the current status says, or show standalone
        current = self._status_var.get()
        # Strip old timer suffix if present
        if " (" in current and current.endswith(")"):
            current = current[:current.rfind(" (")]
        self._status_var.set(f"{current} ({m}m {s}s)")
        self.after(1000, self._tick_timer)

    # ── processing ────────────────────────────────────────────────────────────

    def _process_thread(self):
        slug    = slugify(self._meeting_var.get())
        fmt     = self._fmt_var.get()
        quality = self._quality_var.get()
        meeting_name = self._meeting_var.get().strip()
        ext          = ".webp" if fmt == "WEBP" else ".jpg"

        folder  = Path(self._folder_var.get())
        out_dir = folder / OUTPUT_FOLDER
        out_dir.mkdir(exist_ok=True)

        total  = len(self._cards)
        errors = []
        lines  = [
            f"The Electric Kool-Aid User Meeting Gallery Maker v{__version__}",
            f"Meeting:   {self._meeting_var.get().strip()}",
            f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
            "=" * 60,
            "",
        ]

        for i, card in enumerate(self._cards):
            if self._cancel_requested:
                self._log("Processing cancelled by user.")
                break

            idx   = i + 1
            fname = make_filename(slug, idx, ext)
            out   = out_dir / fname

            self.after(0, self._status, f"Processing {idx}/{total}: {fname}...")
            self.after(0, self._progress.configure, {"value": int(idx / total * 100)})

            try:
                box     = card.get_crop_box()
                cropped = card.orig.crop(box)
                resized = cropped.resize(OUTPUT_SIZE, Image.LANCZOS)

                save_image(resized, out, fmt, quality)
                kb           = out.stat().st_size // 1024
                used_quality = quality

                # ── per-image quality override if over warning threshold ──────
                if kb > WARN_SIZE_KB:
                    self._log(f"[{idx:03d}] {fname}  {kb} KB  [!] over target — pausing...")
                    event  = threading.Event()
                    result = {"quality": quality, "action": "keep"}
                    self.after(0, self._show_quality_dialog,
                               fname, kb, fmt, resized, quality, event, result)
                    event.wait()   # block until user dismisses dialog

                    if result["action"] == "resave":
                        used_quality = result["quality"]
                        save_image(resized, out, fmt, used_quality)
                        kb = out.stat().st_size // 1024
                        self._log(f"       re-saved at quality {used_quality}  ->  {kb} KB")

                photographer = card.get_photographer()
                flag = "  [!]" if kb > WARN_SIZE_KB else ""
                self._log(f"[{idx:03d}] {fname}  {kb} KB{flag}")

                alt = ""

                lines.append(f"{fname}")
                lines.append("-- Copy the lines below into the Licensing Information field when uploading --")
                lines.append(f"Taken by {photographer or '(not set)'}")
                lines.append(f"Last updated: {datetime.now():%d/%m/%Y}")
                lines.append("")

            except Exception as e:
                errors.append(f"{fname}: {e}")
                self._log(f"[{idx:03d}] ERROR -- {e}")

        lic_path = out_dir / "image-credits.txt"
        try:
            lic_path.write_text("\n".join(lines), encoding="utf-8")
            self._log(f"\nCredits written to: {lic_path}")
        except Exception as e:
            self._log(f"\nCould not write credits file: {e}")

        self._last_output_dir = out_dir
        self.after(0, self._on_done, errors, out_dir)

    def _show_quality_dialog(self, fname, kb, fmt, img, quality,
                              event: threading.Event, result: dict):
        """Instantiated on the main thread; processing thread blocks on event."""
        QualityOverrideDialog(self, fname, kb, fmt, img, quality, event, result)

    def _on_done(self, errors, out_dir):
        self._run_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")
        self._open_btn.configure(state="normal")
        self._progress.pack_forget()
        if errors:
            messagebox.showerror("Errors", "\n".join(errors))
        else:
            messagebox.showinfo(
                "Done",
                f"Processed {len(self._cards)} image(s).\n\n"
                f"Output: {out_dir}\n"
                f"Credits: {out_dir / 'image-credits.txt'}")
        elapsed = int(__import__("time").monotonic() - self._job_start)
        m, s = divmod(elapsed, 60)
        self.after(0, setattr, self, "_timer_running", False)
        self._status(f"Done in {m}m {s}s.  Output in {out_dir}")

    # ── open output ───────────────────────────────────────────────────────────

    def _open_output(self):
        if self._last_output_dir and self._last_output_dir.exists():
            try:
                os.startfile(self._last_output_dir)
            except AttributeError:
                import subprocess
                subprocess.Popen(["xdg-open", str(self._last_output_dir)])

    # ── log ───────────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.after(0, self._log_now, msg)

    def _log_now(self, msg: str):
        self._log_widget.configure(state="normal")
        self._log_widget.insert("end", msg + "\n")
        self._log_widget.see("end")
        self._log_widget.configure(state="disabled")

    def _copy_log(self):
        text = self._log_widget.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
            self._status("Log copied to clipboard.")

    def _status(self, msg: str):
        self.after(0, self._status_var.set, msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback
    try:
        App().mainloop()
    except Exception:
        err = traceback.format_exc()
        # Write to a crash log next to the script
        log_path = Path(__file__).parent / "crash-log.txt"
        try:
            log_path.write_text(err, encoding="utf-8")
        except Exception:
            pass
        # Also try to show a message box
        try:
            import tkinter as _tk
            import tkinter.messagebox as _mb
            _root = _tk.Tk()
            _root.withdraw()
            _mb.showerror(
                "Crash",
                f"The app crashed on startup.\n\n"
                f"Error written to:\n{log_path}\n\n"
                f"{err[-800:]}"
            )
            _root.destroy()
        except Exception:
            pass
        raise
