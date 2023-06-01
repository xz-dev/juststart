from .manager_config import ManagerConfig
from .runner import Runner
from .runner_config import get_runner_config
from .error import RunnerError, RunnerManagerError


class RunnerManager:
    def __init__(self, config_file_path, default_runner_config_file_path):
        self.config_manager = ManagerConfig(config_file_path)
        self.runner_dict = dict()
        self._load_runners()

    def _load_runners(self):
        runners_dict = self.runner_dict
        for path, enabled in self.config_manager.get_all_runners_paths():
            if enabled:
                self.start_runner(path)

    def reload_runner(path: str):
        config = RunnerConfig(path)
        runner = self.get_runner(path)
        need_stop = False
        need_start = False

        if runner.args != config.args:
            runner.args = config.args
            need_stop = True
        if runner.env != config.env:
            runner.env = config.env
            need_stop = True
        if need_restart and runner.is_running():
            runner.stop()
            need_start = True

        if runner.stdin != config.stdin:
            runner.stdin = config.stdin
        if runner.stdout != config.stdout:
            runner.stdout = config.stdout
        if runner.stderr != config.stderr:
            runner.stderr = config.stderr

        if need_start:
            runner.start()

    def get_runner(self, path) -> Runner:
        try:
            return self.runner_dict[path]
        except RunnerError as e:
            raise RunnerManager(f"Runner at {path} is not found") from e

    def restart_runner(self, path):
        runner = self.get_runner(path)
        try:
            runner.stop()
        except RunnerError as e:
            logging.info(e.message)
        runner.start()

    def start_runner(self, path):
        if path in runners_dict:
            self.reload_runner(path)
            runner = self.get_runner(path)
        else:
            config = get_runner_config(
                path, default_config=get_runner_config(default_runner_config_file_path)
            )
            runner = Runner(
                path=path,
                args=config.args,
                env=config.env,
                stdin=config.stdin,
                stdout=config.stdout,
                stderr=config.stderr,
            )
            runners_dict[path] = runner
        runner.start()

    def clean_runner(self):
        for path, runner in self.runner_dict.items():
            if not runner.is_running():
                self.runner_dict.pop(path)

    def stop_runner(self, path):
        runner = self.get_runner(path)
        runner.stop()
