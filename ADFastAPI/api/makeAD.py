from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.models import AD_model
from schema.models import AD_schema
from database.database import get_db

from path import Path

from fastapi import UploadFile, File
from datetime import datetime

router = APIRouter(
    prefix='/api/makeAD',
)

# @router.get('/list', response_model=list[AD_schema])
# def AD_list(db: Session = Depends(get_db)):
#     result = db.query(AD_model).all()
#     return result

FILES_IN_LOCAL = '/mnt/sdb1/ad_db/files/'
FILES_IN_DOCKER = Path('/mycode/files/')
CROPPED_IMAGES = ''.join([FILES_IN_DOCKER, 'cropped_images/'])

@router.post('/upload_image')
async def upload_image(file: UploadFile = File(...)):
    saved_file_name = datetime.now().strftime("%Y%m%d%H%M%S")
    file_location = CROPPED_IMAGES + saved_file_name
    file_url = FILES_IN_LOCAL + 'cropped_images/' + saved_file_name

    with open(file_location, 'wb') as image:
        content = await file.read()
        image.write(content)
        image.close()

    return file_url

@router.get('/files/cropped_images/{name_file}')
def get_cropped_image(name_file: str):
    file_url = ''.join([CROPPED_IMAGES, name_file])
    isfile = Path(file_url).isfile()
    return FileResponse(file_url) if isfile else 'Nofile'