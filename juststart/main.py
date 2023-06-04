import argparse
import logging
from pathlib import Path

from .cli_utils import *
from .daemon import Utils, connect_manager, get_objs, run_deamon
from .errors import BaseError
from .runner_manager import RunnerManager
from .runner_manager_config import RunnerManagerConfig


def main():
    parser = argparse.ArgumentParser(
        description="A simple yet extensible cross-platform service manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    # juststart --address <service_address>
    parser.add_argument(
        "--address",
        "--addr",
        type=str,
        default="localhost",
        help="Service manager listen address",
    )
    # juststart --port <service_port>
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=50000,
        help="Service manager listen port number",
    )
    # juststart --password <password>
    parser.add_argument(
        "--password",
        type=str,
        help="Service manager password",
    )
    # juststart --config <config_path>
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to config file",
    )
    # juststart deamon
    subparsers.add_parser("serve", help="Run as a daemon")

    # juststart add <path>
    add_parser = subparsers.add_parser("add", help="Add a service")
    add_parser.add_argument("path")

    # juststart del <path>
    del_parser = subparsers.add_parser("del", help="Delete a service")
    del_parser.add_argument("path")

    # juststart enable <path>
    enable_parser = subparsers.add_parser("enable", help="Enable a service")
    enable_parser.add_argument("path")

    # juststart disable <path>
    disable_parser = subparsers.add_parser("disable", help="Disable a service")
    disable_parser.add_argument("path")

    # juststart start <path>
    start_parser = subparsers.add_parser("start", help="Start a service")
    start_parser.add_argument("path")

    # juststart restart <path>
    restart_parser = subparsers.add_parser("restart", help="Restart a service")
    restart_parser.add_argument("path")

    # juststart stop <path>
    stop_parser = subparsers.add_parser("stop", help="Stop a service")
    stop_parser.add_argument("path")

    # juststart reload_config <path>
    reload_config_parser = subparsers.add_parser(
        "reload_config", help="Reload config for a service"
    )
    reload_config_parser.add_argument("path")

    # juststart status <path>
    status_parser = subparsers.add_parser("status", help="Status of a service")
    status_parser.add_argument("path")

    # juststart list
    status_parser = subparsers.add_parser("list", help="List all services")
    # juststart gc
    status_parser = subparsers.add_parser(
        "gc", help="Garbage collect for stoped services"
    )

    # juststart shutdown
    status_parser = subparsers.add_parser("shutdown", help="Shutdown Daemon")

    args = parser.parse_args()

    def get_config_path() -> str or None:
        config_path = None
        try:
            config_path = args.config
        except AttributeError:
            pass
        if not config_path:
            logging.error("No config file specified")
        elif not Path(config_path).is_dir():
            logging.error("Config file must be a directory")
        else:
            return config_path

    password = args.password
    if password is None:
        config_path = get_config_path()
        if not config_path:
            raise SystemError("If password is not provided, config path must be provided")
        password = get_password_from_config_path(config_path)

    command = args.command
    if command:
        if command == "serve":
            config_path = get_config_path()
            if config_path:
                run_deamon(args.address, args.port, password, config_path)
                return

        share_manager = connect_manager(
            address=args.address, port=args.port, password=password
        )
        runner_manager, manager_config, utils = get_objs(share_manager)
        runner_manager: RunnerManager
        manager_config: RunnerManagerConfig
        uitls: Utils
        if command == "shutdown":
            utils.shutdown()
        elif command == "list":
            print(runner_status_dict_to_str(runner_manager.get_runner_status_dict()))
        elif command == "gc":
            print("\n".join(runner_manager.clean_runner()))
        else:
            path = get_absolute_path(args.path)
            try:
                if command == "add":
                    manager_config.add_runner(path)
                elif command == "del":
                    manager_config.delete_runner(path)
                elif command == "enable":
                    manager_config.enable_runner(path)
                elif command == "disable":
                    manager_config.disable_runner(path)
                elif command == "start":
                    runner_manager.start_runner(path)
                elif command == "restart":
                    runner_manager.restart_runner(path)
                elif command == "stop":
                    runner_manager.stop_runner(path)
                elif command == "reload_config":
                    runner_manager.reload_runner(path)
                elif command == "status":
                    print(utils.get_runner_status(path))
                else:
                    logging.error("Unknown command")
                    return
            except BaseError as e:
                message = e.message
                if e.level == "debug":
                    logging.debug(message)
                elif e.level == "info":
                    print(message)
                elif e.level == "warning":
                    logging.warning(message)
                elif e.level == "error":
                    logging.error(message)
    else:
        parser.print_help()
        raise SystemError("No command specified")
