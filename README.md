# AEB Compositor

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

You can also start it using the provided Makefile:

```bash
make gui
```

After selecting images, click **Create HDR** and then **Save Result** to write `hdr_result.jpg` next to the chosen files.
Use the sliders to tweak saturation, contrast, gamma and brightness before saving.
Two extra buttons let you preview how **Auto Align** and **Deghost** will affect the result before creating the final HDR.

## Web Interface

A minimal Next.js frontend is available in the `frontend` directory. It lets you import images in your browser, shows them grouped by similarity and downloads the processed HDR image.

```bash
cd frontend
npm install  # first time only
npm run dev
```

Open `http://localhost:3000` in your browser and use the **Import Images** button to select your AEB files. Imported files are hashed client-side so similar photos are grouped together. Each group shows a **Create HDR** button to merge that set, and there's also a **Create All** button to process every group at once.

### Docker

To run the web interface in a container, simply execute:

```bash
make run
```

This builds an image using `Dockerfile.web` and starts the app on port 3000.

### Requirements

Install the Python dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

The tools rely on `opencv-python-headless`, `numpy` and `dearpygui` in addition to `exiftool`. On Debian based systems you can install exiftool with `apt-get install exiftool`.

### Release Process

Tagged commits with names starting with `v` trigger an automated workflow.
Pushing a tag such as `v1.0.0` will run the test suite, build the frontend and
upload a zipped archive to the GitHub release page. Create a release with:

```bash
git tag v1.0.0
git push origin v1.0.0
```

After the workflow completes the file `HDR_Compositor-1.0.0.zip` will be
attached to the release.
