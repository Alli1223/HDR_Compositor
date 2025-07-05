# HDR Compositor

This repository contains tools for merging Auto Exposure Bracketing (AEB) images into a single HDR photograph.

## Command Line Usage

`find_and_merge_aeb.py` can be run directly to search a folder for AEB tagged images and create HDR files for each set found.

```bash
python find_and_merge_aeb.py <input_dir> <output_dir>
```

## GUI Application

A simple Tkinter based application is provided in `hdr_gui.py`. It allows you to select 3–5 images manually and create an HDR image which can be saved back to the same directory.

Run the GUI with:

```bash
python hdr_gui.py
```

After selecting images, click **Create HDR** and then **Save Result** to write `hdr_result.jpg` next to the chosen files.

### Requirements

The scripts rely on `opencv-python`, `numpy`, `Pillow` and `exiftool` being available. On Debian based systems you can install exiftool with `apt-get install exiftool`.
