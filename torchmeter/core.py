from inspect import signature
from typing import Any, Dict, Tuple, Union

import torch
import torch.nn as nn
from tqdm import tqdm
from rich import get_console
from rich.rule import Rule
from rich.layout import Layout
from rich.columns import Columns

from torchmeter.engine import OperationTree
from torchmeter.display import TreeRenderer, TabularRenderer
from torchmeter.display import indent_str, data_repr, render_perline

class Meter:

    def __init__(self, 
                 model: Union[nn.Module, str],
                 device:str='cpu',
                 fold_repeat:bool=True,
                 render_time_sep:float=0.15,
                 verbose:bool=True):
        
        assert render_time_sep >= 0, f'`render_time_sep` must be a non-negative number, but got {render_time_sep}.'

        self.fold_repeat = fold_repeat
        self.render_time_sep = render_time_sep
        self.verbose = verbose
        self.__device = torch.device(device)
        self.__tree_levels_args = {
            '0':  {'label': '[b light_coral]<name>[/]', 
                   'guide_style':'light_coral'}
        }
        self.__tree_rpblk_args = { 
            'title': '[i]Repeat [[b]<repeat_time>[/b]] Times[/]',
            'title_align': 'center',
            'highlight': True,
            'style': 'dark_goldenrod',
            'border_style': 'dim',
            'expand': False
        }
        self.tb_col_args = {
            'justify': 'center',
            'vertical': 'middle',
            'overflow': 'fold'
        }
        self.tb_args = {
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
            'safe_box': True,

            'expand': False,
            'leading': 0,
        }

        if isinstance(model, str):
            self.model = torch.load(model, map_location=self.__device)
        elif isinstance(model, nn.Module):
            self.model = model.to(self.__device)
        else:
            raise TypeError(f'model must be a torch.nn.Module or a path to a model, but got {type(model)}')

        self.ipt = {'args':tuple(), 'kwargs':dict()} # TODO: self.ipt_infer()

        self.optree = OperationTree(self.model, verbose=verbose)
        self.optree.root.fold_repeat = fold_repeat

        self.tree_renderer = TreeRenderer(self.optree.root)
        self.tb_renderer = TabularRenderer(self.optree.root)

        self.__measure_param = False
        self.__measure_cal = False
        self.__measure_mem = False
        self.ittp_warmup = 50
        self.ittp_benchmark_time = 100

    def __call__(self, *args, **kwargs):
        self.ipt = {'args': tuple(x.to(self.device) for x in args if isinstance(x, torch.Tensor)), 
                    'kwargs': {k:v.to(self.device) for k,v in kwargs.items() if isinstance(v, torch.Tensor)}}
        return self.model(*self.ipt['args'], **self.ipt['kwargs'])
    
    @property
    def device(self):
        return self.__device
    
    @device.setter
    def device(self, new_device:str):
        self.__device = torch.device(new_device)
        self.model.to(self.__device)
        self.ipt = {'args': tuple(x.to(self.device) for x in self.ipt['args'] if isinstance(x, torch.Tensor)), 
                    'kwargs': {k:v.to(self.device) for k,v in self.ipt['kwargs'].items() if isinstance(v, torch.Tensor)}}

    @property
    def tree_levels_args(self):
        return self.__tree_levels_args
    
    @tree_levels_args.setter
    def tree_levels_args(self, custom_args:Dict[str, Any]) -> None:
        self.__tree_levels_args = custom_args
        self.tree_renderer.render_fold_tree = None
        self.tree_renderer.render_unfold_tree = None

    @property
    def tree_repeat_block_args(self):
        return self.__tree_rpblk_args
    
    @tree_repeat_block_args.setter
    def tree_repeat_block_args(self, custom_args:Dict[str, Any]) -> None:
        self.__tree_rpblk_args = custom_args
        self.tree_renderer.render_fold_tree = None
        self.tree_renderer.render_unfold_tree = None

    @property
    def structure(self):
        rendered_tree = self.tree_renderer.render_fold_tree if self.fold_repeat else self.tree_renderer.render_unfold_tree
        
        if rendered_tree is None:
            rendered_tree = self.tree_renderer(fold_repeat=self.fold_repeat,
                                               level_args=self.tree_levels_args,
                                               repeat_block_args=self.tree_repeat_block_args)
        
        # render_perline(renderable=rendered_tree)
        return rendered_tree

    @property
    def param(self):
        if not self.__measure_param:
            for node in self.optree.all_nodes:
                if node.is_leaf:
                    node.param.measure()

            self.__measure_param = True

        return self.optree.root.param
    
    @property
    def cal(self):
        if not self.__measure_cal:
            if len(self.ipt['args']) + len(self.ipt['kwargs']) == 0:
                raise ValueError("Input unknown! You should perform at least one feed-forward inference before measuring calculation!") 

            hook_ls = [node.cal.measure() for node in self.optree.all_nodes if node.is_leaf]

            # feed forwad
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove(), hook_ls)) 

            self.__measure_cal = True
        
        return self.optree.root.cal

    @property
    def mem(self):
        if not self.__measure_mem:
            if len(self.ipt['args']) + len(self.ipt['kwargs']) == 0:
                raise ValueError("Input unknown! You should perform at least one feed-forward inference before measuring the memory cost!") 

            hook_ls = [node.mem.measure() for node in self.optree.all_nodes if node.is_leaf]

            # feed forwad
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove(), hook_ls))

            self.__measure_mem = True

        return self.optree.root.mem

    @property
    def ittp(self):
        if len(self.ipt['args']) + len(self.ipt['kwargs']) == 0:
            raise ValueError("Input unknown! You should perform at least one feed-forward inference before measuring the inference time or throughput!") 

        for i in tqdm(range(self.ittp_warmup), desc='Warming Up'):
            self.model(*self.ipt['args'], **self.ipt['kwargs'])

        pb = tqdm(total=self.ittp_benchmark_time*len(self.optree.all_nodes), 
                  desc='Benchmark Inference Time & Throughput', 
                  unit='time')
        hook_ls = [node.ittp.measure(device=self.device, 
                                     repeat=self.ittp_benchmark_time,
                                     global_process=pb) 
                    for node in self.optree.all_nodes]

        # feed forwad
        self.model(*self.ipt['args'], **self.ipt['kwargs']) 

        # remove hooks after measurement
        list(map(lambda x:x.remove(), hook_ls))

        return self.optree.root.ittp
        
    def restore_settings(self):
        self.tree_levels_args = {
            '0':  {'label': '[b light_coral]<name>[/]', # default display setting for root node
                   'guide_style':'light_coral'}
        }

        self.tree_repeat_block_args = { 
            'title': '[i]Repeat [[b]<repeat_time>[/b]] Times[/]',
            'title_align': 'center',
            'highlight': True,
            'style': 'dark_goldenrod',
            'border_style': 'dim',
            'expand': False
        }

        self.tb_col_args = {
            'justify': 'center',
            'vertical': 'middle',
            'overflow': 'fold'
        }

        self.tb_args = {
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
            'safe_box': True,

            'expand': False,
            'leading': 0,
        }

    def profile(self, 
                stat, 
                show=True, no_tree=False, 
                force_preset=False,
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

        TREE_TABLE_GAP = 2 # the horizontal gap between tree and table
        
        tb_kwargs['table_settings'] = tb_kwargs.get('table_settings', self.tb_args)
        tb_kwargs['column_settings'] = tb_kwargs.get('column_settings', self.tb_col_args)

        tb, data = self.tb_renderer(stat_name=stat.name, **tb_kwargs)
        
        if not show:
            return tb, data
        
        tree = None if no_tree else self.structure
        
        console = get_console()
        tree_width = console.measure(tree).maximum if tree is not None else 0
        desirable_tb_width = console.measure(tb).maximum
        actual_tb_width = min(desirable_tb_width, console.width - tree_width - TREE_TABLE_GAP)
        
        if actual_tb_width <= 5: # 5 is the minimum width of table
            raise ValueError("The width of the terminal is too small, try to maximize the window and try again.")
        
        # when some cells in the table is overflown, we need to show a line between rows
        if actual_tb_width < desirable_tb_width and not force_preset:
            tb.show_lines = True 
        
        # get main content(i.e. tree & statistics table)
        if no_tree:
            main_content = tb
            main_content_height = len(console.render_lines(tb))
            main_content_width = actual_tb_width
        else:
            main_content = Layout()
            main_content.split_row(Layout(tree, name='left', size=tree_width + TREE_TABLE_GAP),
                                   Layout(tb, name='right', size=actual_tb_width))
            
            temp_options = console.options.update_width(actual_tb_width) 
            tree_height = len(console.render_lines(tree))
            tb_height = len(console.render_lines(tb, options=temp_options))
            main_content_height = max(tree_height, tb_height)
            main_content_width = tree_width + TREE_TABLE_GAP + actual_tb_width

        # get footer content
        footer = Columns(title=Rule('[gray54]s u m m a r y[/]', characters='-', style='gray54'),
                         equal=True, 
                         expand=True)

        forward_args:Tuple[str] = tuple(signature(self.model.forward).parameters.keys())
        ipt_dict = {forward_args[args_idx]: anony_ipt for args_idx, anony_ipt in enumerate(self.ipt['args'])}
        ipt_dict.update(self.ipt['kwargs'])
        ipt_repr = [f"{args_name} = {data_repr(args_val)}" for args_name, args_val in ipt_dict.items()]
        ipt_repr = ',\n'.join(ipt_repr) 

        basic_info = '\n'.join([
            '[dim]' + \
            f'• [b]Model    :[/b] {self.optree.root.name}',
            f'• [b]Device   :[/b] {self.device}',
            f'• [b]Signature:[/b] forward(self, {','.join(forward_args)})',
            f'• [b]Input    :[/b] \n{indent_str(ipt_repr, len('• Inp'), guideline=False)}' + \
            '[/]'
        ])

        stat_info = ['[dim]' + f'• [b]Statistics:[/b] {stat.name}']
        if stat.name == 'ittp':
            stat_info.append(f'• [b]Benchmark Times:[/b] {self.ittp_benchmark_time}')
        stat_info.extend([
            f'• [b]{k}:[/b] {v}' for k, v in stat.crucial_info.items()
        ])
        stat_info[-1] += '[/]'
        stat_info = '\n'.join(stat_info)
        
        footer.add_renderable(basic_info)
        footer.add_renderable(stat_info)

        temp_options = console.options.update_width(main_content_width)
        footer_height = len(console.render_lines(footer, options=temp_options))
        
        # render profile
        canvas = Layout()
        canvas.split_column(Layout(main_content, name='top', size=main_content_height),
                            Layout(footer, name='down', size=footer_height))
        
        console.width = main_content_width
        console.height = main_content_height + footer_height
        if self.render_time_sep:
            render_perline(renderable=canvas, 
                           console=console,
                           time_sep=self.render_time_sep)
        else:
            console.print(canvas)

        return tb, data

if __name__ == '__main__':
    from rich import print
    from torchvision import models

    model = models.resnet18()
    
    metered_model = Meter(model, device='cpu')
    metered_model(torch.randn(1,3,224,224))
    
    # print(metered_model.structure)
    print(metered_model.mem)
    metered_model.profile(metered_model.mem,
                          show=True, no_tree=True,
                          raw_data=False,)
                        #   newcol_name='Percentage',
                        #   newcol_func=lambda col_dict,all_num=metered_model.mem.TotalCost.val: f'{col_dict["Total"]*100/all_num:.3f} %',
                        #   newcol_dependcol=['Total'],
                        #   newcol_type=str,
                        #   newcol_idx=0,
                        #   save_to='.',
                        #   save_format='xlsx')