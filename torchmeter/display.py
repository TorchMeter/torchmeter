from __future__ import annotations
from typing import TYPE_CHECKING

import re
import os
import warnings
from copy import copy, deepcopy
from collections import OrderedDict
from inspect import signature, _empty

from rich import print
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table, Column
from polars import DataFrame

from torchmeter.utils import dfs_task, resolve_savepath
from torchmeter.config import get_config, dict_to_namespace, FlagNameSpace

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional, Union, Sequence
    
    from rich.segment import Segment
    from rich.console import Console, RenderableType
    from polars._typing import PolarsDataType

    from torchmeter.engine import OperationNode
    
    LAZY_STR_TYPE = Optional[Union[str,
                                   Callable[[Dict[str, Any]], str]]]

__all__ = ["render_perline", "TreeRenderer", "TabularRenderer"]
__cfg__ = get_config()

def apply_setting(obj:Any, 
                  setting:FlagNameSpace, 
                  omit:Optional[Union[str, Sequence[str]]]=None,
                  **extra_settings) -> Any:
    """
    This funtion is to adapt to the third-party library api change,
    and to apply the settings to the given object in place.
    
    we can not directly use `obj.__dict__.update(settings)`, cause sometime the 
    obj does not have a `__dict__` attribute. Additionally, the obj's properties names may have
    no relationship with its initialization parameters.
    
    Note: 
        - important property(such as Tree.children) should be in omit, or it will be reset.
        - although all of this, if we want to omit some arguments, we still need to set omit to 
        the inner related attribute name insteat of the initialization parameter name.
    """
    
    # prepare the setting dict
    if isinstance(setting, FlagNameSpace):
        setting_dict = setting.data_dict.copy()
    elif isinstance(setting, dict):
        setting_dict = setting.copy()
    else:
        raise TypeError("The `setting` argument should be a `FlagNameSpace` or a `dict`, " + \
                        f"but got `{type(setting).__name__}`.") 
    setting_dict.update(extra_settings)
    
    # prepare all the initialization arguments
    obj_cls = obj.__class__
    variable_position_idx = None
    variable_keyword_argname = None
    init_args:Dict[str, Any] = OrderedDict()
    for arg_idx, (arg_name, arg) in enumerate(signature(obj_cls).parameters.items()):
        arg_type = arg.kind.name
        
        if arg_type == "VAR_POSITIONAL":
            variable_position_idx = arg_idx
            variable_position_argname = arg_name
            init_args[arg_name] = list(setting_dict.get(arg_name, []))
            
        elif arg_type == "VAR_KEYWORD":
            variable_keyword_argname = arg_name
            if arg_name in setting_dict:
                init_args[arg_name] = setting_dict[arg_name]
            else:
                init_args[arg_name] = {k:v for k,v in setting_dict.items() 
                                       if k not in init_args}
            
        else:
            if arg_name not in setting_dict and arg.default is _empty:
                try: # try to find the property with same name in the object 
                    init_args[arg_name] = getattr(obj, arg_name)
                except AttributeError: # if not, this argment is required but absent
                    raise RuntimeError(f"A required argument `{arg_name}` unknown, " + \
                                       f"consider providing it via `{arg_name}=xxx` or adding it to config.")
            init_args[arg_name] = setting_dict.get(arg_name, arg.default)
    
    # divide the arguments into position and keyword
    if variable_position_idx is not None:
        all_args = tuple(init_args.keys())
        position_args = [init_args[k] for k in all_args[:variable_position_idx]]
        position_args.extend(init_args[variable_position_argname])
        keyword_args = {k:init_args[k] for k in all_args[variable_position_idx+1:]}
    else:
        position_args = []
        keyword_args = init_args
    
    if variable_keyword_argname is not None:
        keyword_args.update(keyword_args[variable_keyword_argname])
        del keyword_args[variable_keyword_argname]
    
    # initialize a mirror object
    temp_obj = obj_cls(*position_args, **keyword_args)
    
    # prepare the state dict
    if hasattr(temp_obj, '__dict__'):
        target_state = temp_obj.__dict__
    else:
        all_states = temp_obj.__slots__
        
        if not isinstance(all_states, (list, tuple, set)):
            all_states = [all_states]
        all_states = [f"_{obj_cls.__name__}{p}" if p.startswith('__') else p
                      for p in all_states]
                
        target_state = {property: getattr(temp_obj, property) 
                        for property in all_states}
    
    # filt out the omit items from the state dict
    if omit is not None:
        if not isinstance(omit, (str, list, tuple, set)):
            raise TypeError("The `omit` argument should be a string, a list, a tuple or a set, " + \
                            f"but got `{type(omit).__name__}`.")
        
        if isinstance(omit, str):
            omit_items = set([omit])
        else:
            if any(not isinstance((inner:=_), str) for _ in omit):
                raise TypeError(f"The `omit` argument receives a `{type(omit).__name__}` of `{type(inner).__name__}`, " + \
                                "but expect the inner type to be str.")
            omit_items = set(omit)
    else:
        omit_items = set()
    
    target_state = {k:v for k,v in target_state.items() if k not in omit_items}
    
    # update obj's state with the setting dict
    if hasattr(obj, '__dict__'):
        obj.__dict__.update(target_state)
    else:
        list(map(lambda kv: setattr(obj,kv[0],kv[1]), target_state.items())) # type: ignore
    
    # return the origin object
    return obj

