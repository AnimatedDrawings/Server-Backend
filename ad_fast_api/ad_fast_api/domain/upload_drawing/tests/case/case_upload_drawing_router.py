import shutil
from ad_fast_api.domain.upload_drawing.sources.features import detect_character
from ad_fast_api.domain.upload_drawing.sources.upload_drawing_router import (
    upload_drawing,
)
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.workspace.sources import conf_workspace as cw
from fastapi import UploadFile
from io import BytesIO


def get_sample1_upload_image():
    sample1_image_path = rf.EXAMPLE1_DIR_PATH / rf.UPLOAD_IMAGE_FILE_NAME

    if not sample1_image_path.exists():
        raise FileNotFoundError(
            f"locust_upload_drawing.py, upload image file not found: {sample1_image_path}"
        )

    with open(sample1_image_path, "rb") as f:
        return f.read()


def remove_workspace_files(ad_id: str):
    tmp_base_path = cw.get_base_path(ad_id=ad_id)
    shutil.rmtree(tmp_base_path)


def create_mock_upload_file():
    image_bytes = get_sample1_upload_image()
    file_stream = BytesIO(image_bytes)

    mock_file = UploadFile(
        file=file_stream,
        filename=rf.UPLOAD_IMAGE_FILE_NAME,
    )
    return mock_file


async def case_upload_drawing_router():
    file = create_mock_upload_file()

    response = await upload_drawing(
        file=file,
    )

    return response


if __name__ == "__main__":
    import asyncio
    from unittest.mock import patch
    from ad_fast_api.domain.upload_drawing.sources.features import detect_character

    with patch.object(
        detect_character,
        "DETECT_CHARACTER_TORCHSERVE_URL",
        new="http://localhost:8080/predictions/drawn_humanoid_detector",
    ):
        response = asyncio.run(case_upload_drawing_router())

    print(response)
    remove_workspace_files(ad_id=response.ad_id)
