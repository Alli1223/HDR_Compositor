import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from find_and_merge_aeb import (
    find_aeb_images_and_exposure_times_from_list,
    load_images,
    create_hdr,
)

def tonemap_mantiuk(hdr_image):
    tonemap = cv2.createTonemapMantiuk()
    tonemap.setSaturation(1.2)
    tonemap.setScale(0.7)
    ldr = tonemap.process(hdr_image.copy())
    ldr_8bit = np.clip(ldr * 255, 0, 255).astype('uint8')
    return ldr_8bit

class HDRGui:
    def __init__(self, root):
        self.root = root
        self.root.title("HDR Compositor")
        self.file_paths = []
        self.hdr_image = None
        self.ldr_image = None

        self.select_btn = tk.Button(root, text="Select Images", command=self.select_files)
        self.select_btn.pack(pady=5)

        self.listbox = tk.Listbox(root, width=80)
        self.listbox.pack(pady=5)

        self.create_btn = tk.Button(root, text="Create HDR", command=self.create_hdr_image)
        self.create_btn.pack(pady=5)

        self.save_btn = tk.Button(root, text="Save Result", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(pady=5)

        self.image_label = tk.Label(root)
        self.image_label.pack(pady=5)

    def select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select AEB Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff")],
        )
        if paths:
            self.file_paths = list(paths)
            self.listbox.delete(0, tk.END)
            for p in self.file_paths:
                self.listbox.insert(tk.END, p)
            self.save_btn.config(state=tk.DISABLED)
            self.image_label.configure(image="")

    def create_hdr_image(self):
        if len(self.file_paths) < 3:
            messagebox.showwarning("Selection Error", "Select at least three images.")
            return
        aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(self.file_paths)
        if len(aeb_images) < 3:
            messagebox.showwarning("AEB Error", "Selected images do not contain enough AEB exposures.")
            return
        images = load_images(aeb_images)
        self.hdr_image = create_hdr(images, exposure_times)
        self.ldr_image = tonemap_mantiuk(self.hdr_image)
        self.display_image(self.ldr_image)
        self.save_btn.config(state=tk.NORMAL)

    def display_image(self, img):
        bgr = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(bgr)
        im.thumbnail((600, 400))
        tk_img = ImageTk.PhotoImage(im)
        self.image_label.configure(image=tk_img)
        self.image_label.image = tk_img

    def save_image(self):
        if self.ldr_image is None:
            return
        first_dir = os.path.dirname(self.file_paths[0])
        save_path = os.path.join(first_dir, "hdr_result.jpg")
        cv2.imwrite(save_path, self.ldr_image)
        messagebox.showinfo("Saved", f"HDR image saved to {save_path}")


def main():
    root = tk.Tk()
    app = HDRGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
