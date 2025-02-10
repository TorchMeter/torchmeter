from copy import deepcopy
from typing import Any, Optional, Tuple, List, Dict, Union, Callable

import torch
import torch.nn as nn
from rich.layout import Layout
from rich import print, get_console

from torchmeter.engine import OperationTree
from torchmeter.display import TreeRenderer, TabularRenderer, render_perline

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

        self.optree = OperationTree(self.model, verbose=verbose)
        self.optree.root.fold_repeat = fold_repeat

        self.tree_renderer = TreeRenderer(self.optree.root)
        self.tb_renderer = TabularRenderer(self.optree.root)

    def __call__(self, *args, **kwargs):
        return self.model(*args, **kwargs)
    
    @property
    def device(self):
        return self.__device
    
    @device.setter
    def device(self, new_device:str):
        self.__device = torch.device(new_device)
        self.model.to(self.__device)

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
        for node in self.optree.nonroot_nodes:
            if node.is_leaf:
                node.param.measure()
        return self.optree.root.param
    
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
                show=False, no_tree=False, 
                **tb_kwargs):
        """To render a tabular profile of the statistics
        
        Args:
            stat
            show
            no_tree
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

        tb, data = self.tb_renderer(stat_name=stat.name, 
                                    table_settings=tb_kwargs.get('table_settings', self.tb_args),
                                    column_settings=tb_kwargs.get('column_settings', self.tb_col_args))

        if no_tree:
            tree = None
            canvas = tb
        else:
            tree = self.structure

            console = get_console()
            tree_width = console.measure(tree).maximum
            tree_height = len(console.render_lines(tree))
            temp_options = console.options.update_width(console.width - tree_width - 2) # 2 is the gap between tree and table
            tb_height = len(console.render_lines(tb, options=temp_options))
            console.height = max(tree_height, tb_height)

            canvas = Layout()
            canvas.split_row(Layout(tree, name='left'),
                             Layout(tb, name='right'))

            if console.width <= tree_width:
                raise ValueError("The width of the terminal is too small, try to maximize the window and try again.")
            canvas['left'].size = tree_width + 2

        if show:
            if self.render_time_sep:
                render_perline(canvas, time_sep=self.render_time_sep)
            else:
                print(canvas)

        return tb, data

if __name__ == '__main__':
    from torchvision import models

    class TestNet(nn.Module):
        def __init__(self):
            super(TestNet, self).__init__()
            
            conv = nn.ModuleList([nn.Conv2d(3,30,3,stride=1) for _ in range(7)])
            self.conv = nn.Sequential(conv,deepcopy(conv))
            self.maxpool = nn.MaxPool2d(2)
            self.br1 = nn.ModuleList([nn.LayerNorm(30),
                                      nn.BatchNorm2d(30),
                                      nn.ModuleList([nn.Linear(2,10) for _ in range(3)]),
                                      nn.BatchNorm2d(30),
                                      nn.ModuleList([nn.Linear(2,10) for _ in range(3)]),
                                      nn.SELU()])
            self.blank1 = nn.Identity()
            self.br2 = nn.ModuleList([nn.LayerNorm(30),
                                      nn.BatchNorm2d(30),
                                      nn.ModuleList([nn.Linear(2,10) for _ in range(3)]),
                                      nn.BatchNorm2d(30),
                                      nn.ModuleList([nn.Linear(2,10) for _ in range(3)]),
                                      nn.SELU()])
            self.blank2 = nn.Identity()
            self.avgpool = nn.AvgPool2d(2)
            self.layer1 = nn.Sequential(
                nn.Conv2d(30,60,3,stride=1),
                nn.BatchNorm2d(60),
                nn.ReLU(),
                nn.Conv2d(60,30,1),
                nn.BatchNorm2d(30),
                nn.ReLU()
            )
            
            self.layer2 = deepcopy(self.layer1)
            self.layer3 = deepcopy(self.layer1)
            
            self.fc = nn.Linear(30,10)
        
        def forward(self,x):
            pass
    
    # model = TestNet()
    model = models.alexnet()
    
    metered_model = Meter(model, device='cpu')
    
    # print(metered_model.structure)
    # print(metered_model.param)
    metered_model.profile(metered_model.param,
                          show=True,
                          newcol_name='Percentage',
                          newcol_func=lambda col_dict,all_num=metered_model.param.total_num.val: f'{col_dict["Numeric_Num"]/all_num*100:.2f} %',
                          newcol_dependcol=['Numeric_Num'],
                          newcol_type=str,)
                        #   newcol_idx=0,
                        #   save_csv=r'C:\Users\Administrater\Desktop',
                        #   save_excel=r'C:\Users\Administrater\Desktop')