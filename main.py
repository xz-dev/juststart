import logging
import argparse
from pathlib import Path

from .daemon import run_deamon, get_runner_manager
from .errors import BaseError



def get_password_from_config_path(config_path: str) -> bytes:
    password_path = Path(config_path).parent / "password"
    try:
        with open(password_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        password = ("".join(secrets.choice(alphabet) for i in range(20))).encode(
            "utf-8"
        )
        with open(password_path, "wb") as f:
            f.write(password)
        return password


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
        "--conf",
        type=str,
        help="Path to config file",
    )
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
    args = parser.parse_args()

    password = args.password
    if not password:
        password = get_password_from_config_path(config_path)

    if args.command:
        runner_manager = get_manager(address=(args.addr, args.port), authkey=password)
        try:
            path = args.path
            if args.command == "add":
                runner_manager.config_manager.add_runner(path)
            elif args.command == "del":
                runner_manager.config_manager.del_runner(path)
            elif args.command == "enable":
                runner_manager.config_manager.enable_runner(path)
            elif args.command == "disable":
                runner_manager.config_manager.disable_runner(path)
            elif args.command == "start":
                runner_manager.start_runner(path)
            elif args.command == "restart":
                runner_manager.restart_runner(path)
            elif args.command == "stop":
                runner_manager.stop_runner(path)
            elif args.command == "reload_config":
                runner_manager.reload_runner(path)
            elif args.command == "status":
                print(runner_manager.status_runner(path).status)
            else: logging.error("use --help to see available commands")
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
        print(dict(args))
        if not args.config:
            parser.print_help()
        else:
            config_path = args.config
            run_deamon(args.address, args.port, password, config_path)
