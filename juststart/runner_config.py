from pathlib import Path
from dataclasses import dataclass
from .env import get_env
from .errors import RunnerConfigError


@dataclass
class RunnerConfig:
    args: list[str]
    env: dict
    auto_restart: bool
    stdin: str
    stdout: str
    stderr: str


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


def get_runner_config(path, default_config: RunnerConfig = None):
    parent = Path(path)
    try:
        with open(parent / "args") as f:
            args = f.readlines()
    except FileNotFoundError:
        args = []
    auto_restart = True
    stdin = parent / "stdin"
    stdout = parent / "stdout"
    stderr = parent / "stderr"
    if default_config is not None:
        args = default_config.args
        auto_restart = default_config.auto_restart
        stdin = default_config.stdin
        stdout = default_config.stdout
        stderr = default_config.stderr

    config_list = __get_runner_config(parent / "conf")
    for config in config_list:
        try:
            auto_restart = __get_single_config("auto_restart", config)
            if type(auto_restart) != bool:
                raise RunnerConfigError(
                    "auto_restart must be -auto_restart or auto_restart"
                )
        except KeyError:
            pass
        try:
            stdin = __get_single_config("stdin", config)
            if stdin == False:
                stdin = None
            elif type(stdin) != str:
                raise RunnerConfigError("stdin must be -stdin or stdin=<path>")
        except KeyError:
            pass
        try:
            stdout = __get_single_config("stdout", config)
            if stdout == False:
                stdout = None
            elif type(stdout) != str:
                raise RunnerConfigError("stdout must be -stdout or stdout=<path>")
        except KeyError:
            pass
        try:
            stderr = __get_single_config("stderr", config)
            if stderr == False:
                stderr = None
            elif type(stderr) != str:
                raise RunnerConfigError("stderr must be -stderr or stderr=<path>")
        except KeyError:
            pass

    return RunnerConfig(
        args=args,
        env=get_env(parent / "env"),
        auto_restart=auto_restart,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
