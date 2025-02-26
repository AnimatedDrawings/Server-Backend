FROM python:3.13.2

WORKDIR /mycode

# Poetry 설치, 가상환경 생성하지 않도록 설정
RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY . .

# Poetry를 사용하여 의존성 설치
RUN poetry install --no-interaction --no-ansi

# 프로젝트 루트 디렉토리로 변경
WORKDIR /ad_fast_api

# 프로젝트 실행
CMD ["python", "main.py"]