from __future__ import annotations

from enum import Enum, IntFlag, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type, Union

    import numpy as np

    FLOAT = Union[float, np.float_]

    UNITS = Union[
        Type["CountUnit"],
        Type["BinaryUnit"],
        Type["TimeUnit"],
        Type["SpeedUnit"],
    ]

__all__ = ["CountUnit", "BinaryUnit", "TimeUnit", "SpeedUnit", "auto_unit"]


@unique
class CountUnit(Enum):
    T = 1e12
    G = 1e9
    M = 1e6
    K = 1e3


@unique
class BinaryUnit(IntFlag):
    TiB = 2**40
    GiB = 2**30
    MiB = 2**20
    KiB = 2**10
    B = 2**0


@unique
class TimeUnit(Enum):
    h = 60**2
    min = 60**1
    s = 60**0
    ms = 1e-3
    us = 1e-6
    ns = 1e-9


@unique
class SpeedUnit(Enum):
    TIPS = 1e12
    GIPS = 1e9
    MIPS = 1e6
    KIPS = 1e3
    IPS = 1e0


def auto_unit(val: Union[int, FLOAT], unit_system: UNITS = CountUnit) -> str:
    unit: Enum

    for unit in list(unit_system):  # type: ignore
        if val >= unit.value:
            if val % unit.value:
                return f"{val / unit.value:.2f} {unit.name}"
            else:
                return f"{int(val // unit.value)} {unit.name}"
    if isinstance(val, int):
        return str(val)
    else:
        return f"{val:.2f}"
