from typing import Union
from decimal import Decimal

import numpy as np
import pytest

from torchmeter._stat_numeric import CountUnit, BinaryUnit, MetricsData, NumericData, UpperLinkData

pytestmark = pytest.mark.vital


class SimpleNumeric(NumericData):
    def __init__(self, value: Union[int, float]) -> None:
        self._value = value

    @property
    def raw_data(self) -> float:
        return float(self._value)


@pytest.fixture
def base_upperlink_data():
    return UpperLinkData(val=100)


@pytest.fixture
def linked_upperlink_data():
    parent = UpperLinkData(val=200)
    child = UpperLinkData(val=50, parent_data=parent)
    return parent, child


class TestNumericData:
    @pytest.mark.parametrize(
        argnames=("a", "b", "expected"),
        argvalues=[
            (5.0, 5.0, True),
            (5.0, 5, True),
            (5.0, 4.9, False),
            (-3.5, -3.5, True),
            (0.0, 0, True),
        ],
    )
    def test_equality(self, a, b, expected) -> None:
        """Test the logic of __eq__ and __ne__"""

        num_a = SimpleNumeric(a)
        assert (num_a == b) == expected
        assert (num_a != b) != expected

    @pytest.mark.parametrize(
        argnames=("a", "b", "latter_larger"),
        argvalues=[
            (5.0, 3.0, False),
            (2.5, 3.0, True),
            (-4.0, -3.0, True),
            (0.0, 0.0, False),
        ],
    )
    def test_ordering(self, a, b, latter_larger) -> None:
        """Test the logic of __lt__, __le__, __gt__, __ge__"""

        num_a = SimpleNumeric(a)
        assert (num_a < b) == (latter_larger and a != b)
        assert (num_a <= b) == (latter_larger or (a == b))
        assert (num_a > b) == (not latter_larger and a != b)
        assert (num_a >= b) == (not latter_larger or a == b)

    @pytest.mark.parametrize(
        argnames=("op", "a", "b", "expected"),
        argvalues=[
            ("+", 5.0, 3.0, 8.0),
            ("+", -2.5, 3.0, 0.5),
            ("-", 10.0, 4.5, 5.5),
            ("*", 2.5, 4.0, 10.0),
            ("/", 9.0, 2.0, 4.5),
            ("+", 5.0, SimpleNumeric(3.0), 8.0),
            ("*", SimpleNumeric(2.0), 3, 6.0),
            ("*", SimpleNumeric(3), 4.0, 12.0),
            ("/", 9.0, SimpleNumeric(3), 3.0),
        ],
    )
    def test_arithmetic_operations(self, op, a, b, expected) -> None:
        """Test the logic of arithmetic operations"""

        if isinstance(a, float):
            a = SimpleNumeric(a)
        if isinstance(b, float):
            b = SimpleNumeric(b)

        result = {
            "+": a + b,
            "-": a - b,
            "*": a * b,
            "/": a / b,
        }[op]

        assert expected == pytest.approx(result)

    def test_reverse_operations(self) -> None:
        """Test the logic of reverse arithmetic operations"""

        num = SimpleNumeric(3.0)

        # __radd__
        assert pytest.approx(2 + num) == 5.0

        # __rsub__
        assert pytest.approx(5 - num) == 2.0

        # __rmul__
        assert pytest.approx(2 * num) == 6.0

        # __rtruediv__
        assert pytest.approx(6 / num) == 2.0

    @pytest.mark.parametrize(
        argnames=("value", "expected"),
        argvalues=[
            (5.5, 5.5),
            (-3.2, -3.2),
            (0.0, 0.0),
        ],
    )
    def test_type_conversion(self, value, expected) -> None:
        """Test type conversion"""

        num = SimpleNumeric(value)
        assert float(num) == expected
        assert int(num) == int(expected)
        assert round(num) == round(expected)

    def test_hash_behavior(self) -> None:
        """Test unhashable"""

        with pytest.raises(TypeError):
            hash(SimpleNumeric(5.0))

        with pytest.raises(TypeError):
            _ = {SimpleNumeric(5.0), SimpleNumeric(5.0)}

    def test_numpy_compatability(self) -> None:
        """Test the compatibility with numpy"""

        num = SimpleNumeric(3.5)
        arr = np.array([num, 1.5, 2.0])
        assert np.sum(arr) == pytest.approx(7.0)
        assert np.mean(arr) == pytest.approx((3.5 + 1.5 + 2.0) / 3)
        assert np.sum(np.sort(arr) == [1.5, 2.0, 3.5]) == len(arr)

    def test_polars_compatability(self) -> None:
        """Test the compatibility with polars"""

        from polars import Series

        num = SimpleNumeric(5.5)
        arr = Series(values=[num, 1.5, 2.0])
        assert arr.sum() == pytest.approx(9.0)
        assert arr.max() == pytest.approx(5.5)
        assert arr.min() == pytest.approx(1.5)
        assert arr.mean() == pytest.approx((1.5 + 2.0 + 5.5) / 3)
        assert sum(arr.sort() == [1.5, 2.0, 5.5]) == len(arr)

    @pytest.mark.parametrize(
        argnames="invalid_input",
        argvalues=[
            "string",
            Decimal("10.5"),
            {"key": "value"},
        ],
    )
    def test_invalid_operations(self, invalid_input) -> None:
        """Test exception thrown in invalid operations"""

        num = SimpleNumeric(5.0)
        with pytest.raises(TypeError):
            _ = num + invalid_input


