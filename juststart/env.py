import os
import subprocess


def _parse_env_output(output):
    env_vars = {}
    lines = output.strip().split("\n")
    for line in lines:
        if line.strip():
            key, value = line.strip().split("=", 1)
            env_vars[key] = value
    return env_vars


def get_env(base_env: dict[str, any], env_file=None):
    args = []
    if os.name == "posix":
        args.append("env")
    elif os.name in ["nt", " ce"]:
        args.append("set")
    try:
        disable_envs = []
        with open(env_file) as f:
            for line in f.readlines():
                line = line.strip()
                if line[0] == "+" and line[1:]:
                    env_key = line[1:].strip()
                    if env_key == "*":
                        base_env = os.environ | base_env
                    else:
                        base_env[env_key] = os.getenv(env_key)
                elif line[0] == "-" and line[1:]:
                    env_key = line[1:].strip()
                    if env_key == "*":
                        return {}
                    else:
                        disable_envs.append(env_key)
                else:
                    if line[:2] in ["\+", "\-"]:
                        line = line[1:]
                    args.append(line)
    except FileNotFoundError:
        pass
    cmd = args[0]
    cmd_args = args[1:]
    process = subprocess.run([cmd, *cmd_args], env=base_env, stdout=subprocess.PIPE)
    return {
        key: value
        for key, value in _parse_env_output(process.stdout.decode("utf-8")).items()
        if key not in disable_envs
    }
