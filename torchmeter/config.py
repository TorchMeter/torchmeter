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

    from typing import Any, Dict, Optional, Sequence, Union, List

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
    no_warp: False
        
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

UNSAFE_KV = {
    'box': BOX
}


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
            _list = []
            for item in v:
                if isinstance(item, dict):
                    _list.append(dict_to_namespace(item))
                else:
                    _list.append(item)
            setattr(ns, k, _list)
            
        else:
            if k.startswith("__FLAG"):
                warnings.warn(f"Key {k} is not a valid level name and the settings will be ignored.")
                continue
            setattr(ns, k, v)
            
    return ns

def namespace_to_dict(ns, safe_resolve=False) -> Dict[str, CFG_CONTENT_TYPE]:
    """
    Recursively converts a FlagNameSpace object to a dictionary.
    """
    if not isinstance(ns, SimpleNamespace):
        raise TypeError(f"Input must be an instance of SimpleNamespace, but got {type(ns)}")

    d:Dict[str, CFG_CONTENT_TYPE] = {}
    for k, v in ns.__dict__.items():
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
            
        elif not k.startswith('__FLAG'):
            d[k] = v
            
    return d

def get_config(config_file:Optional[str]=None) -> Config:
    cfg_file = os.environ.get('TORCHMETER_CONFIG', config_file)
    cfg = Config() # always exist an instance cause display.py and core.py depend on it
    cfg.config_file = cfg_file
    return cfg

class FlagNameSpace(SimpleNamespace):
    
    __flag_key = '__FLAG'
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        
        cnt = 1
        while self.__flag_key in kwargs:
            self.__flag_key += str(cnt)
            cnt += 1
        
        self.mark_unchange()
            
    def __setattr__(self, key: str, value: Any) -> None:
        if key == self.__flag_key:
            raise AttributeError(f"`{key}` is preserved for internal use, could never be changed.")
        super().__setattr__(key, value)
        self.mark_change()
    
    def __delattr__(self, key):
        if key == self.__flag_key:
            raise AttributeError(f"`{key}` is preserved for internal use, could never be deleted.")
        super().__delattr__(key)
        self.mark_change()
    
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
        default_cfg = yaml.safe_load(DEFAULT_CFG)
        for field in DEFAULT_FIELDS:
            if not hasattr(self, field):
                warnings.warn(message=f"Config file {self.config_file} does not contain '{field}' key, \
                                        using default config instead.")
                ns = dict_to_namespace({field:default_cfg[field]})
                setattr(self, field, getattr(ns, field))
    
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
    
    def __repr__(self) -> str:
        d = self.asdict(safe_resolve=True)

        s = '• Config file: ' + (self.config_file if self.config_file else 'None(default setting below)') + '\n'
        for field_name, field_vals in d.items():
            not_container = False
            field_vals_repr = [f"\n• {field_name}: "]
            
            if isinstance(field_vals, dict):
                field_vals_repr.extend([f"{k} = {v} " for k,v in field_vals.items()])
            elif isinstance(field_vals, list):
                field_vals_repr.extend([f"- {v}" for v in field_vals])
            else:
                not_container = True
                field_vals_repr.append(str(field_vals))
            
            # concat field name and field value if it is not a container
            if len(field_vals_repr) == 2 and not_container:
                field_vals_repr = [''.join(field_vals_repr)]
                
            s += indent_str(field_vals_repr, indent=4, process_first=False) + '\n'
        return s

if __name__ == '__main__':
    default_cfg = Config()
    print(default_cfg)
    cfg1 = Config()
    cfg2 = Config()
    if id(cfg1) == id(cfg2):
        print('Singleton Pattern Success.')