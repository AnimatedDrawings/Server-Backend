## Introduction
This repo is created to service result of [Animated Drawings](https://github.com/facebookresearch/AnimatedDrawings) to users.

### Network
![dockernetwork](/dockernetworkimg.png)


### Installation
``` bash
# IN CLI

# check current path "Server-Backend/"
cd Server-Backend/

# clone Repo AnimatedDrawings in AnimatedDrawingsAPI/sources/ directory
git -C AnimatedDrawingsAPI/ clone https://github.com/facebookresearch/AnimatedDrawings.git sources/

### Modify Code
# AnimatedDrawingsAPI/sources/torchserve/Dockerfile
# Line : 3
# FROM continuumio/miniconda3:23.3.1-0 <- add tag

# build docker-compose
sudo docker-compose up -d


# MODIFY CODE
# AnimatedDrawings/animated_drawings/mvc_base_cfg.yaml, line 12
# USE_MESA: False -> USE_MESA: True

# AnimatedDrawingsAPI/sources/example/image_to_annotations.py, line 51, 85
# replace localhost -> torchserve
```


### Test
``` bash
http://localhost:8000/ping
# GET
# ad_fast_api test ping success!!

http://localhost:8000/ping_ad
# GET
# animated_drawings test ping success!!
```