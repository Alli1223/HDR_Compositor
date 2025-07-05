# HDR Compositor

This repository contains tools for merging Auto Exposure Bracketing (AEB) images into a single HDR photograph.

## Command Line Usage

`find_and_merge_aeb.py` can be run directly to search a folder for AEB tagged images and create HDR files for each set found.

```bash
python find_and_merge_aeb.py <input_dir> <output_dir>
```

## GUI Application

A simple DearPyGui based application is provided in `hdr_gui.py`. It allows you to select 3–5 images manually and create an HDR image which can be saved back to the same directory.

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

### Docker

To run the web interface in a container, simply execute:

```bash
make run
```

This builds an image using `Dockerfile.web` with Docker Buildx and starts the app on port 3000. Make sure the Buildx component is installed as described in the Docker documentation.

### Requirements

Install the Python dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

The tools rely on `opencv-python-headless`, `numpy` and `dearpygui` in addition to `exiftool`. On Debian based systems you can install exiftool with `apt-get install exiftool`.