def render_perline(renderable: RenderableType) -> None:
    """
    Output a renderable object line by line. \n
    Each line allows for the setting of a prefix and a suffix, i.e. `line_prefix` and `line_suffix`. \n
    A separator `row_separator` can be set between lines. \n
    At the same time, an interval of `time_sep` seconds is allowed between the output of each line.

    Args:
    ---
        - `renderable` (Union[RenderableType, List[List[Segment]]]): The renderable object to be displayed. Accepts a nested lists of Segments as well.
        
        - `line_prefix` (str, optional): The prefix to be displayed before each line. Accept rich style customization. 
                                         Defaults to ''.
        
        - `line_suffix` (str, optional): The suffix to be displayed after each line. Accept rich style customization. 
                                         Defaults to ''.
        - `row_separator` (str, optional): The separator pattern to be displayed between each line. The pattern will be repeat for the full display width.
                                         Accept rich style customization. Defaults to ''.
        
        - `console` (rich.console.Console, optional): The console object to be used for rendering. If it is not specified, 
                                                      the global console object will be used. Defaults to None.
        
    Returns:
    ---
        None
    """
    
    from time import sleep
    from rich import get_console
    
    time_sep:float = __cfg__.render_interval
    if time_sep < 0:
        raise ValueError(f"The `render_interval` value defined in config must be non-negative, but got `{time_sep}`")

    console:Console = get_console()

    if not time_sep:
        console.print(renderable)

    else:
        lines: List[List[Segment]] = console.render_lines(renderable, new_lines=True)
    
        # a fake implementation of `rich.print`
        console._buffer_index = 0
        for line in lines:
            console._buffer.extend(line)
            console._check_buffer()
            sleep(time_sep)

