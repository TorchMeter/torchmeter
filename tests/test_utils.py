import os
from typing import NoReturn
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch

import numpy as np
import polars as pl
import pytest
from torch import rand as torch_rand
from rich.text import Text
from numpy.random import rand as np_rand

from torchmeter.utils import Timer, Status, hasargs, data_repr, indent_str, resolve_savepath, match_polars_type
from torchmeter._stat_numeric import MetricsData, UpperLinkData


def func_no_args() -> None: ...
def func_one_arg(a) -> None: ...
def func_multi_args(a, b, c) -> None: ...


@pytest.fixture
def chang_to_temp_dir(tmpdir):
    origin_work_dir = os.getcwd()
    os.chdir(tmpdir)

    yield tmpdir.strpath

    os.chdir(origin_work_dir)
    if tmpdir.exists():
        tmpdir.remove(rec=1)


@pytest.fixture
def mock_status(monkeypatch):
    """To mock rich.status.Status.__enter__ and .__exit__"""
    mock_enter = Mock()
    mock_exit = Mock()
    monkeypatch.setattr(Status, "__enter__", mock_enter)
    monkeypatch.setattr(Status, "__exit__", mock_exit)
    return {"enter": mock_enter, "exit": mock_exit}


@pytest.mark.parametrize(
    argnames=("func", "given_args", "will_error"),
    argvalues=[
        (func_no_args, [], False),
        (func_no_args, ["a"], True),
        (func_one_arg, [], False),
        (func_one_arg, ["a"], False),
        (func_one_arg, ["b"], True),
        (func_one_arg, ["a", "b"], True),
        (func_multi_args, [], False),
        (func_multi_args, ["a"], False),
        (func_multi_args, ["b"], False),
        (func_multi_args, ["d"], True),
        (func_multi_args, ["a", "b"], False),
        (func_multi_args, ["a", "d"], True),
        (func_multi_args, ["a", "b", "c"], False),
        (func_multi_args, ["a", "b", "d"], True),
    ],
)
def test_hasargs(func, given_args, will_error) -> None:
    if will_error:
        with pytest.raises(RuntimeError) as e:
            hasargs(func, *given_args)
        assert func.__name__ in str(e.value)

    else:
        hasargs(func, *given_args)


@pytest.mark.usefixtures("chang_to_temp_dir")
class TestResolveSavePath:
    def test_relative_filepath_input(self) -> None:
        temp_dir = os.getcwd()

        file_dir = "relative_dir"
        file_name = "relative_file.txt"
        file_path = os.path.join(temp_dir, file_dir, file_name)

        save_dir, save_file = resolve_savepath(os.path.join(file_dir, file_name), target_ext="txt")
        assert save_dir == os.path.join(temp_dir, file_dir)
        assert save_file == file_path
        assert os.path.exists(save_dir)

    def test_absolute_filepath_input(self) -> None:
        temp_dir = os.getcwd()

        file_dir = "absolute_dir"
        file_name = "absolute_file.txt"
        file_path = os.path.join(temp_dir, file_dir, file_name)

        save_dir, save_file = resolve_savepath(file_path, target_ext="txt")
        assert save_dir == os.path.join(temp_dir, file_dir)
        assert save_file == file_path
        assert os.path.exists(save_dir)

    def test_relative_dirpath_input(self) -> None:
        temp_dir = os.getcwd()

        dir_name = "relative_dir"
        default_file_name = "TestData"
        defaule_file_ext = "txt"
        dir_path = os.path.join(temp_dir, dir_name)

        save_dir, save_file = resolve_savepath(
            dir_path,
            target_ext=defaule_file_ext,
            default_filename=default_file_name,
        )

        assert save_dir == os.path.join(temp_dir, dir_name)
        assert save_file == os.path.join(
            temp_dir,
            dir_name,
            default_file_name + "." + defaule_file_ext,
        )
        assert os.path.exists(save_dir)

    def test_absolute_dirpath_input(self) -> None:
        temp_dir = os.getcwd()

        dir_name = "absolute_dir"
        default_file_name = "TestData"
        defaule_file_ext = "txt"
        dir_path = os.path.join(temp_dir, dir_name)

        save_dir, save_file = resolve_savepath(
            dir_path, target_ext=defaule_file_ext, default_filename=default_file_name
        )

        assert save_dir == os.path.join(temp_dir, dir_name)
        assert save_file == os.path.join(temp_dir, dir_name, default_file_name + "." + defaule_file_ext)
        assert os.path.exists(save_dir)


