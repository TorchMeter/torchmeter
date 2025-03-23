import os
from unittest.mock import ANY, Mock
from unittest.mock import call, patch

import pytest
import torch.nn as nn
from torch import randn as torch_randn
from rich.text import Text
from rich.rule import Rule
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.segment import Segment
from rich.console import Console, Group
from polars import DataFrame, Series

from torchmeter.config import FlagNameSpace
from torchmeter.engine import OperationNode, OperationTree
from torchmeter._stat_numeric import UpperLinkData, MetricsData, CountUnit
from torchmeter.display import (
    __cfg__, 
    dfs_task, render_perline, apply_setting,
    TreeRenderer, TabularRenderer
)

pytestmark = pytest.mark.vital

EXAMPLE_TREE = Tree("0")
TREE_CHILD1 = EXAMPLE_TREE.add("1")
TREE_CHILD1.add("1.1")
TREE_CHILD1.add("1.2")
TREE_CHILD2 = EXAMPLE_TREE.add("Child2")
TREE_CHILD2.add("2.1")
TREE_CHILD2.add("2.2")

EXAMPLE_TABLE = Table("A","B")
EXAMPLE_TABLE.add_row("1", "2")
EXAMPLE_TABLE.add_row("3", "4")

class NoVPAObj:
    """No Variable Positional Arguments"""
    def __init__(self, a, b, c=3):
        self._a = a
        self._b = b
        self._c = c
        
        self._all = a + b + c

class VPAFObj:
    """Variable Positional Arguments at Front"""
    def __init__(self, *a, b=2, c=3):
        self._a = a
        self._b = b
        self._c = c

class VPAMObj:
    """Variable Positional Arguments at Middle"""
    def __init__(self, a, *b, c=3):
        self._a = a
        self._b = b
        self._c = c

class VPALObj:
    """Variable Positional Arguments as Last"""
    def __init__(self, a, b, *c):
        self._a = a
        self._b = b
        self._c = c

class MixedArgsObj:
    """All types of arguments"""
    def __init__(self, a, b=2, *c, d=4, **e):
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._e = e

@pytest.fixture
def mock_console():
    """Fixture providing a mocked console object"""
    console = Mock(spec=Console)
    console.render_lines.return_value = [[Segment("line1")], [Segment("line2")]]
    return console

@pytest.fixture
def mock_config(monkeypatch):
    """Fixture to mock the __cfg__ object"""
    class MockConfig:
        render_interval = 0.1
    monkeypatch.setattr("torchmeter.display.__cfg__", MockConfig())

@pytest.fixture
def simple_tree_renderer():
    opnode = OperationNode(nn.Identity())
    yield TreeRenderer(opnode)
    __cfg__.restore()

@pytest.fixture
def repeat_tree_renderer():
    class RepeatModel(nn.Module):
        def __init__(self):
            super(RepeatModel, self).__init__()
            self.layer0 = nn.Linear(10, 10)
            self.layer1 = nn.Sequential(
                nn.Linear(10, 10),
                nn.ReLU(),
                nn.Linear(10, 10),
                nn.ReLU()
            )
            
    optree = OperationTree(RepeatModel())
    
    yield TreeRenderer(optree.root)
    
    __cfg__.restore()

@pytest.fixture
def simple_tabular_renderer():
    opnode = OperationNode(nn.Identity())
    yield TabularRenderer(opnode)
    __cfg__.restore()

@pytest.fixture
def universal_tabular_renderer():
    class UnuseModel(nn.Module):
        def __init__(self):
            super(UnuseModel, self).__init__()
            
            self.conv = nn.Conv2d(3, 3, 3)
            self.unuse = nn.Identity()
        
        def forward(self, x):
            return self.conv(x)
    
    optree = OperationTree(UnuseModel())
    tabular_renderer = TabularRenderer(optree.root)
    
    yield tabular_renderer
    
    __cfg__.restore()
            
@pytest.fixture
def example_df():
    """
    ┌─────────┬──────┬───────────┬───────────┬─────────────┐
    │ numeric ┆ text ┆ list_col  ┆ nomal_obj ┆ self_obj    │
    │ ---     ┆ ---  ┆ ---       ┆ ---       ┆ ---         │
    │ i64     ┆ str  ┆ list[i64] ┆ object    ┆ object      │
    ╞═════════╪══════╪═══════════╪═══════════╪═════════════╡
    │ 1       ┆ a    ┆ [1, 2]    ┆ example   ┆ 100 K       │
    │ 2       ┆ null ┆ [3]       ┆ dataframe ┆ null        │
    │ null    ┆ c    ┆ null      ┆ null      ┆ 0.00 ± 0.00 │
    └─────────┴──────┴───────────┴───────────┴─────────────┘
    """
    
    from polars import Object as pl_obj

    df = DataFrame({
        "numeric": [1, 2, None],
        "text": ["a", None, "c"],
        "list_col": [[1,2], [3], None],
        "nomal_obj": [
            Text("example"), 
            Text("dataframe"), 
            None
        ]})
    
    self_obj_col = Series(
        name="self_obj",
        values=[
            UpperLinkData(1e5, unit_sys=CountUnit, none_str="test none_str"),
            None,
            MetricsData()
        ],
        dtype = pl_obj
    )

    df.insert_column(len(df.columns), self_obj_col)
    
    return df

@pytest.fixture
def export_dir(tmpdir):
    yield tmpdir.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)

