from __future__ import annotations
from typing import TYPE_CHECKING

import os
import warnings
from threading import Lock
from enum import Enum, unique
from types import SimpleNamespace

import yaml
from rich import box

from torchmeter.utils import indent_str

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    from typing import Any, Dict, Sequence, Union, List
    from typing import Callable, Optional

    CFG_CONTENT_TYPE: TypeAlias = Union[
        int, float, str, bool, None,
        Sequence["CFG_CONTENT_TYPE"],
        Dict[str, "CFG_CONTENT_TYPE"]
    ]

__all__ = ["get_config", "Config"]

DEFAULT_FIELDS = ['render_interval',
                  'tree_fold_repeat', 'tree_repeat_block_args', 'tree_levels_args', 
                  'table_column_args','table_display_args', 
                  'combine']
DEFAULT_CFG = """\
render_interval: 0.15

tree_fold_repeat: True

tree_repeat_block_args:
    title: '[i]Repeat [[b]<repeat_time>[/b]] Times[/]'
    title_align: center
    subtitle: null
    subtitle_align: center
    
    style: dark_goldenrod
    highlight: True
    
    box: HEAVY_EDGE
    border_style: dim
    
    width: null
    height: null
    padding: 
        - 0
        - 1
    expand: False
        
tree_levels_args:
    default:
        label: '[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]'
        
        style: tree
        guide_style: light_coral
        highlight: True
        
        hide_root: False
        expanded: True
      
    '0': 
        label: '[b light_coral]<name>[/]'
        guide_style: light_coral
          
table_column_args:
    style: none
    
    justify: center
    vertical: middle
    
    overflow: fold
    no_wrap: False
        
table_display_args:
    style: spring_green4
    highlight: True
    
    width: null
    min_width: null
    expand: False
    padding: 
        - 0
        - 1
    collapse_padding: False
    pad_edge: True
    leading: 0
    
    title: null
    title_style: bold
    title_justify: center
    
    caption: null
    caption_style: null
    caption_justify: center
    
    show_header: True
    header_style: bold
    
    show_footer: False
    footer_style: italic
    
    show_lines: False
    row_styles: null
    
    show_edge: True
    box: ROUNDED
    safe_box: True
    border_style: null

combine:
    horizon_gap: 2
"""

@unique
class BOX(Enum):
    ASCII = box.ASCII
    ASCII2 = box.ASCII2
    ASCII_DOUBLE_HEAD = box.ASCII_DOUBLE_HEAD
    DOUBLE = box.DOUBLE
    DOUBLE_EDGE = box.DOUBLE_EDGE
    HEAVY = box.HEAVY
    HEAVY_EDGE = box.HEAVY_EDGE
    HEAVY_HEAD = box.HEAVY_HEAD
    HORIZONTALS = box.HORIZONTALS
    MARKDOWN = box.MARKDOWN
    MINIMAL = box.MINIMAL
    MINIMAL_DOUBLE_HEAD = box.MINIMAL_DOUBLE_HEAD
    MINIMAL_HEAVY_HEAD = box.MINIMAL_HEAVY_HEAD
    ROUNDED = box.ROUNDED
    SIMPLE = box.SIMPLE
    SIMPLE_HEAD = box.SIMPLE_HEAD
    SIMPLE_HEAVY = box.SIMPLE_HEAVY
    SQUARE = box.SQUARE
    SQUARE_DOUBLE_HEAD = box.SQUARE_DOUBLE_HEAD

# all the keys should be str, while all the value should be enum
# int each value, all the member's name should not be the same with its value's repr
UNSAFE_KV = {
    'box': BOX
}

def list_to_callbacklist(ls: List[Any], 
                         callback_func: Callable[[], Any]=lambda: None) -> CallbackList:
    _list: List[Any] = []
    for item in ls:
        if isinstance(item, dict):
            _list.append(dict_to_namespace(item))
        elif isinstance(item, list):
            _list.append(list_to_callbacklist(item, callback_func=callback_func))
        else:
            _list.append(item)
    return CallbackList(_list, callback_func=callback_func)

