from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.domain.cutout_character.sources.cutout_character_router import (
    cutout_character,
)
from io import BytesIO
from fastapi import UploadFile


def get_sample1_cutout_character_image():
    sample1_cutout_character_image_path = (
        rf.EXAMPLE1_DIR_PATH / rf.CUTOUT_CHARACTER_IMAGE_FILE_NAME
    )

    if not sample1_cutout_character_image_path.exists():
        raise FileNotFoundError(
            f"locust_upload_drawing.py, upload image file not found: {sample1_cutout_character_image_path}"
        )

    with open(sample1_cutout_character_image_path, "rb") as f:
        return f.read()


def create_mock_upload_file():
    image_bytes = get_sample1_cutout_character_image()
    file_stream = BytesIO(image_bytes)

    mock_file = UploadFile(
        file=file_stream,
        filename=rf.UPLOAD_IMAGE_FILE_NAME,
    )
    return mock_file


async def case_cutout_character_router():
    ad_id = rf.EXAMPLE1_AD_ID
    file = create_mock_upload_file()
    response = await cutout_character(
        ad_id=ad_id,
        file=file,
    )
    return response


if __name__ == "__main__":
    import asyncio
    from unittest.mock import patch
    from ad_fast_api.domain.cutout_character.sources.features import configure_skeleton

    with patch.object(
        configure_skeleton,
        "GET_SKELETON_TORCHSERVE_URL",
        new="http://localhost:8080/predictions/drawn_humanoid_pose_estimator",
    ):
        response = asyncio.run(
            case_cutout_character_router(),
        )

    print(response)
