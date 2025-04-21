from uuid import uuid4
from datetime import datetime
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from pathlib import Path
from typing import Optional


def make_ad_id(
    now: Optional[datetime] = None,
    uuid: Optional[str] = None,
) -> str:
    now = now or datetime.now()
    uuid = uuid or uuid4().hex
    ad_id = now.strftime("%Y%m%d%H%M%S") + "_" + uuid
    return ad_id


def create_base_dir(
    ad_id: str,
    files_path: Optional[Path] = None,
) -> Path:
    base_path = get_base_path(
        ad_id=ad_id,
        files_path=files_path,
    )
    base_path.mkdir()
    return base_path