def dict_to_namespace(d: Dict[str, Any]) -> FlagNameSpace:
    """
    Recursively converts a dictionary to a FlagNameSpace object.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Input must be a dictionary, but got {type(d)}")
    
    ns = FlagNameSpace()
    
    for k, v in d.items():
        # overwrite the value of unsafe key to get the unrepresent value
        if k in UNSAFE_KV:
            v = getattr(UNSAFE_KV[k], v).value

        if isinstance(v, dict):
            setattr(ns, k, dict_to_namespace(v))
            
        elif isinstance(v, list):
            setattr(ns, k, list_to_callbacklist(v, callback_func=ns.mark_change))
        
        elif isinstance(v, set):
            setattr(ns, k, CallbackSet(v, callback_func=ns.mark_change))
            
        else:
            if not isinstance(k, str):
                raise TypeError(f"Attribute name must be a string, but got `{type(k).__name__}`")
            
            setattr(ns, k, v)
            
    return ns

def namespace_to_dict(ns, safe_resolve=False) -> Dict[str, CFG_CONTENT_TYPE]:
    """
    Recursively converts a FlagNameSpace object to a dictionary.
    """
    if not isinstance(ns, SimpleNamespace):
        raise TypeError(f"Input must be an instance of SimpleNamespace, but got {type(ns)}")

    d:Dict[str, CFG_CONTENT_TYPE] = {}
    for k, v in ns.data_dict.items():
        # transform the unrepresent value to its name defined in corresponding Enum
        if k in UNSAFE_KV and safe_resolve:
            v = UNSAFE_KV[k](v).name

        if isinstance(v, SimpleNamespace):
            d[k] = namespace_to_dict(v, safe_resolve=safe_resolve)
            
        elif isinstance(v, list):
            _list: List[CFG_CONTENT_TYPE] = []
            for item in v:
                if isinstance(item, SimpleNamespace):
                    _list.append(namespace_to_dict(item, safe_resolve=safe_resolve))
                else:
                    _list.append(item)
            d[k] = _list
            
        else:
            d[k] = v
            
    return d

def get_config(config_file:Optional[str]=None) -> Config:
    cfg_file = os.environ.get('TORCHMETER_CONFIG', config_file)
    cfg = Config() # always exist an instance cause display.py and core.py depend on it
    cfg.config_file = cfg_file
    return cfg

class CallbackList(list):
    def __init__(self, *args, callback_func=lambda:None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self._callback_func = callback_func
        self._register_callback("append", "extend", "insert",
                                "pop", "remove", "clear",
                                "reverse", "sort",
                                "__setitem__", "__delitem__",
                                "__iadd__", "__imul__")
    
    def _register_callback(self, *methods) -> None:
        for method_name in methods:
            orig_method = getattr(self.__class__, method_name)
            def wrapped_method(*args, _method=orig_method, **kwargs):
                result = _method(*args, **kwargs)
                self._callback_func()
                return result
            setattr(self.__class__, method_name, wrapped_method)  

class CallbackSet(set):
    def __init__(self, *args, callback_func=lambda:None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._callback_func = callback_func
        self._register_callback("add", "update", "difference_update",
                                "intersection_update", "symmetric_difference_update",
                                "discard", "pop", "remove", "clear",
                                "__isub__", "__iand__",
                                "__ixor__", "__ior__")
    
    def _register_callback(self, *methods):
        for method_name in methods:
            orig_method = getattr(self.__class__, method_name)
            def wrapped_method(*args, _method=orig_method, **kwargs):
                result = _method(*args, **kwargs)
                self._callback_func()
                return result
            setattr(self.__class__, method_name, wrapped_method) 

class FlagNameSpace(SimpleNamespace):
    
    __flag_key = '__FLAG'
    
    def __init__(self, **kwargs) -> None:
        list(map(lambda x: setattr(self, x, kwargs[x]), kwargs))        
        self.mark_unchange()
            
    def __setattr__(self, key: str, value: Any) -> None:                
        if key in ("__flag_key", self.__flag_key):
            raise AttributeError(f"`{key}` is preserved for internal use, " + \
                                 "you should never try to set it to a new value.")
        
        if isinstance(value, dict):
            value = dict_to_namespace(value)
        elif isinstance(value, list):
            value = list_to_callbacklist(value, callback_func=self.mark_change)
        elif isinstance(value, set):
            value = CallbackSet(value, callback_func=self.mark_change)
        
        super().__setattr__(key, value)
        
        self.mark_change()
    
    def __delattr__(self, key):
        if key in ("__flag_key", self.__flag_key):
            raise AttributeError(f"`{key}` is preserved for internal use, " + \
                                 "you should never try to delete it.")
                    
        super().__delattr__(key)
        
        self.mark_change()
    
    @property
    def data_dict(self):
        full_dict = self.__dict__.copy()
        del full_dict[self.__flag_key]
        return full_dict
    
    def is_change(self) -> bool:
        res = getattr(self, self.__flag_key) or \
              any(args.is_change() for args in self.__dict__.values() 
                    if isinstance(args, self.__class__))
        self.__dict__[self.__flag_key] = res
        return res
    
    def mark_change(self) -> None:
        self.__dict__[self.__flag_key] = True
    
    def mark_unchange(self) -> None:
        self.__dict__[self.__flag_key] = False
        list(map(lambda x: x.mark_unchange() if isinstance(x, self.__class__) else None, 
                 self.__dict__.values()))        
        
class ConfigMeta(type):
    """To achieve sigleton pattern"""
    
    __instances = None
    __thread_lock = Lock()

    def __call__(cls) -> Config:
        with cls.__thread_lock:
            if cls.__instances is None:
                instance = super().__call__()
                cls.__instances = instance
        return cls.__instances

class Config(metaclass=ConfigMeta):
    
    """You can only read or write the predefined fields in the instance"""
    
    render_interval: float
    tree_fold_repeat: bool
    tree_repeat_block_args: FlagNameSpace
    tree_levels_args: FlagNameSpace
    table_column_args: FlagNameSpace
    table_display_args: FlagNameSpace
    combine: FlagNameSpace

    __slots__ = DEFAULT_FIELDS + ['__cfg_file']
    
    def __init__(self) -> None:
        """Load default settings by default"""
        self.__cfg_file:Optional[str] = None
        self.__load()
            
    @property
    def config_file(self) -> Optional[str]:
        return self.__cfg_file
    
    @config_file.setter
    def config_file(self, file_path:Optional[str]=None) -> None:
        if file_path is not None and not isinstance(file_path, str):
            raise TypeError("You must pass in a string or None to change config or use the default config, " + \
                            f"but got {type(file_path)}.")
                
        if file_path:
            file_path = os.path.abspath(file_path)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Config file {file_path} does not exist.")
            if not file_path.endswith('.yaml'):
                raise ValueError(f"Config file must be a yaml file, but got {file_path}")
        
        self.__cfg_file = file_path
        self.__load()
        self.check_integrity()
            
    def __load(self) -> None:
        if self.config_file is None:
            raw_data = yaml.safe_load(DEFAULT_CFG)
        else:
            with open(self.config_file, 'r') as f:
                raw_data = yaml.safe_load(f)
        
        ns:FlagNameSpace = dict_to_namespace(raw_data)
        for field in ns.__dict__.keys():
            if field.startswith('__FLAG'):
                continue
            setattr(self, field, getattr(ns, field))          

    def restore(self) -> None:
        self.__load()
        self.check_integrity()

    def check_integrity(self) -> None:
        # no need to check integrity when loading default settings
        if self.config_file is None:
            return None
        
        with open(self.config_file, 'r') as f:
            custom_cfg = yaml.safe_load(f)
        
        for field in DEFAULT_FIELDS:
            if field not in custom_cfg:
                warnings.warn(message=f"Config file {self.config_file} does not contain '{field}' field, " + \
                                      "using default settings instead.",
                              category=UserWarning)
    
    def asdict(self, safe_resolve=False) -> Dict[str, CFG_CONTENT_TYPE]:
        d:Dict[str, CFG_CONTENT_TYPE] = {}
        for field in DEFAULT_FIELDS:
            field_val = getattr(self, field)
            if isinstance(field_val, SimpleNamespace):
                d[field] = namespace_to_dict(field_val, safe_resolve=safe_resolve)
            elif isinstance(field_val, list):
                d[field] = [namespace_to_dict(v, safe_resolve=safe_resolve) if isinstance(v, SimpleNamespace) else v 
                            for v in field_val]
            elif isinstance(field_val, dict):
                d[field] = {k:namespace_to_dict(v, safe_resolve=safe_resolve) if isinstance(v, SimpleNamespace) else v 
                            for k,v in field_val.items()}
            else:
                d[field] = field_val
        return d
    
    def dump(self, save_path:str) -> None:
        d = self.asdict(safe_resolve=True)

        with open(save_path, 'w') as f:
            yaml.safe_dump(d, f, 
                           indent=2, sort_keys=False,
                           encoding='utf-8', allow_unicode=True)        

    def __delattr__(self, name: str) -> None:
        # every attribute of Config object is important and should be there
        raise RuntimeError("You cannot delete attributes from Config object.")

    def __repr__(self) -> str:
        d = self.asdict(safe_resolve=True)

        def simple_data_repr(val:Any) -> str: 
            val_repr = []         
            
            if isinstance(val, dict):
                val_repr.append("dict{")
                val_repr.extend([f"{k} = {simple_data_repr(v)}" for k,v in val.items()])
                # val_repr[-1] += "}"
                val_repr.append("}")
            
            elif isinstance(val, (tuple, list, set)):
                val_repr.append(f"{type(val).__name__}(")
                val_repr.extend([f"- {simple_data_repr(v)}" for v in val])
                # val_repr[-1] += ")"
                val_repr.append(")")
            
            else:
                return f"{val} | <{type(val).__name__}>"

            return indent_str(val_repr, indent=4, process_first=False)
        
        s = '• Config file: ' + (self.config_file if self.config_file else 'None(default setting below)') + "\n"*2
        for field_name, field_vals in d.items():              
            s += f"• {field_name}: " + simple_data_repr(field_vals) + "\n"*2
        return s

if __name__ == '__main__':
    default_cfg = Config()
    print(default_cfg)
    cfg1 = Config()
    cfg2 = Config()
    if id(cfg1) == id(cfg2):
        print('Singleton Pattern Success.')