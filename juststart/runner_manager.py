import logging
from asyncio import new_event_loop
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Thread
from .config import enable_compatible_runit

from .errors import ManagerConfigError, RunnerError
from .runner import Runner
from .runner_config import RunnerConfig, get_runner_config
from .runner_manager_config import RunnerManagerConfig
from .utils import delete_directory_and_empty_parents


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

    def _unload_runners(self):
        for path in list(self.runner_dict.keys()):
            try:
                self.stop_runner(path)
                logging.info(f"Runner {path} stopped")
            except RunnerError:
                logging.info(f"Runner {path} had stopped")
        self.clean_runner()

    def start_manager(self):
        def run_event_loop(loop):
            loop.run_forever()

        self.event_loop_thread = Thread(target=run_event_loop, args=(self.loop,))
        self.event_loop_thread.start()

    def stop_manager(self):
        self._unload_runners()
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

    def clean_runner(self):
        deleted_runner_list = []
        for path, runner in list(self.runner_dict.items()):
            if not runner.is_running():
                self._pop_runner(runner)
                deleted_runner_list.append(path)
        return deleted_runner_list

    def restart_runner(self, path):
        try:
            self.stop_runner(path)
        except RunnerError as e:
            logging.info(e.message)
        self.start_runner(path)

    def start_runner(self, path, config: RunnerConfig = None) -> Runner:
        config_path = str(Path(path).parent)
        if config is None:
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
        self._init_runner_runtime(self._get_config_from_runner(runner))
        runner.start(self.loop)
        self.runner_dict[path] = runner
        return runner

    def stop_runner(self, path, check_running: bool = False):
        runner = self.get_runner(path)
        try:
            down_runner_path = f"{path}.down"
            if "down" in enable_compatible_runit and Path(path).name != "down":
                down_runner_path = f"{Path(path).parent / 'down'}"
            RunnerManagerConfig._check_runner(down_runner_path)
            config = self._get_config_from_runner(runner)
            logging.info(f"Pre-run {down_runner_path}")
            down_runner = self.start_runner(down_runner_path, config=config)
            wait_count = 5
            while down_runner.is_running() and wait_count > 0:
                time.sleep(1)
                wait_count -= 1
            self.stop_runner(down_runner.path, check_running=True)
        except ManagerConfigError or RunnerError:
            pass
        # Stop the runner if check_running is False or the runner is running
        if not check_running or (check_running and runner.is_running()):
            runner.stop()
        self._pop_runner(runner)

    def send_signal_runner(self, path, signal):
        runner = self.get_runner(path)
        runner.send_signal(signal)

    def _pop_runner(self, runner):
        config = self._get_config_from_runner(runner)
        self._destroy_runner_runtime(config)
        del self.runner_dict[runner.path]

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
        delete_directory_and_empty_parents(Path(config.stdin).parent, tmp_path)
        delete_directory_and_empty_parents(Path(config.stdout).parent, tmp_path)
        delete_directory_and_empty_parents(Path(config.stderr).parent, tmp_path)
