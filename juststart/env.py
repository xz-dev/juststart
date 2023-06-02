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
        with open(env_file) as f:
            for line in f.readlines():
                args.append(line)
    except FileNotFoundError:
        pass
    process = subprocess.run(*args, env=base_env, stdout=subprocess.PIPE)
    return _parse_env_output(process.stdout.decode("utf-8"))
