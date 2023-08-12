from fastapi import APIRouter
from pathlib import Path
import yaml
from pydantic import BaseModel
from typing import List
from sources.schema import DefaultResponse

router = APIRouter(
    prefix='/api/make_ad/step4',
)

FILES_IN_DOCKER = Path('/mycode/files/')

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
    with open(char_cfg_path.as_posix(), 'w') as f:
        yaml.dump(joints.dict(), f)

    default_response = DefaultResponse()
    default_response.success()
    return default_response.dict()
        