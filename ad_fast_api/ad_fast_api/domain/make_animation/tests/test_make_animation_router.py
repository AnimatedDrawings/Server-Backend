from ad_fast_api.domain.make_animation.sources.errors import (
    make_animation_400_status as ma4s,
)


# def test_make_animation_router_fail_invalid_animation(test_client):
#     # given
#     path = "/make_animation"
#     ad_id = "test_ad_id"
#     ad_animation = "invalid_animation"
#     params = {"ad_id": ad_id, "ad_animation": ad_animation}

#     # when
#     response = test_client.post(
#         path,
#         params=params,
#     )

#     # then
#     assert response.status_code == ma4s.INVALID_ANIMATION.status_code
#     assert response.json()["detail"] == ma4s.INVALID_ANIMATION.detail
