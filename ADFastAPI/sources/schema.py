from pydantic import BaseModel

class DefaultResponse(BaseModel):
    is_success: bool = True
    msg: str = ''
    response: BaseModel | None = None

class BoundingBox(BaseModel):
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0