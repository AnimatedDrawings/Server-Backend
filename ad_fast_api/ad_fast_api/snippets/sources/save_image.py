import aiofiles
from pathlib import Path
from fastapi import UploadFile


def get_file_bytes(file: UploadFile) -> bytes:
    return file.file.read()


async def save_image_async(
    image_bytes: bytes,
    image_name: str,
    base_path: Path,
):
    image_path = base_path.joinpath(image_name)
    async with aiofiles.open(image_path.as_posix(), "wb") as f:
        await f.write(image_bytes)
