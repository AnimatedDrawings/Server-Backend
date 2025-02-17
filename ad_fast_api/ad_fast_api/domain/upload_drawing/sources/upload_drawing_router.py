# from fastapi import APIRouter, UploadFile, File
# from pathlib import Path
# from datetime import datetime
# from uuid import uuid4
# import httpx
# import yaml
# import logging
# from sources.schema import DefaultResponse
# from pydantic import BaseModel

# router = APIRouter(
#     prefix="/api/make_ad/step1",
# )

# FILES_IN_DOCKER = Path("/mycode/files/")
# AD_BASEURL = "http://animated_drawings:8001/"


# class UploadADrawingResponse(BaseModel):
#     ad_id: str
#     bounding_box: dict


# @router.post("/upload_drawing")
# async def upload_drawing(file: UploadFile = File(...)):
#     ad_id = uuid4().hex + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
#     base_path: Path = FILES_IN_DOCKER.joinpath(ad_id)
#     base_path.mkdir()
#     log_path = base_path.joinpath("logs")
#     log_path.mkdir()
#     log_file_path = log_path.joinpath("log.txt")
#     log_file_path.touch()
#     logging.basicConfig(filename=log_file_path.as_posix(), level=logging.DEBUG)

#     original_image_path = base_path.joinpath("image.png")

#     with open(original_image_path.as_posix(), "wb") as image:
#         image.write(file.file.read())
#         image.close()

#     ad_url = AD_BASEURL + "upload_a_drawing"
#     params = {"ad_id": ad_id}
#     default_response = DefaultResponse()

#     async with httpx.AsyncClient() as client:
#         response = await client.get(url=ad_url, params=params, timeout=30)
#         response_dict = response.json()
#         is_success = response_dict["is_success"]
#         if is_success:
#             bounding_box_path = base_path.joinpath("bounding_box.yaml")
#             with open(
#                 bounding_box_path.as_posix(), encoding="UTF-8"
#             ) as bounding_box_yaml:
#                 bounding_box_dict = yaml.load(bounding_box_yaml, Loader=yaml.FullLoader)
#                 my_response = UploadADrawingResponse(
#                     ad_id=ad_id, bounding_box=bounding_box_dict
#                 )
#                 default_response.success(response=my_response)
#                 return default_response.dict()
#         else:
#             msg = response_dict["msg"]
#             logging.critical(msg=msg)
#             default_response.fail(message=msg)
#             return default_response.dict()


from fastapi import APIRouter, UploadFile, File, HTTPException
from ad_fast_api.domain.upload_drawing.features import upload_drawing_feature as udf

router = APIRouter()


@router.post("/upload_drawing")
async def upload_drawing(
    file: UploadFile = File(...),
):
    try:
        ad_id = udf.make_ad_id()
        base_path = udf.create_base_dir(ad_id=ad_id)
        file_bytes = file.file.read()

        await udf.save_image(
            base_path=base_path,
            file_bytes=file_bytes,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
