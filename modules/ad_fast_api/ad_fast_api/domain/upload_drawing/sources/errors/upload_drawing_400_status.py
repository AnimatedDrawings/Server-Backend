from fastapi import HTTPException


UPLOADED_FILE_EMPTY_OR_INVALID = HTTPException(
    status_code=400,
    detail="Uploaded file is empty or invalid.",
)


IMAGE_IS_NOT_RGB = HTTPException(
    status_code=401,
    detail="Image is not RGB.",
)
