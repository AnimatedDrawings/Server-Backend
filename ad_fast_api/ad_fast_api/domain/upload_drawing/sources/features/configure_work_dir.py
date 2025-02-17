import aiofiles
from uuid import uuid4
from datetime import datetime
from datetime import datetime
from ad_fast_api.workspace.sources.work_dir import get_base_path
from pathlib import Path
from fastapi import UploadFile
from typing import Optional


ORIGIN_IMAGE_NAME = "image.png"


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
    base_path: Optional[Path] = None,
) -> Path:
    base_path = base_path or get_base_path(ad_id=ad_id)
    base_path.mkdir()
    return base_path


def get_file_bytes(file: UploadFile) -> bytes:
    return file.file.read()


async def save_origin_image(
    base_path: Path,
    file_bytes: bytes,
):
    origin_image_path = base_path.joinpath(ORIGIN_IMAGE_NAME)
    async with aiofiles.open(origin_image_path.as_posix(), mode="wb") as f:
        await f.write(file_bytes)


async def save_image(file: UploadFile) -> str:
    ad_id = make_ad_id()
    base_path = create_base_dir(ad_id=ad_id)
    file_bytes = get_file_bytes(file=file)
    await save_origin_image(base_path=base_path, file_bytes=file_bytes)
    return ad_id
