from pathlib import Path
from typing import Optional


FILES_PATH = Path(__file__).parent.parent.joinpath("files")


def get_base_path(
    ad_id: str,
    files_path: Optional[Path] = None,
) -> Path:
    files_path = files_path or FILES_PATH
    return files_path.joinpath(ad_id)
