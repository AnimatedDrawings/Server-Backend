from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import httpx

router = APIRouter(
    prefix='/api/make_ad/step1',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

@router.post('/upload_a_drawing')
async def upload_a_drawing(file: UploadFile = File(...)):
    ad_id = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S")
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    base_path.mkdir()
    original_image_path = base_path.joinpath('image.png')

    with open(original_image_path.as_posix(), 'wb') as image:
        image.write(file.file.read())
        image.close()

    ad_url = AD_BASEURL + 'upload_a_drawing'
    params = { 'ad_id' : ad_id }
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params)
        try:
            bounding_box_dict = response.json()
            result = { 'ad_id' : ad_id, 'bounding_box' : bounding_box_dict }
            return result
        except:
            return response.text