class TestApplySetting:

    def test_valid_usage(self):
        """"Test basic functionality and common usage cases"""
        
        # all settings are changed
        obj = NoVPAObj(1, 2, 3)
        apply_setting(obj, setting={"a":10, "b":20, "c":30})
        assert obj._a == 10
        assert obj._b == 20
        assert obj._c == 30

        # partial settings are changed
        obj = NoVPAObj(1, 2, 3)
        apply_setting(obj, setting={"a":10, "b":20})
        assert obj._a == 10
        assert obj._b == 20
        assert obj._c == 3
    
    def test_invalid_usage(self):
        """Test invalid usage cases"""
        
        # invlaid setting type
        with pytest.raises(TypeError):
            apply_setting(NoVPAObj(1,2,3), setting=10)
        
        # invalid omit type, see `test_omit_type`
        
        # required initializatio argument absent
        with pytest.raises(RuntimeError) as e:
            apply_setting(NoVPAObj(1,2,3), setting={'a':10})
            assert "`b` unknown" in str(e.value)

    def test_setting(self):
        """Test the logic of getting setting_dict"""
        
        # use FlagNameSpace to store the setting
        obj = NoVPAObj(1, 2, 3)
        apply_setting(obj, setting=FlagNameSpace(a=100, b=200, c=300))
        assert obj._a == 100
        assert obj._b == 200
        assert obj._c == 300
        
        # use dict to store the setting
        obj = NoVPAObj(1, 2, 3)
        apply_setting(obj, setting={"a":1000, "b":2000, "c":3000})
        assert obj._a == 1000
        assert obj._b == 2000
        assert obj._c == 3000
        
        # update setting with extra_settings
        obj = NoVPAObj(1, 2, 3)
        apply_setting(obj, setting={"a":1000, "b":2000, "c":3000}, 
                      c=30)
        assert obj._a == 1000
        assert obj._b == 2000
        assert obj._c == 30
        
        # invalid setting type
        with pytest.raises(TypeError):
            apply_setting(NoVPAObj(1,2,3), setting=10)

    @pytest.mark.parametrize(
        argnames=("omit_args", "is_error", "key_error_info"),
        argvalues=[
            (None, False, None), # None
            ("a", False, None), # str
            (["a", "b"], False, None), # list
            (("a", "c"), False, None), # list
            ({"a", "b", "c"}, False, None), # set
            ({"a":1, "b":2, "c":3}, True, "but got `dict`"), # dict
            (123, True, "but got `int`"), # int
            ([1,2,3], True, "`list` of `int`") # container of non-str
        ]
    )
    def test_omit_type(self, omit_args, is_error, key_error_info):
        """Test the pass-in type limitation"""

        if is_error:
            with pytest.raises(TypeError) as e:
                apply_setting(NoVPAObj(1, 2, c=10), 
                              setting={"a":10, "b":20, "c":30}, 
                              omit=omit_args)
                assert key_error_info in str(e.value)
        else:
            apply_setting(NoVPAObj(1, 2, c=10), 
                          setting={"a":10, "b":20, "c":30}, 
                          omit=omit_args)
    
    @pytest.mark.parametrize(
        argnames=("obj", "setting", "omit_args", "expected_state"),
        argvalues=[
            # omit one argument
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, "_c", {"_a":10, "_b":20, "_c":10, "_all":60}), 
            
            # not omit one argument
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, "", {"_a":10, "_b":20, "_c":30, "_all":60}),

            # omit multiple arguments
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, ["_a", "_b"], {"_a":1, "_b":2, "_c":30, "_all":60}), 
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, ("_a", "_c"), {"_a":1, "_b":20, "_c":10, "_all":60}),
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, {"_a", "_b", "_c"}, {"_a":1, "_b":2, "_c":10, "_all":60}), 

            # not omit multiple arguments
            (NoVPAObj(1, 2, 10), {"a":10, "b":20, "c":30}, "", {"_a":10, "_b":20, "_c":30, "_all":60}),

            # omit variable positional arguments
            (VPAFObj(1, 2, 3, 4, 5), {"a":[7,8,9], "b":40, "c":50}, "_a", {"_a":(1,2,3,4,5), "_b":40, "_c":50}),
            (VPAMObj(1, 2, 3, 4, 5), {"a":10, "b":[7,8,9], "c":50}, "_b", {"_a":10, "_b":(2,3,4,5), "_c":50}),
            (VPALObj(1, 2, 3, 4, 5), {"a":10, "b":20, "c":[7,8,9]}, "_c", {"_a":10, "_b":20, "_c":(3,4,5)}),

            # not omit variable positional arguments
            (VPAFObj(1, 2, 3, 4, 5), {"a":[7,8,9], "b":40, "c":50}, "", {"_a":(7,8,9), "_b":40, "_c":50}),
            (VPAMObj(1, 2, 3, 4, 5), {"a":10, "b":[7,8,9], "c":50}, "", {"_a":10, "_b":(7,8,9), "_c":50}),
            (VPALObj(1, 2, 3, 4, 5), {"a":10, "b":20, "c":[7,8,9]}, "", {"_a":10, "_b":20, "_c":(7,8,9)}),

            # omit mixed arguments
            (MixedArgsObj(2, 4, 6, 8, d=10, f=12), {"a":10, "b":20, "c":[1,2,3], "d":40, "g":"G"},  
                                             "_a", {"_a":2, "_b":20, "_c":(1,2,3), "_d":40, "_e":{"g":"G"}}),
            (MixedArgsObj(2, 4, 6, 8, d=10, f=12), {"a":10, "b":20, "c":[1,2,3], "d":40, "g":"G"}, 
                                             "_c", {"_a":10, "_b":20, "_c":(6,8), "_d":40, "_e":{"g":"G"}}),
            (MixedArgsObj(2, 4, 6, 8, d=10, f=12), {"a":10, "b":20, "c":[1,2,3], "d":40, "g":"G"},
                                             "_d", {"_a":10, "_b":20, "_c":(1,2,3), "_d":10, "_e":{"g":"G"}}),
            (MixedArgsObj(2, 4, 6, 8, d=10, f=12), {"a":10, "b":20, "c":[1,2,3], "d":40, "g":"G"},
                                             "_e", {"_a":10, "_b":20, "_c":(1,2,3), "_d":40, "_e":{"f":12}}),
            
            # not omit mixed arguments
            (MixedArgsObj(2, 4, 6, 8, d=10, f=12), {"a":10, "b":20, "c":[1,2,3], "d":40, "g":"G"},
                                               "", {"_a":10, "_b":20, "_c":(1,2,3), "_d":40, "_e":{"g":"G"}}),
        ]
    )
    def test_omit_logic(self, obj, setting, omit_args, expected_state):
        """Test the logic of omitting the update of specified arguments"""
        apply_setting(obj, setting, omit=omit_args)
        assert obj.__dict__ == expected_state

    def test_slots_object(self):
        """Test the logic of dealing with slots object"""
        class OneSlotObj:
            __slots__ = "_a"
            def __init__(self, a):
                self._a = a

        class MultiSlotObj:
            __slots__ = ["_a", "_b", "_c"]
            def __init__(self, a, b, c=3):
                self._a = a
                self._b = b
                self._c = c

        # slots just have one attribute
        obj = OneSlotObj(1)
        apply_setting(obj, {'a': 10})
        assert obj._a == 10

        # slots just multi attributes
        obj = MultiSlotObj(1,2,3)
        apply_setting(obj, {"a": 10, "b":20})
        assert obj._a == 10
        assert obj._b == 20
        assert obj._c == 3

    def test_private_property(self):
        """Test whether the function works well when the inner attribute is private"""
        class PrivateObj:
            def __init__(self, a):
                self.__a = a
            
            @property
            def a_val(self):
                return self.__a
                
        class PrivateSlotObj:
            __slots__ = "__a"
            def __init__(self, a):
                self.__a = a
            
            @property
            def a_val(self):
                return self.__a
        
        obj = PrivateObj(1)
        apply_setting(obj, setting={'a': 10})
        assert obj.a_val == 10
        
        obj = PrivateSlotObj(1)
        apply_setting(obj, setting={'a': 10})
        assert obj.a_val == 10

    def test_indirect_property(self):
        """Test whether indirect initialization properties will change synchronously."""
        class IndirectObj:
            def __init__(self, a):
                self.a = a
                self.computed = a * 2 

        obj = IndirectObj(2)
        apply_setting(obj, setting={'a': 5})
        assert obj.a == 5
        assert obj.computed == 10 

    def test_inplace_update(self):
        """Test whether the settings are updated inplace"""
        class Child:
            def __init__(self, value):
                self.value = value

        class Parent:
            def __init__(self, child: Child):
                self.child = child

        child = Child(1)
        parent = Parent(child)
        
        apply_setting(child, setting={"value": 10})
        assert child.value == 10
        assert parent.child.value == 10

    def test_edge_cases(self):
        # omit list is empty
        obj = NoVPAObj(1, 2, 3) 
        apply_setting(obj, 
                      setting={"a":10, "b":20, "c":30}, 
                      omit=[])
        assert obj._a == 10
        assert obj._b == 20
        assert obj._c == 30

class TestRenderPerline:
    def test_negative_interval(self, mock_config, monkeypatch):
        """Test ValueError when render_interval is negative"""
        monkeypatch.setattr("torchmeter.display.__cfg__.render_interval", -0.5)
        with pytest.raises(ValueError) as excinfo:
            render_perline("test")
        assert "non-negative" in str(excinfo.value)

    def test_instant_render(self, mock_config, mock_console, monkeypatch):
        """Test immediate rendering when time_sep is 0"""
        with patch("rich.get_console", return_value=mock_console), \
            patch("time.sleep") as mock_sleep:
            
            monkeypatch.setattr("torchmeter.display.__cfg__.render_interval", 0)
            
            render_perline("test_content")
            
            # Verify console.print called once
            mock_console.print.assert_called_once_with("test_content")
            # and no sleep calls
            mock_sleep.assert_not_called()

    def test_render_line_by_line(self, mock_config, mock_console, monkeypatch):
        """Test line-by-line rendering with time interval"""
        with patch("rich.get_console", return_value=mock_console), \
             patch("time.sleep") as mock_sleep:
            
            monkeypatch.setattr("torchmeter.display.__cfg__.render_interval", 0.1)
            
            render_perline("multi\nline\ncontent")
            
            # Verify render_lines called
            mock_console.render_lines.assert_called_once_with(
                "multi\nline\ncontent", 
                new_lines=True
            )
            
            # Verify buffer operations
            assert mock_console._buffer_index == 0
            mock_console._buffer.extend.assert_has_calls([
                call([Segment("line1")]), # define in mock_console
                call([Segment("line2")])
            ])
            
            # Verify sleep calls between lines
            mock_sleep.assert_has_calls([call(0.1), call(0.1)])

    @pytest.mark.parametrize(
        argnames=("content", "render_lines_num"),
        argvalues=[
            (1, 1),
            (1.5, 1),
            ("123", 1),
            ("1\n2", 2),
            ("1\n2\n3", 3),
            (Rule("test"), 1),
            (Columns(["test1\ntest2", "test3"]), 2),
            (Panel("Hi\nThis is a panel"), 5),
            (Tree("test"), 1),
            (EXAMPLE_TREE, 7),
            (Table(), 3),
            (EXAMPLE_TABLE, 7),
        ]
    )
    def test_various_content(self, content, render_lines_num,
                             mock_console, monkeypatch):
        """Test handling empty renderable content"""
        
        
        with patch("rich.get_console", return_value=mock_console), \
             patch("time.sleep") as mock_sleep:
                 
            # no time interval
            monkeypatch.setattr("torchmeter.display.__cfg__.render_interval", 0)
            render_perline(content)
            mock_console.render_lines.assert_not_called()
        
            # with time interval
            monkeypatch.setattr("torchmeter.display.__cfg__.render_interval", 0.15)
            render_perline(content)
            mock_sleep.call_count == render_lines_num

