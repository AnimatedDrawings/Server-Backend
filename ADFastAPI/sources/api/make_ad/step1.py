from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import httpx
import yaml
import logging
from sources.schema import DefaultResponse, BoundingBox
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/make_ad/step1',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

class UploadADrawingResponse(BaseModel):
    ad_id: str
    bounding_box: BoundingBox

@router.post('/upload_a_drawing')
async def upload_a_drawing(file: UploadFile = File(...)):
    ad_id = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S")
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    base_path.mkdir()
    log_path = base_path.joinpath('logs')
    log_path.mkdir()
    log_file_path = log_path.joinpath('log.txt')
    logging.basicConfig(filename = log_file_path.as_posix(), level = logging.DEBUG)

    original_image_path = base_path.joinpath('image.png')

    with open(original_image_path.as_posix(), 'wb') as image:
        image.write(file.file.read())
        image.close()

    ad_url = AD_BASEURL + 'upload_a_drawing'
    params = { 'ad_id' : ad_id }
    my_response = UploadADrawingResponse(ad_id=ad_id, bounding_box=BoundingBox())

    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params)
        response_dict = response.json()
        is_success = response_dict['is_success']
        if is_success:
            bounding_box_path = base_path.joinpath('bounding_box.yaml')
            with open(bounding_box_path.as_posix(), encoding='UTF-8') as bounding_box_yaml:
                bounding_box_dict = yaml.load(bounding_box_yaml, Loader=yaml.FullLoader)
                bouding_box = BoundingBox.parse_obj(bounding_box_dict)
                my_response.bounding_box = bouding_box
                return DefaultResponse(response = my_response).dict()
        else:
            msg = response_dict['msg']
            return DefaultResponse(is_success=False, msg=msg, response=my_response).dict()

