from fastapi import HTTPException


CUTOUT_CHARACTER_FILE_EMPTY_OR_INVALID = HTTPException(
    status_code=400,
    detail="cutout character file is empty or invalid.",
)
