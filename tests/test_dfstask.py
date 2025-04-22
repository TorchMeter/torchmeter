import pytest

from torchmeter.utils import dfs_task

class TreeNode:
    def __init__(self, val, left=None, right=None) -> None:
        self.val = val
        self.left = left
        self.right = right


class GraphNode:
    def __init__(self, val) -> None:
        self.val = val
        self.children = []


@pytest.fixture
def binary_tree_root():
    """Build a binary tree for test:
         1
       /   \
      2     3
     / \
    4   5
    """
    n4 = TreeNode(4)
    n5 = TreeNode(5)
    n2 = TreeNode(2, n4, n5)
    n3 = TreeNode(3)
    return TreeNode(1, n2, n3)


@pytest.fixture
def cyclic_graph_stnode():
    """Create a cyclic graph:
    A → B → C
    ↑       ↓
    D ← ← ← 
    """
    node_a = GraphNode('A')
    node_b = GraphNode('B')
    node_c = GraphNode('C')
    node_d = GraphNode('D')
    
    node_a.children = [node_b]
    node_b.children = [node_c]
    node_c.children = [node_d]
    node_d.children = [node_a]
    return node_a


@pytest.mark.vital
class TestDfsTask:
    # basic funtion test
    def test_binary_tree_traversal(self, binary_tree_root) -> None:
        """Test standard binary tree preorder traversal using DFS"""

        traversal_order = []
        
        # task function: preorder traversal
        def record_node(subject, pre_res=[]):
            if subject is None:
                return pre_res
            traversal_order.append(subject.val)
            return [*pre_res, subject.val]
        
        dfs_task(
            dfs_subject=binary_tree_root,
            adj_func=lambda n: [child for child in (n.left, n.right) if child is not None],
            task_func=record_node,
            visited_signal_func=lambda x: id(x),
            visited=[]
        )
        
        assert traversal_order == [1, 2, 4, 5, 3]

    def test_cyclic_graph_traversal(self, cyclic_graph_stnode) -> None:
        """Test the traversal of a cyclic graph"""
        visited_nodes = []
        
        def track_nodes(subject, pre_res=[]):
            visited_nodes.append(subject.val)
            return [*pre_res, subject.val]
        
        dfs_task(
            dfs_subject=cyclic_graph_stnode,
            adj_func=lambda n: n.children,
            task_func=track_nodes,
            visited_signal_func=lambda x: x.val,
            visited=[]
        )
        
        assert visited_nodes == ['A', 'B', 'C', 'D']

    # boundary condition test
    def test_single_node_traversal(self, binary_tree_root) -> None:
        """Test single node traversal"""
        def identity_task(subject, pre_res=[]):
            return [*pre_res, subject.val]
        
        result = dfs_task(
            dfs_subject=binary_tree_root,
            adj_func=lambda _: [],
            task_func=identity_task,
            visited=[]
        )
        
        assert result == [1]

    def test_custom_visit_signal(self) -> None:
        """Test custom visit signal function"""
        visited_signals = []
        
        def custom_signal(x):
            sig = f"CUSTOM_{x}"
            visited_signals.append(sig)
            return sig
        
        dfs_task(
            dfs_subject=1,
            adj_func=lambda x: [x + 1] if x < 3 else [],
            task_func=lambda subject, pre_res=[]: None,
            visited_signal_func=custom_signal,
            visited=[]
        )
        
        assert visited_signals == ["CUSTOM_1", "CUSTOM_2", "CUSTOM_3"]

    # Error handling test
    def test_invalid_task_function(self) -> None:
        """Test invalid task function signature"""
        def invalid_task(missing_arg):
            return missing_arg
        
        with pytest.raises(RuntimeError) as excinfo:
            dfs_task(
                dfs_subject=1,
                adj_func=lambda x: [],
                task_func=invalid_task,
                visited=[]
            )
        
        assert "missing following required args: ['subject', 'pre_res']" in str(excinfo.value).lower()

    # Special scenario testing
    def test_mutable_default_visited(self) -> None:
        """Test whether the default visited argument is isolated"""
        def safe_task(subject, pre_res=[]):
            return [*pre_res, subject]
        
        result1 = dfs_task(
            dfs_subject="test",
            adj_func=lambda x: [],
            task_func=safe_task
        )
        
        result2 = dfs_task(
            dfs_subject="test",
            adj_func=lambda x: [],
            task_func=safe_task
        )
        
        assert result1 == ["test"]
        assert result2 == ["test"]  # fail if the default value is shared
