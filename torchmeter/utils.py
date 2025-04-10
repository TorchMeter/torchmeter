from __future__ import annotations
from typing import TYPE_CHECKING

import os
from time import perf_counter
from inspect import signature
from functools import partial

from rich.text import Text
from rich.status import Status

if TYPE_CHECKING:
    from typing import Any, List, Tuple
    from typing import Union, Optional, Callable, Iterable

    from polars import PolarsDataType

__all__ = ["dfs_task", "data_repr", "Timer"]

def resolve_savepath(origin_path:str, 
                     target_ext:str,
                     default_filename:str='Data') -> Tuple[str, str]:
    origin_path = os.path.abspath(origin_path)
    dir, file = os.path.split(origin_path)
    
    # origin_path is a file path
    if '.' in file: 
        os.makedirs(dir, exist_ok=True)
        save_dir = dir
        save_file = os.path.join(dir, os.path.splitext(file)[0]+f".{target_ext}")
    
    # origin_path is a dir path
    else: 
        os.makedirs(origin_path, exist_ok=True)
        save_dir = origin_path
        save_file = os.path.join(origin_path, f"{default_filename}.{target_ext}")
    
    return save_dir, save_file

def hasargs(func:Callable, *required_args:str) -> None:
    if not required_args:
        return 
        
    missing_args = [arg for arg in required_args 
                        if arg not in signature(func).parameters]
    
    if missing_args:
        raise RuntimeError(f"Function `{func.__name__}()` is missing following required args: {missing_args}.")

def dfs_task(dfs_subject:Any,
             adj_func:Callable[[Any], Iterable],
             task_func:Callable[[Any, Any], Any],
             visited_signal_func:Callable[[Any], Any]=lambda x:id(x),
             *,
             visited:Optional[List]=None) -> Any: 
    hasargs(task_func, 'subject', 'pre_res')

    visited_signal = visited_signal_func(dfs_subject)
    
    visited = visited or []
    
    if visited_signal not in visited:
        visited.append(visited_signal)
        try:
            task_res = task_func(subject=dfs_subject)   # type: ignore
        except TypeError:
            # use empty list when no default value for `pre_res`
            task_res = task_func(subject=dfs_subject, pre_res=[])   # type: ignore
        
        for adj in adj_func(dfs_subject): 
            dfs_task(dfs_subject=adj,  
                     adj_func=adj_func,
                     task_func=partial(task_func, pre_res=task_res), # type: ignore
                     visited_signal_func=visited_signal_func, 
                     visited=visited)
    
    try:
        return task_res
    except UnboundLocalError: # revisit visited node
        return None

def indent_str(s:Union[str, Iterable[str]], 
               indent:int=4, 
               guideline:bool=True,
               process_first:bool=True) -> str:
    if isinstance(s, str):
        split_lines:List[str] = s.split("\n")
        
    elif hasattr(s, '__iter__'):
        split_lines = []
        for i in s:
            if not isinstance(i,str):
                raise TypeError("The input should be a string or an iterable object of strings, " + \
                                f"but got `{type(i).__name__}` when travering input.")
            split_lines.extend(i.split("\n"))
            
    else:
        raise TypeError("The input should be a string or a sequence of strings, " + \
                        f"but got `{type(s).__name__}`.")
    
    if not isinstance(indent, int):
        raise TypeError(f"The indent should be an integer, but got `{type(indent).__name__}`")
    indent = max(indent, 0)
        
    res = []
    guideline = not len(split_lines) == 1 and guideline
    
    if indent:
        for line in split_lines:
            indent_line = "│" if guideline else " " 
            indent_line += " "*(indent-1) + line
            res.append(indent_line)

        if not process_first:
            res[0] = res[0][indent:]

        if guideline:
            res[-1] = "└─"[:indent].ljust(indent) + res[-1][indent:]
    else:
        res = split_lines
    
    return '\n'.join(res)

