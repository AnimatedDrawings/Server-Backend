from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
from pydantic import BaseModel

from sources.schema import DefaultResponse
import logging

router = APIRouter(
    prefix='/api/configure_animation',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

ad_animation_set = ['dab', 'zombie']

class ADAnimation(BaseModel):
    name: str

@router.post('/add/{ad_id}')
async def add(ad_id: str, ad_animation: ADAnimation):
    default_response = DefaultResponse()
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    log_file_path = base_path.joinpath('logs/log.txt')
    logging.basicConfig(filename = log_file_path.as_posix(), level = logging.DEBUG)

    ad_animation_dict = ad_animation.dict() 
    ad_animation_name = ad_animation_dict['name']
    if ad_animation_name not in ad_animation_set:
        msg = 'no name in ad animation set'
        default_response.fail(message=msg)
        return default_response.dict()
    
    params = { 
        'ad_id' : ad_id,
        'ad_animation': ad_animation_name
    }

    ad_url = AD_BASEURL + 'add_animation'
    timeout = httpx.Timeout(60)
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params, timeout = timeout)
        response_dict = response.json()
        is_success = response_dict['is_success']
        if is_success:
            default_response.success()
            return default_response.dict()
        else:
            msg = response_dict['msg']
            logging.critical(msg=msg)
            default_response.fail(message = msg)
            return default_response.dict()


@router.post('/download_video/{ad_id}')
def download_video(ad_id: str, ad_animation: ADAnimation):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    ad_animation_dict = ad_animation.dict() 
    ad_animation_name = ad_animation_dict['name']
    video_file_path = base_path.joinpath(f'video/{ad_animation_name}.gif')
    return FileResponse(video_file_path.as_posix(), media_type = 'image/gif')
        