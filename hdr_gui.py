import os
import cv2
import numpy as np
import dearpygui.dearpygui as dpg
import logging

try:  # support running as part of a package or as a script
    from .find_and_merge_aeb import (
        load_images,
        create_hdr,
        group_images_by_hash,
        get_exposure_times_from_list,
    )
    from .hdr_utils import get_medium_exposure_image, tonemap_mantiuk
except ImportError:  # pragma: no cover - fallback for direct execution
    from find_and_merge_aeb import (
        load_images,
        create_hdr,
        group_images_by_hash,
        get_exposure_times_from_list,
    )
    from hdr_utils import get_medium_exposure_image, tonemap_mantiuk

class HDRGui:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_paths = []
        self.groups = []
        self.group_labels = []
        self.hdr_image = None
        self.ldr_image = None

        with dpg.window(label="HDR Compositor", width=800, height=600):
            dpg.add_button(label="Select Images for One HDR", callback=self.select_files_single)
            dpg.add_button(label="Batch HDR Detect", callback=self.select_files_batch)
            self.listbox = dpg.add_listbox(items=[], num_items=5, width=780)
            dpg.add_button(label="Create HDR", callback=self.create_hdr_image)
            self.save_btn = dpg.add_button(label="Save Result", callback=self.save_image, enabled=False)
            with dpg.group() as self.image_group:
                dpg.add_text("HDR preview will appear here")

    def select_files_single(self):
        self.logger.info("Opening file dialog for single HDR selection")
        dpg.show_item("file_dialog_single")

    def select_files_batch(self):
        self.logger.info("Opening file dialog for batch detection")
        dpg.show_item("file_dialog_batch")

    def _files_selected_single(self, sender, app_data):
        self.file_paths = list(app_data["selections"].values())
        self.logger.info("Selected %d images for single HDR", len(self.file_paths))
        self.groups = []
        dpg.configure_item(self.listbox, items=self.file_paths)
        dpg.configure_item(self.save_btn, enabled=False)
        dpg.delete_item(self.image_group, children_only=True)
        dpg.add_text("HDR preview will appear here", parent=self.image_group)

    def _files_selected_batch(self, sender, app_data):
        self.file_paths = list(app_data["selections"].values())
        self.logger.info("Batch selection received %d files", len(self.file_paths))
        self.groups = group_images_by_hash(
            self.file_paths,
            hash_percent_threshold=10.0,
        )
        self.logger.info("Detected %d groups", len(self.groups))
        for i, g in enumerate(self.groups, 1):
            self.logger.info("Group %d: %s", i, g)
        self.group_labels = [f"Group {i+1} ({len(g)} images)" for i, g in enumerate(self.groups)]
        dpg.configure_item(self.listbox, items=self.group_labels)
        dpg.configure_item(self.save_btn, enabled=False)
        dpg.delete_item(self.image_group, children_only=True)
        dpg.add_text("HDR preview will appear here", parent=self.image_group)

    def create_hdr_image(self):
        if self.groups:
            selected_label = dpg.get_value(self.listbox)
            if not selected_label:
                dpg.show_logger()
                dpg.log_warning("Select a group to process.")
                return
            index = self.group_labels.index(selected_label)
            image_paths = self.groups[index]
            self.logger.info("Processing group %d with %d images", index + 1, len(image_paths))
        else:
            image_paths = self.file_paths
            self.logger.info("Processing %d images for single HDR", len(image_paths))

        image_paths, exposure_times = get_exposure_times_from_list(image_paths)
        if len(image_paths) < 3:
            dpg.show_logger()
            dpg.log_warning("Selected images do not contain at least three usable exposures.")
            return

        images = load_images(image_paths)
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
        self.logger.info("HDR image saved to %s", save_path)


def main():
    logging.basicConfig(level=logging.INFO)
    dpg.create_context()
    gui = HDRGui()
    with dpg.file_dialog(directory_selector=False, show=False, callback=gui._files_selected_single, id="file_dialog_single", multiselect=True):
        dpg.add_file_extension(".jpg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".jpeg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".png", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tif", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tiff", color=(255, 255, 255, 255))
    with dpg.file_dialog(directory_selector=False, show=False, callback=gui._files_selected_batch, id="file_dialog_batch", multiselect=True):
        dpg.add_file_extension(".jpg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".jpeg", color=(255, 255, 255, 255))
        dpg.add_file_extension(".png", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tif", color=(255, 255, 255, 255))
        dpg.add_file_extension(".tiff", color=(255, 255, 255, 255))
    dpg.create_viewport(title="HDR Compositor", width=800, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(gui.image_group, True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
