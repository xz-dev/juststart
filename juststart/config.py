import os

_lowercase_env_vars = {k.lower(): v for k, v in os.environ.items()}

# runit: down
enable_compatible_runit = (
    _lowercase_env_vars.get("compatible_runit", "").lower().split(",")
)
