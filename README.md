## Introduction
This repo is created to service result of [Animated Drawings](https://github.com/facebookresearch/AnimatedDrawings) to users. So, I add web-app(FastAPI) and docker-compose. You can use initial setting to checkout "initial" branch

### Network
![dockernetwork](/dockernetworkimg.png)


### Installation
``` bash
# IN CLI
# clone branch name "initial"
git clone -b initial https://github.com/AnimatedDrawings/Server-Backend.git

# check current path "Server-Backend/" and continue installation
cd Server-Backend

# clone AnimatedDrawings and add rest_api dependency
# build docker-compose
git clone https://github.com/facebookresearch/AnimatedDrawings.git
cp -R AnimatedDrawings/examples AnimatedDrawings/rest_api
cp animated_drawings_docker/animated_drawings_api.py AnimatedDrawings/rest_api
docker-compose up -d


# MODIFY CODE
# AnimatedDrawings/rest_api/image_to_annotations.py, line 51, 85
# replace localhost -> torchserve

# AnimatedDrawings/animated_drawings/mvc_base_cfg.yaml, line 12
# USE_MESA: False -> USE_MESA: True
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