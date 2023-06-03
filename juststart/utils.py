from pathlib import Path


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


def is_parent_directory(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False