def data_repr(val:Any) -> str:
    get_type = lambda val: type(val).__name__

    item_repr = lambda val_type, val: (f"[dim]Shape[/]([b green]{list(val.shape)}[/])" if hasattr(val, 'shape') else f"[b green]{val}[/]") + f" [dim]<{val_type}>[/]"

    val_type = get_type(val)
    if isinstance(val, (list, tuple, set, dict)) and len(val) > 0:
        if isinstance(val, dict):
            inner_repr_parts = [(item_repr(get_type(k),k), data_repr(v)) for k, v in val.items()]
            inner_repr:List[str] = [indent_str(f"{record[0]}: {record[1]}", 
                                               indent=2+Text.from_markup(record[0]).cell_len, 
                                               guideline=False, process_first=False) 
                                    for record in inner_repr_parts]
        else:
            inner_repr = [data_repr(i) for i in val]
        
        res_repr = f"[dim]{val_type}[/]("
        res_repr += ',\n'.join(inner_repr)
        res_repr += ')'

        return indent_str(res_repr, indent=len(f"{val_type}("), process_first=False)
    
    elif "function" in val_type and callable(val):
        return f"[b green]{val.__name__}[/] [dim]<function>[/]"
    
    elif hasattr(val, 'shape'):
        if any(not isinstance(i, int) for i in list(val.shape)):
            return f"[b green]obj[/] [dim]<{val.__class__.__module__}.{val_type}>[/]"
        return item_repr(val_type, val)
    
    elif val.__class__.__module__ != "builtins":
        return f"[b green]obj[/] [dim]<{val.__class__.__module__}.{val_type}>[/]"

    else:
        return item_repr(val_type, val)

def match_polars_type(ipt:Any, *, 
                      recheck:bool=False,
                      pre_res:Optional[PolarsDataType]=None)-> PolarsDataType:
        
    import numpy as np
    import polars as pl
    from polars.datatypes._parse import parse_into_dtype
    from polars.series.series import _resolve_temporal_dtype

    if not recheck and pre_res is not None:
        return pre_res

    try:
        pl_type = parse_into_dtype(type(ipt))
        if isinstance(ipt, (list, tuple)):
            # TODO: inner type awareness (following type priority) 
            inner_type = match_polars_type(ipt[0])
            return pl_type(inner_type) # type: ignore
            
        return pl_type
    
    except TypeError:
        if isinstance(ipt, dict):
            fields = {k:match_polars_type(v) for k,v in ipt.items()}
            return pl.Struct(fields=fields)
        
        elif isinstance(ipt, (np.datetime64, np.timedelta64)):
            pl_type = _resolve_temporal_dtype(None, np.dtype(ipt)) # type: ignore 
            return pl_type or pl.Object
        
        elif isinstance(ipt, (np.integer, np.floating)):
            return {
                np.int8: pl.Int8,
                np.int16: pl.Int16,
                np.int32: pl.Int32,
                np.int64: pl.Int64,
                np.uint8: pl.UInt8,
                np.uint16: pl.UInt16,
                np.uint32: pl.UInt32,
                np.uint64: pl.UInt64,
                np.float32: pl.Float32,
                np.float64: pl.Float64
            }[type(ipt)]
            
        elif isinstance(ipt, np.ndarray):
            return pl.Series(ipt).dtype
        
        else:
            # class instance
            return pl.Object

class Timer(Status):
    def __init__(self, task_desc:str, 
                 *args, **kwargs) -> None:
        super(Timer, self).__init__(status=task_desc, *args, **kwargs) # type: ignore
        self.task_desc = task_desc
    
    def __enter__(self):
        super().__enter__()
        self.__start_time = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = perf_counter() - self.__start_time
        super().__exit__(exc_type, exc_val, exc_tb)
        self.console.print(f"[b blue]Finish {self.task_desc} in [green]{elapsed_time:.4f}[/green] seconds[/]")