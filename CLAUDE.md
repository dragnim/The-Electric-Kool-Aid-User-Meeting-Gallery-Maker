# CLAUDE.md — Developer Notes

**The Electric Kool-Aid User Meeting Gallery Maker** — a free, local Windows desktop app that processes up to 20 photos from a software user meeting into web-ready 1080×1080 WebP or JPEG images, with crop adjustment, drag-to-reorder, and per-image quality control.

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
| `App(tk.Tk)` | Main window, processing thread, settings |
| `ImageCard(ttk.Frame)` | Thumbnail, drag handle, crop state, photographer field |
| `CropPopup(tk.Toplevel)` | Modal crop adjuster — uses callback pattern (`on_confirm`) called before `destroy()` |
| `QualityOverrideDialog(tk.Toplevel)` | Blocks processing thread via `threading.Event` when image exceeds warn threshold |

## Key technical decisions

**Crop callback pattern:** `on_confirm(box)` is called inside `_confirm()` before `self.destroy()`. Re-opening passes `existing_box=card._crop_box` to restore previous position. This is critical because Tkinter's `destroy()` wipes instance attributes.

**EXIF orientation:** Fixed at load time via `fix_exif_orientation()`, image `.copy()`-ed into memory immediately, file handle closed — source folder never locked.

**WebP saving:** Always converts to RGB before saving — fixes Errno 22 on Windows with RGBA sources.

## Output

Processed images saved to `processed/` subfolder. Credits file format per image:

```
user-meeting-image_techconf-25_001.webp
-- Copy the lines below into the Licensing Information field when uploading --
Taken by Jane Smith
Last updated: DD/MM/YYYY
```

## Filename convention

`user-meeting-image_{slug}_{index:03d}.webp`

`slugify()`: lowercase, remove apostrophes/smart-quotes, non-alphanumeric → `-`

## File size targets

- Aim: <160 KB
- Warn: >220 KB

Quality override dialog pauses processing thread if image exceeds warn threshold.

## Settings persisted to `~/.umip_settings.json`

`last_folder`, `meeting`, `photographer`, `format`, `quality`

## UI layout (pack order top→bottom)

1. Input folder
2. Meeting details + Format & quality (side by side)
3. Image grid (`expand=True`, scrollable canvas, 7 cols)
4. Buttons + progress bar
5. Log (fixed height, does not expand)
6. Status bar (shows elapsed time during processing)

## Version history

| Version | Changes |
|---------|---------|
| 1.0 | Initial build |
| 1.3 | Crop callback pattern fix |
| 1.5 | Wide window, drag-to-reorder, per-image quality override |
| 2.0 | Ollama alt text integration (later removed) |
| 2.6 | Removed Ollama/alt text/people fields; simplified to core image processing |
