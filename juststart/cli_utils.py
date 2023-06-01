from pathlib import Path

from .runner_manager import RunnerManagerStatus


def get_password_from_config_path(config_path: str) -> bytes:
    password_path = Path(config_path).parent / "password"
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


def get_absolute_path(path) -> str:
    return str(Path(path).expanduser().resolve())


def runner_status_dict_to_str(
    runner_status_dict: dict[str, list[RunnerManagerStatus]]
) -> str:
    result = ""
    for path, status_list in runner_status_dict.items():
        result += f"{path}:\n"
        for status in status_list:
            result += f"    {status}\n"
    return result
