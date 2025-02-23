import re
import os
import warnings
from time import sleep
from copy import copy, deepcopy
from operator import attrgetter
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar

from rich import print, get_console
from rich.rule import Rule
from rich.tree import Tree
from rich.panel import Panel
from rich.segment import Segment
from rich.table import Table, Column
from rich.console import Group, RenderableType
from polars import DataFrame, struct, col
from polars import List as pl_list, Object as pl_object

from torchmeter.config import get_config, dict_to_namespace
from torchmeter.utils import dfs_task, resolve_savepath

__cfg__ = get_config()

__all__ = ["render_perline", "TreeRenderer", "TabularRenderer"]

NAMESPACE_TYPE = TypeVar('NameSpace')

def render_perline(renderable: RenderableType,
                   console=None) -> None:
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
    time_sep = __cfg__.render_interval
    if time_sep < 0:
        raise ValueError(f"The `render_interval` value defined in config must be non-negative, but got {time_sep}")

    console = console or get_console()

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
    
    loop_algebras:str='xyijkabcdefghlmnopqrstuvwz'
    
    def __init__(self, node:"OperationNode"): # noqa # type: ignore 
        self.opnode = node

        self.render_unfold_tree = None
        self.render_fold_tree = None
                
    @property
    def default_level_args(self) -> NAMESPACE_TYPE:
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
    def tree_levels_args(self) -> NAMESPACE_TYPE:
        return __cfg__.tree_levels_args

    @property
    def repeat_block_args(self) -> NAMESPACE_TYPE:
        return __cfg__.tree_repeat_block_args

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
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.default_level_args` with a dict. " + \
                            f"But got {type(custom_args)}.")
        
        valid_setting_keys = set(Tree('.').__dict__.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/tree.html for valid args.")
        self.default_level_args.__dict__.update(custom_args)
        
        self.default_level_args.mark_change()

    @tree_levels_args.setter
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
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.tree_levels_args` with a dict. " + \
                            f"But got {type(custom_args)}.")
                                                            
        # filt out invalid level definations and invalid display settings
        valid_setting_keys = set(Tree('.').__dict__.keys())
        for level, level_args_dict in custom_args.items():
            # assure level is a non-negative integer, 'default' or 'all'
            level = level.lower()
            if not level.isnumeric() and level not in ('default', 'all'):
                warnings.warn(message=f"The `level` key should be numeric, `default` or `all`, but got {level}.\nThis setting will be ignored.\n",
                              category=UserWarning)
                continue
                
            passin_keys = set(level_args_dict.keys())
            invalid_keys = passin_keys - valid_setting_keys
            if invalid_keys:
                raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.tree.Tree`, " + \
                               "refer to https://rich.readthedocs.io/en/latest/tree.html for valid args.")

            if level == 'default':
                self.default_level_args = level_args_dict
            elif level == 'all':
                self.default_level_args = level_args_dict
                # delete all levels settings 
                self.tree_levels_args = {k:v for k,v in self.tree_levels_args.__dict__.items() 
                                         if not k.isnumeric()}
                break
            else:
                getattr(self.tree_levels_args, level).__dict__.update(level_args_dict)
                       
        self.tree_levels_args.mark_change()

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
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.repeat_block_args` with a dict. " + \
                            f"But got {type(custom_args)}.")
                                                        
        footer_key = list(filter(lambda x: x.lower() == 'repeat_footer', custom_args.keys()))
        if footer_key:
            self.repeat_footer = custom_args[footer_key[-1]]
            del custom_args[footer_key[-1]] 
        
        valid_setting_keys = set(Panel('.').__dict__.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.panel.Panel`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/panel.html for valid args.")
        self.repeat_block_args.__dict__.update(custom_args)
        
        self.repeat_block_args.mark_change()
        
    def repeat_footer(self, attr_dict:Dict[str, Any]) -> Union[str, None]:
        """Must have only one args which accept an attribute dict"""
        # basic format of footer in each repeat block
        start_idx = attr_dict['node_id'].split('.')[-1]
            
        repeat_winsz = attr_dict['repeat_winsz']
        if repeat_winsz == 1:
            end_idx = int(start_idx) + attr_dict['repeat_time'] -1
            return f"Where <loop_algebra> ranges from [{start_idx}, {end_idx}]"
        else:
            end_idx = int(start_idx) + attr_dict['repeat_time']*repeat_winsz -1
            valid_vals = list(map(str, range(int(start_idx), end_idx, repeat_winsz)))
            return f"Where <loop_algebra> = {', '.join(valid_vals)}"

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
        
        fold_repeat:bool = __cfg__.tree_fold_repeat
        
        copy_tree = deepcopy(self.opnode)
        origin_algebras = self.loop_algebras
        
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
            target_level_args = getattr(self.tree_levels_args, level, self.default_level_args)
            target_level_args = target_level_args.__dict__

            # disolve label field
            origin_node_id = subject.node_id
            if fold_repeat and int(level) > 1:
                subject.node_id = subject.parent.node_id + f".{subject.node_id.split('.')[-1]}"
            label = self.__resolve_argtext(text=target_level_args.get('label', self.default_level_args.label),
                                           attr_owner=subject)

            # apply display setting
            display_root.__dict__.update({**target_level_args, 'label':label})
            
            if fold_repeat:  
                algebra = self.loop_algebras[0]
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
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f".{algebra}"
                           else:
                               repeat_op_node.node_id = repeat_op_node.parent.node_id + f".({algebra}+{loop_idx})"
                        else:
                            if loop_idx == 0:
                                repeat_op_node.node_id = algebra
                            else:
                                repeat_op_node.node_id = f"{algebra}+{loop_idx}"
                        
                        # disoolve label field for the `rich.Tree` object of the currently traversed node
                        label = self.__resolve_argtext(text=target_level_args.get('label', self.default_level_args.label), 
                                                       attr_owner=repeat_op_node)
                        
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
                        subject.node_id = subject.parent.node_id + f".{algebra}"
                    else:
                        subject.node_id = algebra
                    display_root.label = self.__resolve_argtext(text=target_level_args['label'], attr_owner=subject)

                    block_footer = self.__resolve_argtext(text=self.repeat_footer, attr_owner=subject,
                                                          loop_algebra=algebra, node_id=origin_node_id)
                    if block_footer:
                        repeat_block_content = Group(
                            copy(display_root), # the tree structure of the circulating body
                            Rule(characters='-', style='dim ' + getattr(self.repeat_block_args, 'style','')), # a separator made up of '-'
                            "[dim]" + block_footer + "[/]",
                            fit=True
                        )
                    else:
                        repeat_block_content = copy(display_root)
                    
                    # make a pannel to show repeat information
                    repeat_block = Panel(repeat_block_content)
                    title = self.__resolve_argtext(text=getattr(self.repeat_block_args, 'title', ''), attr_owner=subject, 
                                                   loop_algebra=algebra)
                    repeat_block.__dict__.update({**self.repeat_block_args.__dict__, 
                                                  'title':title,
                                                  'border_style': self.repeat_block_args.border_style + ' ' + self.repeat_block_args.style})
                    
                    # overwrite the label of the first node in repeat block 
                    subject.display_root.label = repeat_block

                    # remove all children nodes of the first repeat item, 
                    # so that only the rendered panel will be displayed
                    subject.display_root.children = []

                if use_algebra:
                    self.loop_algebras = self.loop_algebras[1:]

            return None
        
        # apply display setting for each node by dfs traversal
        dfs_task(dfs_subject=copy_tree,
                 adj_func=lambda x:x.childs.values(),
                 task_func=__apply_display_setting,
                 visited=[])

        self.loop_algebras = origin_algebras
        
        # cache the rendered result
        if fold_repeat:
            self.render_fold_tree = copy_tree.display_root
        else:
            self.render_unfold_tree = copy_tree.display_root
        
        return copy_tree.display_root

    def __resolve_argtext(self,
                          text:Union[str, Callable[[dict], Union[str,None]]], 
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
        
        if text is None:
            return ""
        
        if not isinstance(text, str):
            raise TypeError("The received text(see below) to be resolved is not a string nor None, cannot go ahead.\n" + \
                            f"Type: {type(text)}\nContent: {text}")

        res_str = re.sub(pattern=r'(?<!\\)<(.*?)(?<!\\)>',
                         repl=lambda match: self.resolve_attr(attr_dict.get(match.group(1), None)),
                         string=text)
        res_str = re.sub(pattern=r'\\<|\\>',
                         repl=lambda x: x.group().replace('\\', ''),
                         string=res_str)
        return res_str
    
class TabularRenderer:

    def __init__(self, node:"OperationNode"):  # noqa # type: ignore

        self.opnode = node

        # underlying data
        self.__stats_data = {stat_name:DataFrame() for stat_name in node.statistics}
            
    @property
    def tb_args(self) -> NAMESPACE_TYPE:
        return __cfg__.table_display_args
    
    @property
    def col_args(self) -> NAMESPACE_TYPE:
        return __cfg__.table_column_args

    @property
    def valid_export_format(self) -> List[str]:
        return ['csv', 'xlsx']

    @tb_args.setter
    def tb_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.tb_args` with a dict. " + \
                            f"But got {type(custom_args)}.")
        
        valid_setting_keys = set(Table().__dict__.keys())
        passin_keys = set(custom_args.keys())
        invalid_keys = passin_keys - valid_setting_keys
        if invalid_keys:
            raise KeyError(f"Keys {invalid_keys} is/are not accepted by `rich.table.Table`, " + \
                           "refer to https://rich.readthedocs.io/en/latest/tables.html for valid args.")
        self.tb_args.__dict__.update(custom_args)
        
        self.tb_args.mark_change()
        
    @col_args.setter
    def col_args(self, custom_args:Dict[str, Any]):
        if not isinstance(custom_args, dict):
            raise TypeError(f"You can only overwrite `{self.__class__.__name__}.col_args` with a dict. " + \
                            f"But got {type(custom_args)}.")
        
        valid_setting_keys = set(Column().__dict__.keys())
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
        tb = Table(*tb_fields)

        # apply overall display settings
        tb.__dict__.update(self.tb_args.__dict__)

        # apply column settings to all columns
        for tb_col in tb.columns:
            tb_col.__dict__.update(self.col_args.__dict__)
            tb_col.highlight = self.tb_args.highlight # compatiable with higher version of rich
        
        # collect each column's none replacing string
        col_none_str = {col_name:getattr(df[col_name].drop_nulls()[0], 'none_str', '-') 
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
        if stat_name is not None and not isinstance(stat_name,str):
            raise TypeError(f"`stat_name` must be a string or None, but got {type(stat_name)}.")
            
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
               raw_data:bool=False):
        
        save_path = os.path.abspath(save_path)
        
        # get save path
        if format is None:
            format = os.path.splitext(save_path)[-1]
            if '.' not in format:
                raise ValueError(f"File foramat unknown! Please specify a file format like {save_path}.\n" + \
                                 f"Or you can specify a file format using `format=xxx`, now we support exporting to {self.valid_export_format} file.")
                                  
        format = format.strip('.')
        if format not in self.valid_export_format:
            raise ValueError(f"`{format}` file is not supported, now we only support exporting to {self.valid_export_format} file.")
        
        _, file_path = resolve_savepath(origin_path=save_path,
                                        target_ext=format,
                                        default_filename=f"{self.opnode.name}_{file_suffix}") 
        
        # deal with invalid data
        df = deepcopy(df)
        
        obj_cols = {col_name:df[col_name].drop_nulls().first().__class__ 
                    for col_name, col_type in df.schema.items() if col_type == pl_object}
        df = df.with_columns([
            col(col_name).map_elements(lambda s: getattr(s,'raw_data',s.val) if raw_data else str(s),
                                       return_dtype=float if raw_data else str)
            for col_name in obj_cols.keys()
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
            print(f"{file_suffix.capitalize()} data saved to [b magenta]{file_path}[/]")
        else:
            print(f"Data saved to [b magenta]{file_path}[/]")
    
    def __call__(self,
                 stat_name:str,
                 *, 
                 raw_data:bool=False,
                 pick_cols:List[str]=[],
                 exclude_cols:List[str]=[],
                 custom_cols:Dict[str, str]={},
                 newcol_name:str='',
                 newcol_func:Callable[[Dict[str, Any]], Any]=lambda col_dict: col_dict,
                 newcol_type=None,
                 newcol_idx:int=-1,
                 save_to:Optional[str]=None,
                 save_format:Optional[str]=None): 
        """render rich tabel according to the statistics dataframe.
        Note that `pick_cols` work before `custom_col`
        """

        if stat_name not in self.opnode.statistics:
            raise ValueError(f"`{stat_name}` not in the supported statistics {self.opnode.statistics}.")
        if not isinstance(newcol_idx, int):
            raise ValueError(f"`newcol_idx` must be an integer, but got {type(newcol_idx)}.")
        if not isinstance(custom_cols, dict):
            raise ValueError(f"`custom_cols` must be a dict, but got {type(custom_cols)}.")
        
        data:DataFrame = self.__stats_data[stat_name]
        valid_fields = data.columns or getattr(self.opnode, stat_name).tb_fields
    
        def __fill_cell(subject:"OperationNode", # noqa # type: ignore
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
            val_collector = []
            nocall_nodes = []
            dfs_task(dfs_subject=self.opnode,
                     adj_func=lambda x: x.childs.values(),
                     task_func=__fill_cell,
                     visited=[])
            
            data = DataFrame(data=val_collector, schema=valid_fields, orient='row')
            self.__stats_data[stat_name] = data
            
            if nocall_nodes:
                warnings.warn(message=f"{', '.join(nocall_nodes)}\nThe modules above might be defined but not explicitly called. " + \
                                       "They will be ignored in the measuring, so will not appear in the table below.",
                              category=RuntimeWarning,)
        
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
            invalid_cols = tuple(filter(lambda col_name:col_name not in data.columns, custom_cols.keys()))
            if invalid_cols:
                raise ValueError(f"Column names {invalid_cols} not found in supported columns {data.columns}.")
            data = data.rename(custom_cols)
        
        # add new column
        if newcol_name:
            data = self.__new_col(df=data,
                                  col_name=newcol_name,
                                  col_func=newcol_func,
                                  return_type=newcol_type,
                                  col_idx=newcol_idx)
            self.__stats_data[stat_name] = data

        tb = self.df2tb(df=data, show_raw=raw_data)

        if save_to:
            save_to = os.path.abspath(save_to)  
            if '.' not in os.path.basename(save_to):
                if save_format not in self.valid_export_format:
                    raise ValueError(f"Argument `save_format` must be one in {self.valid_export_format}, but got {save_format}.\n" + \
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

        final_cols = df.columns[:]
        col_idx = (col_idx if col_idx >= 0 else len(df.columns)+col_idx+1) % (len(df.columns)+1)
        final_cols.insert(col_idx, col_name)

        return df.with_columns(
            struct(df.columns)
            .map_elements(col_func, return_dtype=return_type)
            .alias(col_name)
        ).select(final_cols)