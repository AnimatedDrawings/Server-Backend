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


def custom_openapi():
    return make_animation_router.make_animation_openapi(app)


app.openapi = custom_openapi


@app.get("/ping")
def ping():
    return {"ad_fast_api test ping success!!"}


@app.get("/ping_animated_drawings")
def ping_animated_drawings(test_param: int):
    from ad_fast_api.domain.make_animation.sources.features.image_to_animation import (
        get_zero_client,
    )

    respone = get_zero_client().call("ping", test_param)
    return {"ping_animated_drawings": respone}


@app.get("/ping_torchserve")
def ping_torchserve():
    from httpx import Client

    with Client() as client:
        response = client.get("http://torchserve:8080/ping")
    return {"ping_torchserve": response.json()}


if __name__ == "__main__":
    import uvicorn
    from ad_fast_api.snippets.sources.ad_env import get_ad_env

    internal_port = get_ad_env().internal_port
    uvicorn.run(
        "ad_fast_api.main:app",
        host="0.0.0.0",
        port=internal_port,
        reload=True,
        reload_dirs=["/ad_fast_api"],
    )
