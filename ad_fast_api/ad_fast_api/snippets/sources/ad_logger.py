import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from ad_fast_api.workspace.sources.conf_workspace import get_base_path

LOG_FILE_NAME = "log.txt"


def setup_logger(
    ad_id: str,
    base_path: Optional[Path] = None,
    level=logging.INFO,
    max_size=5 * 1024 * 1024,
    backup_count=5,
    log_file_name: Optional[str] = None,
) -> Logger:
    base_path = base_path or get_base_path(ad_id=ad_id)
    log_file = base_path.joinpath(log_file_name or LOG_FILE_NAME)
    log_file.touch(exist_ok=True)

    # 로거 생성
    logger = logging.getLogger(ad_id)
    logger.setLevel(level)

    # 로그 포맷 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # RotatingFileHandler 설정
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
    )
    file_handler.setFormatter(formatter)

    # 스트림 핸들러 설정 (콘솔 출력용)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # 로거에 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# 사용 예시
# if __name__ == "__main__":
# 로거 설정
# logger = setup_logger("my_app", "logs/app.log", level=logging.DEBUG)

# 로그 메시지 작성
# logger.debug("디버그 메시지")
# logger.info("정보 메시지")
# logger.warning("경고 메시지")
# logger.error("에러 메시지")
# logger.critical("심각한 에러 메시지")
