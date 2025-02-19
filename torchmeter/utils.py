import os
import sys
from time import perf_counter
from inspect import signature
from functools import partial
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple, Union

from rich.status import Status

def perfect_savepath(origin_path:str, 
                     target_ext:Optional[str],
                     default_filename:str='Data'):
    origin_path = os.path.abspath(origin_path)
    dir, file = os.path.split(origin_path)
    if '.' in file: # specify a file path
        os.makedirs(dir, exist_ok=True)
        save_dir = dir
        save_file = os.path.join(dir, os.path.splitext(file)[0]+f".{target_ext}")
    else: # specify a dir path
        os.makedirs(origin_path, exist_ok=True)
        save_dir = origin_path
        save_file = os.path.join(origin_path, f"{default_filename}.{target_ext}")
    
    return save_dir, save_file

def check_args(func:Callable, *required_args:Tuple[str]) -> List:
    """
    Check if the function `func` has all the required arguments.

    Args:
    ---
        - `func` (Callable): The function to be checked.
        - `required_args` (Tuple[str]): The names of required arguments.

    Returns:
    ---
        List: A list containing names of missing arguments.
    
    Example:
    ---
    ```python
    def test_func(a, bb, c_c, d9):
        pass

    check_args(test_func, 'a', 'bb', 'c_c', 'd9') 
    # >>> []

    check_args(test_func, 'A', 'e') 
    # >>> ['A', 'e']
    ```
    """
    if not required_args:
        return []
        
    missing_args = [arg for arg in required_args 
                        if arg not in signature(func).parameters]
    if missing_args:
        print(f"[bold red]Missing following args in function `{func.__name__}()`:[/]")
        for arg in missing_args:
            print(f"[red][-] [bold]`{arg}`[/]")
    
    return missing_args

def dfs_task(dfs_subject:Any,
             adj_func:Callable[[Any], Iterable],
             task_func:Callable[[Any, Any], Any],
             visited_signal_func:Callable[[Any], Any]=lambda x:x,
             *,
             visited:List=[]) -> Any: 
    """
    Perform Depth-First Search (DFS) traversal on `dfs_subject`, 
    and complete the specified task at the same time.

    The traversal is implemented by recursion.
    
    Args:
    ---
        - `dfs_subject` (Any): The subject to be traversed.\n\n
        
        - `adj_func` (Callable[[Any], Iterable]): Function to obtain an iterator for child objects of "dfs_subject".
                                                  The function should have one parameter, which is the object to be traversed.
                                                  And the function should return an iterator of child objects.
                                                  
        - `task_func` (Callable[[Any], Any]): Function to perform the task. 
                                              The function should have two specific parameters, one is `subject` used to receive the currently traversed object,
                                              and the other is `pre_res` used to receive the result of the previous level task.
                                              Finally, the function should return the result of the currently traversal task.
                                              
        - `visited_signal_func` (Callable[[Any], Any]): Function to obtain the signal used to identify whether this object is visited.
                                                        The function should have one parameter, which is the object to be traversed.
                                                        And the function should return a signal in any format.
                                                        Defaults to use the traversal object itself.
                                                        
        - `visited` (List, optional): A list to store the visited signals, it's used to avoid visiting a same object repeatly.
                                      Defaults to [].
    
    Returns:
    ---
        Any: The result of the first-level task. Given that each level's task result will be passed to next level,
             therefore you can use a container (such as list) to collect the result of each level's task,
             in this case, although the function returns the result of the first level's task, it has all levels' results in it.
    
    Example:
    ---
        ```python
        class BinaryTree:
            def __init__(self, value, left=None, right=None):
                self.value = value
                self.left = left
                self.right = right
        
        root = BinaryTree(1)
        l_child = BinaryTree(2)
        ll_child = BinaryTree(3)
        root.left = l_child
        l_child.left = ll_child
        
        def print_node(subject, pre_res=[]):
            print(subject.value)
            return pre_res + [subject.value]

        print('Print the left subtree:')
        dfs_res = dfs_task(dfs_subject=root, 
                        adj_func=lambda x:[x.left] if x.left else [],  # stop traversal when there is no left child
                        task_func=print_node, 
                        visited_signal_func=id, # use the addr as visited_signal
                        visited=[])
        # >>> 1
        # >>> 2
        # >>> 3
        
        print(dfs_res)
        # >>> [1, 2, 3]
        ```
    """
    
    missing_args = check_args(task_func, 'subject', 'pre_res')
    if missing_args:
        print(f"[bold red]Argument `task_func` of `{dfs_task.__name__}()` should be passed in a function with two parameters:")
        print('[bold red]1. [magenta]`subject`[/magenta]: the first argument, used to receive the currently traversed object[/]')
        print('[bold red]2. [magenta]`pre_res`[/magenta]: the second argument, used to receive the result of the previous level task[/]')
        sys.exit(1)
    del missing_args

    visited_signal = visited_signal_func(dfs_subject)
    
    if visited_signal not in visited:
        visited.append(visited_signal)
        task_res = task_func(subject=dfs_subject)
        
        for adj in adj_func(dfs_subject): 
            dfs_task(dfs_subject=adj, 
                     adj_func=adj_func,
                     task_func=partial(task_func, pre_res=task_res),
                     visited_signal_func=visited_signal_func, 
                     visited=visited)
    
    return task_res

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
            inner_repr:List[str] = [f"{item_repr(get_type(k),k)}: {data_repr(v)}" for k, v in val.items()]
        else:
            inner_repr:List[str] = [data_repr(i) for i in val]
        
        res_repr = f"[dim]{val_type}[/]("
        res_repr += ',\n'.join(inner_repr)
        res_repr += ')'

        return indent_str(res_repr, indent=len(f"{val_type}("), process_first=False)
    
    else:
        return item_repr(val_type, val)

class Timer(Status):
    def __init__(self, /, task_desc:str,
                 *args, **kwargs):
        super(Timer, self).__init__(status=task_desc, *args, **kwargs)
        self.task_desc = task_desc
    
    def __enter__(self):
        super().__enter__()
        self.__start_time = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ellapsed_time = perf_counter() - self.__start_time
        super().__exit__(exc_type, exc_val, exc_tb)
        self.console.print(f"[b blue]Finish {self.task_desc} in [green]{ellapsed_time:.4f}[/green] seconds[/]")