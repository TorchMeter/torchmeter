from __future__ import annotations
from typing import TYPE_CHECKING

import re
from collections import OrderedDict

import torch.nn as nn
from rich.tree import Tree

from torchmeter.utils import dfs_task, Timer
from torchmeter.statistic import ParamsMeter, CalMeter, MemMeter, IttpMeter

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    OPNODE_LIST = List["OperationNode"]

__all__ = ["OperationNode", "OperationTree"]

class OperationNode:
   
    statistics:Tuple[str, ...] = ('param', 'cal', 'mem', 'ittp') # all statistics stored as attributes

    def __init__(self, 
                 module:nn.Module,
                 name:Optional[str]=None,
                 node_id:str='0',
                 parent:Optional[OperationNode]=None):

        if not isinstance(module, nn.Module):
            raise TypeError(f"You must use an `nn.Module` instance to instantiate `{self.__class__.__name__}`, " + \
                            f"but got `{type(module).__name__}`.")
        
        # basic info
        self.operation = module
        self.type:str = module.__class__.__name__
        self.name:str = name if name else self.type
        self.node_id:str = node_id # index in the model tree, e.g. '1.2.1'
        
        # hierarchical info
        self.parent:Optional[OperationNode] = parent
        self.childs:OrderedDict[str, "OperationNode"] = OrderedDict() # e.g. {'1.2.1': OperationNode, ...} 
        self.is_leaf:bool = len(module._modules) == 0
        
        # repeat info
        self.repeat_winsz:int = 1 # size of repeat block
        self.repeat_time:int = 1
        self._repeat_body:List[Tuple[str, str]] = [] # the ids and names of the nodes in the same repeat block
        
        # display info 
        self.display_root:Tree # set in `OperationTree.__build()`
        self._render_when_repeat:bool = False # whether to render when enable `fold_repeat`, set in `OperationTree.__build()`
        self._is_folded = False # whether the node is folded in a repeat block, set in `OperationTree.__build()`
        self.module_repr = str(self.type) if not self.is_leaf else str(self.operation)

        # statistic info (all read-only)
        self.__param = ParamsMeter(opnode=self)
        self.__cal = CalMeter(opnode=self)
        self.__mem = MemMeter(opnode=self)
        self.__ittp = IttpMeter(opnode=self)

    @property
    def param(self) -> ParamsMeter:
        return self.__param

    @property
    def cal(self) -> CalMeter:
        return self.__cal

    @property
    def mem(self) -> MemMeter:
        return self.__mem
    
    @property
    def ittp(self) -> IttpMeter:
        return self.__ittp
    
    def __repr__(self) -> str:
        return f"{self.node_id} {self.name}: {self.module_repr}"
    
