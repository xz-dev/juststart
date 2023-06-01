import os

from .errors import ManagerConfigError


class RunnerManagerConfig:
    def __init__(self, runner_list_file_path):
        self.runner_list_file_path = runner_list_file_path

    def __get_all_runners_info(self):
        with open(self.runner_list_file_path, "a+") as f:
            f.seek(0)
            for line in f.readlines():
                path = line.strip()
                if path:
                    yield (path[2:], False) if path[0:2] == "- " else (path, True)

    @property
    def runner_info_dict(self) -> dict:
        return dict(self.__get_all_runners_info())

    @runner_info_dict.setter
    def runner_info_dict(self, runners_info: dict):
        with open(self.runner_list_file_path, "w") as f:
            for path in sorted(runners_info):
                is_enabled = runners_info[path]
                f.write(f"- {path}\n" if is_enabled else f"{path}\n")

    def add_runner(self, path):
        runners_info = self.runner_info_dict
        if path in runners_info:
            raise ManagerConfigError(
                f"{path} is already added { 'enabled' if runners_info[path] else 'disabled' }"
            )
        if os.path.isdir(path):
            raise ManagerConfigError(f"{path} is a directory")
        if not os.path.exists(path):
            raise ManagerConfigError(f"{path} does not exist")
        if not os.path.isfile(path):
            raise ManagerConfigError(f"{path} is not a file")
        if not os.access(path, os.X_OK):
            raise ManagerConfigError(
                f"{path} is not executable or not have running permission"
            )
        runners_info[path] = False
        self.runner_info_dict = runners_info

    def delete_runner(self, path):
        runners_info = self.runner_info_dict
        if path not in runners_info:
            raise ManagerConfigError(f"{path} is not added")
        runners_info = self.runner_info_dict()
        runners_info.pop(path)
        self.runner_info_dict = runners_info

    def enable_runner(self, path):
        runners_info = self.runner_info_dict()
        if path not in runners_info:
            raise ManagerConfigError(f"{path} is not added")
        if runners_info[path]:
            raise ManagerConfigError(f"{path} is already enabled", "info")
        runners_info[path] = True
        self.runner_info_dict = runners_info

    def disable_runner(self, path):
        runners_info = self.runner_info_dict()
        if path not in runners_info:
            logging.error(f"{path} is not added")
            return
        if not runners_info[path]:
            raise ManagerConfigError(f"{path} is already disabled", "info")
        runners_info[path] = False
        self.runner_info_dict = runners_info
