from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
from pydantic import BaseModel
import yaml

router = APIRouter(
    prefix='/api/make_ad/step2',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

class BoundingBox(BaseModel):
    top: int
    bottom: int
    left: int
    right: int

@router.post('/find_the_character/{ad_id}')
async def find_the_character(ad_id: str, bounding_box: BoundingBox):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    bounding_box_path = base_path.joinpath('bounding_box.yaml')
    bounding_box_path.unlink(missing_ok=True)
    bounding_box_location = bounding_box_path.as_posix()
    bounding_box_dict = bounding_box.dict()

    with open(bounding_box_location, 'w') as f:
        yaml.dump(bounding_box_dict, f)
    
    ad_url = AD_BASEURL + 'find_the_character'
    params = { 'ad_id' : ad_id }
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params)
        try:
            return response.json()
        except:
            return response.text

@router.get('/download_mask_image/{ad_id}')
def download_mask_image(ad_id: str):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    mask_image_path = base_path.joinpath('masked_img.png')
    return FileResponse(mask_image_path.as_posix())