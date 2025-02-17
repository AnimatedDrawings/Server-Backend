FROM python:3.13.2

WORKDIR /mycode
COPY /ADFastAPI/requirements.txt .
RUN pip install -r requirements.txt