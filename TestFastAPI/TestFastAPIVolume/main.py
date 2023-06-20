from fastapi import FastAPI
import uvicorn
import httpx

app = FastAPI()
timeout = httpx.Timeout(5, read=None)

@app.get('/ping')
def ping():
    return {'MyFastAPI test ping success!!'}

# @app.get('/test_docker_network')
# async def test_docker_network():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url='http://animated_drawings:50/ping')
#         return response.text

# @app.get('/get_my_animated_drawings')
# async def get_my_animated_drawings():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url='http://animated_drawings:50/get_my_animated_drawings', timeout=timeout)
#         return response.text

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=5000, reload=True)