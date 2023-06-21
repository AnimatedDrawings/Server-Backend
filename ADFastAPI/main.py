from fastapi import FastAPI
import uvicorn
import httpx

app = FastAPI()
timeout = httpx.Timeout(5, read=None)

@app.get('/ping')
def ping():
    return {'ad_fast_api test ping success!!'}

@app.get('/ping_ad')
async def test_docker_network():
    async with httpx.AsyncClient() as client:
        response = await client.get(url='http://animated_drawings:8001/ping')
        return response.text

@app.get('/get_my_animated_drawings')
async def get_my_animated_drawings():
    async with httpx.AsyncClient() as client:
        response = await client.get(url='http://animated_drawings:8001/get_my_animated_drawings', timeout=timeout)
        return response.text

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)