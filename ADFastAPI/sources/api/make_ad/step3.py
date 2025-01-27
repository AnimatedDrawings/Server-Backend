from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import httpx
import yaml

import logging
from sources.schema import DefaultResponse
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/make_ad/step3',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

class SeparateCharacterResponse(BaseModel):
    char_cfg: dict

@router.post('/separate_character/{ad_id}')
async def separate_character(ad_id: str, file: UploadFile = File(...)):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)

    # resave masked_img.png
    masked_img_path = base_path.joinpath('masked_img.png')
    with open(masked_img_path.as_posix(), 'wb') as image:
        image.write(file.file.read())
        image.close()

    log_file_path = base_path.joinpath('logs/log.txt')
    logging.basicConfig(filename = log_file_path.as_posix(), level = logging.DEBUG)
    
    ad_url = AD_BASEURL + 'separate_character'
    params = { 'ad_id' : ad_id }
    default_response = DefaultResponse()

    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url, params = params)
        response_dict = response.json()
        is_success = response_dict['is_success']
        if is_success:
            char_cfg_path = base_path.joinpath('char_cfg.yaml')
            with open(char_cfg_path.as_posix(), encoding='UTF-8') as char_cfg_yaml:
                char_cfg_dict = yaml.load(char_cfg_yaml, Loader=yaml.FullLoader)
                my_response = SeparateCharacterResponse(char_cfg=char_cfg_dict)
                default_response.success(response = my_response)
                return default_response.dict()
        else:
            msg = response_dict['msg']
            logging.critical(msg=msg)
            default_response.fail(message = msg)
            return default_response.dict()
        