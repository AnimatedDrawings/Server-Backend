from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from path import Path

from datetime import datetime
from uuid import uuid4

import httpx
import yaml

router = APIRouter(
    prefix='/api/make_ad/step1',
)

FILES_IN_DOCKER = Path('/mycode/files/')

@router.post('/upload_drawing')
def upload_drawing(file: UploadFile = File(...)):
    extension = '.png'
    id = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S")
    base_path: Path = FILES_IN_DOCKER.joinpath(id)
    base_path.mkdir()
    img_str = 'original_image'
    original_image_path: Path = base_path.joinpath(img_str)
    original_image_path.mkdir()

    saved_file_name = img_str + extension
    file_location = str(original_image_path.joinpath(saved_file_name))

    with open(file_location, 'wb') as image:
        image.write(file.file.read())
        image.close()
        return id