class OperationTree:

    def __init__(self, model:nn.Module) -> None:
        
        if not isinstance(model, nn.Module):
            raise TypeError(f"You must use an `nn.Module` instance to instantiate `{self.__class__.__name__}`, " + \
                            f"but got `{type(model).__name__}`.")
        
        self.root = OperationNode(module=model)
        self.root._render_when_repeat = True
        
        with Timer(task_desc="Scanning model"):
            nonroot_nodes, *_ = dfs_task(dfs_subject=self.root, 
                                         adj_func=lambda x:x.childs.values(),
                                         task_func=OperationTree.__build,
                                         visited=[])

        self.all_nodes:OPNODE_LIST = [self.root] + nonroot_nodes
            
    @staticmethod
    def __build(subject:OperationNode,
                pre_res:Tuple[Optional[OPNODE_LIST], Optional[Tree]]=(None, None)) \
                    -> Tuple[OPNODE_LIST, Optional[Tree]]:
        """
        Private method.
        
        This function will explore the model structure, unfold all multi-layers modules, and organize them into a tree structure.
        
        Finally, it will build a display tree and a operation tree in one DFS recursion, simutaneously.
        
        With the built display tree, the terminal display of the model structure can be achieved.
        
        With the built operation tree, the model statistic can be easily and quickly accessed.

        Args:
        ---
        This function serves as the `task_func` in `torchmeter.utils.dfs_task`, 
        therefore having the following two arguments:
        
            - `subject` (OperationNode): the node to be traversed in the operation tree.
            
            - `pre_res` (Tuple[List["OperationNode"], Optional[Tree]]): the container of all nodes and the father node of the display tree 
        
        Returns:
        ---
            Tuple[List["OperationNode"], Optional[Tree]]: the current traversed node of the operation tree and display tree
        """
        
        all_nodes, *display_parent = pre_res
        all_nodes = all_nodes if all_nodes else []
        
        # build display tree
        if display_parent and display_parent[0] is not None:
            display_parent_node = display_parent[0]
            
            # create a tree node of rich.Tree, and record the level of the node in attribute 'label'
            display_node = Tree(label=str(int(display_parent_node.label)+1))  # type: ignore
            
            # add the current node to the father node
            display_parent_node.children.append(display_node)                 # type: ignore
        else:
            # situation of root node
            display_node = Tree(label='0')
        
        # link the display node to the attribute `display_root` of operation node
        subject.display_root = display_node
        
        # build operation tree
        copy_childs, str_childs = [], []
        for access_idx, (module_name, module) in enumerate(subject.operation._modules.items()):
            module_idx = (subject.node_id if subject.node_id != '0' else '') + \
                         ('.' if subject.node_id != '0' else '') + \
                         str(access_idx+1)
                         
            child = OperationNode(module=module,    # type: ignore
                                  name=module_name,
                                  parent=subject,
                                  node_id=module_idx)
            
            all_nodes.append(child)
            
            subject.childs[module_idx] = child
            copy_childs.append(child)
            str_childs.append(re.sub(r'\(.*?\):\s', repl='', string=str(module)))
        
        # find all potantial maximum repeat block in currently traversed level using greedy strategy
        slide_start_idx = 0
        while slide_start_idx < len(str_childs):
            now_node = copy_childs[slide_start_idx]
            now_node._render_when_repeat = True & subject._render_when_repeat
            
            # find the maximum window size `m` that satifies `str_childs[0:m] == str_childs[m:2*m]`
            exist_repeat = False
            for win_size in range((len(str_childs)-slide_start_idx)//2, 0, -1):
                win1_start_end = [slide_start_idx, slide_start_idx+win_size]
                win2_start_end = [slide_start_idx+win_size, slide_start_idx+win_size*2]
                
                if str_childs[slice(*win1_start_end)] == str_childs[slice(*win2_start_end)]:
                    exist_repeat =True
                    break
            
            # if the maximum window size `m` does exist, then try to explore the repeat time of the window
            if exist_repeat:
                # whether all the modules in the window are the same
                inner_repeat = len(set(str_childs[win1_start_end[0]:win2_start_end[1]])) == 1 
                
                # multiply the window size `m` by 2 if all the modules in the window are the same
                repeat_time = win_size*2 if inner_repeat else 2
                win_size = 1 if inner_repeat else win_size
                
                win2_start_end[0] += win_size
                win2_start_end[1] += win_size
                
                while str_childs[slice(*win1_start_end)] == str_childs[slice(*win2_start_end)]:
                    repeat_time += 1
                    
                    win2_start_end[0] += win_size
                    win2_start_end[1] += win_size
                
                now_node.repeat_winsz = win_size
                now_node.repeat_time = repeat_time
                for idx in range(slide_start_idx, slide_start_idx + win_size):
                    inwin_node = copy_childs[idx]
                    inwin_node._render_when_repeat = True & subject._render_when_repeat
                    inwin_node._is_folded = True if idx-slide_start_idx else False
                    now_node._repeat_body.append((inwin_node.node_id, inwin_node.name))

                # skip the modules that is repeated
                slide_start_idx += win_size * repeat_time
                
            else:
                # if there isn't such a window, then the current module is unique, 
                # then jump to the adjacent module and repeat such a procedure
                slide_start_idx += 1
                    
        return (all_nodes, display_node)
    
    def __repr__(self) -> str:
        return self.root.__repr__()
    