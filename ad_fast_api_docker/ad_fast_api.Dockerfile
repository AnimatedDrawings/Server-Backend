FROM python:3.11

WORKDIR /mycode
COPY /ad_fast_api_docker/requirements.txt .
RUN pip install -r requirements.txt