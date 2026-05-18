# The Electric Kool-Aid User Meeting Gallery Maker

A free, local, privacy-respecting Windows desktop app for processing photos from Dyalog user meetings into web-ready 1080×1080 images.

## What it does

- Loads up to 20 photos from a folder
- Lets you adjust the crop point per image (drag to reposition, scroll to resize)
- Drag-and-drop reordering of images before export
- Exports all images as 1080×1080 WebP or JPEG, compressed to a target file size
- Generates an `image-credits.txt` with filenames, photographer credits, and optional AI-generated alt text
- Filenames follow the convention `user-meeting-image_{meeting-slug}_{index}.webp`, e.g. `user-meeting-image_dyalog-26_007.webp`

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

## Alt text (optional)

The app can generate AI alt text for each image entirely locally — no internet connection required after setup, no data sent anywhere, no API key needed.

It uses [Ollama](https://ollama.com) to run a small vision model (`moondream2`, ~1.5 GB) on your own machine. On first run the app will offer to download Ollama and the model automatically.

**Portable install:** Ollama is downloaded as a single `ollama.exe` into an `_ollama/` folder next to the script. To uninstall it completely, just delete that folder.

The alt text prompt includes the meeting name and any people you have named per image (left to right), so it can produce specific descriptions like *"Jim Brown presenting at Dyalog '26."* rather than generic ones.

## Output

All processed images are saved into a `processed/` subfolder inside your chosen input folder, alongside an `image-credits.txt` file:

```
File:         user-meeting-image_dyalog-26_001.webp
Photographer: Johanna Hsu
People:       Jim Brown, Sarah Jones
Size:         134 KB
Alt text:     Jim Brown and Sarah Jones discuss a presentation at Dyalog '26.
```

## File size guidance

| Target | Threshold |
|--------|-----------|
| Aim for | < 160 KB |
| Warning | > 220 KB |

If a processed image exceeds the warning threshold, the app pauses and lets you lower the quality for that image before continuing.

## Folder structure

```
your-project/
├── the-electric-kool-aid-user-meeting-gallery-maker.py   ← main app
├── launch.bat                                             ← Windows launcher
├── requirements.txt
├── _ollama/                                               ← portable Ollama (created on demand)
│   └── ollama.exe
└── your-photos/
    ├── photo1.jpg
    ├── photo2.jpg
    └── processed/                                         ← output folder
        ├── user-meeting-image_dyalog-26_001.webp
        ├── user-meeting-image_dyalog-26_002.webp
        └── image-credits.txt
```

## Settings

User preferences (last folder, meeting name, photographer, format, quality, Ollama model) are saved to `~/.umip_settings.json`. This file is specific to your machine and should not be committed to version control — it is listed in `.gitignore`.

## Licence

MIT — see [LICENSE](LICENSE).
