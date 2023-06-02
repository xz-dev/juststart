import logging
from threading import Thread
from pathlib import Path
from asyncio import new_event_loop
from concurrent.futures import ThreadPoolExecutor

from .errors import RunnerError
from .runner import Runner
from .runner_config import get_runner_config
from .runner_manager_config import RunnerManagerConfig


class RunnerManagerStatus:
    INITED = "INITED"
    NOT_INITED = "NOT_INITED"

    ENABLED_BOOT = "ENABLED_BOOT"
    DISABLED_BOOT = "DISABLED_BOOT"

    INITED_BUT_NOT_SAVED = "INITED_BUT_NOT_SAVED"

    RUNNING = "RUNNING"
    NOT_RUNNING = "NOT_RUNNING"


class RunnerManager:
    def __init__(self, runner_list_file_path, default_runner_config_path):
        monitor_executor = ThreadPoolExecutor()
        self.loop = new_event_loop()
        self.loop.set_default_executor(monitor_executor)
        self.start_manager()

        self.default_runner_config_path = default_runner_config_path
        self.manager_config = RunnerManagerConfig(runner_list_file_path)
        self.runner_dict = dict()
        self._load_runners()

    def _load_runners(self):
        runners_dict = self.runner_dict
        for path, enabled in self.manager_config.runner_info_dict.items():
            if enabled:
                self.start_runner(path)

    def start_manager(self):
        def run_event_loop(loop):
            loop.run_forever()

        self.event_loop_thread = Thread(target=run_event_loop, args=(self.loop,))
        self.event_loop_thread.start()

    def stop_manager(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.event_loop_thread.join()
        self.loop.close()

    def get_runner_status_dict(self) -> dict[str, set[RunnerManagerStatus]]:
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
            runner_status_dict[path] = sorted(status_list)
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
            runner_status_dict[runner.path] = sorted(status_list)
        return sorted(runner_status_dict)

    def reload_runner(self, path: str):
        runner = self.get_runner(path)
        config_path = str(Path(path).parent)
        config = get_runner_config(config_path)
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
            config = get_runner_config(
                config_path,
                base_config=get_runner_config(self.default_runner_config_path),
            )
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
        runner.start(self.loop)

    def clean_runner(self):
        for path, runner in self.runner_dict.items():
            if not runner.is_running():
                self.runner_dict.pop(path)

    def stop_runner(self, path):
        runner = self.get_runner(path)
        runner.stop()
