FROM --platform=linux/amd64 ubuntu:18.04

ENV PYTHONPATH "${PYTHONPATH}:/mycode/AnimatedDrawingsAPI"
ENV PATH="/root/miniconda3/bin:$PATH"
ARG PATH="/root/miniconda3/bin:$PATH"

# install wget
RUN apt-get update \
    && apt-get install -y wget 

# fix opencv-python error
RUN apt-get update \
    && apt-get install -y libgl1-mesa-glx \
    && apt-get install -y libglib2.0-0 

# fix osmesa error
# https://github.com/facebookresearch/AnimatedDrawings/issues/99#issue-1669192538
RUN apt-get update \
    && apt-get install -y libosmesa6-dev freeglut3-dev \
    && apt-get install -y libglfw3-dev libgles2-mesa-dev \
    && apt-get install -y libosmesa6 

# install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 

# install AnimatedDrawings and fix osmesa error
WORKDIR /mycode
COPY /AnimatedDrawingsAPI/sources/setup.py .
RUN conda init bash \
    && . ~/.bashrc \
    && conda create --name animated_drawings python=3.8.13 \
    && conda activate animated_drawings \
    && pip install -e . \
    && export PYOPENGL_PLATFORM=osmesa \
    && conda install -c conda-forge libstdcxx-ng \
    && conda install cmake