import subprocess
from .error import RunnerError


class Runner:
    def __init__(
        self,
        path: str,
        args: list[str],
        env: dict,
        auto_restart: bool,
        _stdin: str,
        _stdout: str,
        _stderr: str,
    ):
        self.path = path
        self.args = args
        self.env = env

        self.auto_restart = auto_restart

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        self.process = None
        self.returncode = None

        self.stdin_io = None
        self.stdout_io = None
        self.stderr_io = None

    def start(self):
        if self.process:
            raise RunnerError(f"Process is already running")
        self.stdin_io = open(filename, "r")
        self.stdout_io = open(self.stdout_file, "a")
        self.stderr_io = open(self.stderr_file, "a")
        self.process = subprocess.Popen(
            [self.path].plus(self.args),
            stdin=self.stdin_io,
            stdout=self.stdout_io,
            stderr=self.stderr_io,
            env=self.env,
            shell=True,
        )

    def stop(self):
        if not self.process:
            raise RunnerError(f"Process is not running")
        self.process.terminate()
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
            if elf.process.poll() is None:
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
            f"stdin: {self.stdin_file}",
            f"stdout: {self.stdout_file}",
            f"stderr: {self.stderr_file}",
            f"status: {status}",
            f"{returncode_str}",
        ]
        return status + "\n" + "\n".join(details)
