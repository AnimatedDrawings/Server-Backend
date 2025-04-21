from ad_fast_api.domain.schema.sources.schemas import Joints
from unittest.mock import patch, Mock
from ad_fast_api.domain.configure_character_joints.sources import (
    configure_character_joints_router,
)


def test_configure_character_joints_success(mock_client):
    # given
    path = "/configure_character_joints"
    ad_id = "dummy_ad_id"
    params = {"ad_id": ad_id}
    body = Joints.mock().model_dump(mode="json")

    # when
    with patch.object(
        configure_character_joints_router,
        "save_joints",
        new=Mock(),
    ) as mock_save_joints:
        response = mock_client.post(
            path,
            params=params,
            json=body,
        )

    # then
    assert response.status_code == 200


def test_configure_character_joints_fail_status_500(mock_client):
    # given
    path = "/configure_character_joints"
    ad_id = "dummy_ad_id"
    params = {"ad_id": ad_id}
    body = Joints.mock().model_dump(mode="json")

    # when
    with patch.object(
        configure_character_joints_router,
        "save_joints",
        new=Mock(side_effect=Exception()),
    ) as mock_save_joints:
        response = mock_client.post(
            path,
            params=params,
            json=body,
        )

    # then
    assert response.status_code == 500
