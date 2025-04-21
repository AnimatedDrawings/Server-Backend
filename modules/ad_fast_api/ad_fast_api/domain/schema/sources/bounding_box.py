from pydantic import BaseModel
from typing import Self


class BoundingBox(BaseModel):
    top: int
    bottom: int
    left: int
    right: int

    @classmethod
    def mock(cls) -> Self:
        return cls(
            top=10,
            bottom=20,
            left=30,
            right=40,
        )
