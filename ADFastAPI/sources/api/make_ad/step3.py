from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import httpx
import yaml

router = APIRouter(
    prefix='/api/make_ad/step3',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

@router.post('/separate_character/{ad_id}')
async def separate_character(ad_id: str, file: UploadFile = File(...)):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    separated_img_path = base_path.joinpath('separated_img.png')

    with open(separated_img_path.as_posix(), 'wb') as image:
        image.write(file.file.read())
        image.close()
    
    ad_url = AD_BASEURL + 'separate_character'
    params = { 'ad_id' : ad_id }
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params)
        try:
            _ = response.json()
            char_cfg_path = base_path.joinpath('char_cfg.yaml')
            with open(char_cfg_path.as_posix(), encoding='UTF-8') as char_cfg_yaml:
                char_cfg_dict = yaml.load(char_cfg_yaml, Loader=yaml.FullLoader)
                return char_cfg_dict
        except:
            return response.text
        