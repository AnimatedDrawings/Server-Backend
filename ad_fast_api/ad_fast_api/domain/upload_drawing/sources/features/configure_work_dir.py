import aiofiles
from uuid import uuid4
from datetime import datetime
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional
from ad_fast_api.domain.upload_drawing.sources.helpers import (
    upload_drawing_http_exception as ude,
)
from ad_fast_api.workspace.sources import conf_workspace as cw


def make_ad_id(
    now: Optional[datetime] = None,
    uuid: Optional[str] = None,
) -> str:
    now = now or datetime.now()
    uuid = uuid or uuid4().hex
    ad_id = now.strftime("%Y%m%d%H%M%S") + "_" + uuid
    return ad_id


def create_base_dir(
    ad_id: str,
    files_path: Optional[Path] = None,
) -> Path:
    base_path = get_base_path(
        ad_id=ad_id,
        files_path=files_path,
    )
    base_path.mkdir()
    return base_path


def get_file_bytes(file: UploadFile) -> bytes:
    return file.file.read()


async def save_origin_image_async(
    base_path: Path,
    file_bytes: bytes,
):
    origin_image_path = base_path.joinpath(cw.ORIGIN_IMAGE_NAME)
    async with aiofiles.open(origin_image_path.as_posix(), "wb") as f:
        await f.write(file_bytes)


async def save_image(file: UploadFile) -> str:
    file_bytes = get_file_bytes(file=file)
    if not file_bytes:
        raise HTTPException(
            status_code=ude.UPLOADED_FILE_EMPTY_OR_INVALID.status_code(),
            detail=ude.UPLOADED_FILE_EMPTY_OR_INVALID.detail(),
        )

    ad_id = make_ad_id()
    base_path = create_base_dir(ad_id=ad_id)
    await save_origin_image_async(base_path=base_path, file_bytes=file_bytes)
    return ad_id
