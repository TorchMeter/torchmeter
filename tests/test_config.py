import os
from enum import Enum
from unittest.mock import patch

import yaml
import pytest

from torchmeter.config import (
    UNSAFE_KV, DEFAULT_CFG, DEFAULT_FIELDS,
    dict_to_namespace, namespace_to_dict,
    FlagNameSpace, 
    get_config, Config
)

DEFAULT_CFG_STRING = """\
• Config file: None(default setting below)

• render_interval: 0.15

• tree_fold_repeat: True

• tree_repeat_block_args: 
│   title = [i]Repeat [[b]<repeat_time>[/b]] Times[/] 
│   title_align = center 
│   subtitle = None 
│   subtitle_align = center 
│   style = dark_goldenrod 
│   highlight = True 
│   box = HEAVY_EDGE 
│   border_style = dim 
│   width = None 
│   height = None 
│   padding = [0, 1] 
└─  expand = False 

• tree_levels_args: 
│   default = {'label': '[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]', 'style': 'tree', 'guide_style': 'light_coral', 'highlight': True, 'hide_root': False, 'expanded': True} 
└─  0 = {'label': '[b light_coral]<name>[/]', 'guide_style': 'light_coral'} 

• table_column_args: 
│   style = none 
│   justify = center 
│   vertical = middle 
│   overflow = fold 
└─  no_warp = False 

• table_display_args: 
│   style = spring_green4 
│   highlight = True 
│   width = None 
│   min_width = None 
│   expand = False 
│   padding = [0, 1] 
│   collapse_padding = False 
│   pad_edge = True 
│   leading = 0 
│   title = None 
│   title_style = bold 
│   title_justify = center 
│   caption = None 
│   caption_style = None 
│   caption_justify = center 
│   show_header = True 
│   header_style = bold 
│   show_footer = False 
│   footer_style = italic 
│   show_lines = False 
│   row_styles = None 
│   show_edge = True 
│   box = ROUNDED 
│   safe_box = True 
└─  border_style = None 

• combine: 
└─  horizon_gap = 2"""

@pytest.fixture(scope="function")
def default_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("default_cfg.yaml")
    with open(temp_cfg_path, 'w') as f:
        f.write(DEFAULT_CFG)
    yield temp_cfg_path.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)
        
@pytest.fixture(scope="function")
def invalid_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("invalid_cfg.txt")
    with open(temp_cfg_path, 'w') as f:
        f.write(DEFAULT_CFG)
    yield temp_cfg_path.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)

@pytest.fixture(scope="function")
def custom_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("custom_cfg.yaml")
    yield temp_cfg_path.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)

def pytest_generate_tests(metafunc):
    if "all_type_data" in metafunc.fixturenames:
        metafunc.parametrize(
            argnames="all_type_data", 
            argvalues=[
                "string", False, 123, 1.23, None, 
                (1,2,3), [4,5,6], {7,8,9},
                lambda : None, (_ for _ in range(5))
            ], 
            ids=map(lambda x:f"val({x})", [
                "string", "bool", "int", "float", "None", 
                "tuple", "list", "set","dict",
                "function", "iterable_obj"
                ]
            )
        )

@pytest.mark.vital
def test_unsafe_kv():
    class T:
        a=1
    for val in UNSAFE_KV.values():
        assert issubclass(val,Enum)
    
        # test whether the val'repr not equal to its corresponding key
        for k, v in val.__members__.items():
            assert str(v) != k

@pytest.mark.vital
def test_default_fields_in_default_setting():
    setting_lines_generator = (line for line in DEFAULT_CFG.split('\n')
                               if len(line) and not line.isspace())
    
    assure_fields = []
    for valid_line in setting_lines_generator:
        for field in DEFAULT_FIELDS:
            if field in valid_line:
                assert valid_line.startswith(field)
                assure_fields.append(field)
                if len(assure_fields) == len(DEFAULT_FIELDS):
                    return
    pytest.fail(f"These fields are missing in default setting: {set(DEFAULT_FIELDS)-set(assure_fields)}")

