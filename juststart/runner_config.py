from pathlib import Path
from dataclasses import dataclass
from .env import get_env
from .errors import RunnerConfigError


@dataclass
class RunnerConfig:
    args: list[str]
    env: dict
    auto_restart: float
    stdin: str
    stdout: str
    stderr: str

    def plus(self, other: "RunnerConfig") -> "RunnerConfig":
        args = self.args
        for arg in self.other:
            if arg[:2] == "- " and arg[2:] in args:
                args.remove(arg[2:])
            else:
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


def _get_default_config(work_path: Path):
    path = Path(work_path)
    return RunnerConfig(
        args=[],
        env={},
        auto_restart=0,
        stdin=path / "stdin",
        stdout=path / "stdout",
        stderr=path / "stderr",
    )


def get_runner_config(path, base_config: RunnerConfig = None) -> RunnerConfig:
    if base_config is None:
        base_config = _get_default_config(path)
    return _get_runner_config(Path(path), base_config)


def _get_runner_config(work_path: Path, base_config: RunnerConfig) -> RunnerConfig:
    parent = work_path.parent
    if (
        (parent / "args").exists()
        or (parent / "env").exists()
        or (parent / "conf").exists()
    ):
        base_config = __get_runner_config(work_path, base_config)
        return _get_runner_config(parent, base_config)
    else:
        return base_config


def __get_runner_config(path: Path, base_config: RunnerConfig):
    try:
        with open(path / "args") as f:
            args = f.readlines()
    except FileNotFoundError:
        args = base_config.args
    env = base_config.env
    auto_restart = base_config.auto_restart
    stdin = base_config.stdin
    stdout = base_config.stdout
    stderr = base_config.stderr

    config_list = __get_runner_config(path / "conf")
    for config in config_list:
        try:
            auto_restart = __get_single_config("auto_restart", config)
            if auto_restart == False:
                auto_restart = -1
            if type(auto_restart) == str:
                auto_restart = float(auto_restart)
            else:
                raise RunnerConfigError(
                    "auto_restart must be -auto_restart or auto_restart or auto_restart=<seconds>"
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

    return base_config.plus(
        RunnerConfig(
            args=args,
            env=get_env(env, path / "env"),
            auto_restart=auto_restart,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
    )
