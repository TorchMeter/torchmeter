from collections import OrderedDict
from unittest.mock import patch

import pytest
import torch.nn as nn

from torchmeter.engine import CalMeter, MemMeter, IttpMeter, ParamsMeter, OperationNode, OperationTree


@pytest.fixture
def linear_model():
    return nn.Linear(10, 5)


@pytest.fixture
def sequential_model():
    """A sequential model with a repeat structure"""
    return nn.Sequential(
        OrderedDict([
            ("first_conv", nn.Conv2d(3, 6, 3)),
            ("first_relu", nn.ReLU()),
            ("second_conv", nn.Conv2d(3, 6, 3)),
            ("second_relu", nn.ReLU()),
        ])
    )


@pytest.fixture
def nested_model(linear_model, sequential_model):
    return nn.Sequential(OrderedDict([("s", sequential_model), ("l", linear_model)]))


@pytest.fixture
def check_scanning_process(capsys):
    yield
    captured = capsys.readouterr()
    assert "Finish Scanning model in" in captured.out


@pytest.mark.vital
class TestOPN:
    def test_invalid_init(self) -> None:
        """Test whether non-module object cannot be initialized"""
        with pytest.raises(TypeError):
            OperationNode(module="not_a_module")

    def test_valid_init(self, linear_model) -> None:
        """Test basic attributes"""

        assert OperationNode.statistics == ("param", "cal", "mem", "ittp")

        node = OperationNode(
            module=linear_model,
            name="TestLinear",
            node_id="1.2.3",
        )

        assert node.operation == linear_model
        assert node.type == "Linear"
        assert node.name == "TestLinear"
        assert node.node_id == "1.2.3"
        assert node.parent is None
        assert isinstance(node.childs, OrderedDict)
        assert node.is_leaf is True
        assert node.repeat_winsz == 1
        assert node.repeat_time == 1
        assert node._repeat_body == []
        assert node._render_when_repeat is False
        assert node._is_folded is False

    def test_module_repr(self, linear_model, sequential_model) -> None:
        """Test the module_repr attribute"""

        node = OperationNode(module=linear_model)
        assert node.module_repr == str(linear_model)

        node = OperationNode(module=sequential_model)
        assert node.module_repr == str(sequential_model.__class__.__name__)

    def test_default_name(self, linear_model) -> None:
        """Test the default name is the type name when no name is provided"""
        node = OperationNode(module=linear_model)
        assert node.name == "Linear"

    def test_hierarchical_attrs(self, linear_model) -> None:
        """Test parent-child relationship"""
        parent = OperationNode(module=nn.Module(), node_id="1")
        child = OperationNode(
            module=linear_model,
            parent=parent,
            node_id="1.1",
        )

        parent.childs["1.1"] = child

        assert child.parent is parent
        assert "1.1" in parent.childs
        assert parent.childs["1.1"] is child

    def test_is_leaf(self, linear_model, sequential_model) -> None:
        """Test the is_leaf property is correcttly set"""
        leaf_node = OperationNode(module=linear_model)
        non_leaf_node = OperationNode(module=sequential_model)

        assert leaf_node.is_leaf is True
        assert non_leaf_node.is_leaf is False

    @pytest.mark.parametrize(
        argnames=("stat_name", "stat_cls"),
        argvalues=[
            ("param", ParamsMeter),
            ("cal", CalMeter),
            ("mem", MemMeter),
            ("ittp", IttpMeter),
        ],
    )
    def test_statistic_attrs(self, linear_model, stat_name, stat_cls) -> None:
        """Test whether all the statistic attributes are created correctly and are all read-only"""
        node = OperationNode(module=linear_model)

        stat = getattr(node, stat_name)
        assert isinstance(stat, stat_cls)
        assert stat._opnode is node

        with pytest.raises(AttributeError):
            node.param = None

        with pytest.raises(AttributeError):
            delattr(node, stat_name)

    def test_repr(self, linear_model, sequential_model) -> None:
        """Test repr"""
        leaf_node = OperationNode(module=linear_model)
        non_leaf_node = OperationNode(module=sequential_model)

        assert repr(leaf_node) == f"0 Linear: {linear_model!s}"
        assert repr(non_leaf_node) == "0 Sequential: Sequential"


