import yaml
from pathlib import Path


def file_to_dict(
    file_path: Path,
) -> dict:
    with open(file_path.as_posix(), "r") as f:
        content = yaml.load(f, Loader=yaml.FullLoader)
    return content


def dict_to_file(
    to_save_dict: dict,
    file_path: Path,
):
    content = yaml.dump(to_save_dict)
    with open(file_path.as_posix(), "w") as f:
        f.write(content)
