import os
from enum import Enum
from unittest.mock import patch, Mock, PropertyMock

import yaml
import pytest

from torchmeter.config import (
    UNSAFE_KV, DEFAULT_CFG, DEFAULT_FIELDS,
    dict_to_namespace, namespace_to_dict, list_to_callbacklist,
    FlagNameSpace, CallbackList, CallbackSet,
    get_config, Config
)

@pytest.fixture()
def default_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("default_cfg.yaml")
    with open(temp_cfg_path, 'w') as f:
        f.write(DEFAULT_CFG)
    yield temp_cfg_path.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)
        
@pytest.fixture()
def invalid_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("invalid_cfg.txt")
    with open(temp_cfg_path, 'w') as f:
        f.write(DEFAULT_CFG)
    yield temp_cfg_path.strpath
    if tmpdir.exists():
        tmpdir.remove(rec=1)

@pytest.fixture()
def custom_cfg_path(tmpdir):
    temp_cfg_path = tmpdir.join("custom_cfg.yaml")
    
    fake_interval = 0.34
    fake_content = f"render_interval: {fake_interval}"
    with open(temp_cfg_path, "w") as f:
        f.write(fake_content)
        
    yield temp_cfg_path.strpath
    
    if tmpdir.exists():
        tmpdir.remove(rec=1)

@pytest.fixture
def clist():
    obj = CallbackList([1,2,3,2])
    obj._callback_func = Mock()
    return obj

@pytest.fixture
def cset():
    obj = CallbackSet([1,3,2])
    obj._callback_func = Mock()
    return obj

