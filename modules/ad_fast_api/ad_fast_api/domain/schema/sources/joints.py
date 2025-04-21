from pydantic import BaseModel
from typing import List


class Skeleton(BaseModel):
    name: str
    parent: str | None = None
    loc: list

    @classmethod
    def mock(cls):
        return cls(
            name="dummy_name",
            parent="dummy_parent",
            loc=[0, 0],
        )


class Joints(BaseModel):
    width: int
    height: int
    skeleton: List[Skeleton]

    @classmethod
    def mock(cls):
        return cls(
            width=100,
            height=100,
            skeleton=[Skeleton.mock()],
        )
