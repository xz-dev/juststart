from pathlib import Path

from .path_helper import is_parent_directory


def delete_directory_and_empty_parents(directory: Path, stop_directory: Path):
    if (
        not is_parent_directory(directory, stop_directory)
        or directory == stop_directory
    ):
        return
    directory.unlink()
    parent_dir = directory.parent
    if not any(parent_dir.iterdir()):
        delete_directory_and_empty_parents(parent_dir, stop_directory)
