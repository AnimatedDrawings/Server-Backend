from fastapi import APIRouter


router = APIRouter()


@router.get("/find_character")
async def find_character(
    ad_id: str,
):
    pass
