import pytest
from pathlib import Path
from faker import Faker
from ad_fast_api.snippets.sources.save_image import save_image_async
from ad_fast_api.snippets.testings.ad_test.ad_test_helper import measure_execution_time


@pytest.mark.asyncio
async def test_save_image_async(tmp_path: Path):
    # given
    image_name = "test.png"
    base_path = tmp_path
    fake = Faker()
    file_bytes = fake.binary(length=10 * 1024 * 1024)

    # when
    await measure_execution_time("save_origin_image")(save_image_async)(
        image_bytes=file_bytes,
        image_name=image_name,
        base_path=base_path,
    )

    # then
    image_path = base_path.joinpath(image_name)
    assert image_path.exists()
    assert image_path.read_bytes() == file_bytes