class TestDictToNamespace:
    @pytest.mark.parametrize(argnames="key",
                             argvalues=["string", False, 123, 1.23, None, (1,2,3)],
                             ids=map(lambda x:f"key({x})", ["string", "bool", "int", "float", "None", "tuple"]))
    def test_valid_input(self, key, all_type_data):
        """Test normal dictionary conversion"""
        input_dict = {key: all_type_data}
        result = dict_to_namespace(input_dict)
        assert isinstance(result, FlagNameSpace)
        assert getattr(result, key) is all_type_data

    def test_invalid_input(self, all_type_data):
        """Test non-dictionary input"""
        with pytest.raises(TypeError):
            dict_to_namespace(all_type_data)

    def test_nested_dict(self):
        """Test the conversion of nested dictionary"""
        
        
        nested_dict = {
            "nested_one": {"key": "value"},
            
            "nested_two": {"key": 
                {"nested_one": {"key": "value"}}
            },
            
            "nested_three": {"key": 
                {"nested_two": {"key": 
                        {"nested_one": {"key": "value"}}
                    }
                }
            }
        }
        result = dict_to_namespace(nested_dict)
        
        def dfs_assert(namespace, depth=0):
            for k, v in namespace.__dict__.items():
                if "__FLAG" in k:
                    continue
                
                if isinstance(v, FlagNameSpace):
                    dfs_assert(v, depth+1)
                else:
                    assert k == "key"
                    assert v == "value"
        
        assert isinstance(result, FlagNameSpace)
        dfs_assert(result)

    def test_list(self):
        """Test the conversion of dictionary containing list"""
        input_dict = {"list": [{"key1": "value1"}, "item2"]}
        result = dict_to_namespace(input_dict)
        assert isinstance(result, FlagNameSpace)
        assert isinstance(result.list[0], FlagNameSpace)
        assert result.list[0].key1 == "value1"
        assert result.list[1] == "item2"

    @pytest.mark.parametrize(argnames="unsafe_key",
                             argvalues=UNSAFE_KV.keys(),
                             ids=map(lambda x:f"unsafe_key({x})", UNSAFE_KV.keys()))
    def test_unsafe_key(self, unsafe_key):
        """""Test the conversion of dict containing unsafe key"""
        vals_enum = UNSAFE_KV[unsafe_key]
        
        valid_safevals = []
        for member in vals_enum:
            input_dict = {unsafe_key: member.name}
            result = dict_to_namespace(input_dict)
            assert isinstance(result, FlagNameSpace)
            assert getattr(result, unsafe_key) is member.value
            valid_safevals.append(member.name)
        
        # test whether invalid value can be safely resolved to None
        with pytest.raises(AttributeError):
            invalid_safeval = 'invalid_safeval'
            while invalid_safeval in valid_safevals:
                invalid_safeval *= 2
            result = dict_to_namespace({unsafe_key: invalid_safeval})

    def test_invalid_key(self):
        """Test the conversion of dictionary containing invalid key"""
        input_dict = {"__FLAG_invalid": "value"}
        with pytest.warns(UserWarning):
            result = dict_to_namespace(input_dict)
            assert not hasattr(result, "__FLAG_invalid")

