from pathlib import Path


REQUEST_FILES_DIR_PATH = Path(__file__).parent.parent.joinpath("request_files")
EXAMPLE1_AD_ID = "example1"
EXAMPLE1_DIR_PATH = REQUEST_FILES_DIR_PATH.joinpath(EXAMPLE1_AD_ID)

GARLIC_AD_ID = "garlic"
GARLIC_DIR_PATH = REQUEST_FILES_DIR_PATH.joinpath(GARLIC_AD_ID)

BOUNDING_BOX_FILE_NAME = "bounding_box.yaml"
UPLOAD_IMAGE_FILE_NAME = "upload_image.png"
CROPPED_IMAGE_FILE_NAME = "cropped_image.png"
CUTOUT_CHARACTER_IMAGE_FILE_NAME = "cutout_character_image.png"
