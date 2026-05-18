# The Electric Kool-Aid User Meeting Gallery Maker

A free, local, privacy-respecting Windows desktop app for processing photos from software user meetings into web-ready 1080×1080 images.

## Should I use this?

Use this if you need to turn a small set of event or user meeting photos into consistent square images for a website gallery. It is designed for batches of up to 20 images, with manual crop control, file-size checks, consistent filenames, and photographer credit text ready to paste into a media gallery upload form.

It does not edit your original images. It does not upload anything. It does not generate alt text. It only processes images in the selected folder, up to 20 at a time.

## What it creates

| Item | Where it goes | Purpose |
|------|--------------|---------|
| 1080×1080 WebP or JPEG images | `processed/` folder | Web-ready gallery images |
| `image-credits.txt` | `processed/` folder | Copy/paste credit text for uploads |
| `.umip_settings.json` | User home folder | Remembers your last settings |

## What it does

- Loads up to 20 photos from a folder
- Lets you adjust the crop point per image (drag to reposition, scroll to resize)
- Drag-and-drop reordering of images before export
- Exports all images as 1080×1080 WebP or JPEG, compressed to a target file size
- Pauses if any image exceeds the file size warning threshold and lets you adjust quality for that image individually
- Generates an `image-credits.txt` with filenames and photographer credits
- Filenames follow the convention `user-meeting-image_{meeting-slug}_{index}.webp`, e.g. `user-meeting-image_techconf-25_007.webp`

## Requirements

- Windows 10 or 11
- Python 3.12 or 3.13 — download from [python.org](https://python.org) (tick "Add Python to PATH" during install)
- [Pillow](https://python-pillow.org/) — installed automatically by `launch.bat`

## Running the app

Double-click `launch.bat`. It will check your Python version, install Pillow if needed, and launch the app.

Or run directly:

```
py the-electric-kool-aid-user-meeting-gallery-maker.py
```

## Output

All processed images are saved into a `processed/` subfolder inside your chosen input folder, alongside an `image-credits.txt` file:

```
user-meeting-image_techconf-25_001.webp
-- Copy the lines below into the Licensing Information field when uploading --
Taken by Jane Smith
Last updated: DD/MM/YYYY
```

## File size guidance

| Target | Threshold |
|--------|-----------|
| Aim for | < 160 KB |
| Warning | > 220 KB |

If a processed image exceeds the warning threshold, the app pauses and lets you lower the quality for that image before continuing.

## Folder structure

The app files can live anywhere. Your photos can also be anywhere — you just browse to them when you run the app. Processed images are saved into a `processed/` subfolder inside whichever folder you select.

```
anywhere-on-your-pc/
├── the-electric-kool-aid-user-meeting-gallery-maker.py   ← main app
├── launch.bat                                             ← Windows launcher
└── requirements.txt

your-photos/                                               ← wherever your photos are
├── photo1.jpg
├── photo2.jpg
└── processed/                                             ← created automatically
    ├── user-meeting-image_techconf-25_001.webp
    ├── user-meeting-image_techconf-25_002.webp
    └── image-credits.txt
```

## Settings

User preferences (last folder, meeting name, photographer, format, quality) are saved to `~/.umip_settings.json`. This file is specific to your machine and should not be committed to version control — it is listed in `.gitignore`.

## Licence

MIT — see [LICENSE](LICENSE).

## Provenance

> **100% Prime AI Slop** 🍋
>
> This tool — every line of code, every comment, and every doc — was written entirely by [Claude](https://claude.ai) (Anthropic). The design decisions were the human's: what the tool needed to do, the output format, the credits file structure, when to stop adding features, and the name. The human's other contributions were knowing what they wanted, asking good questions, and the occasional "that's rubbish, try again."
>
> No code was written by hand. No docs were written by hand. Vibe coding is real, it works, and this is what it looks like when you don't pretend otherwise. If you find a bug, Claude probably wrote it. If you like it, the human probably decided it should exist.
