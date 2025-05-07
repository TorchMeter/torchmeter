from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from functools import total_ordering

import numpy as np

from torchmeter.unit import TimeUnit, CountUnit, SpeedUnit, BinaryUnit, auto_unit

if TYPE_CHECKING:
    import sys
    from typing import Type, Tuple, Union, Callable, Optional, Sequence

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    from numpy.typing import NDArray

    UNIT_TYPE = Optional[Union[Type[CountUnit], 
                               Type[BinaryUnit], 
                               Type[TimeUnit], 
                               Type[SpeedUnit]]]  # fmt: skip

    SEQ_DATA = NDArray[Union[np.int_, np.float_]]

    FLOAT = Union[float, np.float_]
    NUMERIC_DATA_TYPE = Union[int, float]
    SEQ_FUNC = Callable[[SEQ_DATA], FLOAT]


@total_ordering
class NumericData(ABC):
    __slots__: Sequence[str] = []

    @property
    @abstractmethod
    def raw_data(self) -> FLOAT: ...

    def _numeric_op(self, other: Union[object, int, float], op: Callable):  # noqa: ANN202
        other_data = other.raw_data if isinstance(other, NumericData) else other
        return op(self.raw_data, other_data)

    # required for generating other comparison operators
    def __eq__(self, other: object) -> bool:
        return self._numeric_op(other, lambda s, o: s == o)

    def __lt__(self, other: NUMERIC_DATA_TYPE) -> bool:
        return self._numeric_op(other, lambda s, o: s < o)

    # arithmetic operations
    def __add__(self, other: NUMERIC_DATA_TYPE) -> Union[NUMERIC_DATA_TYPE, Self]:
        return self._numeric_op(other, lambda s, o: s + o)

    __radd__ = __add__

    def __sub__(self, other: NUMERIC_DATA_TYPE) -> Union[NUMERIC_DATA_TYPE, Self]:
        return self._numeric_op(other, lambda s, o: s - o)

    __rsub__ = lambda self, other: self._numeric_op(other, lambda s, o: o - s)

    def __mul__(self, other: NUMERIC_DATA_TYPE) -> Union[NUMERIC_DATA_TYPE, Self]:
        return self._numeric_op(other, lambda s, o: s * o)

    __rmul__ = __mul__

    def __truediv__(self, other: NUMERIC_DATA_TYPE) -> Union[float, Self]:
        return self._numeric_op(other, lambda s, o: s / o)

    __rtruediv__ = lambda self, other: self._numeric_op(other, lambda s, o: o / s)

    # type conversion
    def __float__(self) -> float:
        return float(self.raw_data)

    def __int__(self) -> int:
        return int(self.raw_data)

    def __round__(self, ndigits: Optional[int] = None) -> Union[int, FLOAT]:
        return round(self.raw_data, ndigits)


