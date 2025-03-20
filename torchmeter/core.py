from __future__ import annotations
from typing import TYPE_CHECKING

import torch.nn as nn
from rich import get_console
from rich.columns import Columns
from torch import Tensor
from torch import device as tc_device

from torchmeter.config import get_config
from torchmeter.statistic import Statistics
from torchmeter.display import render_perline

if TYPE_CHECKING:
    import sys
    from typing import Any, Dict, List, Tuple, Union, Optional
    
    from rich.tree import Tree
    from rich.text import Text
    from polars import DataFrame

    from torchmeter.config import FlagNameSpace
    from torchmeter.statistic import ParamsMeter, CalMeter, MemMeter, IttpMeter
    
    if sys.version_info >= (3, 8):
        from typing import TypedDict
    else:
        from typing_extensions import TypedDict

    class IPT_TYPE(TypedDict):
        args: Tuple[Any, ...]
        kwargs: Dict[str, Any]

__all__ = ["Meter"]
__cfg__ = get_config()

class Meter:

    def __init__(self, 
                 model: nn.Module,
                 device:Optional[Union[str, tc_device]]=None) -> None:
        
        from torchmeter.engine import OperationTree
        from torchmeter.display import TreeRenderer, TabularRenderer

        if not isinstance(model, nn.Module):
            raise TypeError(f"model must be a nn.Module, but got `{type(model).__name__}`.")
        
        device = device or self.__device_detect(model)
        self.__device = tc_device(device) if isinstance(device, str) else device
        self.model = model.to(self.__device)

        self._ipt:IPT_TYPE = {'args':tuple(), 'kwargs':dict()} # TODO: self.ipt_infer()

        self.optree = OperationTree(self.model)

        self.tree_renderer = TreeRenderer(self.optree.root)
        self.table_renderer = TabularRenderer(self.optree.root)

        self.__measure_param = False
        self.__measure_cal = False
        self.__measure_mem = False
        self.ittp_warmup = 50
        self.ittp_benchmark_time = 100

        self.__has_nocall_nodes:Optional[bool] = None
        self.__has_not_support_nodes:Optional[bool] = None

    def __call__(self, *args, **kwargs) -> Any:
        self._ipt = {'args': args, 'kwargs': kwargs}
        self._ipt2device()
        self.model.to(self.device)
        return self.model(*self._ipt['args'], **self._ipt['kwargs'])
    
    def __getattr__(self, name: str) -> Any:
        
        try:
            # get the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            return super().__getattribute__(name)
        
        except AttributeError:
            return getattr(self.model, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        
        cls_attrs:Dict[str, bool] = self.__get_clsattr_with_settable_flag()
        notchange_cls_attrs = [k for k,v in cls_attrs.items() if not v]
        
        if name in notchange_cls_attrs:
            raise AttributeError(f"`{name}` could never be set.")
        
        try:
            # set the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            
            super().__setattr__(name, value)
            
        except AttributeError:
            setattr(self.model, name, value)
    
    def __delattr__(self, name:str) -> None:
        
        cls_attrs:Dict[str, bool] = self.__get_clsattr_with_settable_flag()
        
        if name in cls_attrs:
            raise AttributeError(f"`{name}` could never be deleted.")
        
        try:
            # delete the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            
            super().__delattr__(name)
            
        except AttributeError:
            delattr(self.model, name)
    
    @property
    def ipt(self):
        return self._ipt
    
    @property
    def device(self) -> tc_device:
        return self.__device
    
    @device.setter
    def device(self, new_device:Union[str, tc_device]) -> None:
        self.__device = tc_device(new_device)
        self.model.to(self.__device)
        if not self._is_ipt_empty():
            self._ipt2device()

    @property
    def tree_fold_repeat(self):
        return __cfg__.tree_fold_repeat
    
    @tree_fold_repeat.setter
    def tree_fold_repeat(self, new_val:bool) -> None:
        if not isinstance(new_val, bool):
            raise TypeError("The `tree_fold_repeat` property can only be rewritten with a boolean, " + \
                            f"but got `{type(new_val).__name__}`.")
        __cfg__.tree_fold_repeat = new_val

    @property
    def tree_levels_args(self) -> FlagNameSpace:
        return self.tree_renderer.tree_levels_args
    
    @tree_levels_args.setter
    def tree_levels_args(self, custom_args:Dict[Any, Dict[str, Any]]) -> None:
        self.tree_renderer.tree_levels_args = custom_args   # type: ignore

    @property
    def tree_repeat_block_args(self) -> FlagNameSpace:
        return self.tree_renderer.repeat_block_args
    
    @tree_repeat_block_args.setter
    def tree_repeat_block_args(self, custom_args:Dict[str, Any]) -> None:
        self.tree_renderer.repeat_block_args = custom_args # type: ignore

    @property
    def table_display_args(self) -> FlagNameSpace:
        return self.table_renderer.tb_args

    @table_display_args.setter
    def table_display_args(self, custom_args:Dict[str, Any]) -> None:
        self.table_renderer.tb_args = custom_args       # type: ignore

    @property
    def table_column_args(self) -> FlagNameSpace:
        return self.table_renderer.col_args

    @table_column_args.setter
    def table_column_args(self, custom_args:Dict[str, Any]) -> None:
        self.table_renderer.col_args = custom_args      # type: ignore

    @property
    def structure(self) -> Tree:
        fold_repeat = __cfg__.tree_fold_repeat
        
        is_rpbk_change = __cfg__.tree_repeat_block_args.is_change()
        
        is_level_change = __cfg__.tree_levels_args.is_change()
        
        if fold_repeat:
            cache_res = self.tree_renderer.render_fold_tree if not is_rpbk_change else None
        else:
            cache_res = self.tree_renderer.render_unfold_tree
        cache_res = cache_res if not is_level_change else None
        
        rendered_tree = self.tree_renderer() if cache_res is None else cache_res
        
        if is_rpbk_change and fold_repeat:
            __cfg__.tree_repeat_block_args.mark_unchange()
        if is_level_change:
            __cfg__.tree_levels_args.mark_unchange()
        
        # render_perline(renderable=rendered_tree)
        return rendered_tree

    @property
    def param(self) -> ParamsMeter:
        if not self.__measure_param:
            list(map(lambda node: node.param.measure(), self.optree.all_nodes))
            self.__measure_param = True

        return self.optree.root.param
    
    @property
    def cal(self) -> CalMeter:
        if not self.__measure_cal:
            if self._is_ipt_empty():
                raise RuntimeError("Input unknown! You should perform at least one feed-forward inference before measuring calculation!") 

            hook_ls = [node.cal.measure() for node in self.optree.all_nodes]

            # feed forwad
            self._ipt2device()
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove() if x is not None else None, hook_ls)) 

            self.__measure_cal = True
        
        return self.optree.root.cal

    @property
    def mem(self) -> MemMeter:
        if not self.__measure_mem:
            if self._is_ipt_empty():
                raise RuntimeError("Input unknown! You should perform at least one feed-forward inference " + \
                                   "before measuring the memory cost!") 

            hook_ls = [node.mem.measure() for node in self.optree.all_nodes]

            # feed forward
            self._ipt2device()
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove() if x is not None else None, hook_ls))

            self.__measure_mem = True

        return self.optree.root.mem

    @property
    def ittp(self) -> IttpMeter:

        from tqdm import tqdm

        if self._is_ipt_empty():
            raise RuntimeError("Input unknown! " + \
                               "You should perform at least one feed-forward inference before measuring the inference time or throughput!") 
        if not isinstance(self.ittp_warmup, int):
            raise TypeError(f"ittp_warmup must be an integer, but got `{type(self.ittp_warmup).__name__}`")
        if self.ittp_warmup < 0:
            raise ValueError(f"ittp_warmup must be greater than or equal to 0, but got `{self.ittp_warmup}`.")
        
        self._ipt2device()

        for i in tqdm(range(self.ittp_warmup), desc='Warming Up'):
            self.model(*self.ipt['args'], **self.ipt['kwargs'])

        pb = tqdm(total=self.ittp_benchmark_time*len(self.optree.all_nodes), 
                  desc='Benchmark Inference Time & Throughput', 
                  unit='module')
        hook_ls = [node.ittp.measure(device=self.device, 
                                     repeat=self.ittp_benchmark_time,
                                     global_process=pb) 
                    for node in self.optree.all_nodes]

        # feed forwad
        self.model(*self.ipt['args'], **self.ipt['kwargs']) 

        # remove hooks after measurement
        list(map(lambda x:x.remove() if x is not None else None, hook_ls))

        del pb

        return self.optree.root.ittp

    @property
    def model_info(self) -> Text:
        from inspect import signature
        from torchmeter.utils import indent_str, data_repr

        forward_args:List[str] = list(signature(self.model.forward).parameters.keys())
        if self._is_ipt_empty():
            ipt_repr = "[dim]Not Provided\n(give an inference first)[/]"
        else:
            ipt_dict = {forward_args[args_idx]: anony_ipt for args_idx, anony_ipt in enumerate(self.ipt['args'])}
            ipt_dict.update(self.ipt['kwargs'])
            ipt_repr_ls = [f"{args_name} = {data_repr(args_val)}" for args_name, args_val in ipt_dict.items()] 
            ipt_repr = ',\n'.join(ipt_repr_ls) 

        forward_args = ["self"] + forward_args
        infos = '\n'.join([
            f"• [b]Model    :[/b] {self.optree.root.name}",
            f"• [b]Device   :[/b] {self.device}",
            f"• [b]Signature:[/b] forward({', '.join(forward_args)})",
            f"• [b]Input    :[/b] \n{indent_str(ipt_repr, indent=3, guideline=False)}"
        ])
        
        console = get_console()
        return console.render_str(infos)

    @property
    def subnodes(self) -> List[str]:
        return [f"({node.node_id}) {node.name}" for node in self.optree.all_nodes]

    def to(self, new_device:Union[str, tc_device]) -> None:
        self.device = new_device # type: ignore

    def rebase(self, node_id:str) -> Meter:
        if not isinstance(node_id, str):
            raise TypeError(f"node_id must be a string, but got `{type(node_id).__name__}`.")
        
        if node_id == "0":
            return self
        
        id_generator = ( (node_idx, node.node_id) for node_idx, node in enumerate(self.optree.all_nodes) )

        for idx, valid_id in id_generator:
            if node_id == valid_id:
                new_base = self.optree.all_nodes[idx]
                return self.__class__(new_base.operation, device=self.device)
        else:
            raise ValueError(f"Invalid node_id: {node_id}. Use `Meter(your_model).subnodes` to check valid ones.")

    def stat_info(self, stat_or_statname:Union[str, Statistics], *, show_warning:bool=True) -> Text:
        if isinstance(stat_or_statname, str):
            stat = getattr(self, stat_or_statname)
        elif isinstance(stat_or_statname, Statistics):
            stat = stat_or_statname
        else:
            raise TypeError(f"Invalid type for stat_or_statname: `{type(stat_or_statname).__name__}`. " + \
                            "Please pass in the statistics name or the statistics object itself.")

        stat_name = stat.name
        infos_ls:List[str] = [f"• [b]Statistics:[/b] {stat_name}"]
        
        if stat_name == 'ittp':
            infos_ls.append(f"• [b]Benchmark Times:[/b] {self.ittp_benchmark_time}")
            
        infos_ls.extend([
            f"• [b]{k}:[/b] {v}" for k, v in stat.crucial_data.items()
        ])
        
        ## warning field, only works when stat is "cal" or "mem"
        if show_warning and stat_name not in ("param", "ittp"):
            # cache for __has_nocall_nodes
            if self.__has_nocall_nodes is None:
                from operator import attrgetter
                
                crucial_data_getter = attrgetter(f"{stat_name}.crucial_data")
                try:
                    list(map(crucial_data_getter, self.optree.all_nodes))
                    self.__has_nocall_nodes = False
                except RuntimeError:
                    self.__has_nocall_nodes = True  
            
            # cache for __has_not_support_nodes
            if stat_name == "cal" and self.__has_not_support_nodes is None:
                self.__has_not_support_nodes = any(n.cal.is_not_supported 
                                                   for n in self.optree.all_nodes)
            
            warns_ls = []
            if self.__has_nocall_nodes:
                warns_ls.append(" "*2 + "[dim yellow]:arrow_forward:  Some nodes are defined but not called explicitly.[/]")
            if stat_name == "cal" and self.__has_not_support_nodes:
                warns_ls.append(" "*2 + "[dim yellow]:arrow_forward:  Some modules don't support calculation measurement yet.[/]")
            if warns_ls:
                warns_ls.insert(0, "[dim yellow]:warning:  Warning: the result may be inaccurate, cause:[/]")
                warns_ls.append(" "*2 + f"[dim cyan]:ballot_box_with_check:  use `Meter(your_model).profile('{stat_name}')` to see more.[/]")
            
            infos_ls.extend(warns_ls)
                    
        infos = '\n'.join(infos_ls)
        
        console = get_console()
        return console.render_str(infos)

    def overview(self, *order:str, show_warning:bool=True) -> Columns:
        """Overview of all statistics"""
        
        from functools import partial
        from rich.panel import Panel
        from rich.box import HORIZONTALS

        order = order or self.optree.root.statistics
        
        invalid_stat = tuple(filter(lambda x: x not in self.optree.root.statistics, order))
        if len(invalid_stat) > 0:
            raise ValueError(f"Invalid statistics: {invalid_stat}")
        
        container = Columns(expand=True, align='center')
        format_cell = partial(Panel, safe_box=True, expand=False, highlight=True, box=HORIZONTALS)
        
        container.add_renderable(format_cell(self.model_info, title='[b]Model INFO[/]', border_style='orange1'))
        container.renderables.extend([format_cell(self.stat_info(stat_name, show_warning=show_warning), 
                                                  title=f"[b]{stat_name.capitalize()} INFO[/]",
                                                  border_style='cyan') 
                                      for stat_name in order])
        
        return container

    def table_cols(self, stat_name:str) -> Tuple[str, ...]:
        if not isinstance(stat_name, str):
            raise TypeError(f"stat_name must be a string, but got `{type(stat_name).__name__}`.")
        
        stats_data_dict:Dict[str, DataFrame] = self.table_renderer.stats_data
        
        if stat_name not in stats_data_dict:
            raise KeyError(f"Statistics `{stat_name}` not in {tuple(stats_data_dict.keys())}.")
        
        stat_data:DataFrame = stats_data_dict[stat_name]
        
        if stat_data.is_empty():
            cols:Tuple[str, ...] = getattr(self.optree.root, stat_name).tb_fields
        else:
            cols = tuple(stat_data.columns)
        
        return cols
    
    def profile(self, 
                stat_name:str, 
                show=True, no_tree=False, 
                **tb_kwargs):
        """To render a tabular profile of the statistics
        
        Args:
            stat
            show
            no_tree
            force_preset: if True, force to use the preset table settings (i.e. self.tb_args)
            tb_kwargs
                - fields:List[str]=[],
                - table_settings:Dict[str, Any]={},
                - column_settings:Dict[str, Any]={},
                - newcol_name:str='',
                - newcol_func:Callable[[Dict[str, Any]], Any]=lambda col_dict: col_dict,
                - newcol_dependcol:List[str]=[],
                - newcol_type=None,
                - newcol_idx:int=-1,
                - save_csv:str=None,
                - save_excel:str=None
        
        """

        from rich.rule import Rule
        from rich.layout import Layout

        # the horizontal gap between tree and table
        TREE_TABLE_GAP = __cfg__.combine.horizon_gap

        if not isinstance(stat_name, str):
            raise TypeError(f"stat_name must be a string, but got `{type(stat_name).__name__}`.") 

        if TREE_TABLE_GAP < 0:
            raise ValueError("The gap between the rendered tree and the rendered table should be non-negative, " + \
                             f"but got `{TREE_TABLE_GAP}`.")
        
        stat = getattr(self, stat_name)
        tb, data = self.table_renderer(stat_name=stat_name, **tb_kwargs)
        
        if not show:
            return tb, data
        
        tree = None if no_tree else self.structure
        
        console = get_console()
        tree_width = console.measure(tree).maximum if not no_tree else 0 # type: ignore
        desirable_tb_width = console.measure(tb).maximum
        actual_tb_width = min(desirable_tb_width, console.width - tree_width - TREE_TABLE_GAP)
        
        if actual_tb_width <= 5: # 5 is the minimum width of table
            raise RuntimeError("The width of the terminal is too small, try to maximize the window or " + \
                               "set a smaller `horizon_gap` value in config and try again.")
        
        # when some cells in the table is overflown, we need to show a line between rows
        if actual_tb_width < desirable_tb_width:
            tb.show_lines = True 
        
        # get main content(i.e. tree & statistics table)
        if no_tree:
            main_content = tb
            tree_height = 0
        else:
            main_content = Layout()
            main_content.split_row(Layout(tree, name='left', size=tree_width + TREE_TABLE_GAP),
                                   Layout(tb, name='right', size=actual_tb_width))
            tree_height = len(console.render_lines(tree)) # type: ignore
        
        temp_options = console.options.update_width(actual_tb_width) 
        tb_height = len(console.render_lines(tb, options=temp_options))
        main_content_height = max(tree_height, tb_height)
        main_content_width = tree_width + actual_tb_width + (0 if no_tree else TREE_TABLE_GAP)

        # get footer content
        footer = Columns(title=Rule('[gray54]s u m m a r y[/]', characters='-', style='gray54'), # type: ignore
                         padding=(1,1),
                         equal=True, 
                         expand=True)
        
        model_info = self.model_info
        stat_info = self.stat_info(stat_or_statname=stat, show_warning=False)
        model_info.style = 'dim'
        stat_info.style = 'dim'
        footer.add_renderable(model_info)
        footer.add_renderable(stat_info)

        temp_options = console.options.update_width(main_content_width)
        footer_height = len(console.render_lines(footer, options=temp_options))
        
        # render profile
        canvas = Layout()
        canvas.split_column(Layout(main_content, name='top', size=main_content_height),
                            Layout(footer, name='down', size=footer_height))
        
        origin_width = console.width
        origin_height = console.height
        console.width = main_content_width
        console.height = main_content_height + footer_height
        
        try: 
            render_perline(renderable=canvas)
        finally:
            # if user interupts the rendering when render_interval > 0
            # still restore the console size
            console.width = origin_width
            console.height = origin_height
        
        return tb, data

    def _is_ipt_empty(self) -> bool:
        return not self._ipt['args'] and not self._ipt['kwargs']
        
    def _ipt2device(self) -> None:
        """Moves all input tensors to the specified device.

        This method checks if the input tensors are already on the specified device. 
        If not, it moves them to the device set in the Meter instance.

        Raises:
            RuntimeError: If input data is needed but not provided (i.e., `self._ipt` is empty).

        Notes:
            - The method only processes tensors in the input.
            - Non-tensor inputs remain unchanged.
        """

        from inspect import signature
        forward_args = signature(self.model.forward).parameters

        if len(forward_args) and self._is_ipt_empty():
            raise RuntimeError("No input data provided.")

        devices = set(arg.device for arg in self._ipt['args'] if isinstance(arg, Tensor))
        devices.update(kwargs.device for kwargs in self._ipt['kwargs'].values() if isinstance(kwargs, Tensor))

        if not len(devices):
            return
        
        if len(devices) == 1 and next(iter(devices)) == self.device:
            return

        self._ipt = {
            'args': tuple(x.to(self.device) if isinstance(x, Tensor) else x 
                          for x in self._ipt['args']),
            'kwargs': {k: (v.to(self.device) if isinstance(v, Tensor) else v) 
                       for k, v in self._ipt['kwargs'].items()}
        }

    def __device_detect(self, model) -> Union[str, tc_device]:
        
        import warnings
        
        try:
            model_first_param = next(model.parameters())
            return model_first_param.device
        
        except StopIteration:
            warnings.warn(category=UserWarning, message=\
                "We can't detect the device where your model is located because no parameter was found in your model. " + \
                "We'll move your model to CPU and do all subsequent analysis based on this CPU version. " + \
                "If this isn't what you want, set a specific device when initializing the `Meter` class, " + \
                "e.g. `Meter(your_model, device='cuda:0')`.")
                          
            return "cpu"
        
    def __repr__(self) -> str:
        return f"Meter(model={self.optree}, device={self.device})"

    @classmethod
    def __get_clsattr_with_settable_flag(cls) -> Dict[str, bool]:
        """Determines which class attributes have setter methods defined.

        This method iterates over all properties of the class and checks if a setter method
        is defined for each property. It returns a dictionary mapping attribute names to a
        boolean indicating whether the attribute is settable.

        Returns:
            Dict[str, bool]: A dictionary where keys are attribute names and values indicate
            whether the attribute has a setter method (True if settable, False otherwise).
        """
        
        return {k:v.fset is not None for k,v in cls.__dict__.items() 
                if isinstance(v, property)}
        