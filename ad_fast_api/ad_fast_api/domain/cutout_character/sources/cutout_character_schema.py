from pydantic import BaseModel


class CutoutCharacterResponse(BaseModel):
    char_cfg: dict