class TestTreeRenderer:
    def teardown_method(self, method):
        __cfg__.restore()
        
    def test_valid_init(self, simple_tree_renderer):
        """Test valid initialization"""
        assert isinstance(simple_tree_renderer.opnode, OperationNode)
        assert simple_tree_renderer.render_unfold_tree is None
        assert simple_tree_renderer.render_fold_tree is None
        assert isinstance(simple_tree_renderer.loop_algebras, str)
        assert len(simple_tree_renderer.loop_algebras) >= 10

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            TreeRenderer(1)

    def test_default_level_args(self, simple_tree_renderer):
        """Test if default_level_args is set and retrieved correctly"""
        
        # retrieve
        ## when default settings is defined
        default_args = simple_tree_renderer.default_level_args
        assert isinstance(default_args, FlagNameSpace)
        assert default_args.is_change()  # newly created, mark as changed
        assert hasattr(default_args, "label")
        
        ## when default settings is not defined
        delattr(simple_tree_renderer.tree_levels_args, "default")
        default_args = simple_tree_renderer.default_level_args
        assert isinstance(default_args, FlagNameSpace)
        assert default_args.is_change()
        assert all(hasattr(default_args, f) 
                for f in ['label', 'style', 'guide_style',   # define in display.py::TreeRenderer::default_level_args
                            'highlight', 'hide_root', 'expanded'])

        # new a single field
        default_args.mark_unchange()
        default_args.test_field = "test field"
        assert default_args.is_change()
        assert default_args.test_field == "test field"

        # update a field
        default_args.mark_unchange()
        default_args.style = "cyan"
        assert default_args.is_change()
        assert default_args.style == "cyan"

        # overwrite
        ## with invalid type
        with pytest.raises(TypeError):
            simple_tree_renderer.default_level_args = 1
        
        ## with invalid field
        with pytest.raises(KeyError):
            simple_tree_renderer.default_level_args = {'invalid_field': 'value'}
        
        ## with combination of invalid field and valid field
        with pytest.raises(KeyError):
            simple_tree_renderer.default_level_args = {'invalid_field': 'value',
                                                'label': "test"}
        
        ## update nothing
        default_args.mark_unchange()
        simple_tree_renderer.default_level_args = {}
        assert default_args.is_change()
        assert all(hasattr(default_args, f) 
                for f in ['label', 'style', 'guide_style',   # define in display.py::TreeRenderer::default_level_args
                            'highlight', 'hide_root', 'expanded'])

        ## with parts of valid fields
        default_args.mark_unchange()
        simple_tree_renderer.default_level_args = {'label': "test",
                                            'style': "magenta"}
        assert default_args.is_change()
        assert default_args.label == "test"
        assert default_args.style == "magenta"
    
    def test_tree_levels_args(self, simple_tree_renderer):
        """Test if tree_levels_args is set and retrieved correctly"""
        
        # retrieve
        levels_args = simple_tree_renderer.tree_levels_args
        assert isinstance(levels_args, FlagNameSpace)
        assert levels_args.is_change()  # newly created, mark as changed

        # new a single field
        levels_args.mark_unchange()
        setattr(simple_tree_renderer.tree_levels_args, "new_field", {})
        assert levels_args.is_change()
        assert isinstance(levels_args.new_field, FlagNameSpace)
        assert len(levels_args.new_field.__dict__) == 1

        # update a field
        levels_args.mark_unchange()
        setattr(simple_tree_renderer.tree_levels_args, "0", {"label": "level zero"})
        assert levels_args.is_change()
        assert hasattr(levels_args, "0")
        level_0_settings = getattr(levels_args, "0")
        assert isinstance(level_0_settings, FlagNameSpace)
        assert level_0_settings.label == "level zero"

        # overwrite
        ## with invalid type
        with pytest.raises(TypeError):
            simple_tree_renderer.tree_levels_args = 1
        
        ## with invalid field
        with pytest.raises(KeyError):
            simple_tree_renderer.tree_levels_args = {'default':{'invalid_field': 'value'}}
        
        ## with combination of invalid field and valid field
        with pytest.raises(KeyError):
            simple_tree_renderer.tree_levels_args = {"default":{'invalid_field': 'value',
                                                                'label': "test"}}
        
        ## with invalid level 
        levels_args.mark_unchange()
        with pytest.warns(UserWarning):
            simple_tree_renderer.tree_levels_args = {"invalid_level": {'label': "test"}}
        assert levels_args.is_change()
        assert not hasattr(levels_args, "invalid_level")


        ## assign `default` settings
        levels_args.mark_unchange()
        simple_tree_renderer.tree_levels_args = {"default": {'label': "test"}}
        assert levels_args.default.label == "test"
        assert levels_args.is_change()

        ## assign `all` settings
        levels_args.mark_unchange()
        simple_tree_renderer.tree_levels_args = {"1": {'label': "test"}}
        simple_tree_renderer.tree_levels_args = {"all": {'label': "all label"}}
        assert levels_args.is_change()
        assert levels_args.default.label == "all label"
        assert not hasattr(levels_args, "0")
        assert not hasattr(levels_args, "1")
        assert not hasattr(levels_args, "all")
        
        ## update nothing
        levels_args.mark_unchange()
        simple_tree_renderer.tree_levels_args = {}
        assert levels_args.is_change()
        assert hasattr(levels_args, "default")
        
        ## update and new level settings
        levels_args.mark_unchange()
        simple_tree_renderer.tree_levels_args = {"default":{"guide_style": "blue"},
                                          "3": {"label": "label 3",
                                                "style": "green",
                                                "guide_style": "red"}}
        assert levels_args.is_change()
        assert hasattr(simple_tree_renderer.default_level_args, "label") # other fields will not be deleted
        assert hasattr(levels_args, "3")
        assert simple_tree_renderer.default_level_args.guide_style == "blue"
        
        level_3_settings = getattr(levels_args, "3")
        assert level_3_settings.label == "label 3"
        assert level_3_settings.style == "green"
        assert level_3_settings.guide_style == "red"
        
        ## verify level case insensitive
        levels_args.mark_unchange()
        simple_tree_renderer.tree_levels_args = {"DeFaulT": {"highlight": False}}
        assert levels_args.is_change()
        assert simple_tree_renderer.default_level_args.highlight is False

    def test_repeat_block_args(self, simple_tree_renderer):
        """Test if repeat_block_args is set and retrieved correctly"""
        
        # retrieve
        rpbk_args = simple_tree_renderer.repeat_block_args
        assert isinstance(rpbk_args, FlagNameSpace)
        assert rpbk_args.is_change()  # newly created, mark as changed

        # new a single field
        rpbk_args.mark_unchange()
        setattr(simple_tree_renderer.repeat_block_args, "111", True)
        assert rpbk_args.is_change()
        assert getattr(rpbk_args, "111") is True

        # update a field
        rpbk_args.mark_unchange()
        setattr(simple_tree_renderer.repeat_block_args, "title_align", "left")
        assert rpbk_args.is_change()
        assert rpbk_args.title_align == "left"

        # overwrite
        ## with invalid type
        with pytest.raises(TypeError):
            simple_tree_renderer.repeat_block_args = 1
        
        ## with invalid field
        with pytest.raises(KeyError):
            simple_tree_renderer.repeat_block_args = {'invalid_field': 'value'}
        
        ## with combination of invalid field and valid field
        with pytest.raises(KeyError):
            simple_tree_renderer.repeat_block_args = {'invalid_field': 'value',
                                                      'border_style': 'yellow'}
            
        ## update nothing
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_block_args = {}
        assert rpbk_args.is_change()
        assert hasattr(rpbk_args, "title")
        
        ## update several settings without repeat_footer 
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_block_args = {"subtitle": "this is a subtitle",
                                           "subtitle_align": "left",
                                           "style": "cyan"}
        assert rpbk_args.is_change()
        assert rpbk_args.subtitle == "this is a subtitle"
        assert rpbk_args.subtitle_align == "left"
        assert rpbk_args.style == "cyan"
        
        ## update several settings with repeat_footer 
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_block_args = {"style": "red",
                                                  "repeat_footer": lambda :"Footer"}
        assert rpbk_args.is_change()
        assert rpbk_args.style == "red"
        assert not hasattr(rpbk_args, "repeat_footer")
        assert simple_tree_renderer.repeat_footer == "Footer"

    def test_repeat_footer(self, simple_tree_renderer):
        """Test if repeat_footer is set and retrieved correctly"""
        
        from inspect import signature
        
        ## retrieve
        repeat_footer = simple_tree_renderer.repeat_footer
        rpbk_args = simple_tree_renderer.repeat_block_args
        assert rpbk_args.is_change()
        assert isinstance(repeat_footer, (str, type(None))) or callable(repeat_footer)
        if callable(repeat_footer):
            args_num = len(signature(repeat_footer).parameters)
            assert args_num <= 1
            
            if not args_num:
                res = repeat_footer()
                assert isinstance(res, (type(None), str))
        
        ## set with None
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_footer = None
        assert simple_tree_renderer.repeat_footer is None
        assert rpbk_args.is_change()
        
        ## set with str
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_footer = "Footer"
        assert simple_tree_renderer.repeat_footer == "Footer"
        assert rpbk_args.is_change()

        ## set with no arg function
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_footer = lambda :"footer"
        assert simple_tree_renderer.repeat_footer == "footer"
        assert rpbk_args.is_change()
        
        with pytest.raises(RuntimeError):
            simple_tree_renderer.repeat_footer = lambda :2
        
        ## set with one arg function
        rpbk_args.mark_unchange()
        simple_tree_renderer.repeat_footer = lambda x: f"Footer {x}"
        assert simple_tree_renderer.repeat_footer("test") == "Footer test"
        assert rpbk_args.is_change()
        
        ## set with more than one args function
        with pytest.raises(RuntimeError):
            simple_tree_renderer.repeat_footer = lambda x, y: f"Footer {x} {y}"
        
        ## set with invalid input
        with pytest.raises(RuntimeError):
            simple_tree_renderer.repeat_footer = 33

    def test_default_footer(self, monkeypatch):
        """Test the default_rpft method logic"""
        from random import sample

        monkeypatch.setattr("torchmeter.display.TreeRenderer.loop_algebras", "xy")

        class RepeatWinszModel(nn.Module):
            def __init__(self, repeat_winsz=1, repeat_time=3):
                super(RepeatWinszModel, self).__init__()
                
                candidate_layers = (
                    nn.Linear(1,10),
                    nn.Conv2d(3,10,1),
                    nn.MaxPool2d(3),
                    nn.AvgPool2d(3),
                    nn.BatchNorm2d(10),
                    nn.ReLU(),
                    nn.Sigmoid(),
                    nn.Identity(),
                )

                self.layer = nn.ModuleList(repeat_time * 
                                           sample(candidate_layers, repeat_winsz))
        
        model = RepeatWinszModel(repeat_winsz=1, repeat_time=3)
        optree = OperationTree(model)
        tree_renderer = TreeRenderer(optree.root)

        res = tree_renderer()
        footer = res.children[0].children[0].label.renderable.renderables[-1]
        footer_str = Text.from_markup(footer).plain
        assert footer_str == "Where x ∈ [1, 3]"
        
        model = RepeatWinszModel(repeat_winsz=2, repeat_time=3)
        optree = OperationTree(model)
        tree_renderer = TreeRenderer(optree.root)
        
        res = tree_renderer()
        footer = res.children[0].children[0].label.renderable.renderables[-1]
        footer_str = Text.from_markup(footer).plain
        assert footer_str == "Where x = 1, 3, 5"            

    def test_resolve_attr(self, simple_tree_renderer):
        """Test whether the resolve_attr method works well"""
        simple_tree_renderer.resolve_attr = lambda x: str(x)
        mock_node = Mock(node_id="1.2")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text="Node <node_id>", 
            attr_owner=mock_node
        )
        assert result == "Node 1.2"
        
        simple_tree_renderer.resolve_attr = lambda x: f"Custom_{x}"
        mock_node = Mock(node_id="1.2")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text="Node <node_id>", 
            attr_owner=mock_node
        )
        assert result == "Node Custom_1.2"
        
        simple_tree_renderer.resolve_attr = lambda x: 12345
        mock_node = Mock(node_id="1.2")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text="Node <node_id>", 
            attr_owner=mock_node
        )
        assert result == "Node 12345"

    def test_resolve_argtext(self, simple_tree_renderer):
        """Test whether argtext is resolved correctly"""
            
        simple_tree_renderer.resolve_attr = lambda x: str(x)
        # resolve placeholders
        mock_node = Mock(node_id="1.2")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text="Node <node_id>", 
            attr_owner=mock_node
        )
        assert result == "Node 1.2"

        # disable placeholders resolution
        text = r"\<node_id\> <node_name>"
        mock_node = Mock(node_name="test", node_id="1")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text=text,
            attr_owner=mock_node
        )
        assert result == "<node_id> test"
        
        # resolve with extra args
        mock_node = Mock(node_id="1.2")
        result = simple_tree_renderer._TreeRenderer__resolve_argtext(
            text="Node <node_id> <node_name>", 
            attr_owner=mock_node,
            node_name="test"
        )
        assert result == "Node 1.2 test"
    
    def test_loop_algebra_rotation(self):
        """Test algebraic symbol cyclic rotation logic"""
        
        # no use algebras
        optree = OperationTree(nn.Identity())
        tree_renderer = TreeRenderer(optree.root)
        tree_renderer.loop_algebras = 'ab'
        tree_renderer()
        assert tree_renderer.loop_algebras == 'ab' 
        
        # use one
        optree = OperationTree(nn.Sequential(nn.Identity(),
                                            nn.Identity(),
                                            nn.Identity()))
        tree_renderer = TreeRenderer(optree.root)
        tree_renderer.loop_algebras = 'ab'
        tree_renderer()
        assert tree_renderer.loop_algebras == 'ba'
        
        # use twice
        optree = OperationTree(nn.Sequential(nn.Identity(),
                                            nn.Identity(),
                                            nn.Identity(),
                                            nn.ReLU(),
                                            nn.Identity(),
                                            nn.Identity()))
        tree_renderer = TreeRenderer(optree.root)
        tree_renderer.loop_algebras = 'ab'
        tree_renderer()
        assert tree_renderer.loop_algebras == 'ab'
        
        # use over preset len
        optree = OperationTree(nn.Sequential(nn.Identity(),
                                            nn.Identity(),
                                            nn.Identity(),
                                            nn.ReLU(),
                                            nn.Identity(),
                                            nn.Identity(),
                                            nn.BatchNorm1d(10),
                                            nn.Identity(),
                                            nn.Identity()))
        tree_renderer = TreeRenderer(optree.root)
        tree_renderer.loop_algebras = 'ab'
        tree_renderer()
        assert tree_renderer.loop_algebras == 'ba'
    
    def test_fold_repeat(self, repeat_tree_renderer, monkeypatch):
        """Test whether the fold_repeat option works well"""

        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)
        res = repeat_tree_renderer()
        assert isinstance(res, Tree)
        assert repeat_tree_renderer.render_fold_tree is not None
        assert repeat_tree_renderer.render_unfold_tree is None
        assert isinstance(res.children[1].children[0].label, Panel)

        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", False)
        res = repeat_tree_renderer()
        assert isinstance(res, Tree)
        assert repeat_tree_renderer.render_unfold_tree is not None
        assert isinstance(res.children[1].children[0].label, str)
        assert isinstance(res.children[1].children[0], Tree)

    def test_isolated_rendering(self, repeat_tree_renderer, monkeypatch):
        """Test whether the rendering is performed in a deepcopy tree"""
        
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)
        origin_tree = repeat_tree_renderer.opnode.display_root
        
        res = repeat_tree_renderer()

        # not pollute the original display tree
        assert len(res.children[1].children) == 1
        assert len(origin_tree.children[1].children) == 4

        assert isinstance(res.children[1].children[0].label, Panel)
        assert all(isinstance(i, Tree) for i in origin_tree.children[1].children)

        # not pollute the original operation tree
        oproot = repeat_tree_renderer.opnode
        assert all(c.node_id == f"2.{c_idx+1}" 
                   for c_idx, c in enumerate(oproot.childs["2"].childs.values()))

    def test_node_id_generation(self, repeat_tree_renderer, monkeypatch):
        """Test the generation logic of tree label"""

        repeat_tree_renderer.loop_algebras = "xx"
        repeat_tree_renderer.repeat_footer = None
        repeat_tree_renderer.tree_levels_args = {"all":{"label": "<node_id>"}}

        # fold_repeat = True
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)

        res = repeat_tree_renderer()

        child_1, child_2 = res.children
        repeat_block = child_2.children[0].label
        repeat_block_inner_tree = repeat_block.renderable
        child_2_1 = repeat_block_inner_tree.children[0]
        child_2_2 = repeat_block_inner_tree.children[1]

        # no child_2_3 and child_2_4, cause they are folded and skipped in rendering
        assert len(repeat_block_inner_tree.children) == 2 
        
        assert all(isinstance(c, Tree) for c in [child_1, child_2, child_2_1, child_2_2])
        assert child_1.label == "1"
        assert child_2.label == "2"
        assert child_2_1.label == "2.x"
        assert child_2_2.label == "2.(x+1)"

        # fold_repeat = False
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", False)

        res = repeat_tree_renderer()

        child_1, child_2 = res.children
        child_2_1 = child_2.children[0]
        child_2_2 = child_2.children[1]
        child_2_3 = child_2.children[2]
        child_2_4 = child_2.children[3]
        assert all(isinstance(c, Tree) for c in [child_1, child_2, 
                                                child_2_1, child_2_2, child_2_3, child_2_4])
        assert child_1.label == "1"
        assert child_2.label == "2"
        assert child_2_1.label == "2.1"
        assert child_2_2.label == "2.2"
        assert child_2_3.label == "2.3"
        assert child_2_4.label == "2.4"

    def test_skip_rendering(self, repeat_tree_renderer, monkeypatch):
        """Test whether the skip logic when fold_repeat = True is correct"""

        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)

        # skip control by `_render_when_repeat`
        oproot = repeat_tree_renderer.opnode
        monkeypatch.setattr(oproot, "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["1"], "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["2"], "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["2"].childs["2.1"], "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["2"].childs["2.2"], "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["2"].childs["2.3"], "_render_when_repeat", False)
        monkeypatch.setattr(oproot.childs["2"].childs["2.4"], "_render_when_repeat", False)

        res = repeat_tree_renderer()

        ## display tree is not change
        assert res.label == "0"
        assert res.children[0].label == "1"
        assert res.children[1].label == "1"
        assert all(c.label == "2" for c in res.children[1].children)

        # skip control by `_is_folded`
        monkeypatch.undo()
        oproot._is_folded = True
        oproot.childs["1"]._is_folded = True
        oproot.childs["2"]._is_folded = True
        oproot.childs["2"].childs["2.1"]._is_folded = True
        oproot.childs["2"].childs["2.2"]._is_folded = True
        oproot.childs["2"].childs["2.3"]._is_folded = True
        oproot.childs["2"].childs["2.4"]._is_folded = True

        ## display tree is not change
        assert res.label == "0"
        assert res.children[0].label == "1"
        assert res.children[1].label == "1"
        assert all(c.label == "2" for c in res.children[1].children)

    def test_repeat_body_generation(self, repeat_tree_renderer, monkeypatch):
        """Test whether the repeat body tree is generated correctly"""
        
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)
        repeat_tree_renderer.repeat_footer = None
        repeat_tree_renderer.tree_levels_args = {"2": {"label": "<type>"}}

        res = repeat_tree_renderer()
        repeat_body_tree = res.children[1].children[0].label.renderable
        
        # repeat body tree structure
        assert isinstance(repeat_body_tree, Tree) 
        assert repeat_body_tree.hide_root is True

        assert len(repeat_body_tree.children) == 2
        assert all(isinstance(c, Tree) for c in repeat_body_tree.children)
        
        # repeat body tree content
        assert "Linear" in repeat_body_tree.children[0].label
        assert "ReLU" in repeat_body_tree.children[1].label

    def test_repeat_block_rendering(self, repeat_tree_renderer, monkeypatch):
        """Test whether the repeat block(panel) can be rendered correctly"""
        
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)
        repeat_tree_renderer.repeat_footer = "Footer"
        repeat_tree_renderer.repeat_block_args = {"title": "test title"}

        res = repeat_tree_renderer()
        repeat_panel = res.children[1].children[0].label

        # repeat panel content
        assert isinstance(repeat_panel, Panel)
        assert repeat_panel.title == "test title"
        
        # repeat panel structure
        assert isinstance(repeat_panel.renderable, Group)
        assert len(repeat_panel.renderable.renderables) == 3

        repeat_body_tree, divider, footer = repeat_panel.renderable.renderables
        assert isinstance(repeat_body_tree, Tree)
        assert isinstance(divider, Rule)
        assert isinstance(footer, str)
        assert "Footer" in footer

    def test_style_application(self, repeat_tree_renderer, monkeypatch):
        """Test the levels styles and repeat block styles are applied correctly"""
        
        monkeypatch.setattr("torchmeter.display.__cfg__.tree_fold_repeat", True)
        repeat_tree_renderer.repeat_footer = None
        
        repeat_tree_renderer.tree_levels_args = {
            "default": {"label": "[<node_id>] <name>-<type>",
                        "guide_style": "red"},
            
            "0": {"label": "<name>",
                "style": "magenta"},
            
            "1": {"label": "<node_id>",
                "guide_style": "blue"},
        }
        
        repeat_tree_renderer.repeat_block_args = {
            "title": "test title",
            "style": "cyan"
        }
        
        # level 0
        res = repeat_tree_renderer()
        assert res.label == "RepeatModel"
        assert res.style == "magenta"
        
        # level 1
        child_1, child_2 = res.children
        assert child_1.label == "1"
        assert child_2.label == "2"
        assert all(c.guide_style == "blue" for c in res.children)
        
        # repeat block (panel)
        repeat_panel = child_2.children[0].label
        assert repeat_panel.title == "test title"
        assert repeat_panel.style == "cyan"
        
        # level 2 (use default setting)
        child_2_1, child_2_2 = repeat_panel.renderable.children
        assert child_2_1.label == "[2.x] 0-Linear"
        assert child_2_2.label == "[2.(x+1)] 1-ReLU"
        assert all(c.guide_style == "red" for c in [child_2_1, child_2_2])

    def test_edge_cases(self):
        """Test the edge cases in rendering"""
        
        class EdgeModel(nn.Module):
            def __init__(self):
                super(EdgeModel, self).__init__()
        
        optree = OperationTree(EdgeModel())
        oproot = optree.root
        tree_renderer = TreeRenderer(oproot)
        
        # no child nodes
        res = tree_renderer()
        assert not res.children
        
        # repeat_time is modified to an invalid value
        oproot.repeat_time = 0
        with pytest.raises(RuntimeError):
            tree_renderer()
        
        # repeat_winsz is modified to an invalid value
        oproot.repeat_winsz = 0
        with pytest.raises(RuntimeError):
            tree_renderer()
            
