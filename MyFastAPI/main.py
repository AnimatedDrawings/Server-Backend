from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/test_ping')
def test_ping():
    return {'MyFastAPI test ping success!!'}

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=12)