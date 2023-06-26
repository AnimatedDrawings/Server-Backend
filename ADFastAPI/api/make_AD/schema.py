from pydantic import BaseModel

class AD(BaseModel):
    id: int
    name: str | None = None

    class Config:
        orm_mode = True
