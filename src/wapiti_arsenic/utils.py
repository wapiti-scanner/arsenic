import socket
from dataclasses import dataclass
from typing import Union


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 0))
        sock.listen(5)
        return sock.getsockname()[1]


def px_to_number(value: str) -> Union[int, float]:
    original = value
    if value.endswith("px"):
        value = value[:-2]
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{original!r} is not an number or <number>px value")


@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float
