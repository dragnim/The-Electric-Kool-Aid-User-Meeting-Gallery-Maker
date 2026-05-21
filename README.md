# The Electric Kool-Aid User Meeting Gallery Maker

A free, local, privacy-respecting Windows desktop app for processing photos from software user meetings into web-ready 1080×1080 images. Two independent tabs — use whichever you need, whenever you need it.

## Should I use this?

Use this if you need to turn a small set of event or user meeting photos into consistent square images for a website gallery, or to produce a single hero image for an event page. It is designed for batches of up to 20 images, with manual crop control, file-size checks, consistent filenames, and credit text ready to paste into a media gallery upload form.

It does not edit your original images. It does not upload anything. It does not generate alt text. It only processes images in the selected folder, up to 20 at a time.

## Two tabs, two workflows

### Gallery tab

Process a batch of up to 20 photos into consistently named gallery images.

| Item | Where it goes | Purpose |
|------|--------------|---------|
| 1080×1080 WebP or JPEG images | `processed/` folder | Web-ready gallery images |
| `image-credits.txt` | `processed/` folder | Copy/paste credit text for uploads |

### Hero Image tab

Process a single image into a hero image for an event page.

| Item | Where it goes | Purpose |
|------|--------------|---------|
| 1080×1080 WebP or JPEG image | Same folder as source | Web-ready hero image |
| `heroImg_…_01.txt` | Same folder as source | Copy/paste licence/source text for uploads |

## What it does

### Gallery tab
- Loads up to 20 photos from a folder
- Lets you adjust the crop per image (drag to reposition, scroll to resize)
- Drag-and-drop reordering of images before export
- Exports all images as 1080×1080 WebP or JPEG, compressed to a target file size
- Pauses if any image exceeds the file size warning threshold and lets you adjust quality individually
- Generates an `image-credits.txt` with filenames, photographer credits, and last-updated-by info
- Filenames: `user-meeting-image_{meeting-slug}_{index}.webp`, e.g. `user-meeting-image_spring-conf-25_007.webp`

### Hero Image tab
- Pick a single source image
- Adjust crop with the same crop tool as the gallery
- Enter the source URL and licence information (free text)
- Exports a 1080×1080 WebP or JPEG with auto-incremented filename
- Generates a matching `.txt` credits file with your source/licence text and a "Last updated by" line
- Filename: `heroImg_user-meeting_{event-slug}_{index}.webp`, e.g. `heroImg_user-meeting_spring-conf-25_01.webp`
- If a file with the same name already exists, the index increments automatically (`_01`, `_02`, …)

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

## Output examples

### Gallery credits (`image-credits.txt`)

```
user-meeting-image_spring-conf-25_001.webp
-- Copy the lines below into the Licensing Information field when uploading --
Taken by Jane Smith
Last updated by MikeM - 21/05/2026

user-meeting-image_spring-conf-25_002.webp
-- Copy the lines below into the Licensing Information field when uploading --
Taken by Alex Jones
Last updated by MikeM - 21/05/2026
```

### Hero credits (`heroImg_user-meeting_spring-conf-25_01.txt`)

```
From Envato, used under our subscription (https://elements.envato.com/stock-market-graph-EFMLMBC).

Last updated by MikeM - 21/05/2026
```

Or for a free-licence source:

```
Downloaded from unsplash.com: https://unsplash.com/photos/... Free to use under the Unsplash licence: https://unsplash.com/license

Last updated by MikeM - 21/05/2026
```

## File size guidance

| Target | Threshold |
|--------|-----------|
| Aim for | < 160 KB |
| Warning | > 220 KB |

If a processed image exceeds the warning threshold, the app pauses and lets you lower the quality for that image before continuing. Applies to both gallery and hero processing.

## Your name field

Both tabs include a "Your name" field. Enter your name once and it will be remembered. It is used in credits as `Last updated by [name] - [date]`. You add the name in the tool; recipients paste the generated text into WordPress (or wherever) when uploading.

## Folder structure

```
anywhere-on-your-pc/
├── the-electric-kool-aid-user-meeting-gallery-maker.py   ← main app
├── launch.bat                                             ← Windows launcher
└── requirements.txt

your-gallery-photos/                                       ← wherever your photos are
├── photo1.jpg
├── photo2.jpg
└── processed/                                             ← created automatically
    ├── user-meeting-image_spring-conf-25_001.webp
    ├── user-meeting-image_spring-conf-25_002.webp
    └── image-credits.txt

your-hero-source/                                          ← wherever the hero source is
├── hero-source.jpg
├── heroImg_user-meeting_spring-conf-25_01.webp            ← saved here automatically
└── heroImg_user-meeting_spring-conf-25_01.txt
```

## Settings

User preferences are saved to `~/.umip_settings.json`. This file is specific to your machine and should not be committed to version control — it is listed in `.gitignore`.

Persisted settings: last folder, meeting name, photographer, your name, format, quality, hero event name, hero format, hero quality.

## Licence

MIT — see [LICENSE](LICENSE).

## Provenance

> **100% Prime AI Slop** 🍋
>
> This tool — every line of code, every comment, and every doc — was written entirely by [Claude](https://claude.ai) (Anthropic). The design decisions were the human's: what the tool needed to do, the output format, the credits file structure, when to stop adding features, and the name. The human's other contributions were knowing what they wanted, asking good questions, and the occasional "that's rubbish, try again."
>
> No code was written by hand. No docs were written by hand. Vibe coding is real, it works, and this is what it looks like when you don't pretend otherwise. If you find a bug, Claude probably wrote it. If you like it, the human probably decided it should exist.