class TestNamespaceToDict:
    def test_valid_input(self, all_type_data):
        """Test normal namespace conversion"""
        ns = FlagNameSpace(key1=all_type_data)
        result = namespace_to_dict(ns)
        assert isinstance(result, dict)
        assert result["key1"] == all_type_data

    def test_invalid_input(self, all_type_data):
        """Test non-FlagNameSpace input"""
        with pytest.raises(TypeError):
            namespace_to_dict(all_type_data)

    @pytest.mark.parametrize(argnames="unsafe_key",
                             argvalues=UNSAFE_KV.keys(),
                             ids=map(lambda x:f"unsafe_key({x})", UNSAFE_KV.keys()))
    @pytest.mark.parametrize(argnames="safe_resolve",
                             argvalues=(True, False),
                             ids=lambda x:f"safe_resolve={x}")
    def test_unsafe_key(self, unsafe_key, safe_resolve):
        """Test the conversion of FlagNameSpace containing unsafe key"""
        vals_enum = UNSAFE_KV[unsafe_key]
        
        valid_vals = []
        for member in list(vals_enum):
            ns = FlagNameSpace()
            setattr(ns, unsafe_key, member.value)
            res_dict = namespace_to_dict(ns, safe_resolve=safe_resolve)
            assert isinstance(res_dict, dict)
            
            if safe_resolve:
                assert res_dict[unsafe_key] == member.name
            else:
                assert res_dict[unsafe_key] == member.value
            valid_vals.append(res_dict[unsafe_key])

        invalid_safeval = 'invalid_val'
        while invalid_safeval in valid_vals:
            invalid_safeval *= 2
                    
        ns = FlagNameSpace()
        setattr(ns, unsafe_key, invalid_safeval)
        res_dict = namespace_to_dict(ns, safe_resolve=safe_resolve)

        if safe_resolve:
            invalid_unsafeval = lambda x: "invalid_unsafeval"
            ns = FlagNameSpace()
            setattr(ns, unsafe_key, invalid_unsafeval)
            
            with pytest.raises(Exception):
                res_dict = namespace_to_dict(ns, safe_resolve=safe_resolve)
            
    def test_nested_namespace(self):
        """Test the conversion of nested FlagNameSpace"""
        ns = FlagNameSpace(
            nested_one=FlagNameSpace(
                nested_two=FlagNameSpace(
                    nested_three=FlagNameSpace(
                        key='value'
                    )
                )
            )
        )

        def dfs_assert(res_dict, depth=0):
            for k, v in res_dict.items():
                if "__FLAG" in k:
                    continue
                
                if isinstance(v, dict):
                    dfs_assert(v, depth+1)
                    assert k.startswith("nested")
                else:
                    assert k == "key"
                    assert v == "value"

        result = namespace_to_dict(ns)
        assert isinstance(result, dict)
        
        dfs_assert(result)

    def test_list(self):
        """Test the conversion of FlagNameSpace containing list"""
        nested_ns = FlagNameSpace(key1="value1")
        ns = FlagNameSpace(list=[nested_ns, "item2"])
        result = namespace_to_dict(ns)
        assert isinstance(result, dict)
        assert isinstance(result["list"][0], dict)
        assert result["list"][0]["key1"] == "value1"
        assert result["list"][1] == "item2"

    def test_invalid_key(self):
        """Test the conversion of FlagNameSpace containing invalid key"""
        ns = FlagNameSpace(__FLAG_invalid="value")
        result = namespace_to_dict(ns)
        assert isinstance(result, dict)
        assert "__FLAG_invalid" not in result

class TestFlagNameSpace:
    def test_init(self):
        flagns = FlagNameSpace(key1="value1", key2=123)
        assert hasattr(flagns, "key1")
        assert hasattr(flagns, "key2")
        assert flagns.key1 == "value1"
        assert flagns.key2 == 123
        assert hasattr(flagns, "_FlagNameSpace__flag_key")
        assert not flagns.is_change()

    def test_flag_unique(self):
        flagns = FlagNameSpace(__FLAG=True, __FLAG1=True)
        assert hasattr(flagns, "__FLAG12")
        assert not flagns.is_change()        

    def test_setattr(self, all_type_data):
        flagns = FlagNameSpace()
        flagns.key1 = all_type_data
        assert flagns.key1 == all_type_data
        assert flagns.is_change()  

        with pytest.raises(AttributeError):
            flagns.__flag_key = "new_value"

        with pytest.raises(AttributeError):
            flagns._FlagNameSpace__flag_key = "new_value"

    def test_delattr(self):
        flagns = FlagNameSpace(key1="value1")
        del flagns.key1
        assert not hasattr(flagns, "key1")
        assert flagns.is_change() 

        with pytest.raises(AttributeError):
            del flagns.__flag_key
        
        with pytest.raises(AttributeError):
            del flagns._FlagNameSpace__flag_key

    def test_is_change(self):
        flagns = FlagNameSpace(key1='1', 
                               key2=[2,3],
                               key3=FlagNameSpace(val3=4))
        assert not flagns.is_change() 

        flagns.key1 = "value1"
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change() 
        
        flagns.key1 += "value2"
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change() 
        
        flagns.key2[1] = 5
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        flagns.key2.append(6)
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        del flagns.key2[0]
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        flagns.key3.val3 = 6
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        flagns.key3.val4 = 7
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        flagns.key3.val4 += 8
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
    def test_mark_change_and_unchange(self):
        flagns = FlagNameSpace(key=FlagNameSpace(subkey=1))
        assert not flagns.is_change()
        assert not flagns.key.is_change()
        
        flagns.mark_change()
        assert flagns.is_change()
        assert not flagns.key.is_change()

        flagns.key.mark_change()
        assert flagns.is_change()
        assert flagns.key.is_change()
        
        flagns.mark_unchange()
        assert not flagns.is_change()
        assert not flagns.key.is_change()

