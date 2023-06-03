from dataclasses import dataclass
from pathlib import Path

from .env import get_env
from .errors import RunnerConfigError


@dataclass
class RunnerConfig:
    args: list[str]
    env: dict
    auto_restart: int
    stdin: str
    stdout: str
    stderr: str

    def plus(self, other: "RunnerConfig") -> "RunnerConfig":
        args = other.args
        for arg in args:
            if arg[:1] == "-" and arg[1:]:
                arg_key = arg[1:].strip()
                if arg_key in self.args:
                    self.args.remove(arg[1:])
                elif arg_key == "*":
                    self.args = []
            self.args.append(arg)
        return RunnerConfig(
            args=self.args,
            env=self.env | other.env,
            auto_restart=other.auto_restart,
            stdin=other.stdin if other.stdin else self.stdin,
            stdout=other.stdout if other.stdout else self.stdout,
            stderr=other.stderr if other.stderr else self.stderr,
        )


def __get_runner_config(path) -> list[str]:
    try:
        with open(path) as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def __get_single_config(key: str, config: str):
    if config.startswith(f"-{key}="):
        return False
    elif config.startswith(key + "="):
        return config[len(key) + 1 :].strip()
    return None


def get_default_config(work_path: Path, std_path: Path):
    path = Path(work_path)
    return RunnerConfig(
        args=[],
        env={},
        auto_restart=1,
        stdin=std_path / "in",
        stdout=std_path / "log",
        stderr=std_path / "log",
    )


def read_runner_config(path: Path, env={}) -> RunnerConfig:
    try:
        with open(path / "args") as f:
            args = f.readlines()
    except FileNotFoundError:
        args = []
    env = get_env(env, path / "env")
    auto_restart = 0
    stdin = None
    stdout = None
    stderr = None
    try:
        with open(path / "config") as f:
            for line in r.readlines():
                auto_restart_value = __get_single_config("auto_restart", line)
                if auto_restart_value is not None:
                    if auto_restart_value == False:
                        auto_restart = 0
                    else:
                        auto_restart = int(auto_restart_value)
                stdin_value = __get_single_config("stdin", line)
                if stdin_value is not None:
                    stdin = stdin_value if stdin_value != False else None
                stdout_value = __get_single_config("stdout", line)
                if stdout_value is not None:
                    stdout = stdout_value if stdout_value != False else None
                stderr_value = __get_single_config("stderr", line)
                if stderr_value is not None:
                    stderr = stderr_value if stderr_value != False else None
    except FileNotFoundError:
        pass
    except IsADirectoryError:
        pass
    return RunnerConfig(
        args=args,
        env=env,
        auto_restart=auto_restart,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


def _get_runner_config(work_path: Path, base_config: RunnerConfig) -> RunnerConfig:
    if work_path == work_path.parent:
        # We reached the root directory
        return base_config

    parent_config = _get_runner_config(work_path.parent, base_config)

    if (
        (work_path / "args").exists()
        or (work_path / "env").exists()
        or (work_path / "config").exists()
    ):
        current_config = read_runner_config(work_path, env=parent_config.env)
        return parent_config.plus(current_config)
    else:
        return parent_config


def get_runner_config(
    work_path: str, default_config_path: str, tmp_dir_path: str
) -> RunnerConfig:
    default_config_path = Path(default_config_path)
    work_path = Path(work_path)
    tmp_dir_path = Path(f"{tmp_dir_path}/{work_path}")
    default_config = get_default_config(work_path, std_path=tmp_dir_path / "std")
    if any(default_config_path.iterdir()):
        base_config = read_runner_config(default_config_path).plus(default_config)
    else:
        base_config = default_config
    return _get_runner_config(work_path, base_config)
