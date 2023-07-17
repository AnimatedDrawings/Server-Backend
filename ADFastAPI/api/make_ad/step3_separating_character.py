from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from path import Path

from datetime import datetime
from uuid import uuid4

from database.database import get_db
from database.models import AD_model

import httpx
import yaml

router = APIRouter(
    prefix='/api/makeAD/step3',
)

FILES_IN_DOCKER = Path('/mycode/files/')
MASKED_IMAGES = ''.join([FILES_IN_DOCKER, 'masked_images/'])
AD_BASEURL = 'http://animated_drawings:8001'


'''
1. [Fast] masked file 로컬 저장
2. [Fast] masked file_location postgres ad_db에 저장
3. [AD]
    1. image_to_annotations/
    2. masked_file_url로 annotation file(char_cfg.yaml) 생성
    3. annotation file url return
    [Fast]
    1. annotation file url postgres ad_db에 저장
    2. annotation file url -> char_cfg.yaml -> Json 변환후 리턴
'''
@router.post('/upload_masked_image')
async def upload_image(file: UploadFile = File(...)):
    extension = '.png'
    file_name = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S")
    saved_file_name = file_name + extension
    file_location = MASKED_IMAGES + saved_file_name

    with open(file_location, 'wb') as image:
        image.write(file.file.read())
        image.close()

    id = file_name
    db_data = AD_model()
    db_data.id = id
    db_data.masked_image_url = file_location
    with get_db() as db:
        db.add(db_data)
        db.commit()
    
    tmp_url = AD_BASEURL + '/image_to_annotations'
    params = {
        'path' : MASKED_IMAGES,
        'file_name' : file_name,
        'extension' : extension
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url = tmp_url, params = params)
        annotation_info_dict = response.json()
        annotation_path = annotation_info_dict['path']
        joint_filename = annotation_info_dict['joint_filename']

        annotation_fileloaction = annotation_path + joint_filename
        with get_db() as db:
            fetched_data = db.query(AD_model).get(id)
            fetched_data.annotations_url = annotation_fileloaction
            db.commit()
        
        with open(annotation_fileloaction, encoding='UTF-8') as char_cfg_yaml:
            char_cfg_dict = yaml.load(char_cfg_yaml, Loader=yaml.FullLoader)
            return char_cfg_dict
    

@router.get('/files/masked_images/{name_file}')
def get_masked_image(name_file: str):
    file_location = ''.join([MASKED_IMAGES, name_file])
    isfile = Path(file_location).isfile()
    return FileResponse(file_location) if isfile else 'Nofile'