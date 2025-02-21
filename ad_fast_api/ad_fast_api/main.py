# from fastapi import FastAPI
# import uvicorn
# import httpx

# from sources.api.make_ad import step1, step2, step3, step4
# from sources.api import configure_animation

# from starlette.exceptions import HTTPException
# from fastapi.exceptions import RequestValidationError


# from sources.error_handling.middleware import add_process_time_header

# from sources.error_handling.exception_handlers import request_validation_exception_handler, http_exception_handler, unhandled_exception_handler
# from sources.error_handling.middleware import log_request_middleware

# app = FastAPI()


# app.middleware("http")(add_process_time_header)
# app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
# app.add_exception_handler(HTTPException, http_exception_handler)
# app.add_exception_handler(Exception, unhandled_exception_handler)

# ad_base_url = "http://animated_drawings:8001"


# app.include_router(step1.router)
# app.include_router(step2.router)
# app.include_router(step3.router)
# app.include_router(step4.router)
# app.include_router(configure_animation.router)


# @app.get("/ping")
# def ping():
#     return {"ad_fast_api test ping success!!"}


# @app.get("/ping_ad")
# async def test_docker_network():
#     async with httpx.AsyncClient() as client:
#         tmp_url = ad_base_url + "/ping"
#         response = await client.get(url=tmp_url)
#         return response.text


# if __name__ == "__main__":
#     from ad_fast_api.workspace.sources import work_dir

#     work_dir.FILES_PATH.mkdir(exist_ok=True)
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


import uvicorn
from fastapi import FastAPI

from ad_fast_api.domain.upload_drawing.sources import upload_drawing_router


app = FastAPI()
app.include_router(upload_drawing_router.router)


@app.get("/ping")
def ping():
    return {"ad_fast_api test ping success!!"}


if __name__ == "__main__":
    from ad_fast_api.workspace.sources import conf_workspace

    conf_workspace.FILES_PATH.mkdir(exist_ok=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
