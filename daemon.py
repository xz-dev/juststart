import logging
from multiprocessing.managers import BaseManager
from .runner_manager import RunnerManager
from .errors import BaseError


class MyManager(BaseManager):
    pass


def runner_wrapper(func) -> tuple[int, str]:
    try:
        return (logging.INFO, func())
    except BaseError as e:
        level = None
        message = e.message
        if e.level == "debug":
            level = logging.DEBUG
            logging.debug(message)
        elif e.level == "info":
            level = logging.INFO
            logging.info(message)
        elif e.level == "warning":
            level = logging.WARNING
            logging.warning(message)
        elif e.level == "error":
            level = logging.ERROR
            logging.error(message)
        return (level, message)


def run_deamon(address: str, port: int, password: bytes, config_path: str):
    default_runner_config_file_path = Path(config_path).parent / "default_runner_config"
    runner_manager = RunnerManager(
        args.config_path, str(default_runner_config_file_path)
    )

    MyManager.register('get_runner_manager', runner_manager)
    manager = MyManager(address=(args.addr, args.port), authkey=password)
    server = manager.get_server()
    server.serve_forever()
