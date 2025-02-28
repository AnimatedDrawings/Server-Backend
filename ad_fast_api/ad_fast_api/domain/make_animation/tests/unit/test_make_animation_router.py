import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ad_fast_api.domain.make_animation.sources.make_animation_router import router
from ad_fast_api.domain.make_animation.sources.errors.make_animation_500_status import (
    NOT_FOUND_ANIMATION_FILE,
)


# Dummy implementations to override the actual operations
def dummy_handle_operation(func, **kwargs):
    """
    Dummy handle_operation function:
    - When calling check_make_animation_info, it returns a dummy relative file path.
    - When calling prepare_make_animation, it returns a dummy configuration path.
    """
    if func.__name__ == "check_make_animation_info":
        # Return a dummy relative file path that our endpoint expects
        return "output.gif"
    elif func.__name__ == "prepare_make_animation":
        return "dummy_config"
    else:
        return None


async def dummy_handle_operation_async(*args, **kwargs):
    """
    Dummy async operation for image_to_animation.
    """
    return


@pytest.fixture
def temp_dir(tmp_path):
    """
    Create a temporary directory with a dummy GIF file.
    The dummy file (output.gif) will simulate the animation output.
    """
    dummy_file = tmp_path / "output.gif"
    dummy_file.write_bytes(b"GIF89a")  # write dummy GIF header bytes
    return tmp_path


@pytest.fixture
def app(temp_dir, monkeypatch):
    """
    Create a FastAPI app with the make_animation router and override
    dependencies such as get_base_path, handle_operation, and handle_operation_async.
    """
    # Override get_base_path to always return the provided temporary directory.
    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.get_base_path",
        lambda ad_id: temp_dir,
    )
    # Override the utility functions to use our dummy implementations.
    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.handle_operation",
        dummy_handle_operation,
    )
    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.handle_operation_async",
        dummy_handle_operation_async,
    )

    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


def test_make_animation_success(app):
    """
    Test that the /make_animation endpoint returns a FileResponse containing the dummy GIF.
    """
    client = TestClient(app)
    response = client.post(
        "/make_animation", params={"ad_id": "test", "ad_animation": "dummy_anim"}
    )
    # Verify that the response status code is 200
    assert response.status_code == 200
    # Verify that the content matches the dummy GIF file
    assert response.content == b"GIF89a"


def test_make_animation_file_not_found(monkeypatch, tmp_path):
    """
    Test the case where the generated animation file is not found.
    In this simulation, we do not create the expected dummy file so that
    the endpoint raises NOT_FOUND_ANIMATION_FILE.
    """

    # Define a dummy get_base_path that returns our temporary path (which does not have output.gif)
    def dummy_get_base_path(ad_id):
        return tmp_path  # No file is created in this directory.

    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.get_base_path",
        dummy_get_base_path,
    )
    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.handle_operation",
        dummy_handle_operation,
    )
    monkeypatch.setattr(
        "ad_fast_api.domain.make_animation.sources.make_animation_router.handle_operation_async",
        dummy_handle_operation_async,
    )

    test_app = FastAPI()
    test_app.include_router(router)
    client = TestClient(test_app)

    response = client.post(
        "/make_animation", params={"ad_id": "test", "ad_animation": "dummy_anim"}
    )

    # Since the file does not exist, our endpoint raises the NOT_FOUND_ANIMATION_FILE exception.
    # The default FastAPI exception handler will produce a 500 status code here.
    assert response.status_code == 500
