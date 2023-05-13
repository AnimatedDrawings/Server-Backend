from fastapi import FastAPI
import uvicorn
import httpx

app = FastAPI()

@app.get('/ping')
def ping():
    return {'MyFastAPI test ping success!!'}

@app.get('/get_from_animated_drawings')
async def get_from_animated_drawings():
    async with httpx.AsyncClient() as client:
        response = await client.get(url='http://animated_drawings:50/return_to_mfa')
        return response.text

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=12, reload=True)