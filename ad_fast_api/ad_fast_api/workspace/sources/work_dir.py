from pathlib import Path


FILES_PATH = Path(__file__).parent.parent.joinpath("files")


def get_base_path(ad_id: str) -> Path:
    return FILES_PATH.joinpath(ad_id)
