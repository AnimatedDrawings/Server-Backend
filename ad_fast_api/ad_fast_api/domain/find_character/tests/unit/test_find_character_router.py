from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from ad_fast_api.main import app
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.domain.find_character.sources import find_character_router as fcr
from fastapi import Response
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.testings.mock_logger import mock_logger


client = TestClient(app)


def test_find_character_success(mock_logger):
    # given
    path = "/find_character"
    ad_id = "test_ad_id"
    params = {"ad_id": ad_id}
    base_path = cw.get_base_path(ad_id=ad_id)
    bounding_box = BoundingBox.mock()
    body = bounding_box.model_dump(mode="json")
    mock_response_content = b"mocked file content"
    mock_response_status_code = 200
    mock_response = Response(
        content=mock_response_content,
        status_code=mock_response_status_code,
    )

    with patch.object(
        fcr,
        "save_bounding_box",
        new=Mock(),
    ) as mock_save_bounding_box, patch.object(
        fcr,
        "setup_logger",
        new=Mock(return_value=mock_logger),
    ) as mock_setup_logger, patch.object(
        fcr,
        "crop_and_segment_character",
        new=Mock(),
    ) as mock_crop_and_segment_character, patch.object(
        fcr,
        "FileResponse",
        new=Mock(return_value=mock_response),
    ) as mock_file_response:
        # when
        response = client.post(path, params=params, json=body)

    # then
    assert response.status_code == mock_response_status_code
    assert response.content == mock_response_content
    mock_save_bounding_box.assert_called_once_with(
        bounding_box=bounding_box,
        base_path=base_path,
    )
    mock_setup_logger.assert_called_once_with(base_path=base_path)
    mock_crop_and_segment_character.assert_called_once_with(
        ad_id=ad_id,
        bounding_box=bounding_box,
        base_path=base_path,
        logger=mock_logger,
    )
    mock_file_response.assert_called_once_with(
        base_path.joinpath(cw.CUTOUT_CHARACTER_IMAGE_NAME).as_posix(),
    )
