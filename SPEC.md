# Specification — The Electric Kool-Aid User Meeting Gallery Maker

## Purpose

A single-file Windows desktop app for processing photos from software user meetings into consistently formatted, web-ready square images. Two independent tabs let the user work on a gallery batch or a single hero image without having to do both in the same session.

---

## Gallery tab

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
  user-meeting-image_spring-conf-25_001.webp
  -- Copy the lines below into the Licensing Information field when uploading --
  Taken by Jane Smith
  Last updated by MikeM - 21/05/2026
  ```
- Date uses the actual processing date in DD/MM/YYYY format
- Name comes from the "Your name" field
- File opens with a header showing meeting name, app version, and generation timestamp

### Crop behaviour
- Default crop: centred square crop of the largest square that fits within the image
- User can adjust the crop per image via a popup crop adjuster
- Crop adjuster shows the full image with a draggable/resizable square overlay
- Adjusted crop is visually indicated on the card (green border, "crop adjusted" label)
- Re-opening the crop popup restores the previously set crop position
- Thumbnail updates immediately when crop is confirmed

### Image grid
- Images displayed in a scrollable grid, 7 columns wide
- Each card shows: drag handle, thumbnail, sequence number, source filename, crop status, Adjust crop button, photographer field
- Cards can be drag-reordered; output index reflects the final grid order
- Sequence numbers update live as cards are reordered
- Photographer field on each card overrides the global default photographer for that image

### Meeting details fields
- Meeting name: free text, used for slug generation and credits file header
- Default photographer: free text, used as fallback when no per-image photographer is set
- Your name: free text, shared with hero tab, used in "Last updated by" credits line
- Format: WebP or JPEG
- Quality: slider, 40–100

---

## Hero Image tab

### Input
- Single file picker — any supported image format
- EXIF orientation corrected at load time; file handle closed immediately

### Output
- Image exported as 1080×1080 pixels
- Supported output formats: WebP, JPEG
- Output saved to the **same folder as the source image** (no subfolder)
- Filename convention: `heroImg_user-meeting_{slug}_{index:02d}.webp`
  - Slug derived from event name field using the same `slugify()` function
  - Index starts at `01` and auto-increments if a file with the same name already exists
  - The user never sees or controls the index

### Credits file
- A `.txt` file is written alongside the image, using the same stem as the image filename
  (e.g. `heroImg_user-meeting_spring-conf-25_01.txt`)
- Format:
  ```
  {source/licence text entered by user}

  Last updated by {name} - {DD/MM/YYYY}
  ```
- If no source/licence text is entered, only the "Last updated by" line is written
- Date uses the actual processing date in DD/MM/YYYY format
- Name comes from the shared "Your name" field

### Crop behaviour
- Same `CropPopup` as gallery tab; same drag/scroll interaction
- Title shows "Adjust crop -- hero image" instead of an image number
- Adjusted crop indicated by green border on the thumbnail

### Event details fields
- Event name: free text, used for slug generation
- Your name: shared StringVar with gallery tab — updating it in either tab updates both
- Format: WebP or JPEG (independent setting from gallery)
- Quality: slider, 40–100 (independent setting from gallery)

### Source & licence information
- Multi-line free text field
- User enters the source URL, licence, and any other credit text
- The "Last updated by" line is appended automatically — not entered by the user

---

## Shared behaviour

### Quality control (both tabs)
- Target file size: < 160 KB
- Warning threshold: > 220 KB
- If a processed image exceeds the warning threshold, processing pauses and a dialog is shown
- The dialog shows the current file size and lets the user accept it or re-save at a lower quality
- The user-chosen quality for that image is used; the global quality setting is unchanged

### Your name field
- Single `tk.StringVar` shared between both tabs
- Persisted to settings so it only needs to be entered once
- Used in credits as `Last updated by {name} - {DD/MM/YYYY}`

### Log and status bar
- Log panel and status bar live outside the notebook — shared by both tabs
- Log shows per-image processing results including filename, size, and any warnings
- Status bar shows current operation and live elapsed time while gallery processing runs
- Progress bar (gallery: determinate; hero: indeterminate spinner) appears during processing

---

## Settings persistence
- Settings saved to `~/.umip_settings.json` on every process run
- Persisted: last folder, meeting name, photographer, your name, format, quality, hero event name, hero format, hero quality
- Settings loaded on startup
- Settings file is user-specific and must not be committed to version control

---

## Non-requirements (explicitly out of scope)
- macOS or Linux support
- Processing more than 20 images per gallery run
- AI-generated alt text
- Cloud upload or any network connectivity
- Installer or bundled executable — distributed as a `.py` file with `launch.bat`
- Multiple hero images per session (handled by auto-increment; user just runs it again)
