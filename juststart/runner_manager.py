import logging
from asyncio import new_event_loop
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Thread

from .errors import RunnerError
from .runner import Runner
from .runner_config import RunnerConfig, get_runner_config
from .runner_manager_config import RunnerManagerConfig
from .utils import delete_directory_and_empty_parents, is_parent_directory


class RunnerManagerStatus:
    INITED = "INITED"
    NOT_INITED = "NOT_INITED"

    ENABLED_BOOT = "ENABLED_BOOT"
    DISABLED_BOOT = "DISABLED_BOOT"

    INITED_BUT_NOT_SAVED = "INITED_BUT_NOT_SAVED"

    RUNNING = "RUNNING"
    NOT_RUNNING = "NOT_RUNNING"


class RunnerManager:
    def __init__(
        self,
        runner_list_file_path: str,
        default_runner_config_path: str,
        tmp_dir_path: str,
    ):
        monitor_executor = ThreadPoolExecutor()
        self.loop = new_event_loop()
        self.loop.set_default_executor(monitor_executor)
        self.start_manager()

        self.default_runner_config_path = default_runner_config_path
        self.tmp_dir_path = tmp_dir_path
        self.manager_config = RunnerManagerConfig(runner_list_file_path)
        self.runner_dict = dict()
        self._load_runners()

    def _load_runners(self):
        runners_dict = self.runner_dict
        for path, enabled in self.manager_config.runner_info_dict.items():
            if enabled:
                self.start_runner(path)
                logging.info(f"Runner {path} booted")
            else:
                logging.info(f"Runner {path} checked")

    def start_manager(self):
        def run_event_loop(loop):
            loop.run_forever()

        self.event_loop_thread = Thread(target=run_event_loop, args=(self.loop,))
        self.event_loop_thread.start()

    def stop_manager(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.event_loop_thread.join()
        self.loop.close()

    def get_runner_status_dict(self) -> dict[str, list[RunnerManagerStatus]]:
        runner_status_dict = {}
        for path, enable in self.manager_config.runner_info_dict.items():
            status_list = set()
            if enable:
                status_list.add(RunnerManagerStatus.ENABLED_BOOT)
            else:
                status_list.add(RunnerManagerStatus.DISABLED_BOOT)
            try:
                runner = self.get_runner(path)
                status_list.add(RunnerManagerStatus.INITED)
                if runner.is_running():
                    status_list.add(RunnerManagerStatus.RUNNING)
                else:
                    status_list.add(RunnerManagerStatus.NOT_RUNNING)
            except RunnerError:
                status_list.add(RunnerManagerStatus.NOT_INITED)
            runner_status_dict[path] = status_list
        for runner in self.runner_dict.values():
            try:
                status_list = runner_status_dict[runner.path]
            except KeyError:
                status_list = set([RunnerManagerStatus.INITED_BUT_NOT_SAVED])
                runner_status_dict[runner.path] = status_list
            if runner.is_running():
                status_list.add(RunnerManagerStatus.RUNNING)
            else:
                status_list.add(RunnerManagerStatus.NOT_RUNNING)
            runner_status_dict[runner.path] = status_list
        sorted_status_dict = {}
        for path, status_list in sorted(runner_status_dict.items()):
            sorted_status_dict[path] = sorted(status_list)
        return sorted_status_dict

    def _get_runner_config(self, config_path: str) -> RunnerConfig:
        return get_runner_config(
            config_path,
            self.default_runner_config_path,
            Path(self.tmp_dir_path) / "runner",
        )

    def _get_config_from_runner(self, runner: Runner) -> RunnerConfig:
        return RunnerConfig(
            args=runner.args,
            env=runner.env,
            auto_restart=runner.auto_restart,
            stdin=runner.stdin,
            stdout=runner.stdout,
            stderr=runner.stderr,
        )

    def reload_runner(self, path: str):
        runner = self.get_runner(path)
        config_path = str(Path(path).parent)
        config = self._get_runner_config(config_path)
        need_stop = False
        need_start = False

        if runner.args != config.args:
            runner.args = config.args
            need_stop = True
        if runner.env != config.env:
            runner.env = config.env
            need_stop = True
        if need_stop and runner.is_running():
            runner.stop()
            need_start = True

        if runner.stdin != config.stdin:
            runner.stdin = config.stdin
        if runner.stdout != config.stdout:
            runner.stdout = config.stdout
        if runner.stderr != config.stderr:
            runner.stderr = config.stderr

        if need_start:
            runner.start(self.loop)

    def get_runner(self, path) -> Runner:
        try:
            return self.runner_dict[path]
        except KeyError:
            raise RunnerError(
                f"Runner at {path} is not in memory, which means it is never started or been gc"
            )

    def restart_runner(self, path):
        try:
            runner = self.get_runner(path)
            runner.stop()
        except RunnerError as e:
            logging.info(e.message)
        self.start_runner(path)

    def start_runner(self, path):
        try:
            runner = self.get_runner(path)
            self.reload_runner(path)
        except RunnerError:
            config_path = str(Path(path).parent)
            config = self._get_runner_config(config_path)
            runner = Runner(
                path=path,
                args=config.args,
                env=config.env,
                auto_restart=config.auto_restart,
                stdin=config.stdin,
                stdout=config.stdout,
                stderr=config.stderr,
            )
            self.runner_dict[path] = runner
        self._start_runner(runner)

    def clean_runner(self):
        for path, runner in self.runner_dict.items():
            if not runner.is_running():
                config = self._get_config_from_runner(runner)
                self._destroy_runner_runtime(config)
                self.runner_dict.pop(path)

    def stop_runner(self, path):
        runner = self.get_runner(path)
        runner.stop()

    def _start_runner(self, runner: Runner):
        self._init_runner_runtime(self._get_config_from_runner(runner))
        runner.start(self.loop)

    @staticmethod
    def _init_runner_runtime(config: RunnerConfig):
        Path(config.stdin).parent.mkdir(parents=True, exist_ok=True)
        Path(config.stdin).touch()
        Path(config.stdout).parent.mkdir(parents=True, exist_ok=True)
        Path(config.stdout).touch()
        Path(config.stderr).parent.mkdir(parents=True, exist_ok=True)
        Path(config.stderr).touch()

    def _destroy_runner_runtime(self, config: RunnerConfig):
        tmp_path = Path(self.tmp_dir_path) / "runner"
        if is_parent_directory(Path(config.stdin), tmp_path):
            delete_directory_and_empty_parents(Path(config.stdin).parent, tmp_path)
        if is_parent_directory(Path(config.stdout), tmp_path):
            delete_directory_and_empty_parents(Path(config.stdout).parent, tmp_path)
        if is_parent_directory(Path(config.stderr), tmp_path):
            delete_directory_and_empty_parents(Path(config.stderr).parent, tmp_path)
