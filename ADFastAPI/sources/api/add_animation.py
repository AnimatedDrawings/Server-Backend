from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
import yaml
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/add_animation',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

@router.post('/{ad_id}')
async def find_character_joints(ad_id: str):
    ad_url = AD_BASEURL + 'add_animation'
    params = { 'ad_id' : ad_id }

    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params, timeout = timeout)
        try:
            return response.json()
        except:
            return response.text
        