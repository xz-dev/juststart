from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from time import time
from typing import Callable

from .errors import RunnerError
from .runner_status import *


class Runner:
    def __init__(
        self,
        path: str,
        args: list[str],
        env: dict,
        auto_restart: int,
        stdin: str,
        stdout: str,
        stderr: str,
        status_changed_hook: Callable[[Runner, RunnerStatus], None],
    ):
        self.path = path
        self._args = args
        self.env = env

        self.auto_restart = auto_restart

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        self._status = None
        self._status_changed_hook = status_changed_hook

        self.booted_num = 0
        self.blocked_num = 0

        self.process = None
        self.returncode = None

        self.stdin_io = None
        self.stdout_io = None
        self.stderr_io = None

    @property
    def status(self) -> RunnerStatus:
        return self._status

    @status.setter
    def status(self, status: RunnerStatus):
        if self._status and self._status.key == status.key:
            raise RunnerError(f"Status is already {status.key}")
        self._status = status
        self._status_changed_hook(self, status)

    @property
    def pid(self) -> int:
        return self.process.pid if self.process else None

    def _set_status(self, status_key: str, data: dict[str, any] = {}):
        self.status = RunnerStatus(status_key, data | {"changed_time": time()})

    def _update_status(self, data: dict[str, any], deleted_keys: list[str] = []):
        self.status = RunnerStatus(
            self.status.key,
            {
                key: value
                for key, value in (self.status.data | data).items()
                if key not in deleted_keys
            },
        )

    def start(self, loop: asyncio.AbstractEventLoop):
        self._set_status(BOOTING)
        self.start_monitoring(loop)

    def start_monitoring(self, loop: asyncio.AbstractEventLoop):
        async def monitor():
            self.auto_restart += 1
            while self.auto_restart > 0 or self.auto_restart == -1:
                await self._check_blocker_list()
                if not self.is_running():
                    await asyncio.to_thread(self._start)
                    self.auto_restart -= 1
                await asyncio.sleep(0.1 if self.auto_restart > 0 else 1)

        future = asyncio.run_coroutine_threadsafe(monitor(), loop)
        return future

    async def _check_blocker(self, path: str):
        self.blocked_program = path
        self.blocked_time = time()
        self._update_status(
            {"blocked_program": path, "blocked_time": self.blocked_time},
        )
        try:
            process = await asyncio.create_subprocess_exec(
                path,
                *self.args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path(path).parent),
                env=self.env,
            )
        except Exception as e:
            self._update_status({"error": e})
        try:
            stdout, stderr = await process.communicate()
            sleep_time = int(stdout)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.blocked_num += 1
            else:
                pass
        except ValueError:
            pass
        if process.returncode != 0:
            if self.status.data["blocked_program"] == path:
                self._update_status(
                    {
                        "blocked_run_num": self.status.data["blocked_run_num"] + 1
                        if "blocked_run_num" in self.status.data
                        else 1,
                    },
                )
            await self._check_blocker(path)

    async def _check_blocker_list(self):
        path = Path(self.path).parent / "blocker"
        if path.exists():
            block_list = [path]
            if path.is_dir():
                block_list = path.iterdir()
            self._set_status(
                BLOCKING,
                {"block_list": block_list},
            )
            for blocker in block_list:
                await self._check_blocker(blocker)

    def _start(self):
        if self.is_running():
            raise RunnerError(f"Process is already running")
        self._set_status(RUNNING_READY)
        self.stdin_io = open(self.stdin, "a+")
        self.stdin_io.seek(0)
        self.stdout_io = open(self.stdout, "a")
        self.stderr_io = open(self.stderr, "a")
        self.process = subprocess.Popen(
            [self.path] + self.args,
            cwd=str(Path(self.path).parent),
            stdin=self.stdin_io,
            stdout=self.stdout_io,
            stderr=self.stderr_io,
            env=self.env,
        )
        self._set_status(RUNNING)
        self.booted_num += 1

    def _shutdown(self):
        self._update_status({"shutdown_command": "SIGTERM"})
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._update_status({"shutdown_command": "SIGKILL"})
            self.process.kill()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            import os

            self._update_status({"shutdown_command": "SIGKILL_OS"})
            os.kill(self.process.pid, signal.SIGKILL)
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._update_status({"error": "kill_fail"})
            logger.error(f"Failed to kill process {self.pid}")

    def stop(self):
        if not self.is_running():
            raise RunnerError(f"{self.path} is not running")
        self._set_status(STOPPING)
        self._shutdown()
        self._set_status(STOPPED)
        self.returncode = self.process.returncode
        if self.stdin_io and not self.stdin_io.closed:
            self.stdin_io.close()
        if self.stdout_io and not self.stdout_io.closed:
            self.stdout_io.close()
        if self.stderr_io and not self.stderr_io.closed:
            self.stderr_io.close()
        self._set_status(DISTROYED)

    def send_signal(self, signal):
        if self.is_running():
            raise RunnerError("Process is not running")
        self._set_status(SIGNAL_READY, {"signal": signal})
        self.process.send_signal(signal)
        self._set_status(SIGNAL_SENT, {"signal": signal})

    def is_running(self):
        if self.process:
            return self.process.poll() is None
        else:
            return False

    def is_blocking(self):
        return self.boot_lock.locked() and not self.is_running()

    @property
    def args(self):
        args = []
        for arg in self._args:
            if arg[:2] == "- " and arg[2:]:
                pass
            else:
                args.append(arg)
        return self._args

    @property
    def stdin(self):
        return self._stdin

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    @stdin.setter
    def stdin(self, path):
        old_stdin_io = self.stdin_io
        if self.process and path:
            self.stdin_io = open(path, "r")
            self.process.stdin = self.stdin
        if old_stdin_io and not old_stdin_io.closed:
            old_stdin_io.close()

    @stdout.setter
    def stdout(self, path):
        old_stdout_io = self.stdout_io
        if self.process and path:
            self.stdout_io = open(path, "a")
            self.process.stdout = self.stdout
        if old_stdout_io and not old_stdout_io.closed:
            old_stdout_io.close()

    @stderr.setter
    def stderr(self, path):
        old_stderr_io = self.stderr_io
        if self.process and path:
            self.stderr_io = open(path, "a")
            self.process.stderr = self.stderr
        if old_stderr_io and not old_stderr_io.closed:
            old_stderr_io.close()

    @property
    def status_dict(self) -> dict:
        return {
            "status": self.status.to_dict(),
            "path": self.path,
            "args": self.args,
            "env": self.env,
            "auto_restart": self.auto_restart,
            "booted_num": self.booted_num,
            "stdin": self.stdin,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }

    def wait(self):
        if self.is_running():
            self.process.wait()
        else:
            raise RunnerError(f"{self.path} is not running")