@pytest.mark.vital
class TestIndentStr:
    # basic function test
    def test_single_line(self) -> None:
        """Test single-line string with default args"""
        result = indent_str("hello")
        assert result == " " * 4 + "hello"

    def test_multi_line(self) -> None:
        """Test multi-line strings with default args"""
        input_str = "first\nsecond\nthird"
        expected = (
            "│   first\n"
            "│   second\n"
            "└─  third"
        )  # fmt: skip
        assert indent_str(input_str) == expected

    def test_string_list_input(self) -> None:
        """Test string list input"""
        ipt_list = ["line1", "line2"]
        expected = (
            "│   line1\n"
            "└─  line2"
        )  # fmt: skip
        assert indent_str(ipt_list) == expected

    # arguments combination test
    @pytest.mark.parametrize(
        argnames=("indent", "expected"),
        argvalues=[
            (-1, "first\nsecond"),
            (0, "first\nsecond"),
            (1, "│first\n└second"),
            (2, "│ first\n└─second"),
            (3, "│  first\n└─ second"),
            (4, "│   first\n└─  second"),
        ],
    )
    def test_indent_variations(self, indent, expected) -> None:
        """Test different indentation levels"""
        assert indent_str("first\nsecond", indent=indent) == expected

    @pytest.mark.parametrize(
        argnames=("guideline", "expected"),
        argvalues=[
            (True, "│   line1\n└─  line2"),
            (False, "    line1\n    line2"),
        ],
    )
    def test_guideline_toggle(self, guideline, expected) -> None:
        """Test guideline activation"""
        assert indent_str("line1\nline2", guideline=guideline) == expected

    def test_not_process_first(self) -> None:
        """Test not to indent first line"""
        result = indent_str("a\nb", process_first=False)
        assert result == "a\n└─  b"

    # boundary condition test
    def test_empty_input(self) -> None:
        """测试空字符串输入"""
        assert indent_str("") == "    "  # single line
        assert indent_str("\n") == "│   \n└─  "  # multi-line

    def test_no_guideline_for_single_line(self) -> None:
        """Test single-line automatic disabling of guide lines"""
        assert indent_str("hello", guideline=True) == "    hello"

    # Special scenario testing
    def test_mixed_lengths_input(self) -> None:
        """Test mixed input with different line lengths"""
        input_lines = "short\nvery long line\nmedium"
        result = indent_str(input_lines)
        expected = (
            "│   short\n"
            "│   very long line\n"
            "└─  medium"
        )  # fmt: skip
        assert result == expected

    # Error handling test
    def test_invalid_indent_type(self) -> None:
        """Test non-integer indent"""
        with pytest.raises(TypeError):
            indent_str("test", indent="4")  # type: ignore

    def test_invalid_input_type(self) -> None:
        """Test non-str input"""
        with pytest.raises(TypeError):
            indent_str(123)

        with pytest.raises(TypeError):
            indent_str(["a", "b", 123])