class TestUpperLinkData:
    def test_valid_init(self) -> None:
        """Test initialization with different arguments"""
        data = UpperLinkData()
        assert data.val == 0
        assert data._UpperLinkData__parent_data is None
        assert data._UpperLinkData__unit_sys is None
        assert data._UpperLinkData__access_cnt == 1
        assert data.none_str == "-"

        parent = UpperLinkData()
        data = UpperLinkData(
            val=100,
            parent_data=parent,
            unit_sys=BinaryUnit,
            none_str="N/A",
        )
        assert data.val == 100
        assert data._UpperLinkData__parent_data is parent
        assert data._UpperLinkData__unit_sys is BinaryUnit
        assert data.none_str == "N/A"

    def test_invalid_init(self) -> None:
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            UpperLinkData(val={})

        with pytest.raises(TypeError):
            UpperLinkData(val=100, parent_data=100)

        with pytest.raises(TypeError):
            UpperLinkData(unit_sys="KB")

        with pytest.raises(TypeError):
            UpperLinkData(none_str=22)

    def test_slots(self, base_upperlink_data) -> None:
        """Test __slots__ restriction"""
        assert not hasattr(base_upperlink_data, "__dict__")

        with pytest.raises(AttributeError):
            base_upperlink_data.invalid_attribute = 42

    def test_raw_data(self, base_upperlink_data) -> None:
        """Test whether the raw_data property is correcttly calculated"""
        assert base_upperlink_data.raw_data == 100.0
        base_upperlink_data.val = 150
        assert base_upperlink_data.raw_data == 150.0

    def test_mark_access(self, base_upperlink_data) -> None:
        """Test whether the mark_access method is correct"""
        assert base_upperlink_data._UpperLinkData__access_cnt == 1
        base_upperlink_data.mark_access()
        base_upperlink_data.mark_access()
        assert base_upperlink_data._UpperLinkData__access_cnt == 3

    def test_inplace_addition(self, base_upperlink_data) -> None:
        """Test inplace addition"""
        base_upperlink_data += 50
        assert base_upperlink_data.val == 150

    def test_linked_update(self, linked_upperlink_data) -> None:
        """Test whether the inplace addition will trigger the update of parent data"""
        parent, child = linked_upperlink_data

        # single linked data update
        child += 50
        assert child.val == 100
        assert parent.val == 250

        # multi linked data update
        grandparent = UpperLinkData(val=500)
        parent._UpperLinkData__parent_data = grandparent
        child += 100
        assert child.val == 200
        assert parent.val == 350
        assert grandparent.val == 600

        # verify the common arithmetic operations
        # will not influence the linked update feature
        assert child + 100 == 300
        assert child.val == 200
        assert parent.val == 350
        assert grandparent.val == 600

        child += 100
        assert child.val == 300
        assert parent.val == 450
        assert grandparent.val == 700

    def test_repr(self, linked_upperlink_data) -> None:
        """Test correct representation"""

        # no unit_sys
        parent, child = linked_upperlink_data
        assert repr(parent) == "200.0"
        assert repr(child) == "50.0"

        # with unit_sys
        data = UpperLinkData(val=1500, unit_sys=BinaryUnit)
        assert repr(data) == "1.46 KiB"  # 1500/1024

        # re-access representation
        data = UpperLinkData(val=300)
        data.mark_access()
        assert repr(data) == "150.0 [dim](×2)[/]"  # noqa: RUF001

    def test_edge_cases(self, base_upperlink_data) -> None:
        """Test some edge cases"""
        # add invalid data
        with pytest.raises(TypeError):
            base_upperlink_data += "invalid_type"


