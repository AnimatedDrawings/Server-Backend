from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import httpx
import yaml
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix='/api/make_ad/step4',
)

FILES_IN_DOCKER = Path('/mycode/files/')
AD_BASEURL = 'http://animated_drawings:8001/'

class Skeleton(BaseModel):
    name: str
    parent: str | None = None
    loc: list

class Joints(BaseModel):
    width: int
    height: int
    skeleton: List[Skeleton]

@router.post('/find_character_joints/{ad_id}')
async def find_character_joints(ad_id: str, joints: Joints):
    base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
    char_cfg_path = base_path.joinpath('char_cfg.yaml')
    joints_dict = joints.dict()
    with open(char_cfg_path.as_posix(), 'w') as f:
        yaml.dump(joints_dict, f)

    return { 'ad_id' : ad_id }
        