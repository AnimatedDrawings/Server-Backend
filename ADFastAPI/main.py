from fastapi import FastAPI
import uvicorn
import httpx

from sources.api.make_ad import step1, step2, step3, step4
from sources.api import add_animation

from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from sources.error_handling.exception_handlers import request_validation_exception_handler, http_exception_handler, unhandled_exception_handler
from sources.error_handling.middleware import log_request_middleware

app = FastAPI()

app.middleware("http")(log_request_middleware)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

ad_base_url = 'http://animated_drawings:8001'

@app.get('/ping')
def ping():
    return {'ad_fast_api test ping success!!'}

@app.get('/ping_ad')
async def test_docker_network():
    async with httpx.AsyncClient() as client:
        tmp_url = ad_base_url + '/ping'
        response = await client.get(url = tmp_url)
        return response.text

app.include_router(step1.router)
app.include_router(step2.router)
app.include_router(step3.router)
app.include_router(step4.router)
app.include_router(add_animation.router)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