class TestTabularRenderer:

    tbval_getter = lambda _, row_idx, col_idx, tb: tb.columns[col_idx]._cells[row_idx]

    def test_valid_init(self, simple_tabular_renderer):
        """Test valid initialization"""
        assert isinstance(simple_tabular_renderer.opnode, OperationNode)
        
        stats_data = simple_tabular_renderer._TabularRenderer__stats_data
        assert len(stats_data) == len(OperationNode.statistics)

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            TabularRenderer(1)

    def test_stats_data(self, simple_tabular_renderer):
        """Test if the stats data property is set and retrieved correctly"""
        
        stats_data = simple_tabular_renderer.stats_data
        assert stats_data is simple_tabular_renderer._TabularRenderer__stats_data
        assert tuple(stats_data.keys()) == OperationNode.statistics
        assert all(df.is_empty() for df in stats_data.values())

    def test_tb_args(self, simple_tabular_renderer):
        """Test if tb_args is set and retrieved correctly"""
        
        # retrieve
        tb_args = simple_tabular_renderer.tb_args
        assert tb_args is __cfg__.table_display_args
        assert tb_args.is_change()  # newly created, mark as changed

        # new a single field
        tb_args.mark_unchange()
        setattr(simple_tabular_renderer.tb_args, "111", True)
        assert tb_args.is_change()
        assert getattr(tb_args, "111") is True

        # update a field
        tb_args.mark_unchange()
        setattr(simple_tabular_renderer.tb_args, "highlight", False)
        assert tb_args.is_change()
        assert tb_args.highlight is False

        # overwrite
        ## with invalid type
        with pytest.raises(TypeError):
            simple_tabular_renderer.tb_args = 1
        
        ## with invalid field
        with pytest.raises(KeyError):
            simple_tabular_renderer.tb_args = {'invalid_field': 'value'}
        
        ## with combination of invalid field and valid field
        with pytest.raises(KeyError):
            simple_tabular_renderer.tb_args = {'invalid_field': 'value',
                                               'border_style': 'yellow'}
            
        ## update nothing
        tb_args.mark_unchange()
        simple_tabular_renderer.tb_args = {}
        assert tb_args.is_change()
        assert hasattr(tb_args, "box")
        
        ## update several settings
        tb_args.mark_unchange()
        simple_tabular_renderer.tb_args = {"style": "red",
                                           "expand": True}
        assert tb_args.is_change()
        assert tb_args.style == "red"
        assert tb_args.expand is True
    
    def test_col_args(self, simple_tabular_renderer):
        """Test if tb_args is set and retrieved correctly"""
        
        # retrieve
        col_args = simple_tabular_renderer.col_args
        assert col_args is __cfg__.table_column_args
        assert col_args.is_change()  # newly created, mark as changed

        # new a single field
        col_args.mark_unchange()
        setattr(simple_tabular_renderer.col_args, "111", True)
        assert col_args.is_change()
        assert getattr(col_args, "111") is True

        # update a field
        col_args.mark_unchange()
        setattr(simple_tabular_renderer.col_args, "justify", "left")
        assert col_args.is_change()
        assert col_args.justify == "left"

        # overwrite
        ## with invalid type
        with pytest.raises(TypeError):
            simple_tabular_renderer.col_args = 1
        
        ## with invalid field
        with pytest.raises(KeyError):
            simple_tabular_renderer.col_args = {'invalid_field': 'value'}
        
        ## with combination of invalid field and valid field
        with pytest.raises(KeyError):
            simple_tabular_renderer.col_args = {'invalid_field': 'value',
                                                'no_wrap': True}
            
        ## update nothing
        col_args.mark_unchange()
        simple_tabular_renderer.col_args = {}
        assert col_args.is_change()
        assert hasattr(col_args, "style")
        
        ## update several settings
        col_args.mark_unchange()
        simple_tabular_renderer.col_args = {"style": "red",
                                            "vertical": "top"}
        assert col_args.is_change()
        assert col_args.style == "red"
        assert col_args.vertical == "top"
    
    def test_df2tb_structure(self, simple_tabular_renderer, example_df):
        """Test the rendering table structure"""

        with patch("torchmeter.display.apply_setting", side_effect=apply_setting) as mock_apply:
            res = simple_tabular_renderer.df2tb(example_df, show_raw=False)
        
        assert isinstance(res, Table)
        assert len(res.columns) == 5
        assert res.row_count == 3

        tb_headers = [col_obj.header for col_obj in res.columns]
        assert tb_headers == ["numeric" ,  "text" ,  "list_col"  ,  "nomal_obj" , "self_obj"]

        assert str(example_df[0,0]) == self.tbval_getter(0, 0, res)
        assert str(example_df[2,1]) == self.tbval_getter(2, 1, res)
        assert str(example_df[1,2].to_list()) == self.tbval_getter(1, 2, res)
        assert str(example_df[0,3]) == self.tbval_getter(0, 3, res)
        
        # 验证样式应用调用
        mock_apply.assert_any_call(obj=ANY,
                                   setting=simple_tabular_renderer.tb_args, 
                                   omit="columns", 
                                   headers=example_df.columns)
        mock_apply.assert_any_call(obj=ANY,
                                   omit="header",
                                   setting=simple_tabular_renderer.col_args, 
                                   highlight=simple_tabular_renderer.tb_args.highlight)
    
    def test_df2tb_none_handling(self, simple_tabular_renderer, example_df):
        """Test none replacement in rendering table"""
        res = simple_tabular_renderer.df2tb(example_df)
        
        # int none
        assert self.tbval_getter(0, 0, res) == "1"
        assert self.tbval_getter(2, 0, res) == "-"
        
        # str none
        assert self.tbval_getter(1, 1, res) == "-"

        # list none
        assert self.tbval_getter(2, 2, res) == "-"
        
        # normal object none
        assert self.tbval_getter(2, 3, res) == "-"

        # self object none
        assert self.tbval_getter(1, 4, res) == "test none_str"

    def test_df2tb_show_raw(self, simple_tabular_renderer, example_df):
        """Test whether the show_raw argument works well"""

        noraml_res = simple_tabular_renderer.df2tb(example_df, show_raw=False)
        raw_res = simple_tabular_renderer.df2tb(example_df, show_raw=True)
        
        # verify not raw display
        assert self.tbval_getter(0, 0, noraml_res) == "1" 
        assert self.tbval_getter(0, 1, noraml_res) == "a"
        assert self.tbval_getter(1, 2, noraml_res) == "[3]"
        assert self.tbval_getter(1, 3, noraml_res) == "dataframe"
        assert self.tbval_getter(0, 4, noraml_res) == "100 K"
        assert self.tbval_getter(2, 4, noraml_res) == "0.00 ± 0.00"

        # verify raw display
        assert self.tbval_getter(0, 0, raw_res) == "1" 
        assert self.tbval_getter(0, 1, raw_res) == "a"
        assert self.tbval_getter(1, 2, raw_res) == "[3]"
        assert self.tbval_getter(1, 3, raw_res) == "dataframe"
        assert self.tbval_getter(0, 4, raw_res) == "100000.0"
        assert self.tbval_getter(2, 4, raw_res) == "0.0"
    
    def test_clear(self, simple_tabular_renderer, example_df, monkeypatch):
        """Test the stat dataframe clearing logic"""

        monkeypatch.setattr(simple_tabular_renderer, 
                            "_TabularRenderer__stats_data", 
                            {"param": example_df,
                            "cal": example_df,
                            "mem": example_df,
                            "ittp": example_df}
        )

        # clear one stat
        assert not simple_tabular_renderer.stats_data['param'].is_empty()
        simple_tabular_renderer.clear("param")
        assert simple_tabular_renderer.stats_data['param'].is_empty()

        # clear all data
        assert not simple_tabular_renderer.stats_data['cal'].is_empty()
        assert not simple_tabular_renderer.stats_data['mem'].is_empty()
        assert not simple_tabular_renderer.stats_data['ittp'].is_empty()
        simple_tabular_renderer.clear()
        assert all(df.is_empty() for df in simple_tabular_renderer.stats_data.values())

        # clear invalid stat
        with pytest.raises(ValueError):
            simple_tabular_renderer.clear("invalid_stat")
        
        # invalid type of pass-in stat_name
        with pytest.raises(TypeError):
            simple_tabular_renderer.clear(1)

    def test_export(self, simple_tabular_renderer, 
                    example_df, export_dir):
        """Test whether the export method works well"""
        
        from polars import read_csv
        
        # format is not specified
        with pytest.raises(ValueError):
            simple_tabular_renderer.export(df=example_df,
                                           save_path=export_dir)
        
        # format is unsupported
        with pytest.raises(ValueError):
            simple_tabular_renderer.export(df=example_df,
                                           save_path=export_dir,
                                           format="png")
        
        # without format specified
        ## file path specified
        expected_file = os.path.join(export_dir, "Data.csv")
        assert not os.path.exists(expected_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=expected_file)
        assert os.path.exists(expected_file)
        os.remove(expected_file)
                
        # with format specified
        ## dir path specified
        ## format without dot
        expected_file = os.path.join(export_dir, "Identity.xlsx")
        assert not os.path.exists(expected_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=export_dir,
                                       format="xlsx")
        assert os.path.exists(expected_file)
        os.remove(expected_file)
        
        # without file suffix
        ## format with dot
        expected_file = os.path.join(export_dir, "Identity.csv")
        assert not os.path.exists(expected_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=export_dir,
                                       format=".csv") 
        assert os.path.exists(expected_file)
        os.remove(expected_file)
        
        # with file suffix
        expected_file = os.path.join(export_dir, "Identity_suffix.csv")
        assert not os.path.exists(expected_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=export_dir,
                                       format=".csv",
                                       file_suffix="suffix") 
        assert os.path.exists(expected_file)
        os.remove(expected_file)
        
        # enable raw_data
        expected_normal_file = os.path.join(export_dir, "Normal.csv")
        assert not os.path.exists(expected_normal_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=expected_normal_file) 
        assert os.path.exists(expected_normal_file)
        
        expected_raw_file = os.path.join(export_dir, "Raw.csv")
        assert not os.path.exists(expected_raw_file)
        simple_tabular_renderer.export(df=example_df,
                                       save_path=expected_raw_file) 
        assert os.path.exists(expected_raw_file)
        
        normal_data = read_csv(expected_normal_file)
        raw_data = read_csv(expected_raw_file)
        
        assert not all(normal_data["self_obj"] == raw_data["self_obj"])
        
        # list data is converted to str when exporting to csv file
        assert normal_data["list_col"][1] == "[3]"
        
        # object data is converted to str
        assert normal_data["self_obj"][0] == "100 K"
        
        os.remove(expected_normal_file)
        os.remove(expected_raw_file)
        
    def test_new_col(self, simple_tabular_renderer, example_df):
        """Test whether the __new_col method works well"""
        
        from polars import Float64
        
        new_col = simple_tabular_renderer._TabularRenderer__new_col
        
        # invalid column name type
        with pytest.raises(TypeError):
            new_col(df=example_df,
                    col_name=1,
                    col_func=lambda x: "test")
        
        # duplicated column name
        with pytest.raises(ValueError):
            new_col(df=example_df,
                    col_name="self_obj",
                    col_func=lambda x: "test")
        
        # invalid new col index type
        with pytest.raises(TypeError):
            simple_tabular_renderer(stat_name="cal", newcol_idx=1.5) 
            
        # invalid column function type
        with pytest.raises(TypeError):
            new_col(df=example_df,
                    col_name="new_col",
                    col_func="test")
                
        # invalid column function argument num
        ## lack
        with pytest.raises(TypeError):
            new_col(df=example_df,
                    col_name="new_col",
                    col_func=lambda :...)
        
        ## exceed
        with pytest.raises(TypeError):
            new_col(df=example_df,
                    col_name="new_col",
                    col_func=lambda x, y:...)
        
        # invalid column function return
        ## invalid return type
        with pytest.raises(TypeError):
            new_col(df=example_df,
                    col_name="new_col",
                    col_func=lambda x: 1)
        
        ## invalid return len
        with pytest.raises(RuntimeError):
            new_col(df=example_df,
                    col_name="new_col",
                    col_func=lambda x: [1])
        
        # verify function is applied correctly
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: ["test"]*len(x),
                         col_idx=0)
        assert new_df.shape == (3, 6)
        assert new_df.columns[0] == "new_col"
        assert new_df["new_col"].to_list() == ["test"]*3
        
        # verify funtion operation will not influence the original dataframe
        new_df = new_col(df=example_df,
                         col_name="origin_numeric",
                         col_func=lambda df: df.drop_in_place(name="numeric"),
                         col_idx=0)
        assert new_df.shape == (3, 6)
        assert example_df.shape == (3, 5)
        assert example_df.columns == ["numeric", "text", "list_col", "nomal_obj", "self_obj"]
        assert new_df["origin_numeric"].to_list() == example_df["numeric"].to_list()

        # verify col_idx
        ## non-negative and in range
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: ["test"]*len(x),
                         col_idx=1)
        assert new_df.shape == (3, 6)
        assert new_df.columns[1] == "new_col"
        
        ## non-negative and out of range (add last)
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: ["test"]*len(x),
                         col_idx=8) 
        assert new_df.shape == (3, 6)
        assert new_df.columns[5] == "new_col"

        ## negative and in range
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: ["test"]*len(x),
                         col_idx=-1)
        assert new_df.shape == (3, 6)
        assert new_df.columns[-1] == "new_col"
        
        ## negative and out of range (add first)
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: ["test"]*len(x),
                         col_idx=-9)
        assert new_df.shape == (3, 6)
        assert new_df.columns[0] == "new_col"
    
        ## verify return_type is correctly applied
        new_df = new_col(df=example_df,
                         col_name="new_col",
                         col_func=lambda x: [1]*len(x),
                         return_type=float)
        assert new_df["new_col"].dtype == Float64
    
    def test_call_valid_use(self, universal_tabular_renderer):
        """Test the valid usage cases of TabularRenderer.__call__"""
        
        tb, data = universal_tabular_renderer(stat_name="param")

        assert isinstance(tb, Table)
        assert isinstance(data, DataFrame)
        assert data.shape == (3, 6) # 1 (unuse) + 2 (conv: weight + bias) 
      
    def test_call_invalid_use(self, simple_tabular_renderer):
        """Test the invalid usage cases of TabularRenderer.__call__"""
        
        # invalid stat name
        with pytest.raises(ValueError):
            simple_tabular_renderer(stat_name="invalid stat")
        
        # invalid pick_col type
        with pytest.raises(TypeError):
            simple_tabular_renderer(stat_name="cal", pick_col=1)
        
        # invalid exclude_cols type
        with pytest.raises(TypeError):
            simple_tabular_renderer(stat_name="cal", exclude_cols=1)
        
        # invalid custom_cols type
        with pytest.raises(TypeError):
            simple_tabular_renderer(stat_name="cal", custom_cols=1)
    
    @patch("torchmeter.display.dfs_task", side_effect=dfs_task)
    def test_call_data_acquisition(self, mock_dfs_task,
                                   simple_tabular_renderer, universal_tabular_renderer):
        """Test the stat data acquisition logic"""
        
        class EasyModel(nn.Module):
            def __init__(self):
                super(EasyModel, self).__init__()
                self.conv = nn.Conv2d(3,10,3)
            def forward(self, x):
                return self.conv(x)
                
        # skipping when using a layer as a model
        simple_tabular_renderer.clear()
        with pytest.raises(RuntimeError):
            simple_tabular_renderer("param")
        
        # fill dataframe through dfs in the first call
        optree = OperationTree(EasyModel())
        tabular_renderer = TabularRenderer(optree.root)
        tabular_renderer.clear()
        tb,data1 = tabular_renderer(stat_name="param")
        assert data1.shape == (2, 6) # 2: weight + bias 
        assert mock_dfs_task.call_count == 2 # root + conv
        
        stat_data = tabular_renderer.stats_data
        assert not stat_data["param"].is_empty()
        
        # reuse data in latter call
        tb, data2 = tabular_renderer(stat_name="param")
        assert mock_dfs_task.call_count == 2 # stay no change
        
        # verify no-called module warning
        oproot = universal_tabular_renderer.opnode
        universal_tabular_renderer.clear()
        list(map(lambda n:n.cal.measure(), list(oproot.childs.values()) + [oproot]))
        with pytest.warns(RuntimeWarning) as w:
            oproot.operation(torch_randn(1, 3, 20, 20))
            tb, data = universal_tabular_renderer(stat_name="cal")
        assert "not explicitly called" in str(w[0].message)        
        
    def test_call_pick_col(self, universal_tabular_renderer):
        """Test the column selection logic"""
        
        universal_tabular_renderer.clear()
        
        # valid usage
        _, data1 = universal_tabular_renderer(stat_name="param",
                                             pick_cols=["Operation_Id", 
                                                        "Operation_Name",
                                                        "Param_Name",
                                                        "Numeric_Num"])
        assert data1.columns == ["Operation_Id", "Operation_Name", "Param_Name", "Numeric_Num"]
        
        # pick and reorder columns
        _, data2 = universal_tabular_renderer(stat_name="param",
                                              pick_cols=["Numeric_Num",
                                                         "Param_Name",
                                                         "Operation_Name",
                                                         "Operation_Id"])
        assert data2.columns == ["Numeric_Num", "Param_Name", "Operation_Name", "Operation_Id"]
        
        # invalid column name
        with pytest.raises(ValueError):
            universal_tabular_renderer(stat_name="param",
                                       pick_cols=["invalid_col"])
            
    def test_call_exclude_col(self, universal_tabular_renderer):
        """Test the column exclusion logic"""
        
        universal_tabular_renderer.clear()
        
        _, data = universal_tabular_renderer("param",
                                             exclude_cols=["Operation_Type", 
                                                           "Operation_Name"])
        assert "Operation_Type" not in data.columns
        assert "Operation_Name" not in data.columns

    def test_call_custom_col(self, universal_tabular_renderer):
        """Test column name customization logic"""
        
        universal_tabular_renderer.clear()
        
        # basic usage
        _, data = universal_tabular_renderer(stat_name="param",
                                             keep_custom_name=False,
                                             custom_cols={"Operation_Id": "Operation Id",
                                                          "Operation_Name": "Operation Name",
                                                          "Numeric_Num": "Numeric Value"})
        assert all(col_name not in data.columns for col_name in ["Operation_Id", 
                                                                 "Operation_Name",
                                                                 "Numeric_Num"])
        assert all(col_name in data.columns for col_name in ["Operation Id", 
                                                              "Operation Name",
                                                              "Numeric Value"])
        
        # invalid column name
        _, data = universal_tabular_renderer(stat_name="param",
                                             keep_custom_name=False,
                                             custom_cols={"invalid_col": "invalid col"})
        assert "invalid_col" not in data.columns
        
        # verify option: whether keep customized column name
        _, data = universal_tabular_renderer(stat_name="param",
                                             keep_custom_name=True,
                                             custom_cols={"Operation_Id": "Operation Id"})
        assert "Operation_Id" not in data.columns
        assert "Operation Id" in data.columns
        
        ## the same column name's recustomization should base on the new name
        _, data = universal_tabular_renderer(stat_name="param",
                                             keep_custom_name=True,
                                             custom_cols={"Operation_Id": "Operation ID"})
        assert "Operation ID" not in data.columns
        
        _, data = universal_tabular_renderer(stat_name="param",
                                             keep_custom_name=True,
                                             custom_cols={"Operation Id": "Operation ID"})
        assert "Operation ID" in data.columns
            
    def test_call_pick_exclude_cooperation(self, universal_tabular_renderer):
        """Test whether exclude logic and selection logic work well together"""
        
        universal_tabular_renderer.clear()
        
        # pick_col and exclude_col are mutually exclusive
        # then exclude_col does not take effect
        _, data = universal_tabular_renderer(stat_name="param",
                                             pick_cols=["Operation_Id",
                                                        "Param_Name",
                                                        "Numeric_Num"],
                                             exclude_cols=["Operation_Name"])
        assert data.columns == ["Operation_Id", "Param_Name", "Numeric_Num"]
        
        # pick_col and exclude_col have intersection
        # then exclude_col takes effect
        _, data = universal_tabular_renderer(stat_name="param",
                                             pick_cols=["Operation_Id",
                                                        "Param_Name",
                                                        "Numeric_Num"],
                                             exclude_cols=["Operation_Id"])
        assert data.columns == ["Param_Name", "Numeric_Num"]

    def test_call_pick_custom_cooperation(self, universal_tabular_renderer):
        """Test whether custom_col logic works after selection logic"""
        
        universal_tabular_renderer.clear()
        
        # pick_col and custom_col are mutually exclusive
        # then custom_col does not take effect
        _, data = universal_tabular_renderer(stat_name="param",
                                             pick_cols=["Operation_Id",
                                                        "Param_Name"],
                                             custom_cols={"Operation_Type": "Operation Type"})
        assert data.columns == ["Operation_Id", "Param_Name"]
        
        # pick_col and custom_col have intersection
        # then use the origin name to pick columns and then customization takes effect
        _, data = universal_tabular_renderer(stat_name="param",
                                             pick_cols=["Operation_Id",
                                                        "Param_Name"],
                                             custom_cols={"Operation_Id": "Operation ID"})
        assert data.columns == ["Operation ID", "Param_Name"]
        
        # selection does happen before customization
        with pytest.raises(ValueError):
            universal_tabular_renderer(stat_name="param",
                                       pick_cols=["Operation ID2"],
                                       custom_cols={"Operation ID": "Operation ID2"})
        
    def test_call_keep_new_col(self, universal_tabular_renderer):
        """Test whether the keep_new_col option works well"""
        
        universal_tabular_renderer.clear()
        
        # not to keep
        _, data = universal_tabular_renderer(stat_name="param",
                                             newcol_name="test",
                                             newcol_func=lambda x: ["test"]*len(x),
                                             keep_new_col=False)
        assert "test" in data.columns
        assert "test" not in universal_tabular_renderer.stats_data["param"].columns
        
        # keep
        _, data = universal_tabular_renderer(stat_name="param",
                                             newcol_name="test",
                                             newcol_func=lambda x: ["test"]*len(x),
                                             keep_new_col=True)
        assert "test" in data.columns
        assert "test" in universal_tabular_renderer.stats_data["param"].columns

    @patch('torchmeter.display.TabularRenderer.export')
    def test_export_trigger(self, mock_export, universal_tabular_renderer):
        """Test whether the save_to argument can trigger export"""

        # not trigger
        universal_tabular_renderer(stat_name="param")
        mock_export.assert_not_called()
        
        # trigger
        universal_tabular_renderer(stat_name="param", save_to="test.csv")
        mock_export.assert_called_once()

    def test_style_application(self, universal_tabular_renderer):
        """Test the levels styles and repeat block styles are applied correctly"""
        
        universal_tabular_renderer.tb_args = {
            "style": "red",
            "highlight": False,
            "caption": "test caption",
            "show_lines": True
        }
        
        universal_tabular_renderer.col_args = {
            "style": "blue",
            "justify": "left",
            "no_wrap": True
        }

        tb, _ = universal_tabular_renderer(stat_name="param")
        col = tb.columns[0]

        assert tb.style == "red"
        assert tb.highlight is False
        assert tb.caption == "test caption"
        assert tb.show_lines is True

        assert col.style == "blue"
        assert col.justify == "left"
        assert col.no_wrap is True

    def test_edge_cases(self, simple_tabular_renderer):
        """Test the edge cases in rendering"""
        
        from polars import Float64 as pl_float64

        # rebder empty dataframe
        empty_df = DataFrame(schema={"col1": pl_float64})
        res = simple_tabular_renderer.df2tb(empty_df)
        
        assert res.row_count == 0
        assert len(res.columns) == 1