class UpperLinkData(NumericData):
    __slots__ = ["val", "none_str", "__access_cnt", "__parent_data", "__unit_sys"]

    def __init__(
        self,
        val: Union[int, float] = 0,
        parent_data: Optional[UpperLinkData] = None,
        unit_sys: UNIT_TYPE = None,
        none_str: str = "-",
    ) -> None:
        if not isinstance(val, (int, float)):
            raise TypeError(f"`val` must be `int` or `float`, but got `{type(val).__name__}`.")

        if not isinstance(parent_data, (UpperLinkData, type(None))):
            raise TypeError(
                "`parent_data` must be an instance of `UpperLinkData` or `None`, "
                + f"but got `{type(parent_data).__name__}`."
            )

        if unit_sys not in (None, CountUnit, BinaryUnit, TimeUnit, SpeedUnit):
            raise TypeError(
                "`unit_sys` must be `None` or one of `(CountUnit, BinaryUnit, TimeUnit, SpeedUnit)`, "
                + f"but got `{type(unit_sys).__name__}`."
            )

        if not isinstance(none_str, str):
            raise TypeError(f"`none_str` must be a string, but got `{type(none_str).__name__}`.")

        self.val = val
        self.__parent_data = parent_data
        self.__unit_sys = unit_sys
        self.__access_cnt = 1

        # Use when there is a "None" in the column where this data is located while rendering the table
        self.none_str = none_str

    @property
    def raw_data(self) -> float:
        return float(self.val)

    def mark_access(self) -> None:
        self.__access_cnt += 1

    def __iadd__(self, other: NUMERIC_DATA_TYPE) -> UpperLinkData:
        if not isinstance(other, (int, float)):
            raise TypeError(
                f"Instances of {self.__class__.__name__} can only be added in place with "
                + f"`int` or `float` data, but provided `{type(other).__name__}`."
            )
        self.val += other
        self.__upper_update(other)
        # self.__access_cnt += 1
        return self

    def __upper_update(self, other: Union[int, float]) -> None:
        if self.__parent_data is not None:
            self.__parent_data += other

    def __repr__(self) -> str:
        if self.__unit_sys is not None:
            base = auto_unit(self.val / self.__access_cnt, self.__unit_sys)
        else:
            base = str(self.val / self.__access_cnt)
        return base + (f" [dim](×{self.__access_cnt})[/]" if self.__access_cnt > 1 else "")  # noqa: RUF001


class MetricsData(NumericData):
    __slots__ = [
        "vals",
        "none_str",
        "__reduce_func",
        "__unit_sys",
    ]

    def __init__(
        self, reduce_func: Optional[SEQ_FUNC] = np.mean, unit_sys: UNIT_TYPE = CountUnit, none_str: str = "-"
    ) -> None:
        if reduce_func is not None and not callable(reduce_func):
            raise TypeError("`reduce_func` must be a callable object, " + f"but got `{type(reduce_func).__name__}`.")
        elif reduce_func is not None:
            _ = reduce_func(np.array([1, 2, 3]))
            if not isinstance(_, (int, float)):
                raise RuntimeError(
                    "The return type of `reduce_func` must be `int` or `float`, " + f"but got `{type(_).__name__}`."
                )

        if unit_sys not in (None, CountUnit, BinaryUnit, TimeUnit, SpeedUnit):
            raise TypeError(
                "`unit_sys` must be `None` or one of `(CountUnit, BinaryUnit, TimeUnit, SpeedUnit)`, "
                + f"but got `{type(unit_sys).__name__}`."
            )

        if not isinstance(none_str, str):
            raise TypeError(f"`none_str` must be a string, but got `{type(none_str).__name__}`.")

        self.vals: SEQ_DATA = np.array([])
        self.__reduce_func = reduce_func if reduce_func is not None else np.mean
        self.__unit_sys = unit_sys
        self.none_str = none_str

    @property
    def metrics(self) -> FLOAT:
        return self.__reduce_func(self.vals) if self.vals.any() else 0.0

    @property
    def iqr(self) -> FLOAT:
        if self.vals.any():
            return np.percentile(self.vals, 75) - np.percentile(self.vals, 25)
        else:
            return 0.0

    @property
    def val(self) -> Tuple[FLOAT, FLOAT]:
        return self.metrics, self.iqr

    @property
    def raw_data(self) -> FLOAT:
        return self.metrics

    def append(self, new_val: Union[int, FLOAT]) -> None:
        if not isinstance(new_val, (int, float)):
            raise TypeError(
                f"Instances of {self.__class__.__name__} can only be appended with `int` or `float` data, "
                + f"but got `{type(new_val).__name__}`."
            )

        self.vals = np.append(self.vals, new_val)

    def clear(self) -> None:
        self.vals = np.array([])

    def __repr__(self) -> str:
        if self.__unit_sys is not None:
            return f"{auto_unit(self.metrics, self.__unit_sys)}" + " ± " + f"{auto_unit(self.iqr, self.__unit_sys)}"
        else:
            return f"{self.metrics:.2f} ± {self.iqr:.2f}"
