import uvicorn
from fastapi import FastAPI

from ad_fast_api.domain.upload_drawing.sources import upload_drawing_router
from ad_fast_api.domain.find_character.sources import find_character_router
from ad_fast_api.domain.cutout_character.sources import cutout_character_router
from ad_fast_api.domain.configure_character_joints.sources import (
    configure_character_joints_router,
)
from ad_fast_api.domain.make_animation.sources import make_animation_router


app = FastAPI()
app.include_router(upload_drawing_router.router)
app.include_router(find_character_router.router)
app.include_router(cutout_character_router.router)
app.include_router(configure_character_joints_router.router)
app.include_router(make_animation_router.router)


@app.get("/ping")
def ping():
    return {"ad_fast_api test ping success!!"}


@app.get("/ping_animated_drawings")
def ping_animated_drawings(test_param: int):
    from zero import ZeroClient

    zero_client = ZeroClient("animated_drawings", 8001)
    respone = zero_client.call("ping", test_param)

    return {"ping_animated_drawings": respone}


if __name__ == "__main__":
    from ad_fast_api.snippets.sources.ad_env import get_ad_env

    internal_port = get_ad_env().internal_port
    uvicorn.run(
        "ad_fast_api.main:app",
        host="0.0.0.0",
        port=internal_port,
        reload=True,
    )
