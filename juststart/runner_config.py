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
        args = self.args
        for arg in self.other:
            if arg[:2] == "- " and arg[2:] in args:
                args.remove(arg[2:])
            args.append(arg)
        return RunnerConfig(
            args=args,
            env=other.env,
            auto_restart=other.auto_restart,
            stdin=other.stdin,
            stdout=other.stdout,
            stderr=other.stderr,
        )


def __get_runner_config(path) -> list[str]:
    try:
        with open(path) as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def __get_single_config(key: str, config: str):
    if config[:6] == f"-{key}":
        return False
    elif config[: len(key)] == key:
        return config[6:].split("=", maxsplit=1)
        if split == 2:
            return split[1:] if split[1:] == " " else split
        else:
            if default_enable_value is not None:
                return default_enable_value
            else:
                return True
    raise KeyError


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
            for line in r.readline():
                try:
                    auto_restart = __get_single_config("auto_restart", line)
                    if auto_restart == False:
                        auto_restart = -1
                    if type(auto_restart) == str:
                        auto_restart = int(auto_restart)
                    else:
                        raise RunnerConfigError(
                            "auto_restart must be -auto_restart or auto_restart or auto_restart=<seconds>"
                        )
                except KeyError:
                    pass
                try:
                    stdin = __get_single_config("stdin", line)
                    if stdin == False:
                        stdin = None
                    elif type(stdin) != str:
                        raise RunnerConfigError("stdin must be -stdin or stdin=<path>")
                except KeyError:
                    pass
                try:
                    stdout = __get_single_config("stdout", line)
                    if stdout == False:
                        stdout = None
                    elif type(stdout) != str:
                        raise RunnerConfigError(
                            "stdout must be -stdout or stdout=<path>"
                        )
                except KeyError:
                    pass
                try:
                    stderr = __get_single_config("stderr", line)
                    if stderr == False:
                        stderr = None
                    elif type(stderr) != str:
                        raise RunnerConfigError(
                            "stderr must be -stderr or stderr=<path>"
                        )
                except KeyError:
                    pass
    except FileNotFoundError:
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
    parent = work_path.parent
    if (
        (parent / "args").exists()
        or (parent / "env").exists()
        or (parent / "conf").exists()
    ):
        return base_config.plus(read_runner_config(work_path, env=base_config.env))
    else:
        return base_config


def get_runner_config(
    work_path: str, default_config_path: str, tmp_dir_path: str
) -> RunnerConfig:
    default_config_path = Path(default_config_path)
    work_path = Path(work_path)
    tmp_dir_path = Path(f"{tmp_dir_path}/{work_path}")
    if any(default_config_path.iterdir()):
        base_config = read_runner_config(default_config_path)
    else:
        base_config = get_default_config(work_path, std_path=tmp_dir_path / "std")
    return _get_runner_config(work_path, base_config)
