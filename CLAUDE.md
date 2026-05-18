# CLAUDE.md

This file provides guidance to Claude (and other AI coding assistants) when working with this repository.

## Project overview

**The Electric Kool-Aid User Meeting Gallery Maker** — a free, local, privacy-respecting Windows desktop app that processes up to 20 photos from a Dyalog user meeting into web-ready 1080x1080 WebP or JPEG images, with crop adjustment, drag-to-reorder, per-image quality control, and optional local AI alt text generation via Ollama.

- **Single-file app:** `the-electric-kool-aid-user-meeting-gallery-maker.py`
- **Current version:** `__version__` constant near the top of the main file
- **Platform:** Windows 10/11 (also runs on macOS/Linux for development)
- **Python:** 3.12+
- **Only non-stdlib dependency:** Pillow

## Running the app

```bat
:: Windows entry point
launch.bat

:: Direct run
py the-electric-kool-aid-user-meeting-gallery-maker.py

:: Dev venv
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py the-electric-kool-aid-user-meeting-gallery-maker.py
```

## Architecture

### Single-file design
Everything is in one file by design: simplicity, auditability, single maintenance point. No sub-modules.

### Key classes

| Class | Purpose |
|-------|---------|
| `App(tk.Tk)` | Main window; owns all top-level UI and the processing thread |
| `ImageCard(ttk.Frame)` | One card per image: drag handle, thumbnail, crop state, photographer, people fields |
| `CropPopup(tk.Toplevel)` | Modal crop adjuster; drag to reposition, scroll-wheel to resize, callback on confirm |
| `QualityOverrideDialog(tk.Toplevel)` | Shown mid-processing when an image exceeds WARN_SIZE_KB; blocks the processing thread via threading.Event |

### Ollama management (module-level functions)

| Function | Purpose |
|----------|---------|
| `ollama_running()` | Checks if Ollama answers at localhost:11434 |
| `ollama_exe_path()` | Returns path to ollama.exe: portable copy first, then PATH |
| `start_ollama(log_fn)` | Starts our portable ollama.exe, waits up to 8s for it to be ready |
| `stop_ollama()` | Terminates our managed process (not externally-started ones) |
| `download_ollama(progress_fn)` | Downloads ollama.exe from GitHub into `_ollama/` next to the script |
| `model_is_pulled(model)` | Checks Ollama's /api/tags to see if a model is locally available |
| `pull_model(model, log_fn)` | Runs `ollama pull <model>` via subprocess, streaming output to log_fn |

Ollama is installed portably into `_ollama/ollama.exe` next to the script. Delete that folder to remove it completely. The app starts Ollama on launch and stops it (if we started it) on close via `WM_DELETE_WINDOW`.

### Threading model

- Ollama startup check runs on a daemon background thread at app launch
- Image processing runs on a daemon background thread
- `QualityOverrideDialog` blocks the processing thread via `threading.Event.wait()`; the dialog is shown via `self.after(0, ...)` on the main thread
- All UI updates marshalled back to main thread via `self.after(0, callback)`
- Crop result delivered via **callback** called before `popup.destroy()` -- never read from `popup.result` after destroy as Tkinter can wipe instance attributes

### Crop popup -- critical design note

`CropPopup` uses an `on_confirm` callback rather than reading `self.result` after `wait_window()`. This is intentional: Tkinter's `destroy()` can wipe instance attributes before `wait_window()` returns, making `popup.result` unreliable. The callback is called *inside* `_confirm()` before `self.destroy()`.

To re-open with the previous crop restored, pass `existing_box=card._crop_box`.

### Filename convention

`user-meeting-image_{meeting-slug}_{index:03d}.webp`

e.g. `user-meeting-image_dyalog-26_007.webp`

`slugify()` lowercases, removes apostrophes/smart-quotes, replaces non-alphanumeric runs with `-`.

### Output

- Output folder: `{input_folder}/processed/`
- Format: WebP (default) or JPEG, quality 40-100 (default 82)
- Always 1080x1080 px, Lanczos resampling
- Always converts to RGB before saving (fixes Errno 22 on Windows with RGBA sources)
- Credits file: `processed/image-credits.txt`

### Credits file format

```
The Electric Kool-Aid User Meeting Gallery Maker v2.2
Meeting:   Dyalog '26
Generated: 2026-05-18 14:32
============================================================

File:         user-meeting-image_dyalog-26_001.webp
Photographer: Johanna Hsu
People:       Jim Brown, Sarah Jones
Size:         134 KB
Alt text:     Jim Brown and Sarah Jones discuss a session at Dyalog '26.

```

### Alt text (Ollama)

- Entirely local -- no data leaves the machine, no API key
- Uses Ollama's REST API: `POST http://localhost:11434/api/generate`
- Default model: `moondream2` (~1.5 GB, vision-capable, CPU-friendly)
- Prompt includes meeting name and people (left to right) for specific descriptions
- Falls back gracefully with an error string if Ollama is not reachable

### Settings

Persisted to `~/.umip_settings.json`:

| Key | Description |
|-----|-------------|
| `last_folder` | Last opened folder |
| `meeting` | Meeting name field |
| `photographer` | Global photographer name |
| `format` | WEBP or JPEG |
| `quality` | Integer 40-100 |
| `alttext` | Bool, whether alt-text generation is enabled |
| `ollama_model` | Ollama model name (default `moondream2`) |

### File size targets

| | KB |
|--|--|
| Aim for | < 160 |
| Soft warning | > 220 |

### UI layout

Window: 1200x820px, resizable. Pack order top to bottom:

1. Input folder
2. Meeting details + Format & quality (side by side)
3. Alt text
4. Image grid (`expand=True` -- takes all spare vertical space)
5. Buttons + progress bar
6. Log (fixed height, does not expand)
7. Status bar (bottom)

Grid: 7 columns, scrollable canvas. Cards are ~130px thumbnails.

### EXIF orientation

`fix_exif_orientation()` is called immediately on load inside `ImageCard.__init__`. The corrected image is `.copy()`-ed into memory and the file handle closed, so the source folder is never locked by the app.

## Known issues / future ideas

- Live per-card file size estimate before export
- macOS/Linux path for portable Ollama (currently Windows-only download URL)
- Support for > 20 images (pagination or multi-batch)
- Drag-to-reorder could show a ghost of the dragged card

## Version history

| Version | Summary |
|---------|---------|
| 1.0 | Initial release |
| 1.1 | EXIF orientation fix; file handle leak fix |
| 1.2 | WebP RGBA->RGB fix (Errno 22); folder locking fix |
| 1.3 | Crop callback pattern (wait_window result unreliable) |
| 1.4 | Crop popup restores previous position; thumbnail updates on crop confirm |
| 1.5 | Wider window (1200px), 7-column grid, drag-to-reorder, per-image quality override |
| 1.6-1.9 | Layout fixes (grid expand, log fixed height) |
| 2.0 | Replaced Anthropic API with local Ollama; people field per card; meeting context in prompt |
| 2.2 | Fixed Ollama download (GitHub API for real URL, User-Agent header) |
| 2.1 | Portable Ollama auto-install into `_ollama/`; startup check and model pull offer |
