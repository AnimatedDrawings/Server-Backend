from fastapi import FastAPI
import uvicorn
import httpx

from domain.AD import AD_router

app = FastAPI()
timeout = httpx.Timeout(5, read=None)

class ADURL:
    def __init__(self):
        self.base_url = 'http://animated_drawings:8001'
    
    def add_path(self, path_list: list) -> str:
        tmp_url = self.base_url
        for path in path_list:
            tmp_url += '/' + path

        return tmp_url

ad_url = ADURL()

@app.get('/ping')
def ping():
    return {'ad_fast_api test ping success!!'}

@app.get('/ping_ad')
async def test_docker_network():
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url.add_path(['ping']))
        return response.text

@app.get('/get_animated_drawings')
async def get_animated_drawings():
    async with httpx.AsyncClient() as client:
        response = await client.get(url = ad_url.add_path(['get_animated_drawings']), timeout=timeout)
        return response.text

app.include_router(AD_router.router)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)