FROM python:3.13.2

ARG ROOT_DIR
ARG INTERNAL_PORT
ARG ANIMATED_DRAWINGS_WORKSPACE_DIR

ENV ROOT_DIR=${ROOT_DIR}
ENV INTERNAL_PORT=${INTERNAL_PORT}
ENV ANIMATED_DRAWINGS_WORKSPACE_DIR=${ANIMATED_DRAWINGS_WORKSPACE_DIR}
ENV PYTHONPATH="${PYTHONPATH}:/${ROOT_DIR}/"

# Install only the necessary dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치, 가상환경 생성하지 않도록 설정
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

WORKDIR /${ROOT_DIR}

# ad_fast_api 디렉토리 전체 복사 (패키지 구조 유지)
COPY ./ad_fast_api ./ad_fast_api
COPY ./pyproject.toml .
COPY ./README.md .

# Poetry를 사용하여 의존성 및 로컬 패키지 설치
RUN poetry install --no-interaction --no-ansi

# 애플리케이션 실행
CMD ["python", "ad_fast_api/main.py"]