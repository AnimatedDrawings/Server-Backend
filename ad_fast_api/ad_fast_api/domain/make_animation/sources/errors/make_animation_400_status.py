from fastapi import HTTPException


INVALID_ANIMATION = HTTPException(
    status_code=400,
    detail="Invalid animation",
)