@pytest.mark.vital
class TestDataRepr:
    @pytest.mark.parametrize(
        argnames=("val", "type_repr"),
        argvalues=[
            (42, "int"),
            (3.14, "float"),
            ("hello", "str"),
            (True, "bool"),
            (None, "NoneType"),
        ],
    )
    def test_simple_data(self, val, type_repr) -> None:
        """Test repr of basic data types"""
        assert data_repr(val) == f"[b green]{val}[/] [dim]<{type_repr}>[/]"

    @pytest.mark.parametrize(
        argnames=("val", "type_repr"),
        argvalues=[
            (np_rand(2, 3, 4), "ndarray"),
            (torch_rand(3, 224, 224), "Tensor"),
            (Mock(shape=(5, 5)), "Mock"),
        ],
    )
    def test_shape_objects(self, val, type_repr) -> None:
        """Test objects with shape attributes"""
        assert data_repr(val) == f"[dim]Shape[/]([b green]{list(val.shape)}[/]) [dim]<{type_repr}>[/]"

    @pytest.mark.parametrize(
        argnames=("val", "type_repr", "inner_type"),
        argvalues=[
            ([1, 2, 3], "list", "int"),
            ([np_rand(2, 3), np_rand(3, 4)], "list", "ndarray"),
            (("1", "2", "3"), "tuple", "str"),
            ((torch_rand(1, 2), torch_rand(3, 4)), "tuple", "Tensor"),
            ({1.0, 2.0, 3.0}, "set", "float"),
            ({Mock(shape=(1, 2)), Mock(shape=(3, 4))}, "set", "Mock"),
        ],
    )
    def test_container_data(self, val, type_repr, inner_type) -> None:
        actual = data_repr(val)

        # verify the overall structure
        assert actual.startswith(f"[dim]{type_repr}[/](")
        assert actual.endswith(")")

        # verify the repr of each item
        for v in val:
            if hasattr(v, "shape"):
                item_segment = f"[dim]Shape[/]([b green]{list(v.shape)}[/]) [dim]<{inner_type}>[/]"
            else:
                item_segment = f"[b green]{v}[/] [dim]<{inner_type}>[/]"
            assert item_segment in actual

        # verify indentation
        lines = actual.split("\n")
        assert all(line.startswith("│" + " " * (len(f"{type_repr}"))) for line in lines[1:-1])

    @pytest.mark.parametrize(
        argnames=("ipt", "key_type", "value_type"),
        argvalues=[
            ({"a": "1", "b": "2"}, "str", "str"),
            ({1: 1, 2: 2}, "int", "int"),
            ({1.0: 1.0, 2.0: 2.0}, "float", "float"),
            ({True: True, False: False}, "bool", "bool"),
            ({None: None}, "NoneType", "NoneType"),
        ],
    )
    def test_simple_data_dict(self, ipt, key_type, value_type) -> None:
        actual = data_repr(ipt)

        # verify the overall structure
        assert actual.startswith("[dim]dict[/](")
        assert actual.endswith(")")

        # verify the repr of each key-value pair
        for k, v in ipt.items():
            key_segment = f"[b green]{k}[/] [dim]<{key_type}>[/]"
            value_segment = f"[b green]{v}[/] [dim]<{value_type}>[/]"
            assert key_segment in actual
            assert value_segment in actual

        # verify indentation
        lines = actual.split("\n")
        assert all(line.startswith("│" + " " * 4) for line in lines[1:-1])

    @pytest.mark.parametrize(
        argnames=("ipt", "key_type", "value_type"),
        argvalues=[
            ({"a": np_rand(2, 3, 4), "b": np_rand(5, 6, 7)}, "str", "ndarray"),
            ({"a": torch_rand(2, 3, 4), "b": torch_rand(5, 6, 7)}, "str", "Tensor"),
            ({"a": Mock(shape=(1, 2, 3, 4)), "b": Mock(shape=(5, 6, 7, 8))}, "str", "Mock"),
        ],
    )
    def test_shape_objects_dict(self, ipt, key_type, value_type) -> None:
        actual = data_repr(ipt)

        # verify the overall structure
        assert actual.startswith("[dim]dict[/](")
        assert actual.endswith(")")

        # verify the repr of each key-value pair
        for k, v in ipt.items():
            if hasattr(k, "shape"):
                key_segment = f"[dim]Shape[/]([b green]{list(k.shape)}[/]) [dim]<{key_type}>[/]"
            else:
                key_segment = f"[b green]{k}[/] [dim]<{key_type}>[/]"

            value_segment = f"[dim]Shape[/]([b green]{list(v.shape)}[/]) [dim]<{value_type}>[/]"
            assert key_segment in actual
            assert value_segment in actual

        # verify indentation
        lines = actual.split("\n")
        assert all(line.startswith("│" + " " * 4) for line in lines[1:-1])

    @pytest.mark.parametrize(
        argnames=("ipt", "key_type", "container_type", "container_key_type", "container_val_type"),
        argvalues=[
            ({"a": {"b": 1, "c": 2}, "d": {"e": 3, "f": 4}}, "str", "dict", "str", "int"),
            ({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}, "str", "list", None, "float"),
            ({"a": (True, False, True), "b": (False, True, False)}, "str", "tuple", None, "bool"),
            ({"a": {"1", "2", "3"}, "b": {"4", "5", "6"}}, "str", "set", None, "str"),
        ],
    )
    def test_container_data_dict(self, ipt, key_type, container_type, container_key_type, container_val_type) -> None:
        """Test dict made up of container, i.e. the nested situation"""
        actual = data_repr(ipt)

        # verify the overall structure
        assert actual.startswith("[dim]dict[/](")
        assert actual.endswith(")")

        # verify the repr of each key-value pair
        for k, v in ipt.items():
            if hasattr(k, "shape"):
                key_segment = f"[dim]Shape[/]([b green]{list(k.shape)}[/]) [dim]<{key_type}>[/]"
            else:
                key_segment = f"[b green]{k}[/] [dim]<{key_type}>[/]"

            value_segment = f"[dim]{container_type}[/]("
            assert key_segment in actual
            assert value_segment in actual

            if isinstance(v, dict):
                for ck, cv in v.items():
                    if hasattr(ck, "shape"):
                        ck_segment = f"[dim]Shape[/]([b green]{list(ck.shape)}[/]) [dim]<{container_key_type}>[/]"
                    else:
                        ck_segment = f"[b green]{ck}[/] [dim]<{container_key_type}>[/]"
                    # simplify logic here
                    # test case one must not have object with shape attribute
                    cv_segment = f"[b green]{cv}[/] [dim]<{container_val_type}>[/]"

                    assert ck_segment in actual
                    assert cv_segment in actual

            else:
                for cv in v:
                    if hasattr(cv, "shape"):
                        cv_segment = f"[dim]Shape[/]([b green]{list(cv.shape)}[/]) [dim]<{container_val_type}>[/]"
                    else:
                        cv_segment = f"[b green]{cv}[/] [dim]<{container_val_type}>[/]"

                    assert cv_segment in actual

        # verify indentation
        lines = actual.split("\n")[1:]
        for idx, container in enumerate(ipt.values()):
            section_len = len(container)
            assert all(line.startswith("│" + " " * len("dict(a <str>:") + "│") 
                       for line in lines[:section_len - 2])  # fmt: skip

            if idx < len(ipt) - 1:
                assert lines[section_len - 2].startswith("│" + " " * len("dict(a <str>:") + "└─")

                lines = lines[section_len - 1 :]
                assert lines[0].startswith("│" + " " * len("dict"))

                lines.pop(0)
            else:
                assert lines[section_len - 2].startswith("└─" + " " * len("dict(a <str>") + "└─")

    def test_empty_container(self) -> None:
        """Test empty container input"""

        assert data_repr([]) == "[b green][][/] [dim]<list>[/]"
        assert data_repr({}) == "[b green]{}[/] [dim]<dict>[/]"
        assert data_repr([[], {}]) == (
            "[dim]list[/]([b green][][/] [dim]<list>[/],\n"
            "└─   [b green]{}[/] [dim]<dict>[/])"
        )  # fmt: skip

    def test_uncommon_input(self) -> None:
        """Test uncommon input"""

        class CustomType: ...

        assert data_repr(CustomType()) == f"[b green]obj[/] [dim]<{CustomType.__module__}.CustomType>[/]"

        func = func_no_args
        assert data_repr(func) == "[b green]func_no_args[/] [dim]<function>[/]"

        mock_obj = Mock(shape="invalid")  # invalid shape
        assert data_repr(mock_obj) == "[b green]obj[/] [dim]<unittest.mock.Mock>[/]"


