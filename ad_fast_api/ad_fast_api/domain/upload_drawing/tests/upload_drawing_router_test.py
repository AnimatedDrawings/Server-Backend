from fastapi import HTTPException
from unittest.mock import patch, AsyncMock, ANY
from ad_fast_api.domain.upload_drawing.testings import fake_upload_drawing as fud
from ad_fast_api.domain.upload_drawing.sources import upload_drawing_router as udr


def test_upload_drawing_success(mock_client):
    with patch.object(
        udr,
        "save_image",
        new=AsyncMock(return_value=fud.fake_ad_id),
    ) as mock_save_image, patch.object(
        udr,
        "detect_character",
        new=AsyncMock(return_value=fud.fake_bounding_box),
    ) as mock_detect:

        # when
        response = mock_client.post(
            "/upload_drawing",
            files=fud.fake_upload_file,
        )

    # then
    assert response.status_code == 200
    assert response.json() == {
        "ad_id": fud.fake_ad_id,
        "bounding_box": fud.fake_bounding_box,
    }
    mock_save_image.assert_awaited_once_with(file=ANY)
    mock_detect.assert_awaited_once_with(ad_id=fud.fake_ad_id)


def test_upload_drawing_save_image_http_exception(mock_client):
    # given
    detail = "File is empty"

    with patch.object(
        udr,
        "save_image",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=400,
                detail=detail,
            )
        ),
    ) as mock_save_image:

        response = mock_client.post(
            "/upload_drawing",
            files=fud.fake_upload_file,
        )

    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    mock_save_image.assert_awaited_once_with(file=ANY)


def test_upload_drawing_detect_character_http_exception(mock_client):
    # given
    detail = "Image is not RGB"

    with patch.object(
        udr,
        "save_image",
        new=AsyncMock(return_value=fud.fake_ad_id),
    ) as mock_save_image, patch.object(
        udr,
        "detect_character",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=415,
                detail=detail,
            )
        ),
    ) as mock_detect:

        response = mock_client.post("/upload_drawing", files=fud.fake_upload_file)

    assert response.status_code == 415
    assert response.json() == {"detail": detail}
    mock_save_image.assert_awaited_once_with(file=ANY)
    mock_detect.assert_awaited_once_with(ad_id=fud.fake_ad_id)


def test_upload_drawing_server_error(mock_client):
    # given
    detail = "Unexpected server error"
    with patch.object(
        udr,
        "save_image",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=500,
                detail=detail,
            )
        ),
    ) as mock_save_image:

        response = mock_client.post("/upload_drawing", files=fud.fake_upload_file)

    assert response.status_code == 500
    assert response.json() == {"detail": detail}
    mock_save_image.assert_awaited_once_with(file=ANY)


# 파일이 없으면 FastAPI에서 자동으로 422 에러 발생
def test_upload_drawing_no_file(mock_client):
    response = mock_client.post("/upload_drawing")

    assert response.status_code == 422
    assert "detail" in response.json()


# 잘못된 파일 키 사용
def test_upload_drawing_wrong_file_key(mock_client):
    response = mock_client.post(
        "/upload_drawing",
        files={
            "wrong_key": (
                "test.png",
                fud.fake_test_file,
                "image/png",
            )
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()
