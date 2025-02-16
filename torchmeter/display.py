import re
import os
import time
import warnings
from copy import copy,deepcopy
from operator import attrgetter
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from rich import print, get_console
from rich.rule import Rule
from rich.tree import Tree
from rich.panel import Panel
from rich.segment import Segment
from rich.table import Table, Column
from rich.box import HEAVY_EDGE, ROUNDED
from rich.console import Group, RenderableType
from polars import DataFrame, struct, col
from polars import List as pl_list, Object as pl_object

from torchmeter.utils import dfs_task, perfect_savepath

def indent_str(s:Union[str, Sequence[str]], 
               indent:int=4, 
               guideline:bool=True,
               process_first:bool=True) -> str:
    res = []
    split_lines = s.split('\n') if isinstance(s, str) else s
    guideline = False if len(split_lines) == 1 else guideline
    
    for line in split_lines:
        indent_line = '│' if guideline else ' ' 
        indent_line += ' '*(indent-1) + str(line)
        res.append(indent_line)

    if not process_first:
        res[0] = res[0][indent:]

    if guideline:
        res[-1] = '└─' + res[-1][2:]
    
    return '\n'.join(res)

def data_repr(val:Any):
    get_type = lambda val: type(val).__name__

    item_repr = lambda val_type, val: (f"[dim]Shape[/]([b green]{list(val.shape)}[/])" if hasattr(val, 'shape') else f"[b green]{val}[/]") + f" [dim]<{val_type}>[/]"

    val_type = get_type(val)
    if isinstance(val, (list, tuple, set, dict)) and len(val) > 0:
        if isinstance(val, dict):
            inner_repr:List[str] = [f'{item_repr(get_type(k),k)}: {data_repr(v)}' for k, v in val.items()]
        else:
            inner_repr:List[str] = [data_repr(i) for i in val]
        
        res_repr = f'[dim]{val_type}[/](' 
        res_repr += ',\n'.join(inner_repr)
        res_repr += ')'

        return indent_str(res_repr, indent=len(f'{val_type}('), process_first=False)
    
    else:
        return item_repr(val_type, val)

