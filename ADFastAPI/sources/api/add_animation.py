from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/add_animation',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

class ADAnimation(BaseModel):
    name: str

@router.post('/{ad_id}')
async def add_animation(ad_id: str, ad_animation: ADAnimation):
    ad_url = AD_BASEURL + 'add_animation'
    ad_animation_dict = ad_animation.dict() 
    ad_animation_name = ad_animation_dict['name']
    params = { 
        'ad_id' : ad_id,
        'ad_animation_name': ad_animation_name
    }

    timeout = httpx.Timeout(60)
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params, timeout = timeout)
        try:
            return response.json()
        except:
            return response.text
        