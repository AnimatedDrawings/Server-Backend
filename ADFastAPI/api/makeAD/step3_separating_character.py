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

@router.post('/upload_masked_image')
def upload_image(file: UploadFile = File(...)):
    saved_file_name = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.png'
    file_location = MASKED_IMAGES + saved_file_name
    file_url = FILES_IN_LOCAL + 'masked_images/' + saved_file_name

    with open(file_location, 'wb') as image:
        image.write(file.file.read())
        image.close()

    return saved_file_name

@router.get('/files/masked_images/{name_file}')
def get_masked_image(name_file: str):
    file_url = ''.join([MASKED_IMAGES, name_file])
    isfile = Path(file_url).isfile()
    return FileResponse(file_url) if isfile else 'Nofile'