from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .env import get_env
from .errors import RunnerConfigError
from .path_utils import search_file_by_keywords


@dataclass
class ConfigFrag:
    auto_restart: int
    stdin: str
    stdout: str
    stderr: str

    def update(
        self, auto_restart: int, stdin: str, stdout: str, stderr: str
    ) -> ConfigFrag:
        self.auto_restart = auto_restart
        if stdin:
            self.stdin = stdin
        if stdout:
            self.stdout = stdout
        if stderr:
            self.stderr = stderr
        return self


@dataclass
class RunnerConfig:
    args: list[str]
    env: dict[str, str]
    auto_restart: int
    stdin: str
    stdout: str
    stderr: str

    def update(
        self,
        args: list[str],
        env: list[str],
        auto_restart: int,
        stdin: str,
        stdout: str,
        stderr: str,
    ) -> RunnerConfig:
        for arg in args:
            if arg[:1] == "-" and arg[1:]:
                arg_key = arg[1:].strip()
                if arg_key in self.args:
                    self.args.remove(arg[1:])
                elif arg_key == "*":
                    self.args = []
            self.args.append(arg)
        self.env = self.env | env
        self.auto_restart = auto_restart
        self.stdin = stdin if stdin else self.stdin
        self.stdout = stdout if stdout else self.stdout
        self.stderr = stderr if stderr else self.stderr
        return self


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


def _parse_env(env_file: list[str], env: dict[str, str]) -> dict:
    for path in env_file:
        env = get_env(env, path)
    return env


def _parse_args(args_file: list[str], args: list[str]) -> list[str]:
    for path in args_file:
        with open(path) as f:
            for arg in f.readlines():
                if arg[:1] == "-" and arg[1:]:
                    arg_key = arg[1:].strip()
                    if arg_key in self.args:
                        args.remove(arg[1:])
                    elif arg_key == "*":
                        args = []
                args.append(arg)
    return args


def __get_single_config(key: str, config: str):
    if config.startswith(f"-{key}"):
        return False
    elif config.startswith(key + "="):
        return config[len(key) + 1 :].strip()
    return None


def _parse_config_frag(config_file: str):
    with open(config_file) as f:
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
        return auto_restart, stdin, stdout, stderr


def _get_runner_config_by_path(
        compound_word: str, config_path: str, runner_config: RunnerConfig
) -> RunnerConfig:
    config_frag = ConfigFrag(
        auto_restart=runner_config.auto_restart,
        stdin=runner_config.stdin,
        stdout=runner_config.stdout,
        stderr=runner_config.stderr,
    )

    keyword_dict = search_file_by_keywords(
        ["args", "env", "config"], config_path, compound_word, search_parent=True
    )

    config_path_list = keyword_dict["config"]
    for config_path in config_path_list:
        config_frag = config_frag.update(_parse_config_frag(config_path))
    args_path_list = keyword_dict["args"]
    args = _parse_args(args_path_list, runner_config.args)
    env_path_list = keyword_dict["env"]
    env = _parse_env(env_path_list, runner_config.env)

    return runner_config.update(
        args=args,
        env=env,
        auto_restart=config_frag.auto_restart,
        stdin=config_frag.stdin,
        stdout=config_frag.stdout,
        stderr=config_frag.stderr,
    )

def get_runner_config(
    runner_path: str, work_path: str, default_config_path: str, tmp_dir_path: str
) -> RunnerConfig:
    work_path = Path(work_path)
    compound_word = Path(runner_path).name
    default_config_path = Path(default_config_path)
    tmp_dir_path = Path(f"{tmp_dir_path}/{work_path}")
    buildin_default_config = get_default_config(work_path, std_path=tmp_dir_path / "std")

    setting_default_config = _get_runner_config_by_path(compound_word, default_config_path, buildin_default_config)

    runner_config = _get_runner_config_by_path(compound_word, work_path, setting_default_config)

    return runner_config
