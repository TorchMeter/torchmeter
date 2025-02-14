import re
import time
import warnings
from copy import deepcopy
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import torch.nn as nn
from rich.tree import Tree

from torchmeter.utils import dfs_task, Verboser
from torchmeter.statistic import ParamsMeter, CalMeter, MemMeter, ITTPMeter

__all__ = ('OperationNode', 'OperationTree')

class OperationNode:
   
    statistics:Tuple[str] = ('param', 'cal', 'mem', 'ittp') # all statistics stored as attributes

    def __init__(self, 
                 module:nn.Module,
                 name:Optional[str]=None,
                 node_id:str='',
                 parent:Optional["OperationNode"]=None,
                 childs:OrderedDict[str, "OperationNode"]=OrderedDict(),
                 **kwargs):

        # basic info
        self.operation = module
        self.type = module.__class__.__name__
        self.name = name if name else self.type
        self.addr = str(id(module))
        self.node_id:str = node_id # index in the model tree, for example '1.2.1'
        
        # hierarchical info
        self.parent:"OperationNode" = parent
        self.childs:OrderedDict[str, "OperationNode"] = childs
        self.is_leaf = False
        
        # repeat info
        self.repeat_winsz = 1 # size of repeat block
        self.repeat_time = 1
        self.repeat_body:List[Tuple[str, str]] = [] # the ids and names of the nodes in the same repeat block
        
        # display info 
        self.display_root:Tree = None # set in `OperationTree.__build()`
        self.fold_repeat = True # TODO: move to a supper level
        self.render_when_repeat = False # whether to render when enable `fold_repeat` in `render_as_tree`, set in `OperationTree.__build()`
        self.is_folded = False # whether the node is folded in a repeat block, set in `OperationTree.__build()`

        self.level_args:List[Dict[str, str]] = []
        self.repeat_block_args:Dict[str, Any] = {}

        # statistic info (all read-only)
        self.__param = ParamsMeter(opnode=self)
        self.__cal = CalMeter(opnode=self)
        self.__mem = MemMeter(opnode=self)
        self.__ittp = ITTPMeter(opnode=self)

        # other info
        for key, value in kwargs.items():
            if key in self.__dict__:
                setattr(self, key, value)
            else:
                warnings.warn(f'`{key}` is not a valid attribute of `OperationNode`, ignored.')

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
    def ittp(self) -> ITTPMeter:
        return self.__ittp

    def __copy__(self):
        new_obj = OperationNode(self.operation)
        new_obj.__dict__ = self.__dict__
        return new_obj

    def __deepcopy__(self, memo):
        new_obj = OperationNode(self.operation)
        memo[id(self)] = new_obj
        new_obj.__dict__ = deepcopy(self.__dict__, memo)
        return new_obj
    
    def __repr__(self):
        op_str = str(self.type) if self.operation._modules else str(self.operation)            
        return f"{self.node_id} {self.name}: {op_str}"
    
class OperationTree:

    def __init__(self, 
                 model:nn.Module,
                 verbose:bool=True):
        
        self.root = OperationNode(module=model,
                                  node_id="0",
                                  render_when_repeat=True)
        
        with Verboser(enable=verbose,
                      enter_text='[b blue]Scaning model in ',
                      enter_args={'end':''}) as vb:
            start = time.time()
            # all_nodes: List[OperationNode], a list holding all operation nodes but the root
            nonroot_nodes, *_ = dfs_task(dfs_subject=self.root, 
                                         adj_func=lambda x:x.childs.values(),
                                         task_func=OperationTree.__build,
                                         visited_signal_func=lambda x:x.addr,
                                         visited=[])
            vb.exit_text = f'[b blue][green]{time.time()-start:.3f}[/green] seconds\n[/]'

        self.all_nodes = [self.root] + nonroot_nodes
            
    @staticmethod
    def __build(subject:"OperationNode",
                pre_res:Tuple[List["OperationNode"], Optional[Tree]]=([],)) \
                    -> Tuple[List["OperationNode"], Optional[Tree]]:
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
        
        # build display tree
        if display_parent:
            display_parent = display_parent[0]
        
            # create a tree node of rich.Tree, and record the level of the node in attribute 'label'
            display_node = Tree(label=str(int(display_parent.label)+1), 
                                guide_style="dark_goldenrod", 
                                highlight=True)
            
            # add the current node to the father node
            display_parent.children.append(display_node)
        else:
            # situation of root node
            display_node = Tree(label='0', 
                                guide_style="dark_goldenrod", 
                                highlight=True)
        
        # link the display node to the attribute `display_root` of operation node
        subject.display_root = display_node
        
        # build operation tree
        copy_childs, str_childs = [], []
        for access_idx, (module_name, module) in enumerate(subject.operation.named_children()):
            module_idx = (subject.node_id if subject.node_id != '0' else '') + \
                         ('.' if subject.node_id != '0' else '') + \
                         str(access_idx+1)
                         
            child = OperationNode(module=module, 
                                  name=module_name,
                                  parent=subject,
                                  childs=OrderedDict(),
                                  node_id=module_idx)
            
            all_nodes.append(child)
            if not module._modules: # if module doen't have child modules
                child.is_leaf = True
            
            subject.childs[module_idx] = child
            copy_childs.append(child)
            str_childs.append(re.sub(r'\(.*?\):\s', repl='', string=str(module)))
        
        # find all potantial maximum repeat block in currently traversed level using greedy strategy
        slide_start_idx = 0
        while slide_start_idx < len(str_childs):
            now_node = copy_childs[slide_start_idx]
            now_node.render_when_repeat = True & subject.render_when_repeat
            
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
                inner_repeat = True if len(set(str_childs[win1_start_end[0]:win2_start_end[1]])) == 1 \
                                    else False
                
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
                    brother_node = copy_childs[idx]
                    brother_node.render_when_repeat = True & subject.render_when_repeat
                    brother_node.is_folded = True if idx-slide_start_idx else False
                    now_node.repeat_body.append((brother_node.node_id, brother_node.name))

                # skip the modules that is repeated
                slide_start_idx += win_size * repeat_time
                
            else:
                # if there isn't such a window, then the current module is unique, 
                # then jump to the adjacent module and repeat such a procedure
                slide_start_idx += 1
                    
        return (all_nodes, display_node)
    
    def __repr__(self):
        return self.root.__repr__()
    