class TreeRenderer:
    """Render a `OperationNode` object as a tree.
    
    A renderer responsible for rendering a `OperationNode` object as a tree without polluting the original `OperationNode` object.

    Features:
        - Rich display: Implemented based on rich, supporting rich text output.

        - Easy-to-understand visualization: auto-fold the repeat block when the `fold_repeat` is set in `render()` method.

        - Highly customizable: Allows custom rendering for even each level of the tree. You can specify your own display settings by 
                               passing a dictionary or a list of dictionaries as `level_args` when you call the object.

    Tips for customization: 
        - customize the display settings for each level: pass a dictionary or a list of dictionaries as `level_args` when you call the object.
            - If you pass a dictionary, it should follow the format: `{'0': {level_0_setting}, '1': {level_1_setting}, ...}`. In this case, 
            the key should be a non-negative int or 'default' or 'all', which means that the settings in value will be used at the target level, 
            the undefined level and all levels from now on.

            - If you pass a list of dictionaries, each dictionary should contain a key `level` to indicate the working level. You should follow 
            the format like `[{'level':'0', **level_0_setting}, {'level':'1', **level_1_setting}, ...]`, the `level` serves the same function as 
            the key set in the dict.

            - As for level settting, it firstly should be attributes of a `rich.tree.Tree` object, mostly used are `label` for the display content of the node,
            `guide_style` for the style of the guide line, `style` for the style of the node, etc. See more at https://rich.readthedocs.io/en/latest/tree.html.
            Note that You can access the attributes of the operation node by using `<·>` in the value. For example, if you want to print the node id, 
            you can set `'label':'<node_id>'`. Typically, the content in the placeholder `<·>` will be replaced by the corresponding attribute of the operation node.
            However, if you want a more dedicated post-process, you can overwrite the `resolve_attr` method of the renderer instance. The method accept the attribute value
            as input and should return a string as output.

        - customize the display settings for repeat block: pass a dictionary as `repeat_block_args` when you call the object.
            - The keys of the dict can be arguments of `rich.panel.Panel` object;
            - In addition, you can set a `repeat_footer` key to pass in a string or a function with an `attr_dict` argument to customize the footer of the repeat block.
              If you use a string, then you can use `<·>` in the string to access the attributes of the operation node. If you use a function, then your function should have an argument
              known as `attr_dict` through which you can access the attributes of the operation node. Finally, you should promise that your function return a string that may contain placeholder or not.
              By the way, if you want to access the loop algebra, you can use `<loop_algebra>` in the string or function.
                               
    
    Attributes:
    ---
        - `node` (OperationNode): the node to be rendered as a tree.

        - `loop_algebras` (str): The loop algebra sequence whose character will be used to generate the unique node id. 
                                 If it is not set, it will used `xyijkabcdefghlmnopqrstuvwz` instead. Defaults to ''.

        - `render_unfold_tree` (rich.tree.Tree): A `rich.tree.Tree` object without folding the repeat nodes. 
                                                 That is to say, this is the original tree structure.

        - `render_fold_tree` (rich.tree.Tree): A `rich.tree.Tree` object with repeat nodes folded as repeat blocks. This is an efficient 
                                               and easy-to-understand way to display.

        - `default_level_args` (Dict[str, Any]): A dictionary containing the default display settings for each level of the tree. 
                                                 The keys of the dict are arguments of `rich.tree.Tree` class. This attribute might be 
                                                 changed by `render()` method if `level_args` is passed in and there is a key `default` or `all` in the passed in setting. 

        - `tree_levels_args` (Dict[str, Any]): A dictionary containing the display settings for each level of the tree. 
                                              The key is the level number, and the value is a dictionary containing the display settings of corresponding level.
                                              This attribute might be changed by `render()` method if `level_args` is passed in.

        - `repeat_block_args` (Dict[str, Any]): A dictionary containing the display settings for the repeat block. This attribute takes effect only when `fold_repeat` is set to True
                                                in `render()` method. Note that the keys can be arguments of `rich.panel.Panel` object, or `repeat_footer` to customize the footer format 
                                                of the repeat block.
    
    Methods:  
    ---
        - `__call__`: Render the OperationNode object and its childs as a tree.      
        - `resolve_attr`: Function to process the attribute value resolved by regex. You should inherit and override this method 
                          to customize the processing pipeline of the attribute value.    

    Examples:  
    ---
        ```python
        from torchvision.models import resnet18
        from torchmeter.engine import OperationTree
        from torchmeter.display import TreeRenderer

        model = resnet18()
        optree = OperationTree(model)

        root_display = {
            'level': 0,
            'label': '[b red]<name>[/]',
            'guide_style':'red',
        }

        level_1_display = {
            'level': 1,
            'label':'[gray35]<node_id> [b green]<name>[/]',
            'guide_style':'green'
        }

        level_2_display = {
            'level': 2,
            'guide_style':'blue'
        }

        repeat_block_args = {
            'title': '[i]Repeat [[b u]<repeat_time>[/b u]] Times[/]',
            'title_align': 'center',
            'highlight': True,
            'repeat_footer': lambda attr_dict: f"First value of <loop_algebra> is {attr_dict['node_id'].split('.')[-1]}"
        }

        renderer = TreeRenderer()
        renderer(optree.root, 
                 level_args=[root_display, level_1_display, level_2_display],
                 repeat_block_args=repeat_block_args)
        ```                                         
    """
    
    loop_algebras:str = "xyijkabcdefghlmnopqrstuvwz" + "XYIJKABCDEFGHLMNOPQRSTUVWZ"
    
    def __init__(self, node:OperationNode) -> None:  
        if node.__class__.__name__ != 'OperationNode':
            raise TypeError("Expected `node` to be an instance of `OperationNode`, " + \
                            f"but got `{type(node).__name__}`.")
            
        self.opnode = node

        self.render_unfold_tree:Optional[Tree] = None
        self.render_fold_tree:Optional[Tree] = None
        
        def default_rpft(attr_dict:Dict[str, Any]) -> str:
            """Must have only one args which accept an attribute dict"""
            # basic format of footer in each repeat block
            start_idx = attr_dict['node_id'].split('.')[-1]
                
            repeat_winsz = attr_dict['repeat_winsz']
            if repeat_winsz == 1:
                end_idx = int(start_idx) + attr_dict['repeat_time'] -1
                return f"Where <loop_algebra> ∈ [{start_idx}, {end_idx}]"
            else:
                end_idx = int(start_idx) + attr_dict['repeat_time']*repeat_winsz -1
                valid_vals = list(map(str, range(int(start_idx), end_idx, repeat_winsz)))
            return f"Where <loop_algebra> = {', '.join(valid_vals)}"
        
        self.__rpft: LAZY_STR_TYPE = default_rpft
                
    @property
    def default_level_args(self) -> FlagNameSpace:
        if not hasattr(self.tree_levels_args, 'default'):
            self.tree_levels_args.default = dict_to_namespace({
                'label':'[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]', # str | Callable
                'style':'tree',
                'guide_style':'light_coral',
                'highlight':True,
                'hide_root':False,
                'expanded':True
            })
        return self.tree_levels_args.default
    
    @property
    def tree_levels_args(self) -> FlagNameSpace:
        return __cfg__.tree_levels_args

    @property
    def repeat_block_args(self) -> FlagNameSpace:
        return __cfg__.tree_repeat_block_args

    @property
    def repeat_footer(self) -> LAZY_STR_TYPE:
        return self.__rpft

    @default_level_args.setter  # type: ignore
    def default_level_args(self, custom_args:Dict[str, Any]) -> None:
        """
        Update the default display settings of the rendered tree with the pass-in dict.
        Note that the keys of the dict should be valid args of `rich.tree.Tree` class.

        Args:
        ---
            - `custom_args` (Dict[str, str]): A dict of new display settings. The keys should be valid args of `rich.tree.Tree` class.

        Raises:
        ---
            - `TypeError`: if the new value is not a dict.
        """
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.default_level_args` with a dict, " + \
                            f"but got `{type(custom_args).__name__}`.")
        
        valid_setting_keys = set(signature(Tree).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/tree.html for valid args.")
        self.default_level_args.__dict__.update(custom_args)
        
        self.default_level_args.mark_change()

    @tree_levels_args.setter    # type: ignore
    def tree_levels_args(self, custom_args:Dict[Any, Dict[str, Any]]) -> None:
        """
        Update the display settings of all levels in the rendered tree with the pass-in list of dict.
        Note that all dicts should have a key `level` to indicate the level of the corresponding display settings.
        To ensure correctly displayed, all key-values pairs in the dict will be valid.

        Args:
        ---
            - `custom_args` (Union[List[Dict[str, Any]], Dict[Any, Dict[str, Any]]]): 
                A list of dict or a dict.
                If a list of dict, each dict should contain a key `level` to indicate the level of the corresponding display settings.
                If a dict, the key should be the level of the corresponding display settings.

        Raises:
        ---
            `TypeError`: if the new value is not a dict or a list of dict.
        """
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.tree_levels_args` with a dict, " + \
                            f"but got `{type(custom_args).__name__}`.")
                                                            
        # filt out invalid level definations and invalid display settings
        valid_setting_keys = set(signature(Tree).parameters.keys())
        for level, level_args_dict in custom_args.items():
            # assure level is a non-negative integer, 'default' or 'all'
            level = level.lower()
            if not level.isnumeric() and level not in ('default', 'all'):
                warnings.warn(message=f"The `level` key should be numeric, `default` or `all`, but got `{level}`.\n" + \
                                      "This setting will be ignored.\n",
                              category=UserWarning)
                continue
                
            passin_keys = set(level_args_dict.keys())
            invalid_keys = passin_keys - valid_setting_keys
            if invalid_keys:
                raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, " + \
                               "refer to https://rich.readthedocs.io/en/latest/tree.html for valid args.")

            if level == 'default':
                self.default_level_args = level_args_dict # type: ignore
            elif level == 'all':
                self.default_level_args = level_args_dict # type: ignore
                # delete all levels settings 
                levels = [level for level in self.tree_levels_args.__dict__.keys() 
                          if level.isnumeric()]
                list(map(lambda level:delattr(self.tree_levels_args, level), levels))   # type: ignore
                break
            else:
                if hasattr(self.tree_levels_args, level):
                    getattr(self.tree_levels_args, level).__dict__.update(level_args_dict)
                else:
                    setattr(self.tree_levels_args, level, dict_to_namespace(level_args_dict)) # type: ignore
                       
        self.tree_levels_args.mark_change()

    @repeat_block_args.setter   # type: ignore
    def repeat_block_args(self, custom_args:Dict[str, Any]) -> None:
        """
        Update the display settings of the repeat block with the pass-in dict.
        Note that the keys of the dict should be valid args of `rich.panel.Panel` class.

        Args:
        ---
            - `custom_args` (Dict[str, Any]): A dict of new display settings. The keys should be valid args of `rich.panel.Panel` class.

        Raises:
        ---
            - `TypeError`: if the new value is not a dict.
        """
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.repeat_block_args` with a dict, " + \
                            f"but got `{type(custom_args).__name__}`.")
                                                        
        footer_key = list(filter(lambda x: x.lower() == 'repeat_footer', custom_args.keys()))
        if footer_key:
            self.repeat_footer = custom_args[footer_key[-1]] # type: ignore
            del custom_args[footer_key[-1]] 
        
        valid_setting_keys = set(signature(Panel).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.panel.Panel`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/panel.html for valid args.")
        self.repeat_block_args.__dict__.update(custom_args)
        
        self.repeat_block_args.mark_change()

    @repeat_footer.setter # type: ignore
    def repeat_footer(self, custom_footer:LAZY_STR_TYPE) -> None:
        from inspect import signature
        
        if callable(custom_footer):
            
            func_args = signature(custom_footer).parameters
            
            if not len(func_args):
                res = custom_footer() # type: ignore
                if not isinstance(res, (type(None), str)):
                    raise RuntimeError("If `repeat_foot` is a parameterless function, its return value must be `str` or `None`, " + \
                                       f"but got a result of type `{type(res).__name__}`.")
                self.__rpft = res
                
            elif len(func_args) == 1:
                self.__rpft = custom_footer
                
            else:
                raise RuntimeError("If `repeat_footer` is a parameterized function, it must have exactly one parameter and will accept a `dict` as input, " + \
                                   f"but there are {len(func_args)} arguments in the passed-in function.")
        
        elif isinstance(custom_footer, (type(None), str)):
            self.__rpft = custom_footer
            
        else:
            raise RuntimeError("The `repeat_footer` can be None, string, a parameterless function, or a function with one argument, " + \
                               f"but got `{type(custom_footer).__name__}`.")

        self.repeat_block_args.mark_change()

    def resolve_attr(self, attr_val:Any) -> str:
        """
        Function to process the attribute value resolved by regex.

        Args:
            attr_val (Any): The attribute value resolved by regex.

        Returns:
            str: the processed result. Must be a string!
        """
        return str(attr_val)
    
    def __call__(self) -> Tree:
        """Render the `OperationNode` object and its childs as a tree without polluting the original `OperationNode` object.
        
        see docs of the class(i.e. `torchmeter.display.TreeRenderer`) for details.

        Args:
        ---
            - `fold_repeat` (bool, optional): whether to fold the repeat nodes. Defaults to True.
            
            - `level_args` (Union[List[Dict[str, Any]], Dict[Any, Dict[str, Any]]], optional): a dict or a list of dicts, whose item controls 
                                                                    the render settings of specific tree level through key(if it's a dict) or key 'level'(if it's a list). 
                                                                    Defaults to {}, which means using the default setting for each level.
            
            - `repeat_block_args` (Dict[str, Any], optional): a dict of display settings for the repeat block. Defaults to {}.

        Returns:
        ---
            rich.tree.Tree: the rendered tree.
        
        Example:
        ---
            see docs of the class(i.e. `torchmeter.display.TreeRenderer`) for details.
        """
        
        from rich.rule import Rule
        from rich.console import Group

        fold_repeat:bool = __cfg__.tree_fold_repeat
        
        copy_tree:OperationNode = deepcopy(self.opnode)
        
        # task_func for `dfs_task`
        def __render_per_node(subject:OperationNode, 
                              pre_res=None) -> None:

            # skip repeat nodes and folded nodes when enable `fold_repeat`
            if fold_repeat and subject.is_folded: 
                return None
            if fold_repeat and not subject.render_when_repeat:
                return None
            
            display_root:Tree = subject.display_root 

            level = str(display_root.label)  

            # update display setting for the currently traversed node
            target_level_args = getattr(self.tree_levels_args, level, self.default_level_args)

            # resolve label field
            origin_node_id = subject.node_id
            if fold_repeat and int(level) > 1:
                subject.node_id = subject.parent.node_id + f".{subject.node_id.split('.')[-1]}"  # type: ignore
            label = self.__resolve_argtext(text=getattr(target_level_args, 'label', self.default_level_args.label),
                                           attr_owner=subject)

            # apply display setting
            apply_setting(obj=display_root, 
                          setting=target_level_args,
                          omit="children",
                          label=label)
            
            if fold_repeat:  
                algebra = self.loop_algebras[0]
                use_algebra = False

                if subject.repeat_winsz < 1:
                    raise RuntimeError("You should never change `repeat_winsz` to be less than 1.")
                if subject.repeat_time < 1:
                    raise RuntimeError("You should never change `repeat_time` to be less than 1.")

                # if the repeat body contains more than one operations
                # get a complete copy of the repeat body, so as to render repeat block more conveniently later.
                if subject.repeat_winsz > 1: 
                    use_algebra = True

                    repeat_body = Tree('.', hide_root=True)
                    
                    for loop_idx, (node_id, node_name) in enumerate(subject.repeat_body):
                        repeat_op_node:OperationNode = subject.parent.childs[node_id]  # type: ignore
                        
                        # update node_id with a algebraic expression which indicates the loop
                        if level != '1':
                           if loop_idx == 0:
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f".{algebra}"  # type: ignore
                           else:
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f".({algebra}+{loop_idx})"  # type: ignore
                        else:
                            if loop_idx == 0:
                                repeat_op_node.node_id = algebra
                            else:
                                repeat_op_node.node_id = f"{algebra}+{loop_idx}"
                        
                        # resolve label field for the `rich.Tree` object of the currently traversed node
                        label = self.__resolve_argtext(text=getattr(target_level_args, 'label', self.default_level_args.label), 
                                                       attr_owner=repeat_op_node)
                        
                        # update display setting for the `rich.Tree` object of the currently traversed node
                        repeat_display_node:Tree = copy(repeat_op_node.display_root)
                        apply_setting(obj=repeat_display_node,
                                      setting=target_level_args,
                                      omit="children",
                                      label=label)
                        
                        # Delete repeat nodes and folded nodes (Note: operate in a copied tree)
                        repeat_display_node.children = [child.display_root for child in repeat_op_node.childs.values() 
                                                            if child.render_when_repeat and not child.is_folded]
                        
                        repeat_body.children.append(repeat_display_node)        
                
                    display_root = repeat_body
                else:
                    # for the case that the repeat body is only a single operation or the current node is just not a repeat node,
                    # just delete its repeat childs or the folded childs and need to do nothing more
                    display_root.children = [child.display_root for child in subject.childs.values() 
                                                if child.render_when_repeat and not child.is_folded]                        
                
                # render the repeat body as a panel
                if subject.repeat_time > 1:
                    use_algebra = True

                    # update node_id with a algebraic expression which indicates the loop
                    if level != '1':
                        subject.node_id = subject.parent.node_id + f".{algebra}" # type: ignore
                    else:
                        subject.node_id = algebra
                    display_root.label = self.__resolve_argtext(text=getattr(target_level_args, 'label', self.default_level_args.label), 
                                                                attr_owner=subject)

                    block_footer = self.__resolve_argtext(text=self.repeat_footer, attr_owner=subject,
                                                          loop_algebra=algebra, node_id=origin_node_id)
                    if block_footer:
                        repeat_block_content:Union[Tree, Group] = Group(
                            copy(display_root), # the tree structure of the circulating body
                            Rule(characters='-', style='dim ' + getattr(self.repeat_block_args, 'style','')), # a separator made up of '-'
                            "[dim]" + block_footer + "[/]",
                            fit=True
                        )
                    else:
                        repeat_block_content = copy(display_root)
                    
                    # make a pannel to show repeat information
                    title = self.__resolve_argtext(text=getattr(self.repeat_block_args, 'title', ''), 
                                                   attr_owner=subject, 
                                                   loop_algebra=algebra)
                    
                    repeat_block = apply_setting(
                        obj=Panel(renderable=repeat_block_content),
                        setting=self.repeat_block_args,
                        omit="renderable",
                        title=title,
                        border_style=self.repeat_block_args.border_style + ' ' + self.repeat_block_args.style
                    )
                    
                    # overwrite the label of the first node in repeat block 
                    subject.display_root.label = repeat_block

                    # remove all children nodes of the first repeat item, 
                    # so that only the rendered panel will be displayed
                    subject.display_root.children = []

                if use_algebra:
                    self.loop_algebras = self.loop_algebras[1:] + algebra

            return None
        
        # apply display setting for each node by dfs traversal
        dfs_task(dfs_subject=copy_tree,
                 adj_func=lambda x:x.childs.values(),
                 task_func=__render_per_node,
                 visited=[])
        
        # cache the rendered result
        if fold_repeat:
            self.render_fold_tree = copy_tree.display_root
        else:
            self.render_unfold_tree = copy_tree.display_root
        
        return copy_tree.display_root  

    def __resolve_argtext(self,
                          text:LAZY_STR_TYPE, 
                          attr_owner:"OperationNode", # noqa # type: ignore
                          **kwargs) -> str: 
        """
        Disolve all placeholders in form of `<·>` in `text`.\n
        If you do not want the content in `<·>` to be resolved, you can use `\\<` or `\\>` to escape it.\n
        For example, `<name>` will be replaced by the value of `attr_owner.name`, while `\\<name\\>` will not be resolved.

        Args:
        ---
            - `text` (str): A string that may contain placeholder in the form of `<·>`.
            - `attr_owner` (OperationNode): The object who owns the attributes to be resolved.
            - `kwargs` (dict): Offering additional attributes.

        Returns:
        ---
            str: Text with all placeholders resolved.
        """
        attr_dict = copy(attr_owner.__dict__)
        attr_dict.update(kwargs)
        
        if callable(text):
            text = text(attr_dict)
        elif text is None:
            return ""

        res_str = re.sub(pattern=r'(?<!\\)<(.*?)(?<!\\)>',
                         repl=lambda match: str(self.resolve_attr(attr_dict.get(match.group(1), None))),
                         string=str(text))
        res_str = re.sub(pattern=r'\\<|\\>',
                         repl=lambda x: x.group().replace('\\', ''),
                         string=res_str)
        return res_str
    
