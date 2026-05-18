# The Electric Kool-Aid User Meeting Gallery Maker

A free, local, privacy-respecting Windows desktop app for processing photos from software user meetings into web-ready 1080×1080 images.

## What it does

- Loads up to 20 photos from a folder
- Lets you adjust the crop point per image (drag to reposition, scroll to resize)
- Drag-and-drop reordering of images before export
- Exports all images as 1080×1080 WebP or JPEG, compressed to a target file size
- Generates an `image-credits.txt` with filenames and photographer credits
- Filenames follow the convention `user-meeting-image_{meeting-slug}_{index}.webp`, e.g. `user-meeting-image_techconf-25_007.webp`

## Requirements

- Windows 10 or 11
- Python 3.12 or later — download from [python.org](https://python.org) (tick "Add Python to PATH" during install)
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
