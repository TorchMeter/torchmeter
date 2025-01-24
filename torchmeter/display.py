import re
import time
import warnings
from copy import copy,deepcopy
from rich import get_console
from rich.rule import Rule
from rich.tree import Tree
from rich.panel import Panel
from rich.box import HEAVY_EDGE
from rich.jupyter import display
from rich.segment import Segment
from typing import Any, Callable, Dict, Iterable, List, TypeVar, Union

from rich.console import (
    Group, 
    WINDOWS,
    _STD_STREAMS_OUTPUT, 
    get_fileno,
)

from .utils import dfs_task

OPN_TYPE = TypeVar("OperationNode")

# 获取 rich 输出底层
# console = get_console()
# render_segs = list(console.render(tree)) # List[rich.Segment]

def render_segments(console:"rich.console.Console"=None, # noqa
                    segments:List[Segment]=[]) -> None:
    """
    Borrow and modify from `rich.console.Console._check_buffer()`

    This function is used to render a list of rich.Segment objects to terminal.
    
    Args:
    ---
        - `console` (rich.console.Console): The console object to render to.

        - `segments` (List[Segment]): list of rich.Segment objects to be rendered.
    
    Returns:
    ---
        None
    """
    
    console = console or get_console()

    with console._lock:
        if console.is_jupyter:  # pragma: no cover
            display(segments, console._render_buffer(segments[:]))
            del segments[:]
            return 
        
        if WINDOWS:
            use_legacy_windows_render = False
            if console.legacy_windows:
                fileno = get_fileno(console.file)
                if fileno is not None:
                    use_legacy_windows_render = (
                        fileno in _STD_STREAMS_OUTPUT
                    )

            if use_legacy_windows_render:
                from rich._win32_console import LegacyWindowsTerm
                from rich._windows_renderer import legacy_windows_render
                buffer = segments[:]
                if console.no_color and console._color_system:
                    buffer = list(Segment.remove_color(buffer))

                legacy_windows_render(buffer, LegacyWindowsTerm(console.file))
            else:
                # Either a non-std stream on legacy Windows, or modern Windows.
                text = console._render_buffer(segments[:])
                # https://bugs.python.org/issue37871
                # https://github.com/python/cpython/issues/82052
                # We need to avoid writing more than 32Kb in a single write, due to the above bug
                write = console.file.write
                # Worse case scenario, every character is 4 bytes of utf-8
                MAX_WRITE = 32 * 1024 // 4
                try:
                    if len(text) <= MAX_WRITE:
                        write(text)
                    else:
                        batch: List[str] = []
                        batch_append = batch.append
                        size = 0
                        for line in text.splitlines(True):
                            if size + len(line) > MAX_WRITE and batch:
                                write("".join(batch))
                                batch.clear()
                                size = 0
                            batch_append(line)
                            size += len(line)
                        if batch:
                            write("".join(batch))
                            batch.clear()
                except UnicodeEncodeError as error:
                    error.reason = f"{error.reason}\n" + \
                        "*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"
                    raise
        else:
            text = console._render_buffer(segments[:])
            try:
                console.file.write(text)
            except UnicodeEncodeError as error:
                error.reason = f"{error.reason}\n" + \
                    "*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"
                raise

        console.file.flush()

def render_segments_perline(segments:Iterable[Segment], time_sep:float=0) -> None:
    """
    Renders segments that make up a single line with `time_sep` seconds between each line.

    Args:
        - `segments` (Iterable[Segment]): An iterable of segments to be rendered. 
        
        - `time_sep` (float, optional): Time to sleep between each line. Defaults to 0.
    """
    assert time_sep >= 0, f"Argument `time_sep` must be non-negative, but got {time_sep}"

    line_segs = []

    for seg in segments:
        if seg.text == '\n':
            render_segments(segments=line_segs)
            time.sleep(time_sep)
            line_segs = []
        
        line_segs.append(seg)
    else:
        if line_segs:
            render_segments(segments=line_segs)    