@pytest.mark.vital
@pytest.mark.usefixtures("check_scanning_process")
class TestOPT:
    def test_single_layer_model(self, linear_model) -> None:
        """Test building operation tree for a single-layer model"""
        tree = OperationTree(linear_model)

        assert len(tree.all_nodes) == 1

        # basic attributes
        root = tree.root
        assert root.operation is linear_model
        assert root.type == "Linear"
        assert root.name == "Linear"
        assert root.node_id == "0"

        # hierarchical attributes
        assert root.parent is None
        assert not root.childs
        assert root.is_leaf is True

        # repeat-related attributes
        assert root.repeat_winsz == 1
        assert root.repeat_time == 1
        assert root._repeat_body == []

        # display-related attributes
        assert root.display_root.label == "0"
        assert root._render_when_repeat is True
        assert root._is_folded is False

    def test_sequential_model(self, sequential_model) -> None:
        """Test building operation tree for a sequential model"""
        tree = OperationTree(sequential_model)

        assert len(tree.all_nodes) == 5

        # basic attributes
        root = tree.root
        assert root.operation is sequential_model
        assert root.type == "Sequential"
        assert root.name == "Sequential"
        assert root.node_id == "0"

        # hierarchical attributes
        assert root.parent is None
        assert len(root.childs) == 4
        assert list(root.childs.keys()) == ["1", "2", "3", "4"]  # it is node_id also
        assert all(c.parent is root for c in root.childs.values())
        assert all(not c.childs for c in root.childs.values())

        assert root.childs["1"].type == "Conv2d"
        assert root.childs["2"].type == "ReLU"
        assert root.childs["3"].type == "Conv2d"
        assert root.childs["4"].type == "ReLU"

        assert root.childs["1"].name == "first_conv"
        assert root.childs["2"].name == "first_relu"
        assert root.childs["3"].name == "second_conv"
        assert root.childs["4"].name == "second_relu"

        # repeat-related attributes
        assert root.repeat_winsz == 1
        assert root.repeat_time == 1
        assert root._repeat_body == []

        assert root.childs["1"].repeat_winsz == 2
        assert root.childs["1"].repeat_time == 2
        assert root.childs["1"]._repeat_body == [("1", "first_conv"), ("2", "first_relu")]
        assert all(c.repeat_winsz == 1 for c in root.childs.values() if c.node_id != "1")
        assert all(c.repeat_time == 1 for c in root.childs.values() if c.node_id != "1")
        assert all(not c._repeat_body for c in root.childs.values() if c.node_id != "1")

        # display-related attributes
        assert all(hasattr(n, "display_root") for n in tree.all_nodes)
        assert root.display_root.label == "0"
        assert all(c.display_root.label == "1" for c in root.childs.values())
        assert root._render_when_repeat is True
        assert root.childs["1"]._render_when_repeat is True
        assert root.childs["2"]._render_when_repeat is True
        assert root.childs["3"]._render_when_repeat is False
        assert root.childs["4"]._render_when_repeat is False
        assert root._is_folded is False
        assert root.childs["1"]._is_folded is False
        assert root.childs["2"]._is_folded is True  # True because in the repeat_body
        assert root.childs["3"]._is_folded is False  # False because skip the visit
        assert root.childs["4"]._is_folded is False  # False because skip the visit

    def test_nested_model(self, nested_model) -> None:
        """Test building operation tree for a sequential model"""
        tree = OperationTree(nested_model)

        assert len(tree.all_nodes) == 7

        # basic attributes
        root = tree.root
        assert root.operation is nested_model
        assert root.type == "Sequential"
        assert root.name == "Sequential"
        assert root.node_id == "0"

        # hierarchical attributes
        assert root.parent is None
        assert len(root.childs) == 2
        assert sum(len(c.childs) for c in root.childs.values()) == 4
        assert list(root.childs.keys()) == ["1", "2"]  # it is node_id also

        child_1 = root.childs["1"]
        child_2 = root.childs["2"]
        assert list(child_1.childs.keys()) == ["1.1", "1.2", "1.3", "1.4"]  # it is node_id also
        assert not child_2.childs
        assert all(c.parent is root for c in root.childs.values())
        assert all(c.parent is child_1 for c in child_1.childs.values())

        assert root.childs["1"].type == "Sequential"
        assert root.childs["2"].type == "Linear"
        assert child_1.childs["1.1"].type == "Conv2d"
        assert child_1.childs["1.2"].type == "ReLU"
        assert child_1.childs["1.3"].type == "Conv2d"
        assert child_1.childs["1.4"].type == "ReLU"

        assert root.childs["1"].name == "s"
        assert root.childs["2"].name == "l"
        assert child_1.childs["1.1"].name == "first_conv"
        assert child_1.childs["1.2"].name == "first_relu"
        assert child_1.childs["1.3"].name == "second_conv"
        assert child_1.childs["1.4"].name == "second_relu"

        # repeat-related attributes
        assert root.repeat_winsz == 1
        assert root.repeat_time == 1
        assert root._repeat_body == []

        assert all(c.repeat_winsz * c.repeat_time == 1 for c in root.childs.values())
        assert all(not c._repeat_body for c in root.childs.values())
        assert child_1.childs["1.1"].repeat_winsz == 2
        assert child_1.childs["1.1"].repeat_time == 2
        assert child_1.childs["1.1"]._repeat_body == [("1.1", "first_conv"), ("1.2", "first_relu")]
        assert all(c.repeat_winsz * c.repeat_time == 1 for c in child_1.childs.values() if c.node_id != "1.1")
        assert all(not c._repeat_body for c in child_1.childs.values() if c.node_id != "1.1")

        # display-related attributes
        assert all(hasattr(n, "display_root") for n in tree.all_nodes)
        assert root.display_root.label == "0"
        assert all(c.display_root.label == "1" for c in root.childs.values())
        assert all(c.display_root.label == "2" for c in child_1.childs.values())
        assert root._render_when_repeat is True
        assert all(c._render_when_repeat is True for c in root.childs.values())
        assert child_1.childs["1.1"]._render_when_repeat is True
        assert child_1.childs["1.2"]._render_when_repeat is True
        assert child_1.childs["1.3"]._render_when_repeat is False
        assert child_1.childs["1.4"]._render_when_repeat is False
        assert root._is_folded is False
        assert all(c._is_folded is False for c in root.childs.values())
        assert child_1.childs["1.1"]._is_folded is False
        assert child_1.childs["1.2"]._is_folded is True  # True because in the repeat_body
        assert child_1.childs["1.3"]._is_folded is False  # False because skip the visit
        assert child_1.childs["1.4"]._is_folded is False  # False because skip the visit

    def test_repeat_detection(self) -> None:
        """Test repeat detection"""
        model = nn.Sequential(*[nn.Conv2d(3, 6, 3) for _ in range(4)], nn.ReLU())

        tree = OperationTree(model)
        root = tree.root

        assert root.repeat_winsz == 1
        assert root.repeat_time == 1
        assert root._repeat_body == []

        assert all(c.repeat_winsz * c.repeat_time == 1 for c in root.childs.values() if c.name != "0")
        assert all(not c._repeat_body for c in root.childs.values() if c.name != "0")

        assert root.childs["1"].repeat_winsz == 1  # not 4 because all the layers in the repeat block are the same
        assert root.childs["1"].repeat_time == 4
        assert root.childs["1"]._repeat_body == [("1", "0")]

        assert root._render_when_repeat is True
        assert root.childs["1"]._render_when_repeat is True
        assert root.childs["2"]._render_when_repeat is False
        assert root.childs["3"]._render_when_repeat is False
        assert root.childs["4"]._render_when_repeat is False
        assert root.childs["5"]._render_when_repeat is True
        assert root._is_folded is False
        assert root.childs["1"]._is_folded is False
        assert root.childs["2"]._is_folded is False  # True because in the repeat_body
        assert root.childs["3"]._is_folded is False  # False because skip the visit
        assert root.childs["4"]._is_folded is False  # False because skip the visit
        assert root.childs["5"]._is_folded is False

    def test_display_tree_construction(self, nested_model) -> None:
        """Test building display tree"""
        tree = OperationTree(nested_model)

        root = tree.root
        child_1 = root.childs["1"]
        child_2 = root.childs["2"]

        # verify display tree label, i.e. the level of the node in the display tree
        assert root.display_root.label == "0"
        assert all(c.display_root.label == "1" for c in root.childs.values())
        assert all(c.display_root.label == "2" for c in child_1.childs.values())

        # verify display tree hierarchical structure
        assert len(root.display_root.children) == 2
        assert len(child_1.display_root.children) == 4
        assert not len(child_2.display_root.children)
        assert child_2.display_root in root.display_root.children

    def test_large_scale_model_construction(self) -> None:
        model = nn.Sequential(*[nn.Sequential(nn.Linear(100, 100), nn.ReLU()) for _ in range(100)])
        tree = OperationTree(model)

        assert len(tree.all_nodes) == 301
        assert tree.root.childs["100"].childs["100.2"].type == "ReLU"

    def test_custom_module(self) -> None:
        """Test model made up of custom module and standard module"""

        class CustomLayer(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.layer = nn.Linear(10, 10)

        model = nn.Sequential(CustomLayer(), nn.Sequential(nn.ReLU(), nn.Tanh()))

        tree = OperationTree(model)
        root = tree.root

        assert root.childs["1"].type == "CustomLayer"
        assert root.childs["2"].type == "Sequential"

        assert root.childs["1"].childs["1.1"].name == "layer"
        assert root.childs["1"].childs["1.1"].type == "Linear"
        assert root.childs["2"].childs["2.1"].name == "0"
        assert root.childs["2"].childs["2.1"].type == "ReLU"
        assert root.childs["2"].childs["2.2"].name == "1"
        assert root.childs["2"].childs["2.2"].type == "Tanh"

    def test_repr(self, nested_model) -> None:
        """Test __repr__ logic"""

        tree = OperationTree(nested_model)
        root = tree.root

        with patch.object(root, "__repr__", wraps=root.__repr__) as mock_opn_repr:
            str(tree)
            mock_opn_repr.assert_called_once()


@pytest.mark.vital
def test_invalid_init() -> None:
    """Test whether non-module object cannot be initialized"""
    with pytest.raises(TypeError):
        OperationTree(model="not_a_module")
