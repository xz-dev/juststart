import subprocess


def get_env(env_file=None):
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
    process = subprocess.run(*args, stdout=subprocess.PIPE)
    return process.env
