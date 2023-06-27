from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.models import AD_model
from schema.models import AD_schema
from database.database import get_db

from path import Path


router = APIRouter(
    prefix='/api/make_AD',
)

@router.get('/list', response_model=list[AD_schema])
def AD_list(db: Session = Depends(get_db)):
    result = db.query(AD_model).all()
    return result

FILES_DIR = Path('/mycode/files/')

@router.get('/files/cropped_images/{name_file}')
def get_cropped_image(name_file: str):
    file_url = ''.join([FILES_DIR, '/cropped_images/', name_file])
    isfile = Path(file_url).isfile()
    return FileResponse(file_url) if isfile else 'Nofile'