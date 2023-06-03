from time import time
import asyncio
import subprocess
from pathlib import Path
from .errors import RunnerError


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
    ):
        self.path = path
        self._args = args
        self.env = env

        self.auto_restart = auto_restart
        self.booted_num = 0
        self.boot_lock = asyncio.Lock()
        self.blocked_num = 0
        self.blocked_time = 0
        self.blocked_program = None

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        self.process = None
        self.returncode = None

        self.stdin_io = None
        self.stdout_io = None
        self.stderr_io = None

    def start(self, loop: asyncio.AbstractEventLoop):
        self.start_monitoring(loop)

    def start_monitoring(self, loop: asyncio.AbstractEventLoop):
        async def monitor():
            if self.boot_lock.locked():
                return
            async with self.boot_lock:
                self.auto_restart += 1
                while self.auto_restart > 0:
                    await self._check_blocker_list()
                    if not self.is_running():
                        await asyncio.to_thread(self._start)
                        self.auto_restart -= 1
                    await asyncio.sleep(0.1)

        future = asyncio.run_coroutine_threadsafe(monitor(), loop)
        return future

    async def _check_blocker(self, path: str):
        self.blocked_program = path
        self.blocked_time = time()
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
            self.blocked_program = e
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
            await self._check_blocker(path)

    async def _check_blocker_list(self):
        path = Path(self.path).parent / "blocker"
        if path.exists():
            if path.is_dir():
                for blocker in path.iterdir():
                    await self._check_blocker(blocker)
            else:
                await self._check_blocker(path)

    def _start(self):
        if self.is_running():
            raise RunnerError(f"Process is already running")
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
        self.booted_num += 1

    def _shutdown(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            import os
            os.kill(self.process.pid, signal.SIGKILL)
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.error(f"Failed to kill process {self.process.pid}")

    def stop(self):
        if not self.is_running():
            raise RunnerError(f"{self.path} is not running")
        self._shutdown()
        self.returncode = self.process.returncode
        if self.stdin_io and not self.stdin_io.closed:
            self.stdin_io.close()
        if self.stdout_io and not self.stdout_io.closed:
            self.stdout_io.close()
        if self.stderr_io and not self.stderr_io.closed:
            self.stderr_io.close()

    def send_signal(self, signal):
        if not self.process:
            raise RunnerError("Process is not running")
        self.process.send_signal(signal)

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
    def status_str(self) -> str:
        if self.is_blocking():
            status = f"Booting(blocked: {self.blocked_num})"
            ext_str = f"blocked_time: {self.blocked_time}\n"
            ext_str += f"blocked_program: {self.blocked_program}"
        elif self.booted_num > 0:
            if self.is_running():
                status = "Running"
                ext_str = f"last returncode: {self.returncode}"
            else:
                status = "Stopped"
                ext_str = f"returncode: {self.returncode}"
        else:
            status = "Never run"
            ext_str = f"returncode: {self.returncode}"
        details = [
            f"path: {self.path}",
            f"args: {self.args}",
            f"env: {self.env}",
            f"auto_restart: {self.auto_restart}",
            f"booted_num: {self.booted_num}",
            f"stdin: {self.stdin}",
            f"stdout: {self.stdout}",
            f"stderr: {self.stderr}",
            f"",
            f"status: {status}",
            f"{ext_str}",
        ]
        return status + "\n" + "\n".join(details)
