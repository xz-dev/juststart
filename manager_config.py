from pathlib import Path
from .runner import Runner
from .error import ManagerConfigError


class ManagerConfig:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path

    def get_all_runners_paths(self):
        with open(self.config_file_path, "r") as f:
            for path in f.readlines():
                yield (path[2:], False) if path[0:2] == "- " else (path, True)

    def get_runners_info(self) -> dict:
        return dict(self.get_all_runners_paths())

    def rewrite_config_file(self, runners_info: dict):
        with open(self.config_file_path, "w") as f:
            for path in sorted(runners_info):
                is_enabled = runners_info[path]
                f.write(f"- {path}\n" if is_enabled else f"{path}\n")

    def add_runner(self, path):
        runners_info = self.get_runners_info()
        if path in runners_info:
            raise ManagerConfigError(
                f"{path} is already added { 'enabled' if runners_info[path] else 'disabled' }"
            )
        runner_path = Path(path)
        if runner_path.is_dir():
            raise ManagerConfigError(f"{path} is a directory")
        if not runner_path.is_executable():
            raise ManagerConfigError(f"{path} is not executable")
        runners_info[path] = False
        self.rewrite_config_file(runners_info)

    def delete_runner(self, path):
        if path not in self.runners_info:
            raise ManagerConfigError(f"{path} is not added")
        runners_info = self.get_runners_info()
        runners_info.pop(path)
        self.rewrite_config_file(runners_info)

    def enable_runner(self, path):
        runners_info = self.get_runners_info()
        if path not in runners_info:
            raise ManagerConfigError(f"{path} is not added")
        if runners_info[path]:
            raise ManagerConfigError(f"{path} is already enabled", "info")
        runners_info[path] = True
        self.rewrite_config_file(runners_info)

    def disable_runner(self, path):
        runners_info = self.get_runners_info()
        if path not in runners_info:
            logging.error(f"{path} is not added")
            return
        if not runners_info[path]:
            raise ManagerConfigError(f"{path} is already disabled", "info")
        runners_info[path] = False
        self.rewrite_config_file(runners_info)
