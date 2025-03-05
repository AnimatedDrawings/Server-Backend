import time
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse


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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    request_body = await request.body()

    print()
    print("-------------------------------------")
    print(f"REQUEST_URL : {request.url}")
    # print(f"REQUEST_BODY : {request_body}")
    print(f"REQUEST_HEADERS : {request.headers}")

    response = await call_next(request)

    process_time = time.time() - start_time
    print(f"PROCESS_TIME : {process_time}")
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    # 만약 HTTPException으로 인해 리턴된 JSON에 detail이 있다면
    # try:
    #     decoded_response = response_body.decode("utf-8")
    #     print(f"RESPONSE_BODY : {decoded_response}")
    # except UnicodeDecodeError:
    #     pass

    print("-------------------------------------")
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print()
    print("#####################################")
    print("######### HTTPException 발생 #########")
    print(f"detail: {exc.detail}")
    print(f"status_code: {exc.status_code}")
    print("#####################################")
    print()
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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