def render_perline(renderable: Union[RenderableType, List[List[Segment]]],
                   line_prefix:'str'='',
                   line_suffix:'str'='',
                   row_separator:'str'='',
                   console=None, 
                   time_sep:float=0.15) -> None:
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
        
        - `time_sep` (float, optional): The time in second between each line output. Defaults to 0.15.
    
    Returns:
    ---
        None
    """
    assert time_sep >= 0, f"Argument `time_sep` must be non-negative, but got {time_sep}"
    assert '\n' not in row_separator, "You don't have to add \\n manually in Argument `row_separator`, " + \
                                      "we will do it for you to ensure the correct display."

    console = console or get_console()
    console_width = console.width
    temp_options = deepcopy(console.options)

    # render all items according to their origin width
    ## ensure renderable object is fully displayed
    if isinstance(renderable, list):
        obj_width = 0
        lines: List[List[Segment]] = []
        for line_segs in renderable:
            # discard the last space in the line, so as to have a fit display of the renderable object
            if line_segs[-1].text.isspace():
                line_segs.pop(-1)
            
            line_width = Segment.get_line_length(line_segs)
            obj_width = max(obj_width, line_width)

            lines.append(line_segs)
    else:
        obj_width = min(console.measure(renderable).maximum, console_width)
        temp_options.max_width = obj_width
        lines: List[List[Segment]] = console.render_lines(renderable, options=temp_options)

    ## ensure prefix is fully displayed
    residual_width = console_width - obj_width # >= 0
    if line_prefix and residual_width > 0:
        prefix_width = console.measure(line_prefix).maximum
        assert prefix_width <= residual_width, \
            f"Argument `line_prefix` is too long to display, try to maximize the windows or set a value less than {residual_width} in length."
        prefix: List[Segment] = list(console.render(line_prefix))[:-1] # -1 to discard default '\n' in the end
    else:
        prefix_width = 0
        prefix = []
    
    ## pick the left most available part of suffix if there isn't enough space
    residual_width -= prefix_width
    if line_suffix and residual_width > 0:
        suffix_width = min(console.measure(line_suffix).maximum, residual_width)
        suffix: List[Segment] = list(console.render(line_suffix[:residual_width]))[:-1]
    else:
        suffix_width = 0
        suffix = []
    
    ## render row separator: repeat the pass-in pattern to full display width
    if row_separator:
        total_width = obj_width + prefix_width + suffix_width

        single_sep: List[Segment] = list(console.render(row_separator))[:-1] 

        plain_text: str = ''.join([s.text for s in single_sep])
        times, remainder = divmod(total_width, len(plain_text))

        if remainder:
            rowsep_segs: List[Segment] = single_sep * times
            for seg in single_sep:
                if len(seg) > remainder:
                    rowsep_segs.append(seg.split_cells(remainder)[0])
                    break
                else:
                    rowsep_segs.append(seg)
                    remainder -= len(seg) 
        else:
            rowsep_segs = single_sep * times
        
        rowsep_segs = [Segment.line()] + rowsep_segs + [Segment.line()]
    else:
        rowsep_segs = [Segment.line()]
    
    # a fake implementation of `rich.print`
    console._buffer_index = 0
    for line in lines:
        console._buffer.extend(prefix + line + suffix + rowsep_segs)
        console._check_buffer()
        time.sleep(time_sep)

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

        - `tree_level_args` (Dict[str, Any]): A dictionary containing the display settings for each level of the tree. 
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
    def __init__(self, 
                 node:"OperationNode", # noqa # type: ignore 
                 loop_algebras:str='xyijkabcdefghlmnopqrstuvwz'):
        self.opnode = deepcopy(node)
        self.loop_algebras:str = loop_algebras

        self.render_unfold_tree = None
        self.render_fold_tree = None
        
        # basic display format for a rendered tree
        self.__default_level_args = {
            'label':'[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]', # str | Callable
            'style':'tree',
            'guide_style':'light_coral',
            'highlight':True,
            'hide_root':False,
            'expanded':True
        }
        
        self.__levels_args:Dict[Dict[str, Any]] = {
            '0':  {'label': '[b light_coral]<name>[/]', # default display setting for root node
                   'guide_style':'light_coral'}
        }
                
        # basic display format for all repeat blocks in a rendered tree
        self.__rpblk_args = { 
            'title': '[i]Repeat [[b]<repeat_time>[/b]] Times[/]',
            'title_align': 'center',
            'highlight': True,
            'style': 'dark_goldenrod',
            'border_style': 'dim',
            'box': HEAVY_EDGE,
            'expand': False
        }
        
        # basic format of footer in each repeat block
        def __default_rpft(attr_dict:dict) -> str:
            start_idx = attr_dict['node_id'].split('.')[-1]
            
            repeat_winsz = attr_dict['repeat_winsz']
            if repeat_winsz == 1:
                end_idx = int(start_idx) + attr_dict['repeat_time'] -1
                return f"Where <loop_algebra> ranges from [{start_idx}, {end_idx}]"
            else:
                end_idx = int(start_idx) + attr_dict['repeat_time']*repeat_winsz -1
                valid_vals = list(map(str, range(int(start_idx), end_idx, repeat_winsz)))
                return f"Where <loop_algebra> = {', '.join(valid_vals)}"
        self.repeat_footer = __default_rpft 
        
    @property
    def default_level_args(self) -> Dict[str, Any]:
        return self.__default_level_args
    
    @property
    def tree_level_args(self) -> Dict[str, Any]:
        return self.__levels_args

    @property
    def repeat_block_args(self) -> Dict[str, Any]:
        return self.__rpblk_args

    @default_level_args.setter
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
            raise TypeError(f'The new value of `TreeRenderer.default_level_args` must be a dict. But got {type(custom_args)}.')
        
        valid_setting_keys = tuple(Tree('.').__dict__.keys())
        self.__default_level_args.update(custom_args)
        self.__default_level_args = {k:v for k, v in self.__default_level_args.items() if k in valid_setting_keys}

    @tree_level_args.setter
    def tree_level_args(self, 
                        custom_args:Union[List[Dict[str, Any]], Dict[Any, Dict[str, Any]]]) -> None:
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
        if not isinstance(custom_args, (list, dict)):
            raise TypeError(f'The new value of `TreeRenderer.tree_level_args` must be a dict or a list of dict. But got {type(custom_args)}.')
        
        # convert to dict if input a list of dict
        if isinstance(custom_args, list):
            _custom_args = {}
            for level_args_dict in custom_args:
                if not isinstance(level_args_dict, dict):
                    warnings.warn(message=f"Non-dict entity found in `custom_args`: \n{level_args_dict}.\nThis entity will be ignored.\n",
                                  category=UserWarning)
                elif 'level' not in level_args_dict:
                    warnings.warn(message=f"Key `level` not found in pass-in setting: \n{custom_args}.\nThis setting will be ignored.\n",
                                  category=UserWarning)
                else:
                    level = str(level_args_dict.pop('level'))
                    _custom_args[level] = level_args_dict
        else:
            _custom_args = custom_args
        
        '''
        _custom_args = {
            '0': {level_0_setting},
            '1': {level_1_setting},
            ...
        }
        '''
        
        # filt out invalid level definations and invalid display settings
        valid_setting_keys = tuple(Tree('.').__dict__.keys())
        for level, level_args_dict in _custom_args.items():
            # assure level is a non-negative integer, 'default' or 'all'
            level = level.lower()
            if not level.isnumeric() and level not in ('default', 'all'):
                warnings.warn(message=f"The `level` key should be numeric, `default` or `all`, but got {level}.\nThis setting will be ignored.\n",
                              category=UserWarning)
                continue

            level_args_dict = {k:v for k, v in level_args_dict.items() if k in valid_setting_keys}

            if level == 'default':
                self.default_level_args = level_args_dict
            elif level == 'all':
                self.default_level_args = level_args_dict
                _custom_args = {} # all layer use the default setting
                break
            else:
                _custom_args[level] = level_args_dict
               
        self.__levels_args = _custom_args

    @repeat_block_args.setter
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
            raise TypeError(f'The new value of `TreeRenderer.repeat_block_args` must be a dict. But got {type(custom_args)}.')
        
        footer_key = list(filter(lambda x: x.lower() == 'repeat_footer', custom_args.keys()))
        if footer_key:
            self.repeat_footer = custom_args[footer_key[-1]] 
        
        valid_setting_keys = tuple(Panel('.').__dict__.keys())
        self.__rpblk_args.update(custom_args)
        self.__rpblk_args = {k:v for k, v in self.__rpblk_args.items() 
                                     if k in valid_setting_keys and k not in footer_key}

    def __call__(self,
                 *,
                 fold_repeat:bool=True,
                 level_args:Union[List[Dict[str, Any]], Dict[Any, Dict[str, Any]]]={},
                 repeat_block_args:Dict[str, Any]={}) -> Tree:
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
        
        assert isinstance(level_args, (list, dict)), f"Argument `level_args` must be a dict or a list of dicts, but got {type(level_args)}"
        assert isinstance(repeat_block_args, dict), f"Argument `repeat_block_args` must be a dict, but got {type(repeat_block_args)}"
        
        # check, clean and apply `level_args`, 
        if level_args:
            self.tree_level_args = level_args
        del level_args
        
        # check, clean and apply `repeat_block_args`
        if repeat_block_args:
            self.repeat_block_args = repeat_block_args
        del repeat_block_args
        
        # task_func for `dfs_task`
        def __apply_display_setting(subject:"OperationNode", # noqa # type: ignore
                                    pre_res=None) -> None:

            # skip repeat nodes and folded nodes when enable `fold_repeat`
            if fold_repeat and subject.is_folded: 
                return None
            if fold_repeat and not subject.render_when_repeat:
                return None
            
            display_root = subject.display_root 

            level = str(display_root.label)  

            # update display setting for the currently traversed node
            target_level_args = self.tree_level_args.get(level, self.default_level_args)

            # disolve label field
            origin_node_id = subject.node_id
            if fold_repeat and int(level) > 1:
                subject.node_id = subject.parent.node_id + f".{subject.node_id.split('.')[-1]}"
            label = self.__resolve_argtext(text=target_level_args['label'], attr_owner=subject)

            # apply display setting
            display_root.__dict__.update({**target_level_args, 'label':label})
            
            if fold_repeat:  
                loop_algebra = self.loop_algebras[0]
                use_algebra = False

                # if the repeat body contains more than one operations
                # get a complete copy of the repeat body, so as to render repeat block more conveniently later.
                if subject.repeat_winsz > 1: 
                    use_algebra = True

                    repeat_body = Tree('.', hide_root=True)
                    
                    for loop_idx, (node_id, node_name) in enumerate(subject.repeat_body):
                        repeat_op_node:"OperationNode" = subject.parent.childs[node_id] # type: ignore # noqa
                        
                        # update node_id with a algebraic expression which indicates the loop
                        if level != '1':
                           if loop_idx == 0:
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f'.{loop_algebra}'
                           else:
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f'.({loop_algebra}+{loop_idx})'
                        else:
                            if loop_idx == 0:
                                repeat_op_node.node_id = loop_algebra
                            else:
                                repeat_op_node.node_id = f'{loop_algebra}+{loop_idx}'
                        
                        # disoolve label field for the `rich.Tree` object of the currently traversed node
                        label = self.__resolve_argtext(text=target_level_args['label'], attr_owner=repeat_op_node)
                        
                        # update display setting for the `rich.Tree` object of the currently traversed node
                        repeat_display_node = copy(repeat_op_node.display_root)
                        repeat_display_node.__dict__.update({**target_level_args, 'label':label})
                        
                        # Delete repeat nodes and folded nodes (Note: operate in a copied tree)
                        repeat_display_node.children = [child.display_root for child in repeat_op_node.childs.values() 
                                                            if child.render_when_repeat and not child.is_folded]
                        
                        repeat_body.add(repeat_display_node)        
                
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
                        subject.node_id = subject.parent.node_id + f'.{loop_algebra}'
                    else:
                        subject.node_id = loop_algebra
                    display_root.label = self.__resolve_argtext(text=target_level_args['label'], attr_owner=subject)

                    if self.repeat_footer:
                        repeat_block_content = Group(
                            copy(display_root), # the tree structure of the circulating body
                            Rule(characters='-', style=self.repeat_block_args.get('style','')), # a separator made up of '-'
                            self.__resolve_argtext(text=self.repeat_footer, attr_owner=subject, 
                                                 loop_algebra=loop_algebra, node_id=origin_node_id),
                            fit=True
                        )
                    else:
                        repeat_block_content = copy(display_root)
                    
                    # make a pannel to show repeat information
                    repeat_block = Panel(repeat_block_content)
                    title = self.__resolve_argtext(text=self.repeat_block_args.get('title', ''), attr_owner=subject, 
                                                   loop_algebra=loop_algebra)
                    repeat_block.__dict__.update({**self.repeat_block_args, 'title':title})
                    
                    # overwrite the label of the first node in repeat block 
                    subject.display_root.label = repeat_block

                    # remove all children nodes of the first repeat item, 
                    # so that only the rendered panel will be displayed
                    subject.display_root.children = []

                if use_algebra:
                    self.loop_algebras = self.loop_algebras[1:]

            return None
        
        # apply display setting for each node by dfs traversal
        dfs_task(dfs_subject=self.opnode,
                 adj_func=lambda x:x.childs.values(),
                 task_func=__apply_display_setting,
                 visited_signal_func=lambda x:str(id(x)),
                 visited=[])

        # store the rendered result
        if fold_repeat:
            self.render_fold_tree = self.opnode.display_root
        else:
            self.render_unfold_tree = self.opnode.display_root
        
        return self.opnode.display_root

    def resolve_attr(self, attr_val:Any) -> str:
        """
        Function to process the attribute value resolved by regex.

        Args:
            attr_val (Any): The attribute value resolved by regex.

        Returns:
            str: the processed result. Must be a string!
        """
        return str(attr_val)

    def __resolve_argtext(self,
                          text:Union[str, Callable[[dict], str]], 
                          attr_owner:"OperationNode", # noqa # type: ignore
                          **kwargs) -> str: 
        """
        Disolve all placeholders in form of `<·>` in `text`.\n
        If you do not want the content in `<·>` to be resolved, you can use `\\<` or `\\>` to escape it.\n
        For example, `<name>` will be replaced by the value of `attr_owner.name`, while `\\<name\\>` will not be disolved.

        Args:
        ---
            - `text` (str): A string that may contain placeholder in the form of `<·>`.
            - `attr_owner` (OperationNode): The object who owns the attributes to be disolved.
            - `kwargs` (dict): Offering additional attributes.

        Returns:
        ---
            str: Text with all placeholders disolved.
        """
        attr_dict = copy(attr_owner.__dict__)
        attr_dict.update(kwargs)
        
        if isinstance(text, Callable):
            text = text(attr_dict)
        
        if not isinstance(text, str):
            warnings.warn(message='The received text(see below) to be resolved is not a string, cannot go ahead.\n' + \
                                  f'Type: {type(text)}\n Content: {text}',
                          category=UserWarning)

        res_str = re.sub(pattern=r'(?<!\\)<(.*?)(?<!\\)>',
                         repl=lambda match: self.resolve_attr(attr_dict.get(match.group(1), None)),
                         string=text)
        res_str = re.sub(pattern=r'\\<|\\>',
                         repl=lambda x: x.group().replace('\\', ''),
                         string=res_str)
        return res_str

    def __deepcopy__(self, memo) -> "TreeRenderer":
        new_obj = TreeRenderer()
        memo[id(self)] = new_obj
        new_obj.__dict__.update(self.__dict__)
        return new_obj
    
class TabularRenderer:

    def __init__(self, 
                 node:"OperationNode"):  # noqa # type: ignore

        self.opnode = node

        # underlying data
        self.__stats_data = {stat_name:DataFrame() for stat_name in node.statistics}

        # basic display format for each column
        self.__default_col_args = {
            'justify': 'center',
            'vertical': 'middle',
            'overflow': 'fold'
        }

        self.__default_tb_args = {
            'style': 'spring_green4',
            'highlight': True,

            'title': None,
            'title_style': 'bold',
            'title_justify': 'center',
            'title_align': 'center',

            'show_header': True,
            'header_style': 'bold',

            'show_footer': False,
            'footer_style': 'italic',

            'show_lines': False,

            'show_edge': True,
            'box': ROUNDED,
            'safe_box': True,

            'expand': False,
            'leading': 0,
        }
            
    @property
    def tb_args(self):
        return self.__default_tb_args
    
    @property
    def col_args(self):
        return self.__default_col_args

    @property
    def datas(self):
        return self.__stats_data

    @property
    def valid_export_format(self) -> Sequence[str]:
        return ('csv', 'xlsx')

    @tb_args.setter
    def tb_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f'The new value of `TabularRenderer.tb_args` must be a dict. But got {type(custom_args)}.')
    
        valid_setting_keys = tuple(Table().__dict__.keys())
        self.__default_tb_args.update(custom_args)
        self.__default_tb_args = {k:v for k, v in self.__default_tb_args.items() if k in valid_setting_keys}

    @col_args.setter
    def col_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f'The new value of `TabularRenderer.col_args` must be a dict. But got {type(custom_args)}.')

        valid_setting_keys = tuple(Column().__dict__.keys())
        self.__default_col_args.update(custom_args)
        self.__default_col_args = {k:v for k, v in self.__default_col_args.items() if k in valid_setting_keys}

    @staticmethod
    def __get_fields(stat:"Statistics", # noqa # type: ignore
                     ipt_fields:List[str]):
        """pick valid fields to display in the final table"""

        valid_fields = stat.tb_fields

        filted_fields = []
        if ipt_fields: # filt out invalid fields
            for field in ipt_fields:
                if field not in valid_fields:
                    warnings.warn(message=f'Field `{field}` not in the supported fields ({valid_fields}), \nwill be ignored.',
                                  category=UserWarning)
                    continue
                filted_fields.append(field)
        else:
            # use all fields by default
            filted_fields.extend(valid_fields)
        
        return filted_fields

    def __new_col(self, 
                  df:DataFrame,
                  col_name:str, 
                  col_func:Callable[[Dict], Any],
                  used_cols:List[str],
                  return_type=None,
                  col_idx:int = -1) -> DataFrame:
        assert len(used_cols) > 0, 'You need to specify the columns used in the function for creating new columns, \
                                     and pass them to `newcol_dependcol` as a list.'
        for used_name in used_cols:
            assert used_name in df.columns, f'Column `{used_name}` is not in the table.\nValid columns are {df.columns}.'

        final_cols = df.columns[:]
        col_idx = (col_idx if col_idx >= 0 else len(df.columns)+col_idx+1) % (len(df.columns)+1)
        final_cols.insert(col_idx, col_name)

        return df.with_columns(
            struct(used_cols)
            .map_elements(col_func, return_dtype=return_type)
            .alias(col_name)
        ).select(final_cols)

    def df2tb(self, df:DataFrame, show_raw:bool = False) -> Table:
        # create rich table
        tb_fields = df.columns
        tb = Table(*tb_fields)

        # apply overall display settings
        tb.__dict__.update(self.tb_args)

        # apply column settings to all columns
        for tb_col in tb.columns:
            tb_col.__dict__.update(self.col_args)
        
        # collect each column's none replacing string
        col_none_str = {col_name:getattr(df[col_name].drop_nulls().first(), 'none_str', '-') 
                        for col_name, col_type in df.schema.items()}
        
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

    def clear(self, stat_name:Optional[str]=None):
        if stat_name:
            self.__stats_data[stat_name].clear()
        else:
            for stat in self.__stats_data.values():
                stat.clear()

    def export(self, 
               df:DataFrame, 
               save_path:str, 
               format:Optional[str]=None,
               file_suffix:str='',
               raw_data:bool=False):
        
        # get save path
        if format is None:
            format = os.path.splitext(save_path)[-1]
            assert '.' in format, 'File foramat unknown!\n' + \
                                  f'Please specify a file path, not a dierectory path like {save_path}.\n' + \
                                  f'Or specify a file format using `format=xxx`, now we support exporting to {self.valid_export_format} file.'
                                  
        format = format.strip('.')
        assert format in self.valid_export_format, \
                f'`{format}` file is not supported, now we only support exporting {self.valid_export_format} file.'
        
        _, file_path = perfect_savepath(origin_path=save_path,
                                       target_ext=format,
                                       default_filename=f'{self.opnode.name}_{file_suffix}') 
        
        # deal with invalid data
        df = deepcopy(df)
        
        obj_cols = {col_name:df[col_name].drop_nulls().first().__class__ 
                    for col_name, col_type in df.schema.items() if col_type == pl_object}
        df = df.with_columns([
            col(col_name).map_elements(lambda s: getattr(s,'raw_data',s.val) if raw_data else str(s),
                                       return_dtype=float if raw_data else str)
            for col_name, obj_cls in obj_cols.items()
        ])            
        
        # export 
        if format == 'csv':
            # list column -> str
            ls_cols = [col_name for col_name, col_type in df.schema.items() if col_type == pl_list]
            df = df.with_columns([
                col(col_name).map_elements(lambda s: str(s.to_list()), return_dtype=str)
                for col_name in ls_cols
            ])
            df.write_csv(file=file_path)
        elif format == 'xlsx':
            df.write_excel(workbook=file_path, autofit=True)
        
        # output saving message
        if file_suffix:
            print(f'{file_suffix.capitalize()} data saved to [b magenta]{file_path}[/]')
        else:
            print(f'Data saved to [b magenta]{file_path}[/]')
    
    def __call__(self,
                 stat_name:str, 
                 raw_data:bool=False,
                 *, 
                 fields:List[str]=[],
                 table_settings:Dict[str, Any]={},
                 column_settings:Dict[str, Any]={},
                 newcol_name:str='',
                 newcol_func:Callable[[Dict[str, Any]], Any]=lambda col_dict: col_dict,
                 newcol_dependcol:List[str]=[],
                 newcol_type=None,
                 newcol_idx:int=-1,
                 save_to:Optional[str]=None,
                 save_format:Optional[str]=None): 
        
        assert isinstance(newcol_idx, int), f'`newcol_idx` must be an integer, but got {type(newcol_idx)}.'
        assert stat_name in self.opnode.statistics, \
            f"`{stat_name}` not in the supported statistics {self.opnode.statistics}"
        
        stat:"Statistic" = getattr(self.opnode, stat_name) # noqa # type: ignore

        # initialize the statistics data sheet
        valid_fields = self.__get_fields(stat, fields)
        data:DataFrame = self.__stats_data[stat_name]
    
        def __fill_cell(subject:"OperationNode", # noqa # type: ignore
                        pre_res=None):
            if not subject.is_leaf:
                return

            val_getter = attrgetter(*valid_fields)

            node_stat = getattr(subject, stat_name)

            stat_infos = node_stat.detail_val
            if stat_infos:
                for rec in stat_infos: # rec: NamedTuple
                    vals = val_getter(rec)
                    val_collector.append(vals)
            else:
                val_collector.append(['-']*len(valid_fields))

        # only when the table is empty, then explore the data using dfs
        # otherwise, rerange and return it directly
        if data.is_empty():
            val_collector = []
            dfs_task(dfs_subject=self.opnode,
                     adj_func=lambda x: x.childs.values(),
                     task_func=__fill_cell,
                     visited_signal_func=lambda x: str(id(x)),
                     visited=[])
            data = DataFrame(data=val_collector, schema=valid_fields, orient='row')
        else:
            data = data.select(valid_fields)
        
        if newcol_name:
            data = self.__new_col(df=data,
                                  col_name=newcol_name,
                                  col_func=newcol_func,
                                  used_cols=newcol_dependcol,
                                  return_type=newcol_type,
                                  col_idx=newcol_idx)


        self.tb_args = table_settings
        self.col_args = column_settings
        tb = self.df2tb(df=data, show_raw=raw_data)

        self.datas[stat_name] = data

        if save_to:
            save_to = os.path.abspath(save_to)  
            if '.' not in os.path.basename(save_to):
                assert save_format in self.valid_export_format, \
                    f"Argument `save_format` must be one in {self.valid_export_format}, but got {save_format}\n" + \
                    "Alternatively, you can set `save_to` to a concrete file path, like `path/to/file.xlsx`"
            
            self.export(df=data,
                        save_path=save_to,
                        format=save_format,
                        file_suffix=stat_name,
                        raw_data=raw_data)

        return tb, data