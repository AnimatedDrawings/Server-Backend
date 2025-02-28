FROM python:3.13.2

ARG WORK_DIR
ARG INTERNAL_PORT
ARG ANIMATED_DRAWINGS_WORKSPACE_DIR

ENV INTERNAL_PORT=${INTERNAL_PORT}
ENV ANIMATED_DRAWINGS_WORKSPACE_DIR=${ANIMATED_DRAWINGS_WORKSPACE_DIR}

# Install only the necessary dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치, 가상환경 생성하지 않도록 설정
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

WORKDIR /${WORK_DIR}/ad_fast_api

# 먼저 pyproject.toml과 poetry.lock을 복사하여 의존성만 설치
COPY pyproject.toml poetry.lock* ./

# Poetry를 사용하여 의존성만 설치 (--no-root 옵션 추가)
RUN poetry install --no-interaction --no-ansi --no-root

# 나머지 코드 복사
COPY . .

# ad_fast_api/workspace/files 디렉토리 생성
RUN mkdir -p /ad_fast_api/workspace/files

# 애플리케이션 실행 (모듈 방식으로 실행)
CMD ["python", "-m", "ad_fast_api.main"]