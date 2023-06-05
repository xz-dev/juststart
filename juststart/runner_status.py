from enum import Enum


class RunnerStatusKey(Enum):
    BOOTING = "booting"
    BLOCKING = "blocking"
    RUNNING_READY = "running_ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DESTROYED = "destroyed"

    SIGNAL_READY = "signal_ready"
    SIGNAL_SENT = "signal_sent"

    def __str__(self):
        return self.value


class RunnerStatus:

    def __init__(self, key: RunnerStatusKey, data: dict[str, any] = {}):
        self.key = key
        self.data = data

    def to_dict(self):
        return {"key": self.key.value, "data": self.data}
