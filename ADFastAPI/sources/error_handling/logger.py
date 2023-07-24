import logging

uvicorn_access = logging.getLogger("uvicorn_access")
uvicorn_access.disabled = True

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.getLevelName(logging.DEBUG))
