from fnmatch import filter
from pathlib import Path


def is_parent_dir(parent_path: str, child_path: str) -> bool:
    parent = Path(parent_path)
    child = Path(child_path)

    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def check_path_valid(path: str) -> bool:
    return Path(path).exists()


def _check_path_name(path: Path, name: str) -> bool:
    if path.name == name:
        return True
    elif path.parent != path:
        return _check_path_name(path.parent, name)
    else:
        return False


def try_path_without_glob(path: str, path_list: list[str]) -> list[str]:
    return [p for p in path_list if _check_path_name(Path(p), path)]


def try_path_with_glob(path: str, path_list: list[str]) -> list[str]:
    return filter(path_list, path)


def try_glob_both_side(path: str, path_list: list[str]) -> list[str]:
    return filter(path_list, f"*{path}*")


def filter_path_list(path: str, all_path_list: list[str]) -> list[str]:
    path_list = try_path_without_glob(path, all_path_list)
    if path_list:
        return path_list
    path_list = try_path_with_glob(path, all_path_list)
    if path_list:
        return path_list
    path_list = try_glob_both_side(path, all_path_list)
    if path_list:
        return path_list
    else:
        return []
