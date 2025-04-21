from pydantic import BaseModel
from ad_fast_api.domain.schema.sources.schemas import Joints


class CutoutCharacterResponse(BaseModel):
    char_cfg: Joints
