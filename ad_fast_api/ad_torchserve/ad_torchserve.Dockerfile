# Use Python 3.8.13-slim as the base image.
FROM python:3.8.13-slim

# Disable GPU usage in the container
ENV CUDA_VISIBLE_DEVICES=""

# Install OS-level dependencies.
RUN mkdir -p /usr/share/man/man1 && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        ca-certificates \
        curl \
        vim \
        sudo \
        default-jre \
        git \
        gcc \
        build-essential \
        wget && \
    rm -rf /var/lib/apt/lists/*

# Fix bug for xtcocoapi, a dependency of mmpose.
RUN git clone https://github.com/jin-s13/xtcocoapi.git
WORKDIR /xtcocoapi                              
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py install                      
WORKDIR /                                      

# Install openmim for model management.
RUN pip install --no-cache-dir openmim 

# Install CPU-only versions of PyTorch, Torchserve, and Torchvision.
RUN pip install --no-cache-dir torch==2.0.0 --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir torchserve
RUN pip install --no-cache-dir torchvision==0.15.1 --extra-index-url https://download.pytorch.org/whl/cpu

# Install additional deep learning libraries.
RUN pip install --no-cache-dir mmdet==2.27.0   # Object detection library.
RUN pip install --no-cache-dir mmpose==0.29.0   # Pose estimation library.
RUN pip install --no-cache-dir numpy==1.24.4    # Numerical computations library.
RUN mim install mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.0.0/index.html  # Install MMCV (full version for OpenMMLab, CPU version).

# Prepare Torchserve model directory and download model archives.
RUN mkdir -p /home/torchserve/model-store
RUN wget https://github.com/facebookresearch/AnimatedDrawings/releases/download/v0.0.1/drawn_humanoid_detector.mar -P /home/torchserve/model-store/
RUN wget https://github.com/facebookresearch/AnimatedDrawings/releases/download/v0.0.1/drawn_humanoid_pose_estimator.mar -P /home/torchserve/model-store/
COPY config.properties /home/torchserve/config.properties

# Start Torchserve
CMD torchserve --start --disable-token-auth --ts-config /home/torchserve/config.properties && sleep infinity