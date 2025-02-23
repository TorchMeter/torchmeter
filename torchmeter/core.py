from inspect import signature
from functools import partial
from typing import Any, Dict, List, Tuple

import torch.nn as nn
from tqdm import tqdm
from rich import get_console
from rich.rule import Rule
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns
from rich.box import HORIZONTALS
from torch import Tensor
from torch import device as tc_device

from torchmeter.config import get_config
from torchmeter.engine import OperationTree
from torchmeter.utils import indent_str, data_repr
from torchmeter.display import TreeRenderer, TabularRenderer, render_perline

__cfg__ = get_config()

__all__ = ["Meter"]

class Meter:

    def __init__(self, 
                 model: nn.Module,
                 device:str='cpu') -> None:
        
        self.__device = tc_device(device)

        if not isinstance(model, nn.Module):
            raise TypeError(f"model must be a nn.Module, but got {type(model)}.")
        self.model = model.to(self.__device)

        self.ipt = {'args':tuple(), 'kwargs':dict()} # TODO: self.ipt_infer()

        self.optree = OperationTree(self.model)

        self.tree_renderer = TreeRenderer(self.optree.root)
        self.table_renderer = TabularRenderer(self.optree.root)

        self.__measure_param = False
        self.__measure_cal = False
        self.__measure_mem = False
        self.ittp_warmup = 50
        self.ittp_benchmark_time = 100

    def __call__(self, *args, **kwargs) -> Any:
        self.ipt = {'args': args, 'kwargs': kwargs}
        self._ipt2device()
        return self.model(*self.ipt['args'], **self.ipt['kwargs'])
    
    @property
    def device(self) -> tc_device:
        return self.__device
    
    @device.setter
    def device(self, new_device:str) -> None:
        self.__device = tc_device(new_device)
        self.model.to(self.__device)
        if not self._is_ipt_empty():
            self._ipt2device()

    @property
    def tree_levels_args(self):
        return self.tree_renderer.tree_levels_args
    
    @tree_levels_args.setter
    def tree_levels_args(self, custom_args:Dict[Any, Dict[str, Any]]) -> None:
        self.tree_renderer.tree_levels_args = custom_args

    @property
    def tree_repeat_block_args(self):
        return self.tree_renderer.repeat_block_args
    
    @tree_repeat_block_args.setter
    def tree_repeat_block_args(self, custom_args:Dict[str, Any]) -> None:
        self.tree_renderer.repeat_block_args = custom_args

    @property
    def table_display_args(self):
        return self.table_renderer.tb_args

    @table_display_args.setter
    def table_display_args(self, custom_args:Dict[str, Any]) -> None:
        self.table_renderer.tb_args = custom_args

    @property
    def table_column_args(self):
        return self.table_renderer.col_args

    @table_column_args.setter
    def table_column_args(self, custom_args:Dict[str, Any]) -> None:
        self.table_renderer.col_args = custom_args

    @property
    def structure(self):
        fold_repeat = __cfg__.tree_fold_repeat
        
        is_rpbk_change = __cfg__.tree_repeat_block_args.is_change()
        
        is_level_change = __cfg__.tree_levels_args.is_change()
        
        if fold_repeat:
            cache_res = self.tree_renderer.render_fold_tree if not is_rpbk_change else None
        else:
            cache_res = self.tree_renderer.render_unfold_tree
        cache_res = cache_res if not is_level_change else None
        
        rendered_tree = self.tree_renderer() if cache_res is None else cache_res
        
        if is_rpbk_change:
            __cfg__.tree_repeat_block_args.mark_unchange()
        if is_level_change:
            __cfg__.tree_levels_args.mark_unchange()
        
        # render_perline(renderable=rendered_tree)
        return rendered_tree

    @property
    def param(self):
        if not self.__measure_param:
            list(map(lambda node: node.param.measure(), self.optree.all_nodes))
            self.__measure_param = True

        return self.optree.root.param
    
    @property
    def cal(self):
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
    def mem(self):
        if not self.__measure_mem:
            if self._is_ipt_empty():
                raise RuntimeError("Input unknown! You should perform at least one feed-forward inference before measuring the memory cost!") 

            hook_ls = [node.mem.measure() for node in self.optree.all_nodes]

            # feed forwad
            self._ipt2device()
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove() if x is not None else None, hook_ls))

            self.__measure_mem = True

        return self.optree.root.mem

    @property
    def ittp(self):
        if self._is_ipt_empty():
            raise RuntimeError("Input unknown! You should perform at least one feed-forward inference before measuring the inference time or throughput!") 

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

        return self.optree.root.ittp

    @property
    def model_info(self) -> "rich.text.Text": # noqa # type: ignore
        forward_args:Tuple[str] = tuple(signature(self.model.forward).parameters.keys())
        ipt_dict = {forward_args[args_idx]: anony_ipt for args_idx, anony_ipt in enumerate(self.ipt['args'])}
        ipt_dict.update(self.ipt['kwargs'])
        ipt_repr = [f"{args_name} = {data_repr(args_val)}" for args_name, args_val in ipt_dict.items()]
        ipt_repr = ',\n'.join(ipt_repr) 

        infos = '\n'.join([
            f"• [b]Model    :[/b] {self.optree.root.name}",
            f"• [b]Device   :[/b] {self.device}",
            f"• [b]Signature:[/b] forward(self, {', '.join(forward_args)})",
            f"• [b]Input    :[/b] \n{indent_str(ipt_repr, indent=3, guideline=False)}"
        ])
        
        console = get_console()
        return console.render_str(infos)

    @property
    def subnodes(self) -> List[str]:
        return [f"({node.node_id}) {node.name}" for node in self.optree.all_nodes]

    def rebase(self, node_id:str) -> "Meter":
        id_generator = ( (node_idx, node.node_id) for node_idx, node in enumerate(self.optree.all_nodes) )

        for idx, valid_id in id_generator:
            if node_id == valid_id:
                new_base = self.optree.all_nodes[idx]
                return self.__class__(new_base.operation, device=self.device)
        else:
            raise ValueError(f"Invalid node_id: {node_id}. Use `Meter(your_model).subnodes` to check valid ones.")

    def stat_info(self, stat_name:str):
        stat = getattr(self, stat_name)

        infos:List[str] = [f"• [b]Statistics:[/b] {stat_name}"]
        if stat_name == 'ittp':
            infos.append(f"• [b]Benchmark Times:[/b] {self.ittp_benchmark_time}")
        infos.extend([
            f"• [b]{k}:[/b] {v}" for k, v in stat.crucial_data.items()
        ])
                    
        infos = '\n'.join(infos)
        
        console = get_console()
        return console.render_str(infos)

    def overview(self, *order:Tuple[str]) -> Columns:
        """Overview of all statistics"""
        
        order = order or self.optree.root.statistics
        
        invalid_stat = tuple(filter(lambda x: x not in self.optree.root.statistics, order))
        if len(invalid_stat) > 0:
            raise AttributeError(f"Invalid statistics: {invalid_stat}")
        
        container = Columns(expand=True, align='center')
        format_cell = partial(Panel, safe_box=True, expand=False, highlight=True, box=HORIZONTALS)
        
        container.add_renderable(format_cell(self.model_info, title='[b]Model INFO[/]', border_style='orange1'))
        container.renderables.extend([format_cell(self.stat_info(stat_name), 
                                                  title=f"[b]{stat_name.capitalize()} INFO[/]",
                                                  border_style='cyan') 
                                      for stat_name in order])
        
        return container

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

        TREE_TABLE_GAP = __cfg__.combine.horizon_gap # the horizontal gap between tree and table
        
        tb, data = self.table_renderer(stat=getattr(self,stat_name), **tb_kwargs)
        
        if not show:
            return tb, data
        
        tree = None if no_tree else self.structure
        
        console = get_console()
        tree_width = console.measure(tree).maximum if tree is not None else 0
        desirable_tb_width = console.measure(tb).maximum
        actual_tb_width = min(desirable_tb_width, console.width - tree_width - TREE_TABLE_GAP)
        
        if actual_tb_width <= 5: # 5 is the minimum width of table
            raise ValueError("The width of the terminal is too small, try to maximize the window or " + \
                             "set a smaller `horizon_gap` value in your config and try again.")
        
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
            tree_height = len(console.render_lines(tree))
        
        temp_options = console.options.update_width(actual_tb_width) 
        tb_height = len(console.render_lines(tb, options=temp_options))
        main_content_height = max(tree_height, tb_height)
        main_content_width = tree_width + actual_tb_width + (0 if no_tree else TREE_TABLE_GAP)

        # get footer content
        footer = Columns(title=Rule('[gray54]s u m m a r y[/]', characters='-', style='gray54'),
                         padding=(1,1),
                         equal=True, 
                         expand=True)
        
        model_info = self.model_info
        stat_info = self.stat_info(stat_name=stat_name)
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

        render_perline(renderable=canvas, console=console)

        console.width = origin_width
        console.height = origin_height
        
        return tb, data

    def _is_ipt_empty(self) -> bool:
        return not self.ipt['args'] and not self.ipt['kwargs']
        
    def _ipt2device(self) -> None:
        if self._is_ipt_empty():
            raise ValueError("No input data provided.")

        devices = set(arg.device for arg in self.ipt['args'] if isinstance(arg, Tensor))
        devices.update(kwargs.device for kwargs in self.ipt['kwargs'].values() if isinstance(kwargs, Tensor))

        if len(devices) == 1 and next(iter(devices)) == self.device:
            return

        self.ipt = {
            'args': tuple(x.to(self.device) if isinstance(x, Tensor) else x 
                          for x in self.ipt['args']),
            'kwargs': {k: (v.to(self.device) if isinstance(v, Tensor) else v) 
                       for k, v in self.ipt['kwargs'].items()}
        }

    def __repr__(self) -> str:
        return f"Meter(model={self.optree}, device={self.device})"