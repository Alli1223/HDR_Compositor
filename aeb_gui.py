import os
import cv2
import numpy as np
import dearpygui.dearpygui as dpg

try:  # support running as part of a package or as a script
    from .find_and_merge_aeb import (
        find_aeb_images_and_exposure_times_from_list,
        load_images,
        create_hdr,
    )
    from .hdr_utils import get_medium_exposure_image, tonemap_mantiuk
except ImportError:  # pragma: no cover - fallback for direct execution
    from find_and_merge_aeb import (
        find_aeb_images_and_exposure_times_from_list,
        load_images,
        create_hdr,
    )
    from hdr_utils import get_medium_exposure_image, tonemap_mantiuk

class AEBGui:
    def __init__(self):
        self.file_paths = []
        self.hdr_image = None
        self.ldr_image = None

        with dpg.window(label="AEB Compositor", width=800, height=600):
            dpg.add_button(label="Select Images", callback=self.select_files)
            self.listbox = dpg.add_listbox(items=[], num_items=5, width=780)
            dpg.add_button(label="Create HDR", callback=self.create_hdr_image)
            self.save_btn = dpg.add_button(label="Save Result", callback=self.save_image, enabled=False)
            with dpg.group() as self.image_group:
                dpg.add_text("HDR preview will appear here")

    def select_files(self):
        dpg.show_item("file_dialog")

    def _file_selected(self, sender, app_data):
        self.file_paths = list(app_data["selections"].values())
        dpg.configure_item(self.listbox, items=self.file_paths)
        dpg.configure_item(self.save_btn, enabled=False)
        dpg.delete_item(self.image_group, children_only=True)
        dpg.add_text("HDR preview will appear here", parent=self.image_group)

    def create_hdr_image(self):
        if len(self.file_paths) < 3:
            dpg.show_logger()
            dpg.log_warning("Select at least three images.")
            return
        aeb_images, exposure_times = find_aeb_images_and_exposure_times_from_list(self.file_paths)
        if len(aeb_images) < 3:
            dpg.show_logger()
            dpg.log_warning("Selected images do not contain enough AEB exposures.")
            return
        images = load_images(aeb_images)
        self.hdr_image = create_hdr(images, exposure_times)
        ref_image = get_medium_exposure_image(images, exposure_times)
        self.ldr_image = tonemap_mantiuk(self.hdr_image, ref_image)
        self.display_image(self.ldr_image)
        dpg.configure_item(self.save_btn, enabled=True)

    def display_image(self, img):
        rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        height, width = rgba.shape[:2]
        data = (rgba / 255.0).flatten().astype(np.float32)
        if dpg.does_item_exist("hdr_texture"):
            dpg.set_value("hdr_texture", data)
            dpg.configure_item("hdr_texture", width=width, height=height)
        else:
            with dpg.texture_registry(show=False):
                dpg.add_static_texture(width, height, data, tag="hdr_texture")
        if dpg.does_item_exist("hdr_image"):
            dpg.configure_item("hdr_image", texture_tag="hdr_texture")
        else:
            dpg.add_image("hdr_texture", parent=self.image_group, tag="hdr_image")

    def save_image(self):
        if self.ldr_image is None:
            return
        first_dir = os.path.dirname(self.file_paths[0])
        save_path = os.path.join(first_dir, "hdr_result.jpg")
        cv2.imwrite(save_path, self.ldr_image)
        dpg.show_logger()
        dpg.log_info(f"HDR image saved to {save_path}")


def main():
    dpg.create_context()
    gui = AEBGui()
    with dpg.file_dialog(directory_selector=False, show=False, callback=gui._file_selected, id="file_dialog", multiselect=True):
        dpg.add_file_extension(".jpg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".jpeg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".png", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tif", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tiff", color=(255, 255, 255, 255))
    dpg.create_viewport(title="AEB Compositor", width=800, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(gui.image_group, True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
