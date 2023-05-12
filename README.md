Installation

```
# clone MyFastAPI 
git clone https://github.com/chminipark/MyFastAPP.git

# check current path "MyFastApp/." and continue installation
cd MyFastApp

# clone AnimatedDrawings and add rest_api dependency
# build docker-compose
git clone https://github.com/facebookresearch/AnimatedDrawings.git
cp -R AnimatedDrawings/examples AnimatedDrawings/rest_api
cp animated_drawings_docker/animated_drawings_api.py AnimatedDrawings/rest_api
docker-compose up -d
```