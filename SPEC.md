# Specification — The Electric Kool-Aid User Meeting Gallery Maker

## Purpose

A single-file Windows desktop app for processing photos from software user meetings into consistently formatted, web-ready square images. The goal is to make it fast and repeatable to go from a folder of raw photos to a set of correctly sized, cropped, and credited images ready for upload to a media gallery.

## Core requirements

### Input
- Load up to 20 images from a single folder
- Supported input formats: JPEG, PNG, WebP, TIFF, BMP
- EXIF orientation must be corrected at load time
- Source folder must never be locked (file handles closed immediately after load)

### Output
- All images exported as 1080×1080 pixels
- Supported output formats: WebP, JPEG
- Output saved to a `processed/` subfolder inside the input folder
- Filename convention: `user-meeting-image_{slug}_{index:03d}.webp`
  - Slug derived from meeting name: lowercase, apostrophes/smart-quotes removed, non-alphanumeric characters replaced with `-`
  - Index is zero-padded to 3 digits, reflecting the order shown in the grid

### Credits file
- An `image-credits.txt` is written to the `processed/` folder alongside the images
- Format per image:
  ```
  user-meeting-image_techconf-25_001.webp
  -- Copy the lines below into the Licensing Information field when uploading --
  Taken by Jane Smith
  Last updated: DD/MM/YYYY
  ```
- Date uses the actual processing date in DD/MM/YYYY format
- File opens with a header showing meeting name, app version, and generation timestamp

## Crop behaviour

- Default crop: centred square crop of the largest square that fits within the image
- User can adjust the crop per image via a popup crop adjuster
- Crop adjuster shows the full image with a draggable/resizable square overlay
- Adjusted crop is visually indicated on the card (green border, "crop adjusted" label)
- Re-opening the crop popup restores the previously set crop position
- Thumbnail updates immediately when crop is confirmed

## Image grid

- Images displayed in a scrollable grid, 7 columns wide
- Each card shows: drag handle, thumbnail, sequence number, source filename, crop status, Adjust crop button, photographer field
- Cards can be drag-reordered; output index reflects the final grid order
- Sequence numbers update live as cards are reordered
- Photographer field on each card overrides the global default photographer for that image

## Quality control

- Target file size: < 160 KB
- Warning threshold: > 220 KB
- If a processed image exceeds the warning threshold, processing pauses and a dialog is shown
- The dialog shows the current file size and lets the user either accept it or re-save at a lower quality
- The user-chosen quality for that image is used; the global quality setting is unchanged

## Meeting details

- Meeting name: free text, used for slug generation and credits file header
- Default photographer: free text, used as fallback when no per-image photographer is set
- Format: WebP or JPEG
- Quality: slider, 1–95

## Settings persistence

- Settings saved to `~/.umip_settings.json` on every process run
- Persisted: last folder, meeting name, photographer, format, quality
- Settings loaded on startup
- Settings file is user-specific and must not be committed to version control

## Status and feedback

- Log panel shows per-image processing results including filename, size, and any warnings
- Status bar shows current operation and live elapsed time while processing
- Progress bar fills as images are processed
- Processing runs on a background thread; UI remains responsive
- Cancel button stops processing after the current image completes

## Non-requirements (explicitly out of scope)

- macOS or Linux support
- Processing more than 20 images per run
- AI-generated alt text
- Cloud upload or any network connectivity
- Installer or bundled executable — distributed as a `.py` file with `launch.bat`