@pytest.mark.vital
class TestMatchPolarsType:
    is_same_type = lambda _, val, pl_type: match_polars_type(val).is_(pl_type)

    @pytest.mark.parametrize(
        argnames=("input_value", "expected_type"),
        argvalues=[
            # basic types
            (42, pl.Int64),
            (3.14, pl.Float64),
            ("text", pl.Utf8),
            (True, pl.Boolean),
            (np.int8(5), pl.Int8),
            (np.int16(5), pl.Int16),
            (np.int32(5), pl.Int32),
            (np.int64(5), pl.Int64),
            (np.uint8(5), pl.UInt8),
            (np.uint16(5), pl.UInt16),
            (np.uint32(5), pl.UInt32),
            (np.uint64(5), pl.UInt64),
            (np.float32(1.2), pl.Float32),
            (np.float64(1.2), pl.Float64),
            # decimal
            (Decimal("1.2"), pl.Decimal),
            # time related types
            (date.today(), pl.Date),
            (datetime.now(), pl.Datetime("us")),
            (np.datetime64("2023-01-01"), pl.Date),
            (np.datetime64("2023-01-01T12"), pl.Object),
            (np.timedelta64(1, "us"), pl.Duration("us")),
            (np.timedelta64(1, "D"), pl.Object),
            # container types
            ([1, 2, 3], pl.List(pl.Int64)),
            ((1.0, 2.0, 3.0), pl.List(pl.Float64)),
            ((1, 2.0, 3.0), pl.List(pl.Int64)),
            ({"A": 1, "B": "b"}, pl.Struct({"A": pl.Int64, "B": pl.Utf8})),
            (set(), pl.Object),
            # ndarray
            (np.array([1, 2, 3], dtype=np.int64), pl.Int64),  # 1D int
            (np.array([1.1, 2.2], dtype=np.float64), pl.Float64),  # 1D float
            (np.array([[1, 2], [3, 4]], dtype=np.int64), pl.Array(pl.Int64, 2)),  # 2D
            (np.array([1, "a"], dtype=object), pl.Object),  # structed ndarray
            # class instance
            (Timer(task_desc="test"), pl.Object),
            (Status(status="test"), pl.Object),
            (UpperLinkData(2), pl.Object),
            (MetricsData(), pl.Object),
        ],
    )
    def test_type_inference(self, input_value, expected_type) -> None:
        """Test basic functionality"""

        assert self.is_same_type(input_value, expected_type)

    @pytest.mark.parametrize(
        argnames="pre_res_value",
        argvalues=[
            pl.Int64,
            pl.Float64,
            pl.Date,
            pl.Object,
            pl.List(pl.Float64),
            pl.Array(pl.Float64, 2),
        ],
    )
    def test_pre_res_option(self, pre_res_value) -> None:
        """Test the logic of pre_res option(early return)"""

        result = match_polars_type(
            "return pre_res no matter what this is",
            recheck=False,
            pre_res=pre_res_value,
        )
        assert result.is_(pre_res_value)

    def test_recheck_option(self) -> None:
        """Test the logic of recheck option(force recheck the type)"""

        result = match_polars_type(
            42,
            recheck=True,
            pre_res=pl.Utf8,
        )

        assert result.is_(pl.Int64)

    def test_edge_cases(self) -> None:
        """Test the edge use of the function"""

        # structured array
        structured_array = np.array(
            [("Rex", 9, 81.0), ("Fido", 3, 27.0)],
            dtype=[("name", "U10"), ("age", "i4"), ("weight", "f4")],
        )  # fmt: skip
        assert self.is_same_type(structured_array, pl.Object)

        # nested container
        nested_ls = [[1, 2], (3.0, 4.0)]

        assert self.is_same_type(nested_ls, pl.List(pl.List(pl.Int64)))


