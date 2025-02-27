FROM python:3.8.13

ENV PYTHONPATH "${PYTHONPATH}:/app/AnimatedDrawings"

# install wget
RUN apt-get update && \
    apt-get install -y wget 

# fix opencv-python error
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# fix osmesa error
# https://github.com/facebookresearch/AnimatedDrawings/issues/99#issue-1669192538
RUN apt-get update && \
    apt-get install -y libosmesa6-dev freeglut3-dev && \
    apt-get install -y libglfw3-dev libgles2-mesa-dev && \
    apt-get install -y libosmesa6 

# git 설치
RUN apt-get update && \
    apt-get install -y git

WORKDIR /app

# 저장소 클론하기
RUN git clone https://github.com/facebookresearch/AnimatedDrawings.git

# AnimatedDrawings 디렉토리에서 pip install 실행
RUN cd AnimatedDrawings && pip install -e .

# zerorpc 설치
COPY ./rpc_server.py .
RUN pip install zerorpc

# rpc_server.py 실행
CMD ["python", "rpc_server.py"]