def pytest_generate_tests(metafunc):
    if "all_type_data" in metafunc.fixturenames:
        metafunc.parametrize(
            argnames="all_type_data", 
            argvalues=[
                "string", False, 123, 1.23, None, 
                (1,2,3), [4,5,6], {7,8,9}, {"A":1, "B":2}, 
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
    """Test whether the UNSAFE_KV is correctly defined."""
   
    for key, val in UNSAFE_KV.items():
        assert isinstance(key, str)
        assert issubclass(val,Enum)
    
        # test whether the val'repr not equal to its corresponding key
        for k, v in val.__members__.items():
            assert str(v) != k

@pytest.mark.vital
def test_default_fields_in_default_setting():
    """Test whether all default fields are defined in default setting"""
    
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

def test_list_to_callbacklist():
    """Test the logic of list_to_callbacklist function"""
    
    ls = [1, "2", 3., None, (6,), 
          {7}, {"eight":8}, [9]]
    res = list_to_callbacklist(ls)
    assert res[:6] == [1, "2", 3., None, (6,), {7}]
    assert isinstance(res[6], FlagNameSpace)
    assert res[6].eight == 8
    assert isinstance(res[7], CallbackList)
    assert res[7] == [9]
    
class TestListToCallbackList:
    ...

class TestDictToNamespace:
    
    @pytest.mark.parametrize(
        argnames=("key", "is_error"),
        argvalues=[
            ("string", False), 
            (False, True), 
            (123, True), 
            (1.23, True), 
            (None, True), 
            ((1,2,3), True)
        ],
        ids=map(lambda x:f"key({x})", ["string", "bool", "int", "float", "None", "tuple"])
    )
    def test_valid_input(self, key, is_error, all_type_data):
        """Test normal dictionary conversion"""
        input_dict = {key: all_type_data}
        
        if is_error:
            with pytest.raises(TypeError):
                dict_to_namespace(input_dict)
        else:
            result = dict_to_namespace(input_dict)
            assert isinstance(result, FlagNameSpace)
            
            key_res = getattr(result, key)
            if isinstance(all_type_data, dict):
                assert isinstance(key_res, FlagNameSpace)
            else:
                assert key_res == all_type_data

    def test_invalid_input(self, all_type_data):
        """Test non-dictionary input"""
        if not isinstance(all_type_data, dict):
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
            for k, v in namespace.data_dict.items():
                
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
        assert isinstance(result.list, CallbackList)        
        assert isinstance(result.list[0], FlagNameSpace)
        
        assert result.list[0].key1 == "value1"
        assert result.list[1] == "item2"
        
    def test_set(self):
        """Test the conversion of dictionary containing set"""
        input_dict = {"set": {"item1", "item2"}}
        result = dict_to_namespace(input_dict)
        
        assert isinstance(result, FlagNameSpace)
        assert isinstance(result.set, CallbackSet)        
        
        assert result.set == {"item1", "item2"}

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
        
        # verify the invalid value error
        with pytest.raises(AttributeError):
            invalid_safeval = 'invalid_safeval'
            while invalid_safeval in valid_safevals:
                invalid_safeval *= 2
            result = dict_to_namespace({unsafe_key: invalid_safeval})

    def test_invalid_key(self):
        """Test the conversion of dictionary containing invalid key"""

        with pytest.raises(AttributeError):
            dict_to_namespace({"__FLAG": "value"})
        
        with pytest.raises(AttributeError):
            dict_to_namespace({"__flag_key": 123})

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
        
        if not safe_resolve:
            namespace_to_dict(ns, safe_resolve=safe_resolve)
            
            invalid_unsafeval = lambda x: "invalid_unsafeval"
            ns = FlagNameSpace()
            setattr(ns, unsafe_key, invalid_unsafeval)
            
            namespace_to_dict(ns, safe_resolve=safe_resolve)
            
        else:
            with pytest.raises(Exception):
                namespace_to_dict(ns, safe_resolve=safe_resolve)
            
            invalid_unsafeval = lambda x: "invalid_unsafeval"
            ns = FlagNameSpace()
            setattr(ns, unsafe_key, invalid_unsafeval)
            
            with pytest.raises(Exception):
                namespace_to_dict(ns, safe_resolve=safe_resolve)
            
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
        
        with pytest.raises(AttributeError):
            FlagNameSpace(__FLAG="value")
        
        with pytest.raises(AttributeError):
            FlagNameSpace(__flag_key="value")

class TestCallbackList:
    def test_init(self):
        """Test the initialization of callback list"""
        
        # verify default callback function
        clist = CallbackList((1, 2, 3))
        assert isinstance(clist, list)
        assert clist == [1, 2, 3]
        assert clist._callback_func() is None
        
        # verify callback funtion specification
        clist = CallbackList({4, 5, 6}, callback_func=lambda: 42)
        assert isinstance(clist, list)
        assert clist == [4, 5, 6]
        assert clist._callback_func() == 42
    
    def test_inheritance(self):
        """Test whether the list type is maintained."""
        assert issubclass(CallbackList, list)
        assert isinstance(CallbackList(), list)
    
    def test_append(self, clist):
        """Test the append method of callback list"""
        clist.append(42)
        assert clist == [1,2,3,2,42]
        clist._callback_func.assert_called_once()

    def test_extend(self, clist):
        """Test the extend method of callback list"""
        clist.extend([1, 2, 3])
        assert clist == [1,2,3,2,1, 2, 3]
        clist._callback_func.assert_called_once()

    def test_insert(self, clist):
        """Test the insert method of callback list"""
        
        clist.insert(0, 10)
        assert clist == [10,1,2,3,2]
        assert clist._callback_func.call_count == 1

    def test_pop(self, clist):
        """Test the pop method of callback list"""
        
        clist.pop()
        assert clist == [1,2,3]
        assert clist._callback_func.call_count == 1

    def test_remove(self, clist):
        """Test the remove method of callback list"""
        
        clist.remove(2)
        assert clist == [1, 3, 2]
        assert clist._callback_func.call_count == 1
    
    def test_clear(self, clist):
        """Test the clear method of callback list"""
        
        clist.clear()
        assert not len(clist)
        assert clist._callback_func.call_count == 1    

    def test_reverse(self, clist):
        """Test the reverse method of callback list"""
        
        clist.reverse()
        assert clist == [2, 3, 2, 1]
        assert clist._callback_func.call_count == 1
    
    def test_sort(self, clist):
        """Test the sort method of callback list"""
        
        clist.sort()
        assert clist == [1, 2, 2, 3]
        assert clist._callback_func.call_count == 1
        
    def test_setitem(self, clist):
        """Test the setitem method of callback list"""
        
        clist[0] = 10
        assert clist == [10, 2, 3, 2]
        assert clist._callback_func.call_count == 1

    def test_delitem(self, clist):
        """Test the delitem method of callback list"""
        
        del clist[0]
        assert clist == [2, 3, 2]
        assert clist._callback_func.call_count == 1
    
    def test_iadd(self, clist):
        """Test the iadd method of callback list"""
        
        clist += [10, 20, 30]
        assert clist == [1, 2, 3, 2, 10, 20, 30]
        assert clist._callback_func.call_count == 1
    
    def test_imul(self, clist):
        """Test the imul method of callback list"""
        
        clist *= 2
        assert clist == [1, 2, 3, 2, 1, 2, 3, 2]
        assert clist._callback_func.call_count == 1
    
    def test_multi_calls(self, clist):
        """Test whether the callback function is called correctly in multiple calls"""
        
        clist.append(10)
        clist.extend([20, 30])
        clist.append(40)
        assert clist == [1, 2, 3, 2, 10, 20, 30, 40]
        assert clist._callback_func.call_count == 3

    def test_callback_trigger_order(self):
        """Test callback function is triggered after origin api ends"""
        
        result = []
        cl = CallbackList()
        cl._callback_func = lambda: result.append(len(cl))
        
        cl.append(10)
        cl.extend([20, 30])
        assert result == [1, 3] 
        
    def test_edge_cases(self, clist):
        """Test some edge usage cases"""
        
        # empty operation
        clist.append(None)
        clist.extend([])
        assert clist == [1,2,3,2,None]
        assert clist._callback_func.call_count == 2
        clist._callback_func.reset_mock()
        
        # invalid usage of origin api
        with pytest.raises(TypeError):
            clist.append(1, 2, 3)  
        assert clist._callback_func.call_count == 0

        with pytest.raises(TypeError):
            clist.extend(1) 
        assert clist._callback_func.call_count == 0

class TestCallbackSet:
    def test_init(self):
        """Test the initialization of callback set"""
        
        # verify default callback function
        cset = CallbackSet((1, 2, 3))
        assert isinstance(cset, set)
        assert cset == {1, 2, 3}
        assert cset._callback_func() is None
        
        # verify callback funtion specification
        cset = CallbackSet([4, 4, 6], callback_func=lambda: 42)
        assert isinstance(cset, set)
        assert cset == {4, 6}
        assert cset._callback_func() == 42
    
    def test_inheritance(self):
        """Test whether the set type is maintained."""
        assert issubclass(CallbackSet, set)
        assert isinstance(CallbackSet(), set)
    
    def test_add(self, cset):
        """Test the add method of callback set"""
        cset.add(42)
        assert cset == {1,2,3,42}
        cset._callback_func.assert_called_once()

    def test_update(self, cset):
        """Test the update method of callback set"""
        cset.update({10,6,8})
        assert cset == {1, 2, 3, 6, 8, 10}
        cset._callback_func.assert_called_once()

    def test_difference_update(self, cset):
        """Test the difference_update method of callback set"""
        
        cset.difference_update({2, 3})
        assert cset == {1}
        assert cset._callback_func.call_count == 1

    def test_intersection_update(self, cset):
        """Test the intersection_update method of callback set"""
        
        cset.intersection_update({2})
        assert cset == {2}
        assert cset._callback_func.call_count == 1

    def test_symmetric_difference_update(self, cset):
        """Test the symmetric_difference_update method of callback set"""
        
        cset.symmetric_difference_update({2, 3, 4})
        assert cset == {1, 4}
        assert cset._callback_func.call_count == 1
    
    def test_discard(self, cset):
        """Test the discard method of callback set"""
        
        cset.discard(1)
        assert cset == {2,3}
        assert cset._callback_func.call_count == 1    

    def test_pop(self, cset):
        """Test the pop method of callback set"""
        
        cset.pop()
        assert cset == {2,3}
        assert cset._callback_func.call_count == 1
    
    def test_remove(self, cset):
        """Test the remove method of callback set"""
        
        cset.remove(2)
        assert cset == {1, 3}
        assert cset._callback_func.call_count == 1
        
    def test_clear(self, cset):
        """Test the clear method of callback set"""
        
        cset.clear()
        assert not len(cset)
        assert cset._callback_func.call_count == 1

    def test_isub(self, cset):
        """Test the isub method of callback set"""
        
        cset -= {2}
        assert cset == {1, 3}
        assert cset._callback_func.call_count == 1
        
    def test_iand(self, cset):
        """Test the iand method of callback set"""
        
        cset &= {3}
        assert cset == {3}
        assert cset._callback_func.call_count == 1
    
    def test_ixor(self, cset):
        """Test the iadd method of callback set"""
        
        cset ^= {2,4}
        assert cset == {1,3,4}
        assert cset._callback_func.call_count == 1
    
    def test_ior(self, cset):
        """Test the ior method of callback set"""
        
        cset |= {4, 5}
        assert cset == {1,2,3,4,5}
        assert cset._callback_func.call_count == 1
    
    def test_multi_calls(self, cset):
        """Test whether the callback function is called correctly in multiple calls"""
        
        cset.add(10)
        cset.update({20, 30})
        cset.add(40)
        assert cset == {1,2,3,10,20,30,40}
        assert cset._callback_func.call_count == 3

    def test_callback_trigger_order(self):
        """Test callback function is triggered after origin api ends"""
        
        result = []
        cl = CallbackSet()
        cl._callback_func = lambda: result.append(len(cl))
        
        cl.add(10)
        cl.update({20, 30})
        assert result == [1, 3] 
        
    def test_edge_cases(self, cset):
        """Test the edge cases of callback set"""
        
        # empty operation
        cset.add(None)
        cset.update(set())
        assert cset == {1,3,2,None}
        assert cset._callback_func.call_count == 2
        cset._callback_func.reset_mock()
        
        # invalid usage of origin api
        with pytest.raises(TypeError):
            cset.add(1, 2, 3)  
        assert cset._callback_func.call_count == 0

        with pytest.raises(KeyError):
            cset.remove(100) 
        assert cset._callback_func.call_count == 0

class TestFlagNameSpace:
    def test_init(self):
        flagns = FlagNameSpace(key1="value1", key2=123)
        assert hasattr(flagns, "key1")
        assert hasattr(flagns, "key2")
        assert flagns.key1 == "value1"
        assert flagns.key2 == 123
        assert hasattr(flagns, "_FlagNameSpace__flag_key")
        assert not flagns.is_change()

    def test_setattr(self, all_type_data):
        flagns = FlagNameSpace()
        flagns.key1 = all_type_data
        
        # verify the flag is toggled
        assert flagns.is_change()
        
        # verify the dict, list and set value is transformed to corresponding format
        if isinstance(all_type_data, dict):
            assert isinstance(flagns.key1, FlagNameSpace) 
            for k, v in all_type_data.items():
                assert getattr(flagns.key1, k) == v
        elif isinstance(all_type_data, list):
            assert isinstance(flagns.key1, CallbackList)
            assert flagns.key1 == all_type_data
        elif isinstance(all_type_data, set):
            assert isinstance(flagns.key1, CallbackSet)
            assert flagns.key1 == all_type_data
        else:
            assert flagns.key1 == all_type_data 
        
        # invalid key
        with pytest.raises(AttributeError):
            setattr(flagns, "__FLAG", "new_value")
        
        with pytest.raises(AttributeError):
            setattr(flagns, "__flag_key", "new_value")

    def test_delattr(self):
        flagns = FlagNameSpace(key1="value1")
        del flagns.key1
        assert not hasattr(flagns, "key1")
        
        # verify the flag is toggled
        assert flagns.is_change() 

        with pytest.raises(AttributeError):
            del flagns.__FLAG
            
        with pytest.raises(AttributeError):
            del flagns._FlagNameSpace__FLAG
        
        with pytest.raises(AttributeError):
            del flagns.__flag_key
        
        with pytest.raises(AttributeError):
            del flagns._FlagNameSpace__flag_key

    def test_data_dict(self):
        """Test the data_dict property is set and retrieved correctly"""
        
        flagns = FlagNameSpace(key1="value1", key2=123)
        
        assert hasattr(flagns, "data_dict")
        
        # verify content
        data_dict = flagns.data_dict
        assert isinstance(data_dict, dict)
        assert "__FLAG" not in data_dict
        assert data_dict["key1"] == "value1"
        assert data_dict["key2"] == 123
        
        # verify memory independence
        data_dict["key1"] = "value2"
        assert flagns.key1 == "value1"

    def test_update(self):
        """Test the logic of update method"""
        
        flagns = FlagNameSpace(key1="value1", key2=123)
                
        # invalid input type
        with pytest.raises(TypeError):
            flagns.update(123)
        
        # verify flag toggle
        assert flagns.is_change() is False
        
        # add new key
        ## with dict
        assert "key3" not in flagns.__dict__
        flagns.update({"key3": 456})
        assert flagns.key3 == 456
        assert "key2" in flagns.__dict__
        assert flagns.is_change()
        
        ## with FlagNameSpace
        assert "key4" not in flagns.__dict__
        flagns.update(FlagNameSpace(key4=789))
        assert flagns.key4 == 789
        assert "key3" in flagns.__dict__
        
        # update existing key
        ## with dict
        assert flagns.key1 != "000"
        flagns.update({"key1": "000"})
        assert flagns.key1 == "000"
        assert "key4" in flagns.__dict__
        
        ## with FlagNameSpace
        assert flagns.key2 != "123"
        flagns.update(FlagNameSpace(key2="123"))
        assert flagns.key2 == "123"
        assert "key3" in flagns.__dict__
            
        # dict to FlagNameSpace    
        flagns.update({"key5": {"subkey1": 901}})
        assert isinstance(flagns.key5, FlagNameSpace)
        assert flagns.key5.data_dict == {"subkey1": 901}
        
        # verify origin structure keeping
        with pytest.raises(RuntimeError):
            flagns.update({"key5": 901})
            
        # verify replace option
        flagns.mark_unchange()
        flagns.update({"key5": 901}, replace=True)
        assert flagns.data_dict == {"key5": 901}
        assert flagns.is_change()

    def test_is_change(self):
        flagns = FlagNameSpace(key1='1', 
                               key2=[2,[3, 3]],
                               key3=FlagNameSpace(val3=4))
        assert not flagns.is_change() 

        # common case
        flagns.key1 = "value1"
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change() 
        
        flagns.key1 += "value2"
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change() 
        
        # modify list
        ## modify common element
        flagns.key2[0] = 5
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
        
        ## modify nested list
        flagns.key2[0][0] = 7
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        # modify namespace
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
        
        # add new key
        flagns.key4 = {1, 2}
        assert flagns.is_change()
        assert flagns.is_change()
        flagns.mark_unchange()
        
        # del key
        del flagns.key1
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        # modify set
        flagns.key4.add(3)
        assert flagns.is_change()
        flagns.mark_unchange()
        assert not flagns.is_change()
        
        flagns.key4.remove(2)
        assert flagns.is_change()
        flagns.mark_unchange()
        
    def test_mark_change_and_unchange(self):
        flagns = FlagNameSpace(key=FlagNameSpace(subkey=1))
        assert not flagns.is_change()
        assert not flagns.key.is_change()
        
        # parent change, child no need to  change
        flagns.mark_change()
        assert flagns.is_change()
        assert not flagns.key.is_change()
        flagns.mark_unchange()

        # child change, parent change
        flagns.key.mark_change()
        assert flagns.is_change()
        assert flagns.key.is_change()
        flagns.key.mark_unchange()
        
        # parent reset to not change, childs do it too
        flagns.key.mark_change()
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
        with pytest.warns(UserWarning) as w:
            config = get_config(custom_cfg_path)
            assert isinstance(config, Config)
            assert config.config_file == custom_cfg_path
            assert config.render_interval == 0.34
        assert len(w) == len(DEFAULT_FIELDS) - 1

@pytest.mark.vital
class TestConfig:
    def setup_method(self, method):
        cfg = Config()
        cfg.config_file = None
        
    def test_init(self, custom_cfg_path):
        # init with no config file
        config = Config()
        assert config.config_file is None
        
        default_settings_dict = yaml.safe_load(DEFAULT_CFG)
        default_ns = dict_to_namespace(default_settings_dict)
        for field in DEFAULT_FIELDS:
            assert getattr(config, field) == getattr(default_ns, field)
        
        # init with config file
        with pytest.warns(UserWarning):
            config = Config(custom_cfg_path)
            assert config.config_file == custom_cfg_path
            assert config.render_interval == 0.34
        
    def test_ban_delete_or_new_field(self):
        config = Config()
        with pytest.raises(AttributeError):
            config.new_attr = 123
        
        for field in DEFAULT_FIELDS + ["config_file"]:
            with pytest.raises(RuntimeError):
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

        # custom config file specified is tested in TestGetConfig::test_get_custom_file

    def test_setattr(self):
        """Test the logic of setattr"""
        
        config = Config()
        
        # set attribute that is not in the DEFAULT_FIELDS
        with pytest.raises(AttributeError):
            config.invalid_attr = 1
        
        # set attribute whose value is not a FlagNameSpace
        assert config.render_interval != 0.6
        config.render_interval = 0.6
        assert config.render_interval == 0.6
        
        assert config.tree_fold_repeat is True
        config.tree_fold_repeat = False
        assert config.tree_fold_repeat is False
        
        # set attribute whose value is a FlagNameSpace
        # verify the action is actually a update
        ## with dict
        assert config.tree_repeat_block_args.title_align != "left"
        config.tree_repeat_block_args = {"title_align": "left"}
        assert config.tree_repeat_block_args.title_align == "left"
        
        assert config.tree_levels_args.default.guide_style != "red"
        config.tree_levels_args = {"default": {"guide_style": "red"}}
        assert config.tree_levels_args.default.guide_style == "red"
        assert "label" in config.tree_levels_args.default.__dict__
        
        assert "new_field" not in config.table_column_args.__dict__
        config.table_column_args = {"new_field": 1}
        assert "new_field" in config.table_column_args.__dict__
        assert config.table_column_args.new_field == 1
        
        with pytest.raises(TypeError): 
            # typerror trigger in `FlagNameSpace.update`,
            # cause the value of `table_display_args` is a FlagNameSpace instance
            config.table_display_args = 1
        
        config.combine = {"new_field": {"sub_field1": 1, "sub_field2": 2}}
        assert "new_field" in config.combine.__dict__
        assert isinstance(config.combine.new_field, FlagNameSpace)
        assert config.combine.new_field.data_dict == {"sub_field1": 1, "sub_field2": 2}

        ## with another FlagNameSpace
        assert config.tree_repeat_block_args.title_align != "right"
        config.tree_repeat_block_args = FlagNameSpace(title_align="right")
        assert config.tree_repeat_block_args.title_align == "right"
        
        assert config.tree_levels_args.default.guide_style != "blue"
        config.tree_levels_args = FlagNameSpace(default={"guide_style": "blue"})
        assert config.tree_levels_args.default.guide_style == "blue"
        assert "label" in config.tree_levels_args.default.__dict__
        
        assert "new_field2" not in config.table_column_args.__dict__
        config.table_column_args = FlagNameSpace(new_field2=2)
        assert "new_field2" in config.table_column_args.__dict__
        assert config.table_column_args.new_field2 == 2
        
        config.combine = FlagNameSpace(new_field3={"sub_field1": 1, "sub_field2": 2})
        assert "new_field3" in config.combine.__dict__
        assert isinstance(config.combine.new_field, FlagNameSpace)
        assert config.combine.new_field3.data_dict == {"sub_field1": 1, "sub_field2": 2}

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
        
        config.tree_levels_args = {"2": {"label": "1"}}
        config.restore()
        assert "2" not in config.tree_levels_args.__dict__

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

    @patch("torchmeter.config.Config.asdict")
    def test_repr(self, mock_asdict):
        """Test the logic of `__repr__` method."""
        
        expected = (
            "• Config file: test_config.yaml\n\n"
            "• field A: 0.45 | <float>\n\n"
            "• field B: 123 | <int>\n\n"
            "• field C: list(\n"
            "│   - 4 | <int>\n"
            "│   - 5 | <int>\n"
            "│   - 6 | <int>\n"
            "└─  )\n\n"
            "• field D: tuple(\n"
            "│   - 7 | <int>\n"
            "│   - 8 | <int>\n"
            "│   - 9 | <int>\n"
            "└─  )\n\n"
            "• field E: namespace{\n"
            "│   subfield A = None | <NoneType>\n"
            "│   subfield B = True | <bool>\n"
            "│   subfield C = test | <str>\n"
            "│   subfield D = tuple(\n"
            "│   │   - 1 | <str>\n"
            "│   │   - 2 | <str>\n"
            "│   │   - 3 | <str>\n"
            "│   └─  )\n"
            "└─  }"
        )
        
        cfg = Config() 
        
        mock_asdict.return_value = {"field A": 0.45,
                                    "field B": 123,
                                    "field C": [4, 5, 6],
                                    "field D": (7, 8, 9),
                                    "field E": {"subfield A": None, 
                                                "subfield B": True,
                                                "subfield C": "test",
                                                "subfield D": ("1", "2", "3")}}
        
        with patch.object(Config, "config_file",
                          new_callable=PropertyMock,
                          return_value="test_config.yaml"):
        
            assert str(cfg).strip() == expected

    def test_singleton(self, custom_cfg_path):
        # verify same instance
        config1 = Config()
        config2 = Config()
        assert id(config1) == id(config2)
        
        # verify synchronization of changes
        config2.render_interval = 0.45
        assert config1.render_interval == 0.45
        
        # verify change is kept
        config3 = Config()
        assert config3.render_interval == 0.45
        
        # verify reload when a new config_path is specified
        with pytest.warns(UserWarning):
            config4 = Config(custom_cfg_path)
        assert id(config1) == id(config4)
        assert config4.render_interval == 0.34
        