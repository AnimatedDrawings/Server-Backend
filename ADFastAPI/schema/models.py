from pydantic import BaseModel
from fastapi import UploadFile

class AD_schema(BaseModel):
    id: int
    cropped_image_url: str | None = None

    class Config:
        orm_mode = True