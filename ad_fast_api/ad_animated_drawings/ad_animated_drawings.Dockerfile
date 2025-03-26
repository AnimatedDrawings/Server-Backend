FROM python:3.8.13

ARG WORK_DIR
ARG INTERNAL_PORT
ARG ANIMATED_DRAWINGS_WORKSPACE_DIR

ENV INTERNAL_PORT=${INTERNAL_PORT}
ENV PYTHONPATH "${PYTHONPATH}:/${WORK_DIR}/AnimatedDrawings"

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

WORKDIR /${WORK_DIR}

# AnimatedDrawings 저장소를 GitHub에서 클론
RUN git clone https://github.com/facebookresearch/AnimatedDrawings.git
RUN cd AnimatedDrawings && pip install -e .

# zerorpc 설치
RUN pip install zeroapi
COPY ./rpc_server.py .

# 도커볼륨 workspace 디렉토리 생성
RUN mkdir -p /${ANIMATED_DRAWINGS_WORKSPACE_DIR}/files
RUN mkdir -p /${ANIMATED_DRAWINGS_WORKSPACE_DIR}/config

# rpc_server.py 실행
CMD ["python", "rpc_server.py"]