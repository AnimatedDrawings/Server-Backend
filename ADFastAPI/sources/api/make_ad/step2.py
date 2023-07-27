# from fastapi import APIRouter, UploadFile, File
# from pathlib import Path
# from datetime import datetime
# from uuid import uuid4
# import httpx

# router = APIRouter(
#     prefix='/api/make_ad/step1',
# )

# FILES_IN_DOCKER = Path('/mycode/files/')
# AD_BASEURL = 'http://animated_drawings:8001/'

# @router.post('/upload_drawing')
# async def upload_drawing(file: UploadFile = File(...)):
#     extension = '.png'
#     id = uuid4().hex + '_' + datetime.now().strftime("%Y%m%d%H%M%S")
#     base_path: Path = FILES_IN_DOCKER.joinpath(id)
#     base_path.mkdir()
#     img_str = 'original_image'
#     saved_file_name = img_str + extension
#     file_location = str(base_path.joinpath(saved_file_name))

#     with open(file_location, 'wb') as image:
#         image.write(file.file.read())
#         image.close()

#     detect_bounding_box_url = AD_BASEURL + 'detect_bounding_box'
#     params = { 'id' : id }
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url = detect_bounding_box_url, params = params)
#         try:
#             return response.json()
#         except:
#             return response.text