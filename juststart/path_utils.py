import re
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


"""Search current directory and its child directoty and its parent directory by keyword in the keyword_list
Search all child directory but ended when the parent directory not have any match file.
Return a dict of file key is keyword and value is the path list which include the keyword in the name.
"""


def _search_file_by_keywords(
    keyword_list: list[str], path: Path, compound_word: str, search_parent: bool = False
) -> dict[str, list[str]]:
    result = {keyword: [] for keyword in keyword_list}

    def add_files_recursively(
        file_path: Path, file_regex_pattern: str = None
    ) -> list[str]:
        if file_path.is_file():
            if file_regex_pattern and not re.match(file_regex_pattern, file_path.name):
                return []
            else:
                return [str(file_path)]
        elif file_path.is_dir():
            files = []
            for child in file_path.iterdir():
                files.extend(add_files_recursively(child, file_regex_pattern))
            return files
        else:
            return []

    def add_matching_files_to_result(
        keyword: str,
        pattern: str,
        dir_regex_pattern: str = None,
        file_regex_pattern: str = None,
    ):
        matching_files = [file for file in path.glob(pattern) if file != path]
        if dir_regex_pattern:
            matching_files = [
                file for file in matching_files if re.match(regex_pattern, str(file))
            ]
        for file in matching_files:
            result[keyword].extend(add_files_recursively(file, file_regex_pattern))

    # search parent directory
    if search_parent:
        for parent in path.parents:
            if parent == parent.parent:
                break
            for keyword in keyword_list:
                if keyword in parent.name:
                    add_matching_files_to_result(keyword, keyword)

    # search current directory and child directory
    for keyword in keyword_list:
        add_matching_files_to_result(keyword, keyword)
        if compound_word:
            # search in current directory
            add_matching_files_to_result(
                keyword,
                f"*{keyword}.{compound_word}*",
                dir_regex_pattern=rf"{keyword}\.{compound_word}.*",
                file_regex_pattern=rf".*{keyword}\.{compound_word}(\..*)?",
            )
            add_matching_files_to_result(
                keyword,
                f"{compound_word}.{keyword}*",
                dir_regex_pattern=rf".*{compound_word}\.{keyword}",
                file_regex_pattern=rf".*{compound_word}\.{keyword}(\..*)?",
            )

            # search in child directories
            add_matching_files_to_result(
                keyword,
                f"**/*{keyword}.{compound_word}*",
                dir_regex_pattern=rf"{keyword}\.{compound_word}.*",
                file_regex_pattern=rf".*{keyword}\.{compound_word}(\..*)?",
            )
            add_matching_files_to_result(
                keyword,
                f"**/{compound_word}.{keyword}*",
                dir_regex_pattern=rf".*{compound_word}\.{keyword}",
                file_regex_pattern=rf".*{compound_word}\.{keyword}(\..*)?",
            )

    return result


def search_file_by_keywords(
    keyword_list: list[str],
    path: str,
    compound_word: str = None,
    search_parent: bool = False,
) -> dict[str, list[str]]:
    return _search_file_by_keywords(keyword_list, Path(path), compound_word, search_parent)
