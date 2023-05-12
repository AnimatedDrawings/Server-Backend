FROM --platform=linux/amd64 ubuntu:18.04

ENV PATH="/root/miniconda3/bin:$PATH"
ARG PATH="/root/miniconda3/bin:$PATH"

# update apt
RUN apt-get update \
    && apt-get install -y wget \
    && rm -rf /var/lib/apt/lists/* 

# install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 

# install AnimatedDrawings
WORKDIR /mycode
COPY /AnimatedDrawings/setup.py .
RUN conda init bash \
    && . ~/.bashrc \
    && conda create --name animated_drawings python=3.8.13 \
    && conda activate animated_drawings \
    && pip install -e .