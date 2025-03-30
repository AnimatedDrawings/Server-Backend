from fastapi import UploadFile
from ad_fast_api.domain.upload_drawing.sources.errors import (
    upload_drawing_400_status as ud4s,
)
from ad_fast_api.workspace.sources.conf_workspace import (
    get_base_path,
    BOUNDING_BOX_FILE_NAME,
    ORIGIN_IMAGE_NAME,
)
from ad_fast_api.domain.upload_drawing.sources.features.configure_work_dir import (
    make_ad_id,
    create_base_dir,
)
from ad_fast_api.domain.upload_drawing.sources.features.detect_character import (
    detect_character_from_origin_async,
    calculate_bounding_box,
    sort_detection_results,
    check_detection_results,
    check_image_is_rgb,
    resize_image,
)
from ad_fast_api.snippets.sources.save_image import save_image_async, get_file_bytes
from ad_fast_api.snippets.sources.save_dict import dict_to_file
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.snippets.sources.ad_logger import setup_logger


async def save_origin_image_async(file: UploadFile) -> str:
    file_bytes = get_file_bytes(file=file)
    if not file_bytes:
        raise ud4s.UPLOADED_FILE_EMPTY_OR_INVALID

    ad_id = make_ad_id()
    base_path = create_base_dir(ad_id=ad_id)
    await save_image_async(
        image_bytes=file_bytes,
        image_name=ORIGIN_IMAGE_NAME,
        base_path=base_path,
    )
    return ad_id


async def detect_character(ad_id: str) -> BoundingBox:
    base_path = get_base_path(ad_id=ad_id)
    logger = setup_logger(ad_id=ad_id)

    try:
        img = check_image_is_rgb(
            base_path=base_path,
            logger=logger,
        )
    except Exception as e:
        raise ud4s.IMAGE_IS_NOT_RGB

    img = resize_image(img=img)

    resp = await detect_character_from_origin_async(
        img=img,
        logger=logger,
    )

    detection_results = check_detection_results(
        resp=resp,
        logger=logger,
    )
    sort_detection_results(
        detection_results=detection_results,
        logger=logger,
    )

    bounding_box = calculate_bounding_box(
        detection_results=detection_results,
        logger=logger,
    )

    to_save_dict = bounding_box.model_dump(mode="json")
    file_path = base_path.joinpath(BOUNDING_BOX_FILE_NAME)
    dict_to_file(
        to_save_dict=to_save_dict,
        file_path=file_path,
    )

    return bounding_box
