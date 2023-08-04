from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/configure_animation',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

ad_animation_name_set = ['dab', 'zombie']

class ADAnimation(BaseModel):
    ad_id: str
    name: str

@router.post('/add/{ad_id}')
async def add(ad_id: str, ad_animation: ADAnimation):
    ad_animation_dict = ad_animation.dict() 
    ad_animation_name = ad_animation_dict['name']
    if ad_animation_name not in ad_animation_name_set:
        return 'no ad animation name'
    params = { 
        'ad_id' : ad_id,
        'ad_animation_name': ad_animation_name
    }

    ad_url = AD_BASEURL + 'add_animation'
    timeout = httpx.Timeout(60)
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params, timeout = timeout)
        try:
            return response.json()
        except:
            return response.text
        
@router.post('/download_video/{ad_id}')
def download_video(ad_id: str, ad_animation: ADAnimation):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    ad_animation_dict = ad_animation.dict() 
    ad_animation_name = ad_animation_dict['name']
    video_file_path = base_path.joinpath(f'video/{ad_animation_name}.gif')
    if not video_file_path.exists():
        return 'no file'
    return FileResponse(video_file_path.as_posix(), media_type = 'image/gif')
        