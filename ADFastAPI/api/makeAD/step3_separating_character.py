from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.models import AD_model
from schema.models import AD_schema
from database.database import get_db

from path import Path

from fastapi import UploadFile, File
from datetime import datetime
from uuid import uuid4

import httpx

router = APIRouter(
    prefix='/api/makeAD/step3',
)

# @router.get('/list', response_model=list[AD_schema])
# def AD_list(db: Session = Depends(get_db)):
#     result = db.query(AD_model).all()
#     return result

FILES_IN_LOCAL = '/mnt/sdb1/ad_db/files/'
FILES_IN_DOCKER = Path('/mycode/files/')
MASKED_IMAGES = ''.join([FILES_IN_DOCKER, 'masked_images/'])
ad_base_url = 'http://animated_drawings:8001'


'''
1. [Fast] masked file 로컬 저장
2. [Fast] masked file_url postgres ad_db에 저장
3. [AD]
    1. api_image_to_annotations/?file_url={},
    2. file_url로 annotation file(char_cfg.yaml) 생성
    3. annotation file url return
    [Fast]
    1. annotation file url postgres ad_db에 저장
    2. annotation file url -> char_cfg.yaml -> Json 변환후 리턴

시뮬로 간단히 json받는거까지
'''

@router.post('/upload_masked_image')
async def upload_image(file: UploadFile = File(...)):
    saved_file_name = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.png'
    file_location = MASKED_IMAGES + saved_file_name
    file_url = FILES_IN_LOCAL + 'masked_images/' + saved_file_name

    with open(file_location, 'wb') as image:
        image.write(file.file.read())
        image.close()
    
    
    
    tmp_url = ad_base_url + '/image_to_annotations'
    params = {'file_url' : file_url}
    async with httpx.AsyncClient() as client:
        response = await client.get(url = tmp_url, params = params)
        return response.text
    

@router.get('/files/masked_images/{name_file}')
def get_masked_image(name_file: str):
    file_url = ''.join([MASKED_IMAGES, name_file])
    isfile = Path(file_url).isfile()
    return FileResponse(file_url) if isfile else 'Nofile'