class TreeRenderer:

    def __init__(self):
        self.console = get_console()

        self.loop_algebras:str='xyijkabcdefghlmnopqrstuvwz'

        self.render_unfold_tree = None
        self.render_fold_tree = None
        
        # basic display format for a rendered tree
        self.__level_args = {
            'label':'[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]', # str | Callable
            'style':'tree',
            'guide_style':'light_coral',
            'highlight':True,
            'hide_root':False,
            'expanded':True
        }
        
        self.tree_level_args:List[Dict[str, str]] = [
            {'level': 0,
             'label': '[b light_coral]<name>[/]', # default display setting for root node
             'guide_style':'light_coral'}
        ]
        
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
                return f"Where <loop_algebra> ∈ \[{start_idx}, {end_idx}]"
            else:
                end_idx = int(start_idx) + attr_dict['repeat_time']*repeat_winsz -1
                valid_vals = list(map(str, range(int(start_idx), end_idx, repeat_winsz)))
                return f"Where <loop_algebra> = {', '.join(valid_vals)}"
        self.repeat_footer = __default_rpft 
        
    @property
    def default_level_args(self) -> Dict[str, str]:
        return self.__level_args
    
    @default_level_args.setter
    def default_level_args(self, custom_args:Dict[str, str]) -> Dict[str, str]:
        if not isinstance(custom_args, dict):
            raise TypeError(f'The new value of `default_level_args` must be a dict. But got {type(custom_args)}.')
        self.__level_args.update(custom_args)

    @property
    def default_rpblk_args(self) -> Dict[str, Any]:
        return self.__rpblk_args
    
    @default_rpblk_args.setter
    def default_rpblk_args(self, custom_args:Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(custom_args, dict):
            raise TypeError(f'The new value of `default_rpblk_args` must be a dict. But got {type(custom_args)}.')
        
        footer_key = list(filter(lambda x: x.lower() == 'repeat_footer', custom_args.keys()))
        if footer_key:
            self.repeat_footer = custom_args[footer_key[-1]] 
            del custom_args[footer_key[-1]]
        self.__rpblk_args.update(custom_args)

    def render(self,
               node:"OperationNode", # noqa
               level_args:List[Dict[str, Any]]=[],
               fold_repeat:bool=True,
               repeat_block_args:Dict[str, Any]={},
               ) -> None:
        """
        Renders the OperationNode object and its childs as a tree. 
        
        It has following features:
            - enables each row to be rendered at a specific time interval
            
            - allows custom rendering for even each level of the tree. You can specify your own rendering by 
            passing a list of dictionaries to `level_args`. 
            
            Each dictionary should have the key `level` to indicate the level at which it works, 
            Otherwise, this dictionary will be ignored. 
            
            Besides it, the other key-value pairs will be passed as `args` to `rich.Tree` for rendering.
            Here offer the default display setting as a glimpse of the allowed key-value pairs, 
            refer more at https://rich.readthedocs.io/en/latest/tree.html:

                1. 'label':'[gray35](<node_id>) [b green]<name>[/b green] [b cyan]<type>[/]' # what to print
                    you can use `<·>` to access the attributes of the operation node, such as `node_id`, `name`, `type` etc.

                2. 'style':'tree',                 # style of this node

                3. 'guide_style':'dark_goldenrod', # guide-line style

                4. 'highlight':True,               # whether to highlight renderable (if str)

                5. 'hide_root':False,              # whether to hide root node

                6. 'expanded':True                 # whether to display children
            
        You can learn how to use this function from the example section below.

        Args:
        ---
            - `node` (OperationNode): the node to be rendered as a tree
            
            - `level_args` (List[Dict[str, Any]], optional): a list of dictionaries, each of which controls 
                                                                    the render settings of specific tree level through key 'level'. 
                                                                    Defaults to [], which means using the default setting for each level.
            
            - `time_sep` (float, optional): time interval between each render. 
                                            Defaults to 0.15.

        Returns:
        ---
            None
        
        Example:
        ---
            ```python
            from torchvision.models import resnet18
            from torchmeter.engine import OperationTree
            from torchmeter.display import render_as_tree

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

            render_as_tree(optree.root, 
                        time_sep=0.1, 
                        level_args=[root_display, level_1_display, level_2_display])
            ```
        """
        
        assert isinstance(level_args, list), f"Argument `level_args` must be a list of dictionaries, but got {type(level_args)}"
        assert isinstance(repeat_block_args, dict), f"Argument `repeat_block_args` must be a dictionary, but got {type(repeat_block_args)}"
        
        # check and clean each dict in `level_args`, 
        # discard non-dict entity and the entity without `level` attr in pass-in `level_args`
        for custom_args in level_args:
            if not isinstance(custom_args, dict):
                warnings.warn(message=f"Non-dict entity found in `level_args`: {custom_args}. This entity will be ignored.\n",
                              category=UserWarning)
            elif 'level' not in custom_args:
                warnings.warn(message=f"Key `level` not found in pass-in setting: {custom_args}. This setting will be ignored.\n",
                              category=UserWarning)
            else:
                self.tree_level_args.append(custom_args)
        
        # then link each dict with its target level to `valid_level_args`
        valid_level_args = {}
        for custom_args in self.tree_level_args:
            # discard invalid setting
            accept_args = {k:v for k,v in custom_args.items() 
                            if k in node.display_root.__dict__}
            
            # link level and corresponding setting
            level = str(custom_args['level'])
            if level.lower() == 'default':
                self.default_level_args.update(accept_args)
            elif level.lower() == 'all':
                self.default_level_args.update(accept_args)
                valid_level_args.clear()
                break
            else:
                valid_level_args[level] = accept_args
        del level_args
        
        # check and clean `repeat_block_args`
        valid_repeat_args = {**self.default_rpblk_args, **repeat_block_args}
        self.repeat_footer = valid_repeat_args.get('repeat_footer', self.repeat_footer)
        if repeat_block_args:
            valid_repeat_args = {k:v for k,v in valid_repeat_args.items() 
                                    if k in Panel('').__dict__}
        del repeat_block_args
        
        # task_func for `dfs_task`
        def __apply_display_setting(subject:"OperationNode", # noqa
                                    pre_res=None) -> None:

            # skip repeat nodes and folded nodes when enable `fold_repeat`
            if fold_repeat and subject.is_folded: 
                return None
            if fold_repeat and not subject.render_when_repeat:
                return None
            
            display_root = subject.display_root 

            level = str(display_root.label)  

            # update display setting for the currently traversed node
            target_level_args = valid_level_args.get(level, self.default_level_args)

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
                        repeat_op_node:"OperationNode" = subject.parent.childs[node_id] # noqa
                        
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
                            Rule(characters='-', style=valid_repeat_args.get('style','')), # a separator made up of '-'
                            self.__resolve_argtext(text=self.repeat_footer, attr_owner=subject, 
                                                 loop_algebra=loop_algebra, node_id=origin_node_id),
                            fit=True
                        )
                    else:
                        repeat_block_content = copy(display_root)
                    
                    # make a pannel to show repeat information
                    repeat_block = Panel(repeat_block_content)
                    title = self.__resolve_argtext(text=valid_repeat_args.get('title', ''), attr_owner=subject, 
                                                   loop_algebra=loop_algebra)
                    repeat_block.__dict__.update({**valid_repeat_args, 'title':title})
                    
                    # overwrite the label of the first node in repeat block 
                    subject.display_root.label = repeat_block

                    # remove all children nodes of the first repeat item, 
                    # so that only the rendered panel will be displayed
                    subject.display_root.children = []

                if use_algebra:
                    self.loop_algebras = self.loop_algebras[1:]

            return None
        
        # apply display setting for each node by dfs traversal
        copy_tree = deepcopy(node)
        dfs_task(dfs_subject=copy_tree,
                 adj_func=lambda x:x.childs.values(),
                 task_func=__apply_display_setting,
                 visited_signal_func=lambda x:str(id(x)),
                 visited=[])

        # store the rendered result
        if fold_repeat:
            self.render_fold_tree = copy_tree.display_root
        else:
            self.render_unfold_tree = copy_tree.display_root
        
        return copy_tree.display_root

    def resolve_attr(self, attr_val:Any) -> str:
        '''
        if the resolving attribute doesn't exist, then the `attr_val` will be `None`
        '''
        return str(attr_val)

    def __resolve_argtext(self,
                          text:Union[str, Callable[[dict], str]], 
                          attr_owner:OPN_TYPE, # noqa
                          **kwargs) -> str: 
        """
        Disolve all placeholders in form of `<·>` in `text`.

        Args:
            - `text` (str): A string that may contain placeholder in the form of `<·>`.
            - `attr_owner` (OperationNode): The object who owns the attributes to be disolved.

        Returns:
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