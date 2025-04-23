from fastapi import HTTPException


class VideoFileNotExistError(Exception):
    pass


NOT_FOUND_ANIMATION_FILE = HTTPException(
    status_code=500,
    detail="애니메이션 파일을 찾을 수 없습니다.",
)