class TestMetricsData:
    def test_valid_init(self) -> None:
        """Test initialization with different arguments"""
        m = MetricsData()
        assert isinstance(m.vals, np.ndarray)
        assert not len(m.vals)
        assert m._MetricsData__reduce_func is np.mean
        assert m._MetricsData__unit_sys is CountUnit
        assert m.none_str == "-"

        custom_func = np.median
        m = MetricsData(reduce_func=custom_func, unit_sys=BinaryUnit, none_str="N/A")
        assert m._MetricsData__reduce_func is custom_func
        assert m._MetricsData__unit_sys is BinaryUnit
        assert m.none_str == "N/A"

    def test_invalid_init(self) -> None:
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            MetricsData(reduce_func=100)

        with pytest.raises(RuntimeError):
            MetricsData(reduce_func=str)

        with pytest.raises(TypeError):
            MetricsData(unit_sys=100)

        with pytest.raises(TypeError):
            MetricsData(none_str=22)

    def test_slots(self) -> None:
        """Test __slots__ restriction"""
        m = MetricsData()
        with pytest.raises(AttributeError):
            m.invalid_attr = 100

    def test_empty_data_properties(self) -> None:
        empty_m = MetricsData()
        assert empty_m.metrics == 0.0
        assert empty_m.iqr == 0.0
        assert empty_m.val == (0.0, 0.0)
        assert empty_m.raw_data == 0.0

    def test_single_value_properties(self) -> None:
        m = MetricsData()
        m.append(5.0)
        assert m.metrics == 5.0
        assert not m.iqr
        assert m.val == (5.0, 0.0)

    def test_multi_value_properties(self) -> None:
        m = MetricsData()
        m.vals = np.array([2.0, 4.0, 6.0, 10.0])
        assert m.metrics == 5.5
        assert m.iqr == 3.5  # Q3=7.0, Q1=3.5

    def test_reduce_func(self) -> None:
        m = MetricsData()
        m.vals = np.array([1.0, 2.0, 6.0])
        assert m.metrics == 3.0  # mean

        m._MetricsData__reduce_func = np.median
        assert m.metrics == 2.0  # median

        m._MetricsData__reduce_func = np.sum
        assert m.metrics == 9.0  # sum

    def test_data_management(self) -> None:
        m = MetricsData()

        with pytest.raises(TypeError):
            m.append([1.0, 2.0, 3.0, 4.0, 5.0])

        m.append(1.0)
        m.append(2.0)
        m.append(4.0)
        assert m.vals.tolist() == [1.0, 2.0, 4.0]

        m.clear()
        assert not len(m.vals)

    def test_repr(self) -> None:
        """Test correct representation"""
        # no unit
        m = MetricsData(unit_sys=None)
        m.append(1.5)
        m.append(2.5)
        assert repr(m) == "2.00 ± 0.50"  # mean 2.0, IQR=0.5(Q3=2.25, Q1=1.75)

        # default unit: CountUnit
        m = MetricsData()
        m.append(1000)
        m.append(2000)
        assert repr(m) == "1.50 K ± 500.00"  # mean 1500, IQR=500

        # custom unit
        m = MetricsData(unit_sys=BinaryUnit)
        m.append(1000)
        m.append(2000)
        assert repr(m) == "1.46 KiB ± 500 B"  # (mean 1500)/1024, IQR=500

    def test_edge_cases(self) -> None:
        """Test some edge cases"""
        # all zero
        m = MetricsData()
        m.append(0)
        m.append(0)
        m.append(0)
        assert m.metrics == 0.0
        assert m.iqr == 0.0

        # negative value
        m = MetricsData()
        m.append(-2)
        m.append(0)
        m.append(2)
        assert m.metrics == 0.0
        assert m.iqr == 2.0  # Q3=1.0, Q1=-1.0
