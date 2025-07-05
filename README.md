# HDR Compositor

This repository contains tools for merging Auto Exposure Bracketing (AEB) images into a single HDR photograph.

## Command Line Usage

`find_and_merge_aeb.py` can be run directly to search a folder for AEB tagged images and create HDR files for each set found. Optional flags enable automatic alignment and ghost removal.

```bash
python find_and_merge_aeb.py <input_dir> <output_dir> [--ghost LEVEL] [--align]
```

## GUI Application

A simple DearPyGui based application is provided in `hdr_gui.py`. It allows you to select 3–5 images manually and create an HDR image which can be saved back to the same directory. The interface includes a slider for ghost removal strength and a checkbox to automatically align the photos.

Run the GUI with:

```bash
python hdr_gui.py
```

After selecting images, click **Create HDR** and then **Save Result** to write `hdr_result.jpg` next to the chosen files.

## Web Interface

A minimal Next.js frontend is available in the `frontend` directory. It lets you select images in your browser and downloads the processed HDR image.

```bash
cd frontend
npm install  # first time only
npm run dev
```

Open `http://localhost:3000` in your browser, select your AEB images and click **Create HDR**.
The page includes a slider for ghost removal strength and a checkbox to enable automatic alignment. These values are sent to the backend, which sets the corresponding `GHOST_LEVEL` and `AUTO_ALIGN` environment variables when invoking `process_uploads.py`.

### Docker

To run the web interface in a container, simply execute:

```bash
make run
```

This builds an image using `Dockerfile.web` and starts the app on port 3000.

### Requirements

The scripts rely on `opencv-python`, `numpy`, `dearpygui` and `exiftool` being available. On Debian based systems you can install exiftool with `apt-get install exiftool`.
