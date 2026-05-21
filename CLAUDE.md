# CLAUDE.md — Developer Notes

**The Electric Kool-Aid User Meeting Gallery Maker** — a free, local Windows desktop app with two independent tabs:

- **Gallery tab** — processes up to 20 photos from a user meeting into web-ready 1080×1080 WebP or JPEG images, with crop adjustment, drag-to-reorder, and per-image quality control.
- **Hero Image tab** — processes a single image into a 1080×1080 hero image with source/licence credits, saved alongside the source file.

## Key files

| File | Purpose |
|------|---------|
| `the-electric-kool-aid-user-meeting-gallery-maker.py` | Single-file app |
| `launch.bat` | Windows launcher — checks Python version, installs Pillow, runs app |
| `requirements.txt` | `Pillow>=10.0.0` only |
| `~/.umip_settings.json` | Per-user settings (not committed) |

## Architecture

Single-file design. Key classes:

| Class | Role |
|-------|------|
| `App(tk.Tk)` | Main window, tab notebook, processing threads, settings |
| `ImageCard(ttk.Frame)` | Thumbnail, drag handle, crop state, photographer field (gallery tab) |
| `CropPopup(tk.Toplevel)` | Modal crop adjuster — used by both gallery and hero tabs |
| `QualityOverrideDialog(tk.Toplevel)` | Blocks processing thread via `threading.Event` when image exceeds warn threshold |

## Key technical decisions

**Tab structure:** `ttk.Notebook` with Gallery and Hero Image tabs. The log and status bar live outside the notebook so both tabs share them. Status bar is packed `side="bottom"` first, then log `side="bottom"`, then notebook fills remaining space.

**Crop callback pattern:** `on_confirm(box)` is called inside `_confirm()` before `self.destroy()`. Re-opening passes `existing_box` to restore previous position. Critical because Tkinter's `destroy()` wipes instance attributes.

**CropPopup index parameter:** Accepts `int` (gallery) or `str` (hero — passes `"hero image"`). Title built conditionally.

**Shared StringVar:** `self._your_name_var` is created in `_build_gallery_ui` and reused by `_build_hero_ui`. Both tabs show the same field backed by one variable.

**EXIF orientation:** Fixed at load time via `fix_exif_orientation()`, image `.copy()`-ed into memory immediately, file handle closed — source folder never locked.

**WebP saving:** Always converts to RGB before saving — fixes Errno 22 on Windows with RGBA sources.

## Gallery output

Processed images saved to `processed/` subfolder. Credits file format per image:

```
user-meeting-image_spring-conf-25_001.webp
-- Copy the lines below into the Licensing Information field when uploading --
Taken by Jane Smith
Last updated by MikeM - 21/05/2026
```

## Hero output

Hero image and credits `.txt` saved in the **same folder as the source image** (no subfolder).

Credits file format:
```
From Envato, used under our subscription (https://elements.envato.com/...).

Last updated by MikeM - 21/05/2026
```

The source/licence block is free text entered by the user. The "Last updated by" line is appended automatically using the "Your name" field and today's date.

## Filename conventions

**Gallery:** `user-meeting-image_{slug}_{index:03d}.webp`

**Hero:** `heroImg_user-meeting_{slug}_{index:02d}.webp`

Hero index auto-increments (`_01`, `_02`, …) if a file with the same name already exists in the output folder. The user never sees or controls this.

`slugify()`: lowercase, remove apostrophes/smart-quotes, non-alphanumeric → `-`

## File size targets

- Aim: <160 KB
- Warn: >220 KB

Quality override dialog pauses the processing thread if an image exceeds the warn threshold. Applies to both gallery and hero processing.

## Settings persisted to `~/.umip_settings.json`

`last_folder`, `meeting`, `photographer`, `your_name`, `format`, `quality`, `hero_meeting`, `hero_format`, `hero_quality`

## UI layout

Top-level (outside notebook):
1. `ttk.Notebook` (expand=True)
2. Log (fixed height, does not expand) — packed `side="bottom"`
3. Status bar — packed `side="bottom"` before log

Gallery tab (pack order top→bottom):
1. Input folder
2. Meeting details (name, default photographer, your name) + Format & quality (side by side)
3. Image grid (expand=True, scrollable canvas, 7 cols)
4. Buttons + progress bar

Hero Image tab (pack order top→bottom):
1. Source image (file picker + thumbnail + crop button)
2. Event details (name, your name) + Format & quality (side by side)
3. Source & licence information (multi-line text area)
4. Buttons + progress bar

## Version history

| Version | Changes |
|---------|---------|
| 1.0 | Initial build |
| 1.3 | Crop callback pattern fix |
| 1.5 | Wide window, drag-to-reorder, per-image quality override |
| 2.0 | Ollama alt text integration (later removed) |
| 2.6 | Removed Ollama/alt text/people fields; simplified to core image processing |
| 3.0 | Hero Image tab; Your Name field; updated credits format |