@pytest.mark.vital
class TestGetConfig:
    def test_get_default(self):
        with patch.dict(os.environ, {}, clear=True):  
            config = get_config()
            assert isinstance(config, Config)
            assert config.config_file is None  
            for field in DEFAULT_FIELDS:
                assert hasattr(config, field)

    def test_get_from_env(self, default_cfg_path):
        with patch.dict(os.environ, {"TORCHMETER_CONFIG": default_cfg_path}):
            config = get_config()
            assert isinstance(config, Config)
            assert config.config_file == default_cfg_path

    def test_get_from_path(self, default_cfg_path):
        config = get_config(default_cfg_path)
        assert isinstance(config, Config)
        assert config.config_file == default_cfg_path

    def test_config_file_not_exist(self):
        fake_config_path = "/fake/path/to/nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            get_config(fake_config_path)

    def test_get_invalid_file(self, invalid_cfg_path):
        with pytest.raises(ValueError):
            get_config(invalid_cfg_path)

    def test_get_custom_file(self, custom_cfg_path):
        fake_interval = 0.34
        fake_content = f"render_interval: {fake_interval}"
        with open(custom_cfg_path, "w") as f:
            f.write(fake_content)

        with pytest.warns(UserWarning) as w:
            config = get_config(custom_cfg_path)
            assert isinstance(config, Config)
            assert config.config_file == custom_cfg_path
            assert config.render_interval == fake_interval
        assert len(w) == len(DEFAULT_FIELDS) - 1

@pytest.mark.vital
class TestConfig:
    def test_init(self):
        config = Config()
        assert config.config_file is None
        
        default_settings_dict = yaml.safe_load(DEFAULT_CFG)
        default_ns = dict_to_namespace(default_settings_dict)
        for field in DEFAULT_FIELDS:
            assert getattr(config, field) == getattr(default_ns, field)
        
    def test_ban_delete_or_new_field(self):
        config = Config()
        with pytest.raises(AttributeError):
            config.new_attr = 123
        
        for field in DEFAULT_FIELDS + ["config_file"]:
            with pytest.raises(AttributeError):
                delattr(config, field)

    def test_config_file_property(self, invalid_cfg_path, custom_cfg_path):
        """Test the property `config_file` getter and setter"""
        config = Config()
        assert config.config_file is None
        
        with pytest.raises(TypeError):
            config.config_file = 123  

        with pytest.raises(FileNotFoundError):
            config.config_file = "/fake/path/to/nonexistent.yaml"

        with pytest.raises(ValueError):
            config.config_file = invalid_cfg_path

        _ = TestGetConfig()
        _.test_get_custom_file(custom_cfg_path)

    def test_delattr(self):
        config = Config()
        for field in DEFAULT_FIELDS + ["config_file"]:
            with pytest.raises(RuntimeError):
                delattr(config, field)

    def test_restore(self):
        default_settings = yaml.safe_load(DEFAULT_CFG)
        config = Config()
        
        config.render_interval = 0.45
        config.restore()
        
        assert config.render_interval == default_settings['render_interval']

    def test_check_integrity(self, custom_cfg_path):
        config = Config()
        assert config.check_integrity() is None
        
        _ = TestGetConfig()
        _.test_get_custom_file(custom_cfg_path)     

    def test_asdict(self):
        config = Config()
        
        safe_dict = config.asdict(safe_resolve=True)
        default_safe_dict = yaml.safe_load(DEFAULT_CFG)
        assert isinstance(safe_dict, dict)
        assert set(safe_dict.keys()) == set(DEFAULT_FIELDS)
        assert safe_dict == default_safe_dict
        
        unsafe_dict = config.asdict(safe_resolve=False)
        default_unsafe_dict = yaml.safe_load(DEFAULT_CFG)
        
        def dfs_replace_unsafe_value(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    dfs_replace_unsafe_value(v)
                elif k in UNSAFE_KV:
                    d[k] = getattr(UNSAFE_KV[k], v).value
            return d
        
        assert isinstance(safe_dict, dict)
        assert set(safe_dict.keys()) == set(DEFAULT_FIELDS)
        assert unsafe_dict == dfs_replace_unsafe_value(default_unsafe_dict)

    def test_dump(self, custom_cfg_path):
        config = Config()
        config.dump(custom_cfg_path)
        assert os.path.exists(custom_cfg_path)

    def test_repr(self):
        config_str = str(Config())
        assert config_str.strip() == DEFAULT_CFG_STRING

    def test_singleton(self):
        config1 = Config()
        config2 = Config()
        assert id(config1) == id(config2)
        
        config2.render_interval = 0.45
        assert config1.render_interval == 0.45