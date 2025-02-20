import os
import warnings
from threading import Lock
from typing import Optional
from enum import Enum, unique
from types import SimpleNamespace

import yaml
from rich import box

from torchmeter.utils import indent_str

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


def dict_to_namespace(d):
    """
    Recursively converts a dictionary to a FlagNameSpace object.
    """
    assert isinstance(d, dict), f"Input must be a dictionary, but got {type(d)}"
    
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

def namespace_to_dict(ns, safe_resolve=False):
    """
    Recursively converts a FlagNameSpace object to a dictionary.
    """
    assert isinstance(ns, SimpleNamespace), f"Input must be an instance of SimpleNamespace, but got {type(ns)}"

    d = {}
    for k, v in ns.__dict__.items():
        # transform the unrepresent value to its name defined in corresponding Enum
        if k in UNSAFE_KV and safe_resolve:
            v = UNSAFE_KV[k](v).name

        if isinstance(v, SimpleNamespace):
            d[k] = namespace_to_dict(v, safe_resolve=safe_resolve)
            
        elif isinstance(v, list):
            _list = []
            for item in v:
                if isinstance(item, SimpleNamespace):
                    _list.append(namespace_to_dict(item, safe_resolve=safe_resolve))
                else:
                    _list.append(item)
            d[k] = _list
            
        elif not k.startswith('__FLAG'):
            d[k] = v
            
    return d

def get_config():
    cfg_file = os.environ.get('TORCHMETER_CONFIG', None)
    return Config(config_file=cfg_file)

class FlagNameSpace(SimpleNamespace):
    
    __flag_key = '__FLAG'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        cnt = 1
        while self.__flag_key in kwargs:
            self.__flag_key += str(cnt)
            cnt += 1
        
        self.mark_unchange()
            
    def __setattr__(self, key, value):
        assert key != self.__flag_key, f"`{key}` is preserved for internal use, could never be changed."
        super().__setattr__(key, value)
        self.mark_change()
    
    def __delattr__(self, key):
        assert key != self.__flag_key, f"`{key}` is preserved for internal use, can not be deleted."
        super().__delattr__(key)
        self.mark_change()
    
    def is_change(self):
        res = getattr(self, self.__flag_key) or \
              any(args.is_change() for args in self.__dict__.values() 
                    if isinstance(args, self.__class__))
        self.__dict__[self.__flag_key] = res
        return res
    
    def mark_change(self):
        self.__dict__[self.__flag_key] = True
    
    def mark_unchange(self):
        self.__dict__[self.__flag_key] = False
        list(map(lambda x: x.mark_unchange() if isinstance(x, self.__class__) else None, 
                 self.__dict__.values()))        
        
class ConfigMeta(type):
    """To achieve sigleton pattern"""
    
    _instances = None
    _thread_lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._thread_lock:
            if cls._instances is None:
                instance = super().__call__(*args, **kwargs)
                cls._instances = instance
        return cls._instances

class Config(metaclass=ConfigMeta):
    
    """You can only read or write the predefined fields in the instance"""
    
    __slots__ = DEFAULT_FIELDS + ['__cfg_file']
    
    def __init__(self, config_file:Optional[str]=None):
        self.__cfg_file = None
        
        self.config_file = config_file
    
    @property
    def config_file(self):
        return self.__cfg_file
    
    @config_file.setter
    def config_file(self, config_file:Optional[str]=None):
        assert config_file is None or isinstance(config_file, str), \
                f"You must pass in a string or None to change config or use the default config, \
                  but got {type(config_file)}."
                
        if config_file:
            config_file = os.path.abspath(config_file)
            assert os.path.exists(config_file), f"Config file {config_file} does not exist."
        
        self.__cfg_file = config_file
        self.__load()
        self.check_integrity()
            
    def __load(self):
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

    def restore(self):
        self.__load()
        self.check_integrity()

    def check_integrity(self):
        default_cfg = yaml.safe_load(DEFAULT_CFG)
        for field in DEFAULT_FIELDS:
            if not hasattr(self, field):
                warnings.warn(message=f"Config file {self.config_file} does not contain '{field}' key, \
                                        using default config instead.")
                ns = dict_to_namespace({field:default_cfg[field]})
                setattr(self, field, getattr(ns, field))
    
    def asdict(self, safe_resolve=False):
        d = {}
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
    
    def dump(self, save_path:str):
        d = self.asdict(safe_resolve=True)

        with open(save_path, 'w') as f:
            yaml.safe_dump(d, f, 
                           indent=2, sort_keys=False,
                           encoding='utf-8', allow_unicode=True)        
    
    def __repr__(self):
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