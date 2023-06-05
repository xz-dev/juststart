import shutil
import logging
from pathlib import Path

from .errors import ManagerConfigError
from .runner_manager import RunnerManagerStatus
from .runner_manager_config import RunnerManagerConfig


def print_screen_divider():
    cols = shutil.get_terminal_size().columns
    print(f"{'-' * cols}")


def pretty_print_str(obj, indent=0) -> str:
    result = ""
    if isinstance(obj, dict):
        for key, value in obj.items():
            result += "  " * indent + str(key) + ": "
            value_result = pretty_print_str(value, indent + 1)
            if isinstance(value, dict) or isinstance(value, list):
                result += "\n"
            else:
                value_result = value_result.strip()
            result += value_result + "\n"
    elif isinstance(obj, list):
        for item in obj:
            result += pretty_print_str(item, indent + 1) + "\n"
    else:
        result += "  " * indent + str(obj)
    return result


def pretty_print(obj, indent=0) -> str:
    return print(pretty_print_str(obj, indent))


def get_password_from_config_path(config_path: str) -> bytes:
    password_path = Path(config_path) / "password"
    try:
        with open(password_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        logging.warning("Password file not found, generating a new one")
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        password = ("".join(secrets.choice(alphabet) for i in range(20))).encode(
            "utf-8"
        )
        with open(password_path, "wb") as f:
            f.write(password)
        logging.warning("Password file saved to %s", password_path)
        return password


def get_expanduser_path(path) -> str:
    return str(Path(path).expanduser())


def get_absolute_path(path) -> str:
    return str(Path(path).resolve(strict=True))


def runner_status_dict_to_str(
    runner_status_dict: dict[str, list[RunnerManagerStatus]]
) -> str:
    result = ""
    for path, status_list in runner_status_dict.items():
        result_list = [f"{path}:"]
        if RunnerManagerStatus.INITED_BUT_NOT_SAVED in status_list:
            result_list.append("[volatile]")
        if RunnerManagerStatus.RUNNING in status_list:
            result_list.append("running")
        elif RunnerManagerStatus.NOT_RUNNING in status_list:
            if RunnerManagerStatus.INITED in status_list:
                result_list.append("[gc]")
            else:
                result_list.append("stopped")
        if RunnerManagerStatus.ENABLED_BOOT in status_list:
            result_list.append("boot")
        if len(result_list) == 1:
            result_list.append("[idle]")
        try:
            RunnerManagerConfig._check_runner(path)
        except ManagerConfigError:
            result_list.append("[broken]")
        result_list.append("\n")
        result += " ".join(result_list)
    return result[:-1]
