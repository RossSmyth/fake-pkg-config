from dataclasses import dataclass


@dataclass(order=True, slots=True, frozen=True)
class Lib:
    """A pkg-config module"""

    name: str
