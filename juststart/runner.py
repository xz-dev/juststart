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
        auto_restart: float,
        stdin: str,
        stdout: str,
        stderr: str,
    ):
        self.path = path
        self.args = args
        self.env = env

        self.auto_restart = auto_restart
        self.booted_num = 0

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        self.process = None
        self.returncode = None

        self.stdin_io = None
        self.stdout_io = None
        self.stderr_io = None

    def start(self, loop: asyncio.AbstractEventLoop):
        self._start()
        self.start_monitoring(loop)

    def start_monitoring(self, loop: asyncio.AbstractEventLoop):
        async def monitor():
            while True:
                if self.auto_restart < 0:
                    break
                if not self.is_running():
                    if self.auto_restart > 0:
                        await asyncio.sleep(self.auto_restart)
                    await asyncio.to_thread(self._start)
                await asyncio.sleep(0.1)

        future = asyncio.run_coroutine_threadsafe(monitor(), loop)
        return future

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

    def stop(self):
        if not self.is_running():
            raise RunnerError(f"Process is not running")
        self.process.terminate()
        self.process.wait()
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

    @stdin.setter
    def stdout(self, path):
        old_stdout_io = self.stdout_io
        if self.process and path:
            self.stdout_io = open(path, "a")
            self.process.stdout = self.stdout
        if old_stdout_io and not old_stdout_io.closed:
            old_stdout_io.close()

    @stdin.setter
    def stderr(self, path):
        old_stderr_io = self.stderr_io
        if self.process and path:
            self.stderr_io = open(path, "a")
            self.process.stderr = self.stderr
        if old_stderr_io and not old_stderr_io.closed:
            old_stderr_io.close()

    @property
    def status_str(self) -> str:
        if self.process:
            if self.process.poll() is None:
                status = "Running"
                returncode_str = f"last returncode: {self.returncode}"
            else:
                status = "Stopped"
                returncode_str = f"returncode: {self.returncode}"
        else:
            status = "Never run"
            returncode_str = f"returncode: {self.returncode}"
        details = [
            f"path: {self.path}",
            f"args: {self.args}",
            f"env: {self.env}",
            f"auto_restart: {self.auto_restart}",
            f"booted_num: {self.booted_num}",
            f"stdin: {self.stdin}",
            f"stdout: {self.stdout}",
            f"stderr: {self.stderr}",
            f"status: {status}",
            f"{returncode_str}",
        ]
        return status + "\n" + "\n".join(details)