class TabularRenderer:

    def __init__(self, node:OperationNode) -> None: 
        if node.__class__.__name__ != 'OperationNode':
            raise TypeError("Expected `node` to be an instance of `OperationNode`, " + \
                            f"but got `{type(node).__name__}`.")
            
        self.opnode = node

        # underlying data
        self.__stats_data:Dict[str, DataFrame] = {stat_name:DataFrame() for stat_name in node.statistics}

    @property
    def stats_data(self):
        return self.__stats_data

    @property
    def tb_args(self) -> FlagNameSpace:
        return __cfg__.table_display_args
    
    @property
    def col_args(self) -> FlagNameSpace:
        return __cfg__.table_column_args

    @property
    def valid_export_format(self) -> List[str]:
        return ['csv', 'xlsx']

    @tb_args.setter # type: ignore
    def tb_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.tb_args` with a dict, " + \
                            f"but got `{type(custom_args).__name__}`.")
        
        valid_setting_keys = set(signature(Table).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.table.Table`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/tables.html for valid args.")
        self.tb_args.__dict__.update(custom_args)
        
        self.tb_args.mark_change()
        
    @col_args.setter # type: ignore
    def col_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.col_args` with a dict, " + \
                            f"but got `{type(custom_args).__name__}`.")
        
        valid_setting_keys = set(signature(Column).parameters.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.table.Column`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/columns.html for valid args.")
        self.col_args.__dict__.update(custom_args)
        
        self.col_args.mark_change()

    def df2tb(self, df:DataFrame, show_raw:bool = False) -> Table:
        # create rich table
        tb_fields = df.columns
        tb = apply_setting(
            obj=Table(*tb_fields),
            setting=self.tb_args,
            omit="columns",
            headers=tb_fields
        )

        # apply column settings to all columns
        list(map(lambda tb_col: apply_setting(obj=tb_col, 
                                              omit="header",
                                              setting=self.col_args,
                                              highlight = self.tb_args.highlight), tb.columns))
        if df.is_empty():
            return tb
        
        # collect each column's none replacing string
        col_none_str = {col_name:getattr(df[col_name].drop_nulls()[0], 'none_str', '-') 
                        for col_name in df.schema.keys()}
        
        # fill table
        for vals_dict in df.iter_rows(named=True):
            str_vals = []
            for col_name,col_val in vals_dict.items():
                if col_val is None:
                    str_vals.append(col_none_str[col_name])
                elif show_raw:
                    str_vals.append(str(getattr(col_val, 'raw_data', col_val)))
                else:
                    str_vals.append(str(col_val))
            
            tb.add_row(*str_vals)
        
        return tb

    def clear(self, stat_name:Optional[str]=None) -> None:
        if not isinstance(stat_name, (str, type(None))):
            raise TypeError(f"`stat_name` must be a string or None, but got `{type(stat_name).__name__}`.")
            
        valid_stat_name = self.opnode.statistics
        if isinstance(stat_name,str):
            if stat_name not in valid_stat_name:
                raise ValueError(f"`{stat_name}` not in the supported statistics {valid_stat_name}.")
            self.__stats_data[stat_name] = DataFrame()
        else:
            self.__stats_data = {stat_name:DataFrame() for stat_name in valid_stat_name}

    def export(self, 
               df:DataFrame, 
               save_path:str, 
               format:Optional[str]=None,
               file_suffix:str='',
               raw_data:bool=False) -> None:
        
        from polars import col
        from polars import Float64 as pl_float
        from polars import String as pl_str
        from polars import List as pl_list
        from polars import Object as pl_object

        save_path = os.path.abspath(save_path)
        
        # get save path
        if format is None:
            format = os.path.splitext(save_path)[-1]
            if '.' not in format:
                raise ValueError("File format unknown! Please specify a path to a file.\n" + \
                                 f"Or you can specify a file format using `format=xxx`, now we support exporting to {self.valid_export_format} file.")
                                  
        format = format.strip('.')
        if format not in self.valid_export_format:
            raise ValueError(f"`{format}` file is not supported, now we only support exporting to {self.valid_export_format} file.")
        
        default_filename = f"{self.opnode.name}_{file_suffix}" if file_suffix else self.opnode.name
        _, file_path = resolve_savepath(origin_path=save_path,
                                        target_ext=format,
                                        default_filename=default_filename) 
        
        # deal with invalid data
        df = deepcopy(df)
        
        obj_cols:Dict[str, Any] = {col_name:df[col_name].drop_nulls()[0].__class__ 
                                   for col_name, col_type in df.schema.items() if col_type == pl_object}
        df = df.with_columns([
            col(col_name).map_elements(lambda s: getattr(s,'raw_data',s.val) if raw_data else str(s),
                                       return_dtype=pl_float if raw_data else pl_str)
            for col_name in obj_cols.keys()
        ])            
        
        # export 
        if format == 'csv':
            # list column -> str
            ls_cols = [col_name for col_name, col_type in df.schema.items() if col_type == pl_list]
            df = df.with_columns([
                col(col_name).map_elements(lambda s: str(s.to_list()), return_dtype=pl_str)
                for col_name in ls_cols
            ])
            df.write_csv(file=file_path)
        elif format == 'xlsx':
            df.write_excel(workbook=file_path, autofit=True)
        
        # output saving message
        if file_suffix:
            print(f"{file_suffix.capitalize()} data saved to [b magenta]{file_path}[/]")
        else:
            print(f"Data saved to [b magenta]{file_path}[/]")
    
    def __call__(self,
                 stat_name:str,
                 *, 
                 raw_data:bool=False,
                 pick_cols:Sequence[str]=[],
                 exclude_cols:Sequence[str]=[],
                 custom_cols:Dict[str, str]={},
                 keep_custom_name:bool=False,
                 newcol_name:str='',
                 newcol_func:Callable[[Dict[str, Any]], Any]=lambda col_dict: col_dict,
                 newcol_type:Optional[PolarsDataType]=None,
                 newcol_idx:int=-1,
                 keep_new_col:bool=False,
                 save_to:Optional[str]=None,
                 save_format:Optional[str]=None): 
        """render rich tabel according to the statistics dataframe.
        Note that `pick_cols` work before `custom_col`
        """

        from operator import attrgetter

        if stat_name not in self.opnode.statistics:
            raise ValueError(f"`{stat_name}` not in the supported statistics {self.opnode.statistics}.")
        if not isinstance(newcol_idx, int):
            raise TypeError(f"`newcol_idx` must be an integer, but got `{type(newcol_idx).__name__}`.")
        if not isinstance(pick_cols, (tuple, list)):
            raise TypeError(f"`pick_cols` must be a list or tuple, but got `{type(pick_cols).__name__}`.")
        if not isinstance(exclude_cols, (tuple, list)):
            raise TypeError(f"`exclude_cols` must be a list or tuple, but got `{type(exclude_cols).__name__}`.")
        if not isinstance(custom_cols, dict):
            raise TypeError(f"`custom_cols` must be a dict, but got `{type(custom_cols).__name__}`.")
        
        data:DataFrame = self.__stats_data[stat_name]
        valid_fields = data.columns or getattr(self.opnode, stat_name).tb_fields
    
        def __fill_cell(subject:OperationNode, 
                        pre_res=None):
            if subject.node_id == '0':
                return

            val_getter = attrgetter(*valid_fields)

            node_stat = getattr(subject, stat_name)
            
            try:
                stat_infos = node_stat.detail_val
                if stat_infos:
                    for rec in stat_infos: # rec: NamedTuple
                        vals = val_getter(rec)
                        val_collector.append(vals)
            except RuntimeError:
                nocall_nodes.append(f"({subject.node_id}){subject.name}")

        # only when the table is empty, then explore the data using dfs
        if data.is_empty():            
            val_collector:List[Any] = []
            nocall_nodes:List[str] = []
            dfs_task(dfs_subject=self.opnode,
                     adj_func=lambda x: x.childs.values(),
                     task_func=__fill_cell,
                     visited=[])
            
            if not val_collector:
                raise RuntimeError(f"No {stat_name} data collected, the reasons are three-folds:\n" + \
                                   "1. No module is called, make sure that your model's `forward` method is not empty.\n" + \
                                   "2. The whole model is empty and has no sublayers.\n" + \
                                   "3. You use a single layer as a model, consider putting it in a class and try again.\n")
            data = DataFrame(data=val_collector, schema=valid_fields, orient='row')
            self.__stats_data[stat_name] = data
            
            if nocall_nodes:
                warnings.warn(message=f"{', '.join(nocall_nodes)}\nThe modules above might be defined but not explicitly called. " + \
                                       "They will be ignored in the measuring, so will not appear in the table below.",
                              category=RuntimeWarning)
        
        # pick columns, order defined by `pick_cols`
        if pick_cols:
            invalid_cols = tuple(filter(lambda col_name:col_name not in valid_fields, pick_cols))
            if invalid_cols:
                raise ValueError(f"Column names {invalid_cols} not found in supported columns {data.columns}.")
        else:
            pick_cols = valid_fields
        # not use set is to keep order
        final_cols = [col_name for col_name in pick_cols if col_name not in exclude_cols] 
        data = data.select(final_cols)
        
        # custom columns name, order defined by `custom_col`
        if custom_cols:
            custom_cols = {k:v for k,v in custom_cols.items() if k in final_cols}
            data = data.rename(custom_cols)
            if keep_custom_name:
                self.__stats_data[stat_name] = data
        
        # add new column
        if newcol_name:
            data = self.__new_col(df=data,
                                  col_name=newcol_name,
                                  col_func=newcol_func,
                                  return_type=newcol_type,
                                  col_idx=newcol_idx)
            if keep_new_col:
                self.__stats_data[stat_name] = data

        tb = self.df2tb(df=data, show_raw=raw_data)

        if save_to:
            save_to = os.path.abspath(save_to)  
            if '.' not in os.path.basename(save_to):
                if save_format not in self.valid_export_format:
                    raise ValueError(f"Argument `save_format` must be one in {self.valid_export_format}, but got `{save_format}`. " + \
                                     "Alternatively, you can set `save_to` to a concrete file path, like `path/to/file.xlsx`")
            
            self.export(df=data,
                        save_path=save_to,
                        format=save_format,
                        file_suffix=stat_name,
                        raw_data=raw_data)

        return tb, data
    
    def __new_col(self, 
                  df:DataFrame,
                  col_name:str, 
                  col_func:Callable[[Dict], Any],
                  return_type=None,
                  col_idx:int = -1) -> DataFrame:

        from polars import Series

        if not isinstance(col_name, str):
            raise TypeError(f"`col_name` must be a string, but got `{type(col_name).__name__}`.")

        if col_idx < 0:
            col_idx = len(df.columns) + col_idx + 1 if abs(col_idx) <= len(df.columns) else 0
            
        final_cols = df.columns[:]
        final_cols.insert(col_idx, col_name)

        new_col_data = list(map(col_func, df.iter_rows(named=True)))

        return df.with_columns(
            Series(new_col_data, dtype=return_type)
            .alias(col_name)
        ).select(final_cols)