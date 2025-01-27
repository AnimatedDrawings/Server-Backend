FROM python:3.11

WORKDIR /mycode
COPY /ADFastAPI/requirements.txt .
RUN pip install -r requirements.txt