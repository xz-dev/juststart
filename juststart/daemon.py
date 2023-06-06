import asyncio
import logging
import signal
from multiprocessing.managers import BaseManager
from pathlib import Path
from threading import Thread

from .errors import BaseError
from .runner_manager import RunnerManager
from .runner_manager_config import RunnerManagerConfig


class MyManager(BaseManager):
    pass


class Utils:
    def __init__(self, runner_manager: RunnerManager):
        self.runner_manager = runner_manager

    def get_runner_status(self, path: str) -> dict:
        return self.runner_manager.get_runner(path).status_dict

    def shutdown(self):
        global shutdown
        shutdown = True


shutdown = False


def _handle_sigterm(signum, frame):
    global shutdown
    shutdown = True
    logging.warning("Received SIGTERM, shutting down...")


# 注册 SIGTERM 信号处理器
signal.signal(signal.SIGTERM, _handle_sigterm)


def get_manager(address: tuple[str, int], authkey: bytes) -> BaseManager:
    return MyManager(address=address, authkey=authkey)


def connect_manager(address: str, port: int, password: bytes) -> MyManager:
    MyManager.register("get_runner_manager")
    MyManager.register("get_runner_manager_config")
    MyManager.register("get_utils")
    manager = get_manager(address=(address, port), authkey=password)
    manager.connect()
    return manager


def get_objs(manager: MyManager) -> tuple[RunnerManager, RunnerManagerConfig, Utils]:
    return (
        manager.get_runner_manager(),
        manager.get_runner_manager_config(),
        manager.get_utils(),
    )


def test_is_running(address: str, port: int, password: bytes):
    try:
        get_objs(address, port, password)
        return True
    except:
        return False


async def cancel_all_tasks():
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)


def run_deamon(address: str, port: int, password: bytes, config_dir_path: str):
    global shutdown
    shutdown = False
    config_dir = Path(config_dir_path)

    # monkey patch
    monkey_patch_dir = config_dir / "monkey_patch"
    if monkey_patch_dir.exists():
        for patch_file in monkey_patch_dir.iterdir():
            exec(patch_file.read_text())

    runner_list_file_path = config_dir / "runner_list"
    default_runner_config_file_path = config_dir / "default"
    default_runner_config_file_path.mkdir(parents=True, exist_ok=True)
    tmp_dir_path = config_dir / "runtime_tmp"
    tmp_dir_path.mkdir(parents=True, exist_ok=True)
    runner_manager = RunnerManager(
        runner_list_file_path=str(runner_list_file_path),
        default_runner_config_path=str(default_runner_config_file_path),
        tmp_dir_path=str(tmp_dir_path),
    )
    utils = Utils(runner_manager)
    logging.warning("runner_manager: %s", runner_manager)
    MyManager.register("get_runner_manager", lambda: runner_manager)
    MyManager.register(
        "get_runner_manager_config", lambda: runner_manager.manager_config
    )
    MyManager.register("get_utils", lambda: utils)
    manager = get_manager(address=(address, port), authkey=password)
    server = manager.get_server()
    logging.warning("server: address=%s, port=%s", address, port)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        while server_thread.is_alive() and not shutdown:
            server_thread.join(timeout=1)
        logging.warning("Client ask shutdown")
    except KeyboardInterrupt:
        pass
    finally:
        logging.warning("Shutting down the server...")
        asyncio.run(cancel_all_tasks())
        runner_manager.stop_manager()
        logging.warning("Server stopped")
        logging.warning("Lock file deleted")
        logging.warning("Bye!")