@pytest.mark.vital
class TestTimer:
    # basic function test
    @pytest.mark.parametrize(
        argnames="task",
        argvalues=[
            "basic task",  # normal string
            "",  # empty string
            "任务描述",  # Non-ASCII characters
            "a" * 200,  # long string
            "special_!@#$%^&*",  # special characters
        ],
    )
    def test_basic_use(self, task, mock_status, capsys) -> None:
        from time import sleep

        from rich import get_console

        console = get_console()
        console_width = console.width
        if len(task) > console_width:
            task = [task[i : i + console_width] for i in range(0, len(task), console_width)]
            task = "\n" + "\n".join(task)

        with Timer(task_desc=task):
            sleep(1)

        mock_status["enter"].assert_called_once()
        mock_status["exit"].assert_called_once()

        captured = capsys.readouterr()
        plain_text = Text.from_ansi(captured.out).plain
        assert f"Finish {task} in" in plain_text
        assert "seconds" in plain_text

    # boundary condition test
    def test_short_time(self, capsys) -> None:
        with Timer("short task"):
            # quit immediately
            pass

        captured = capsys.readouterr()
        assert "0.0000" in captured.out

    def test_long_time(self, capsys) -> None:
        with patch("torchmeter.utils.perf_counter") as mock_time:
            # Simulate a one-year time difference
            mock_time.side_effect = [0.0, 31536000.0]
            with Timer("long task"):
                pass

        captured = capsys.readouterr()
        assert "31536000.0000" in captured.out

    # Error handling test
    def test_exception_handling(self, mock_status) -> NoReturn:
        class CustomError(Exception): ...

        with pytest.raises(CustomError), Timer("error task"):
            raise CustomError("test error")

        assert mock_status["enter"].assert_called_once
        assert mock_status["exit"].assert_called_once

    # verify time accuracy
    def test_time_accuracy(self, capsys) -> None:
        with patch("torchmeter.utils.perf_counter") as mock_time:
            mock_time.side_effect = [100.0, 100.1234]
            with Timer("precision test"):
                pass

        captured = capsys.readouterr()
        assert "0.1234" in captured.out
