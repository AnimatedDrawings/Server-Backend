from pydantic import BaseModel


class UploadDrawingResponse(BaseModel):
    ad_id: str
    bounding_box: dict
