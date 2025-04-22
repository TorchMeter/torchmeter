from unittest.mock import ANY, MagicMock, PropertyMock, patch

import pytest
import torch.nn as nn
from rich import get_console
from torch import equal as torch_equal
from torch import randn as torch_randn
from torch import float16, float32
from rich.text import Text
from torch.cuda import is_available as is_cuda
from rich.layout import Layout
from torch.utils.hooks import RemovableHandle

from torchmeter.core import Meter, __cfg__, tc_device
from torchmeter.core import __cfg__ as core_cfg
from torchmeter.utils import data_repr, indent_str
from torchmeter.engine import CalMeter, MemMeter, IttpMeter, ParamsMeter, OperationNode, OperationTree
from torchmeter.display import TreeRenderer, TabularRenderer

pytestmark = pytest.mark.vital


class ExampleModel(nn.Module):
    def __init__(self) -> None:
        super(ExampleModel, self).__init__()
        self.layer0 = nn.Linear(10, 10)
        self.layer1 = nn.Sequential(
            nn.Linear(10, 10),
            nn.ReLU(),
            nn.Linear(10, 10),
            nn.ReLU()
        )
        
    def forward(self, ipt):
        return self.layer1(self.layer0(ipt))


class EmptyModel(nn.Module):
    def __init__(self) -> None:
        super(EmptyModel, self).__init__()

    def forward(self) -> None:
        pass


class RepeatModel(nn.Module):
    def __init__(self, repeat_nodes=1) -> None:
        super(RepeatModel, self).__init__()
                
        self.layer_ls = nn.ModuleList([nn.Identity() for _ in range(repeat_nodes)])


class TestMeter:
    
    model_getter = lambda _, metered_model: metered_model.optree.root.operation
    
    def test_valid_init(self) -> None:
        """Test valid initialization and basic functionality"""
        model = ExampleModel()
        
        # init a gpu model
        if is_cuda():
            gpu_model = Meter(model, device="cuda:0") 
            assert gpu_model._Meter__device.type == "cuda"
            assert self.model_getter(gpu_model).layer0.weight.device.type == "cuda"
        
        # init a cpu model
        cpu_model = Meter(model, device="cpu") 
        assert cpu_model._Meter__device.type == "cpu"
        assert self.model_getter(cpu_model).layer0.weight.device.type == "cpu"
        
        assert cpu_model._ipt == {'args': tuple(), 'kwargs': dict()}
        assert isinstance(cpu_model.optree, OperationTree)
        assert isinstance(cpu_model.tree_renderer, TreeRenderer)
        assert isinstance(cpu_model.table_renderer, TabularRenderer)
        
        assert cpu_model._Meter__measure_param is False
        assert cpu_model._Meter__measure_cal is False
        assert cpu_model._Meter__measure_mem is False
        assert cpu_model._Meter__has_nocall_nodes is None
        assert cpu_model._Meter__has_not_support_nodes is None
        
        assert hasattr(cpu_model, "ittp_warmup")
        assert hasattr(cpu_model, "ittp_benchmark_time")
        # set ittp_warmup and ittp_benchmark_time to a lower value to save time
        cpu_model.ittp_warmup = 2
        cpu_model.ittp_benchmark_time = 2
        
        cpu_model(torch_randn(1, 10))
        assert hasattr(cpu_model, "ipt")
        assert hasattr(cpu_model, "device")
        assert hasattr(cpu_model, "tree_fold_repeat")
        assert hasattr(cpu_model, "tree_levels_args")
        assert hasattr(cpu_model, "tree_repeat_block_args")
        assert hasattr(cpu_model, "table_display_args")
        assert hasattr(cpu_model, "table_column_args")
        assert hasattr(cpu_model, "structure")
        assert hasattr(cpu_model, "param")
        assert hasattr(cpu_model, "cal")
        assert hasattr(cpu_model, "mem")
        assert hasattr(cpu_model, "ittp")
        assert hasattr(cpu_model, "model_info")
        assert hasattr(cpu_model, "subnodes")

    def test_invalid_init(self) -> None:
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            Meter("not a model")

    def test_call(self) -> None:
        """Test the logic of __call__ method"""
        ipt = torch_randn(1, 10)
        model = ExampleModel()
        
        # cpu_model
        # call with positional argument
        cpu_model = Meter(model, device="cpu")
        output = cpu_model(ipt)
        assert output.shape == (1, 10)
        assert output.device.type == "cpu"
        assert cpu_model.ipt["args"][0] is ipt
        assert not len(cpu_model.ipt["kwargs"])
        
        # call with keyword argument
        output2 = cpu_model(ipt=ipt)
        assert output2.shape == (1, 10)
        assert output2.device.type == "cpu"
        assert cpu_model.ipt["kwargs"]["ipt"] is ipt
        assert not len(cpu_model.ipt["args"])
        
        # new input reset statistics measured flags
        cpu_model._Meter__measure_param = True
        cpu_model._Meter__measure_cal = True
        cpu_model._Meter__measure_mem = True
        cpu_model(torch_randn(2, 10)) # different input triggers reset
        assert not cpu_model._Meter__measure_param 
        assert not cpu_model._Meter__measure_cal 
        assert not cpu_model._Meter__measure_mem
        
        cpu_model._Meter__measure_param = True
        cpu_model._Meter__measure_cal = True
        cpu_model._Meter__measure_mem = True
        cpu_model(torch_randn(2, 10)) # same input not triggers reset
        assert cpu_model._Meter__measure_param 
        assert cpu_model._Meter__measure_cal 
        assert cpu_model._Meter__measure_mem
        
        if is_cuda():
            # gpu_model
            # call with positional argument
            gpu_model = Meter(model, device="cuda:0")
            output = gpu_model(ipt)
            assert output.shape == (1, 10)
            assert output.device.type == "cuda"
            assert torch_equal(gpu_model.ipt["args"][0], ipt.to("cuda:0"))
            assert not len(gpu_model.ipt["kwargs"])
            
            # call with keyword argument
            output = gpu_model(ipt=ipt)
            assert output.shape == (1, 10)
            assert output.device.type == "cuda"
            assert torch_equal(gpu_model.ipt["kwargs"]['ipt'], ipt.to("cuda:0"))
            assert not len(gpu_model.ipt["args"])
    
    def test_attr_operation(self) -> None:
        """Test the logic of overwritten __get(del)attr__ method"""
        
        model = ExampleModel()
        model.test_attr = "ATTR"
        model.param = "PARAM"
        model.test_method = lambda: "enter test method"
        
        metered_model = Meter(model)
        
        # getter
        # get self attr
        assert hasattr(metered_model, "param")
        assert isinstance(metered_model.optree, OperationTree)
        
        # get origin model's attr
        assert hasattr(metered_model, "test_attr")
        assert metered_model.test_attr == "ATTR"
        
        # get attr with same name defined in origin model
        assert isinstance(metered_model.param, ParamsMeter)
        assert metered_model.ORIGIN_param == "PARAM"
        
        # get not exist attr
        with pytest.raises(AttributeError):
            getattr(metered_model, "not_exist_attr")
            
        # call origin model's method
        assert metered_model.test_method() == "enter test method"
        
        # setter
        # set self attr
        # common attr
        origin_val = metered_model.ittp_warmup
        setattr(metered_model, "ittp_warmup", "10")
        assert origin_val != metered_model.ittp_warmup
        assert metered_model.ittp_warmup == "10"
        
        # class property that can be set
        setattr(metered_model, "device", "cpu")
        
        # class property that can not be set
        with pytest.raises(AttributeError):
            setattr(metered_model, "param", "Param")

        # set origin model's attr
        model.test_attr = "NEW_ATTR"
        assert metered_model.test_attr == "NEW_ATTR"
        
        # set attr with same name defined in origin model
        model.param = "NEW_PARAM"
        assert isinstance(metered_model.param, ParamsMeter)
        assert metered_model.ORIGIN_param == "NEW_PARAM"
        
        # set not exist attr
        setattr(metered_model, "not_exist_attr", "NOW_EXIST")
        assert metered_model.not_exist_attr == "NOW_EXIST"
        
        setattr(model, "not_exist_attr_2", "NOW_EXIST_2")
        assert metered_model.not_exist_attr_2 == "NOW_EXIST_2"
        
        # set origin model's method
        model.test_method = lambda: "enter test method 2"
        assert metered_model.test_method() == "enter test method 2"
        
        # delttr
        # del self attr
        del metered_model.ittp_warmup
        assert not hasattr(metered_model, "ittp_warmup")
        with pytest.raises(AttributeError):
            del metered_model.param
        
        # del origin model's attr
        del model.test_attr
        assert not hasattr(metered_model.model, "test_attr")
        
        # del attr with same name defined in origin model
        del model.param
        assert not hasattr(metered_model, "ORIGIN_param")

        # del not exist attr
        with pytest.raises(AttributeError):
            del metered_model.not_exist_attr_3
            
        # del origin model's method
        del model.test_method
        with pytest.raises(AttributeError):
            metered_model.test_method()
    
    def test_ipt(self) -> None:
        """Test the ipt property is set and retrieved correctly"""
        
        metered_model = Meter(ExampleModel())
        metered_model._ipt = "test_ipt"
        
        # verify whether ipt property is linked to _ipt
        assert metered_model.ipt == "test_ipt"
    
    def test_device(self) -> None:
        """Test the device property is set and retrieved correctly"""
        
        model = ExampleModel()
        metered_model = Meter(model, device="cpu")
        metered_model.ipt["args"] = (torch_randn(1, 10, device=tc_device("cpu")), )
        metered_model.ipt["kwargs"] = {'ipt': torch_randn(1, 10, device=tc_device("cpu"))}
        
        # retrieve
        assert hasattr(metered_model, "device")
        assert metered_model.device is metered_model._Meter__device
        assert metered_model.device.type == "cpu"
        
        # set        
        if is_cuda():
            metered_model.device = "cuda:0"
            assert metered_model.device.type == "cuda"
            assert metered_model.ipt["args"][0].device.type == "cuda"
            assert metered_model.ipt["kwargs"]['ipt'].device.type == "cuda"
            assert self.model_getter(metered_model).layer0.weight.device.type == "cuda"
    
    def test_to(self) -> None:
        """Test the logic of changing model's device through `to` method"""
        
        metered_model = Meter(ExampleModel())
        
        # verify link to `device` method
        with patch.object(Meter, "device",
                          new_callable=PropertyMock,
                          return_value=Meter.device) as mock_device_property:
            metered_model.to("cpu")
            mock_device_property.assert_called_once_with("cpu")
        
        # invalid input type
        with pytest.raises(RuntimeError):
            metered_model.to("not a device")
    
    def test_auto_detect_device(self) -> None:
        """Test whether the device is auto detected when no device is specified"""
        
        # verify auto detect the device of cpu model
        autodevice_model = Meter(ExampleModel().to("cpu")) 
        assert autodevice_model.device.type == "cpu"
        
        # verify auto detect the device of gpu model
        if is_cuda():
            autodevice_model = Meter(ExampleModel().to("cuda:0")) 
            assert autodevice_model.device.type == "cuda"
        
        # verify auto move no parameter model to cpu
        with pytest.warns(UserWarning):
            empty_model = Meter(EmptyModel())
            assert empty_model.device.type == "cpu"
        
    def test_is_ipt_empty(self) -> None:
        """Test the logic of _is_ipt_empty method"""
        
        # empty
        metered_model = Meter(ExampleModel())
        assert metered_model._is_ipt_empty()
        
        # only positional argument
        metered_model._ipt = {"args": (torch_randn(1, 10), ), 
                             "kwargs": {}}
        assert not metered_model._is_ipt_empty()
        
        # only keyword argument
        metered_model._ipt = {"args": (),
                             "kwargs": {'ipt': torch_randn(1, 10)}}
        assert not metered_model._is_ipt_empty()
        
        # both
        metered_model.ipt["args"] = (torch_randn(1, 10), )
        assert not metered_model._is_ipt_empty()

    @pytest.mark.skipif(not is_cuda(), reason="requires gpu")
    def test_ipt2device(self) -> None:
        """Test the logic of _ipt2device method"""
        
        metered_model = Meter(ExampleModel())
        to_method = torch_randn(1).to
        
        # empty ipt (no need)
        empty_metered_model = Meter(EmptyModel(), device="cpu")
        empty_metered_model._ipt2device()

        # empty ipt(needed)
        with pytest.raises(RuntimeError):
            metered_model._ipt2device()
            
        # non Tensor ipt
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            non_tensor_ipt = {"args": (1, "2", 3., None, lambda x: x, {1, 2}), 
                              "kwargs": {"A": 1, "B": "2", "C": 3., "D": None, "E": lambda x: x, "F": {1, 2}}}
            metered_model._ipt = non_tensor_ipt
            metered_model._ipt2device()
            mock_to.assert_not_called()
        
        # single tensor ipt
        # same device with model, will not move
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            single_tensor_ipt = {"args": (torch_randn(1, 10), ),
                                 "kwargs": {"A": 1, "B": "2", "C": 3., "D": None, "E": lambda x: x, "F": {1, 2}}}
            metered_model._ipt = single_tensor_ipt
            metered_model._ipt2device()
            mock_to.assert_not_called()
        
        # different device with model, will move to model's device
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            single_tensor_ipt = {"args": (1, "2", 3., None, lambda x: x, {1, 2}), 
                                 "kwargs": {"A": torch_randn(1, 10, device=tc_device("cuda:0"))}}
            metered_model._ipt = single_tensor_ipt
            metered_model._ipt2device()
            mock_to.assert_called_once()
            assert metered_model.ipt["kwargs"]["A"].device.type == "cpu"
        
        # multiple tensor ipt
        # same device with model, will not move
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            multiple_tensor_ipt = {"args": (torch_randn(1, 10), ),
                                   "kwargs": {"A": torch_randn(1, 10), "B": torch_randn(1, 10)}}
            metered_model._ipt = multiple_tensor_ipt
            metered_model._ipt2device()
            mock_to.assert_not_called()
        
        # mixed device, will move all tensor to model's device
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            multiple_tensor_ipt = {"args": (torch_randn(1, 10), ),
                                   "kwargs": {"A": torch_randn(1, 10), 
                                              "B": torch_randn(1, 10, device=tc_device("cuda:0"))}}
            metered_model._ipt = multiple_tensor_ipt
            metered_model._ipt2device()
            assert mock_to.call_count == 3
            assert metered_model.ipt["kwargs"]["B"].device.type == "cpu"
        
        # different device with model, will move all tensor to model's device
        with patch("torch.Tensor.to", side_effect=to_method) as mock_to:
            multiple_tensor_ipt = {"args": (torch_randn(1, 10, device=tc_device("cuda:0")), ),
                                   "kwargs": {"A": torch_randn(1, 10, device=tc_device("cuda:0"))}}
            metered_model._ipt = multiple_tensor_ipt
            metered_model._ipt2device()
            assert mock_to.call_count == 2
            assert metered_model.ipt["args"][0].device.type == "cpu"
            assert metered_model.ipt["kwargs"]["A"].device.type == "cpu"
    
    @pytest.mark.parametrize(
        argnames=("origin", "new", "expected"), 
        argvalues=[
            # empty
            ({"args": tuple(), "kwargs": {}}, 
             {"args": (1,), "kwargs": {}}, True),
            
            # different number of anonymous args
            ({"args": (1,)}, {"args": (1, 2)}, True),
            
            # same number but different inner value
            # different type in same position
            ({"args": (1, 2)}, {"args": (1., 2)}, True),
            
            # different shape of tensor in same position
            ({"args": (torch_randn(1, 10), )}, {"args": (torch_randn(1, 20), )}, True),
            
            # different dtype of tensor in same position
            ({"args": (torch_randn(1, 10, dtype=float16), )}, 
             {"args": (torch_randn(1, 10, dtype=float32), )}, True),
            
            # different value in same position
            ({"args": (1, 2)}, {"args": (2, 2)}, True),
            
            # all same input without tensor data
            ({"args": (1, 2), "kwargs": {}}, 
             {"args": (1, 2), "kwargs": {}}, False),
            
            # all same input with tensor data of same shape and same dtype
            ({"args": (torch_randn(1, 10, dtype=float32), ), "kwargs": {}},
             {"args": (torch_randn(1, 10, dtype=float32), ), "kwargs": {}}, False),
            
            # different number of keyword args
            ({"args": tuple(), "kwargs": {"a": 1, "b": 2}}, 
             {"args": tuple(), "kwargs": {"a": 1}}, True),
            
            # same number but different keys
            ({"args": tuple(), "kwargs": {"a": 1, "b": 2}}, 
             {"args": tuple(), "kwargs": {"a": 1, "c": 2}}, True),
            
            # same number but different values
            # different value type of same key
            ({"args": tuple(), "kwargs": {"a": 1}}, 
             {"args": tuple(), "kwargs": {"a": 1.}}, True),
            
            # different shape of tensor in value of same key
            ({"args": tuple(), "kwargs": {"a": torch_randn(1, 10)}}, 
             {"args": tuple(), "kwargs": {"a": torch_randn(1, 20)}}, True),
            
            # different dtype of tensor in value of same key
            ({"args": tuple(), "kwargs": {"a": torch_randn(1, 10, dtype=float16)}},
             {"args": tuple(), "kwargs": {"a": torch_randn(1, 10, dtype=float32)}}, True),
            
            # different value of same key
            ({"args": tuple(), "kwargs": {"a": 1}}, 
             {"args": tuple(), "kwargs": {"a": 2}}, True),
            
            # all same input without tensor data
            ({"args": tuple(), "kwargs": {"b": 2, "c": 3}}, 
             {"args": tuple(), "kwargs": {"b": 2, "c": 3}}, False),
            
            # all same input with tensor data of same shape and same dtype
            ({"args": tuple(), "kwargs": {"d": torch_randn(1, 10, dtype=float32)}},
             {"args": tuple(), "kwargs": {"d": torch_randn(1, 10, dtype=float32)}}, False)            
            
        ]
    )
    def test_is_ipt_changed(self, origin, new, expected, monkeypatch) -> None:
        """Test the logic of __ipt_is_changed method"""
        
        metered_model = Meter(ExampleModel())
        target_method = metered_model._Meter__is_ipt_changed
            
        monkeypatch.setattr(metered_model, "_ipt", origin)
        assert target_method(new) is expected           
    
    def test_repr(self) -> None:
        """Test correct representation of Meter object"""
        
        metered_model = Meter(ExampleModel())
        
        mock_optree = MagicMock()
        mock_optree.__repr__ = lambda _: "model_info"
        
        mock_device = MagicMock()
        mock_device.__repr__ = lambda _: "device_info"
        
        with patch.object(metered_model, "optree", new=mock_optree), \
             patch("torchmeter.core.Meter.device", new=mock_device):
                        
            res = str(metered_model)
                        
            assert res == "Meter(model=model_info, device=device_info)"
    
    def test_tree_fold_repeat(self) -> None:
        """Test whether the `tree_fold_repeat` property is set and retrieved correctly."""
        
        metered_model = Meter(ExampleModel())
        
        assert hasattr(metered_model, "tree_fold_repeat")
        
        # retrieve
        assert metered_model.tree_fold_repeat == __cfg__.tree_fold_repeat
        
        # valid set
        metered_model.tree_fold_repeat = False
        assert metered_model.tree_fold_repeat is False
        assert __cfg__.tree_fold_repeat is False
        
        # invalid set
        with pytest.raises(TypeError):
            metered_model.tree_fold_repeat = 1

    @pytest.mark.parametrize(
        argnames=("attr_name", "upper_bound"),
        argvalues=[
            ("tree_levels_args", "tree_renderer.tree_levels_args"),
            ("tree_repeat_block_args", "tree_renderer.repeat_block_args"),
            ("table_display_args", "table_renderer.tb_args"),
            ("table_column_args", "table_renderer.col_args")
        ]
    )
    def test_setting_related_property(self, attr_name, upper_bound) -> None:
        """Test the setting related properties are set and retrieved correctly"""           

        from operator import attrgetter
        
        metered_model = Meter(ExampleModel())
        
        upper_getter = attrgetter(upper_bound)
        
        assert getattr(metered_model, attr_name) is upper_getter(metered_model)
    
    @patch("torchmeter.config.FlagNameSpace.mark_unchange")
    @patch("torchmeter.core.__cfg__.tree_levels_args.is_change")
    @patch("torchmeter.core.__cfg__.tree_repeat_block_args.is_change")
    def test_structure(self, 
                       mock_rpbk_change, mock_level_change, 
                       mock_mark_unchange, monkeypatch) -> None:
        """Test the rendered tree is correctly cached until some settings are changed"""

        metered_model = Meter(ExampleModel())
        
        mock_tree_renderer = MagicMock(spec=TreeRenderer)
        # overwrite tree_renderer()
        mock_tree_renderer.return_value = "re-render_tree" 
        # overwrite tree_renderer property with mock object
        monkeypatch.setattr(metered_model, "tree_renderer", mock_tree_renderer)
                
        # verify if the fold tree is cached
        with monkeypatch.context() as m:
            m.setattr(core_cfg, "tree_fold_repeat", True)
            # overwrite render result
            mock_tree_renderer.render_fold_tree = "rendered_fold_tree"
            
            # no change, no need to re-render
            mock_rpbk_change.return_value = False
            mock_level_change.return_value = False
            assert metered_model.structure == "rendered_fold_tree"
            mock_mark_unchange.assert_not_called()
                
            # only repeat block args changed, need to re-render
            mock_rpbk_change.return_value = True
            mock_level_change.return_value = False
            assert metered_model.structure == "re-render_tree"
            mock_mark_unchange.assert_called_once()
            mock_mark_unchange.reset_mock()
            
            # only level args changed, need to re-render
            mock_rpbk_change.return_value = False
            mock_level_change.return_value = True
            assert metered_model.structure == "re-render_tree"
            mock_mark_unchange.assert_called_once()
            mock_mark_unchange.reset_mock()
            
            # both settings changed, need to re-render
            mock_rpbk_change.return_value = True
            mock_level_change.return_value = True
            assert metered_model.structure == "re-render_tree"
            assert mock_mark_unchange.call_count == 2
            mock_mark_unchange.reset_mock()
        
        # verify if the unfold tree is cached
        with monkeypatch.context() as m:
            m.setattr(core_cfg, "tree_fold_repeat", False)
            # overwrite render result
            mock_tree_renderer.render_unfold_tree = "rendered_unfold_tree"
            
            # no change, no need to re-render
            mock_rpbk_change.return_value = False
            mock_level_change.return_value = False
            assert metered_model.structure == "rendered_unfold_tree"
            mock_mark_unchange.assert_not_called()
                
            # only repeat block args changed, no need to re-render
            mock_rpbk_change.return_value = True
            mock_level_change.return_value = False
            assert metered_model.structure == "rendered_unfold_tree"
            mock_mark_unchange.assert_not_called()
            
            # only level args changed, need to re-render
            mock_rpbk_change.return_value = False
            mock_level_change.return_value = True
            assert metered_model.structure == "re-render_tree"
            mock_mark_unchange.assert_called_once()
            mock_mark_unchange.reset_mock()
            
            # both settings changed, need to re-render
            mock_rpbk_change.return_value = True
            mock_level_change.return_value = True
            assert metered_model.structure == "re-render_tree"
            mock_mark_unchange.assert_called_once()
            mock_mark_unchange.reset_mock()
    
    @patch("torchmeter.statistic.ParamsMeter.measure")
    def test_param_property(self, mock_measure) -> None:
        """Test the parameter measurement result is retrieved and cached correctly"""
        
        metered_model = Meter(ExampleModel())
        assert metered_model._Meter__measure_param is False
        
        # verify the measurement is triggered for all operationnode
        res = metered_model.param
        assert isinstance(res, ParamsMeter)
        assert mock_measure.call_count == len(metered_model.subnodes)
        assert metered_model._Meter__measure_param is True
        
        # verify the result is cached
        mock_measure.reset_mock()
        res2 = metered_model.param
        assert res2 is res
        mock_measure.assert_not_called()
    
    @patch("torchmeter.core.Meter._ipt2device")
    @patch("torchmeter.statistic.CalMeter.measure")
    def test_cal_property(self, mock_measure, mock_ipt2device) -> None:
        """Test the calculation measurement result is retrieved and cached correctly"""
        
        metered_model = Meter(ExampleModel())
        assert metered_model._Meter__measure_cal is False
        
        # mock a RemovableHandle object
        mock_handle = MagicMock(spec=RemovableHandle)
        mock_handle.remove.return_value = "removed"
        mock_measure.return_value = mock_handle
        
        # verify access the property when the input is unknown
        with pytest.raises(RuntimeError):
            metered_model.cal
        
        # verify auto move input the model's device
        # verify the measurement is triggered for all operationnode
        metered_model._ipt = {"args": tuple(), "kwargs": {"ipt": torch_randn(1, 10)}}
        res = metered_model.cal
        mock_ipt2device.assert_called_once()
        assert isinstance(res, CalMeter)
        assert metered_model._Meter__measure_cal is True
        assert mock_measure.call_count == len(metered_model.subnodes)
        assert mock_handle.remove.call_count == len(metered_model.subnodes)
        
        # verify the result is cached
        mock_measure.reset_mock()
        mock_handle.reset_mock()
        res2 = metered_model.cal
        assert res2 is res
        mock_measure.assert_not_called()
        mock_handle.remove.assert_not_called()

    @patch("torchmeter.core.Meter._ipt2device")
    @patch("torchmeter.statistic.MemMeter.measure")
    def test_mem_property(self, mock_measure, mock_ipt2device) -> None:
        """Test the memory-access measurement result is retrieved and cached correctly"""
        
        metered_model = Meter(ExampleModel())
        assert metered_model._Meter__measure_mem is False
        
        # mock a RemovableHandle object
        mock_handle = MagicMock(spec=RemovableHandle)
        mock_handle.remove.return_value = "removed"
        mock_measure.return_value = mock_handle
        
        # verify access the property when the input is unknown
        with pytest.raises(RuntimeError):
            metered_model.mem
        
        # verify auto move input the model's device
        # verify the measurement is triggered for all operationnode
        metered_model._ipt = {"args": tuple(torch_randn(1, 10),), "kwargs": {}}
        res = metered_model.mem
        mock_ipt2device.assert_called_once()
        assert isinstance(res, MemMeter)
        assert metered_model._Meter__measure_mem is True
        assert mock_measure.call_count == len(metered_model.subnodes)
        assert mock_handle.remove.call_count == len(metered_model.subnodes)
        
        # verify the result is cached
        mock_measure.reset_mock()
        mock_handle.reset_mock()
        res2 = metered_model.mem
        assert res2 is res
        mock_measure.assert_not_called()
        mock_handle.remove.assert_not_called()

    @patch("torchmeter.core.Meter._ipt2device")
    @patch("torchmeter.statistic.IttpMeter.measure")
    def test_ittp_property(self, mock_measure, mock_ipt2device, monkeypatch) -> None:
        """Test the inference time & throughput measurement result is retrieved correctly"""
        
        metered_model = Meter(ExampleModel())
        
        # mock a RemovableHandle object
        mock_handle = MagicMock(spec=RemovableHandle)
        mock_handle.remove.return_value = "removed"
        mock_measure.return_value = mock_handle
        
        # verify access the property when the input is unknown
        with pytest.raises(RuntimeError):
            metered_model.ittp
        
        metered_model._ipt = {"args": tuple(torch_randn(1, 10),), "kwargs": {}}
        
        # invalid warmup type
        with pytest.raises(TypeError):
            monkeypatch.setattr(metered_model, "ittp_warmup", "invalid")
            metered_model.ittp
        
        # invalid warmup value
        with pytest.raises(ValueError):
            monkeypatch.setattr(metered_model, "ittp_warmup", -1)
            metered_model.ittp
        
        monkeypatch.undo()
        
        # normal usage
        with patch.object(metered_model.model, "forward", wraps=metered_model.model.forward) as mock_call:
            monkeypatch.setattr(metered_model, "ittp_warmup", 10)
            res = metered_model.ittp

            # verify auto move input the model's device
            mock_ipt2device.assert_called_once()

            # verify the model is warmup for specified times before measurement
            assert mock_call.call_count == 10 + 1 # warmup + 1 feed-forward

            # verify the measurement is triggered for all operationnode
            assert isinstance(res, IttpMeter)
            assert mock_measure.call_count == len(metered_model.subnodes)
            assert mock_handle.remove.call_count == len(metered_model.subnodes)
            
            # verify the result is not cached
            mock_ipt2device.reset_mock()
            mock_call.reset_mock()
            mock_measure.reset_mock()
            mock_handle.reset_mock()
            res2 = metered_model.ittp
            assert res2 is res
            mock_ipt2device.assert_called_once()
            assert mock_call.call_count == 10 + 1
            assert mock_measure.call_count == len(metered_model.subnodes)
            assert mock_handle.remove.call_count == len(metered_model.subnodes)

    @patch("torchmeter.utils.data_repr", wraps=data_repr)
    @patch("torchmeter.utils.indent_str", wraps=indent_str)
    def test_model_info_property(self, mock_indent_str, mock_data_repr, monkeypatch) -> None:
        """Test the model_info property is set and retrieved correctly"""
        
        from dataclasses import dataclass

        from numpy import ones as np_ones
        
        @dataclass
        class TextData():
            model: str       # type: ignore
            device: str      # type: ignore
            forward_sig: str # type: ignore
            input: str       # type: ignore
        
        def text_resolve(info: Text) -> TextData:
            plain_str = info.plain
            infos = plain_str.split("\n")
            return TextData(model=infos[0], device=infos[1], 
                            forward_sig=infos[2], input="\n".join((infos[3:])))

        def reset_all_mock() -> None:
            mock_data_repr.reset_mock()
            mock_indent_str.reset_mock()

        metered_model = Meter(ExampleModel())
        
        # verify output type
        direct_res = metered_model.model_info
        assert isinstance(direct_res, Text)
        
        # verify model name 
        monkeypatch.setattr(metered_model.optree.root, "name", "test_name")
        res = text_resolve(metered_model.model_info)
        assert "test_name" in res.model
        
        # verify device
        # cpu
        with patch("torchmeter.core.Meter.device", new=tc_device("cpu")):
            res = text_resolve(metered_model.model_info)
            assert "cpu" in res.device
        
        # gpu
        with patch("torchmeter.core.Meter.device", new=tc_device("cuda:20")):
            res = text_resolve(metered_model.model_info)
            assert "cuda:20" in res.device
        
        # verify forward args representation
        # without args
        monkeypatch.setattr(metered_model.model, "forward", lambda: None)
        res = text_resolve(metered_model.model_info)
        assert "forward(self)" in res.forward_sig

        # with multiple args
        monkeypatch.setattr(metered_model.model, "forward", lambda a, b, c=2: None)
        res = text_resolve(metered_model.model_info)
        assert "forward(self, a, b, c)" in res.forward_sig
        
        # with variable args
        monkeypatch.setattr(metered_model.model, "forward", lambda a, *var_position, **var_kw: None)
        res = text_resolve(metered_model.model_info)
        assert "forward(self, a, var_position, var_kw)" in res.forward_sig
        
        # verify input representation
        # empty input
        reset_all_mock()
        metered_model._ipt = {"args": tuple(), "kwargs": {}}
        res = text_resolve(metered_model.model_info)
        mock_data_repr.assert_not_called()
        mock_indent_str.assert_called_once()
        assert "Not Provided" in res.input
        
        # any input (all have pass-in value)
        reset_all_mock()
        metered_model._ipt = {"args": (torch_randn(1, 10), 20, 3), "kwargs": {}}
        monkeypatch.setattr(metered_model.model, "forward", lambda a, b, c=2: None)
        res = text_resolve(metered_model.model_info)
        assert mock_data_repr.call_count == 3
        mock_indent_str.assert_called_once()
        assert all(t in res.input for t in ["a = Shape([1, 10])",
                                            "b = 20",
                                            "c = 3"])
        
        # any input (part of them have pass-in value)
        reset_all_mock()
        metered_model._ipt = {"args": (torch_randn(1, 10), 20), "kwargs": {}}
        monkeypatch.setattr(metered_model.model, "forward", lambda a, b, c=2: None)
        res = text_resolve(metered_model.model_info)
        assert mock_data_repr.call_count == 2
        mock_indent_str.assert_called_once()
        assert all(t in res.input for t in ["a = Shape([1, 10])",
                                            "b = 20"]) 
        assert "c = 2" not in res.input
        
        # any input (pass-in value through keyword argument)
        reset_all_mock()
        metered_model._ipt = {"args": tuple(), "kwargs": {"a": torch_randn(1, 10), "b": 20, "c": 20}}
        monkeypatch.setattr(metered_model.model, "forward", lambda a, b, c=2: None)
        res = text_resolve(metered_model.model_info)
        assert mock_data_repr.call_count == 3
        mock_indent_str.assert_called_once()
        assert all(t in res.input for t in ["a = Shape([1, 10])",
                                            "b = 20",
                                            "c = 20"]) 

        # any input (pass-in value through keyword argument and positional argument)
        reset_all_mock()
        metered_model._ipt = {"args": (torch_randn(1, 10), np_ones([3, 4, 5])), "kwargs": {"c": 40}}
        monkeypatch.setattr(metered_model.model, "forward", lambda a, b, c=2: None)
        res = text_resolve(metered_model.model_info)
        assert mock_data_repr.call_count == 3
        mock_indent_str.assert_called_once()
        assert all(t in res.input for t in ["a = Shape([1, 10])",
                                            "b = Shape([3, 4, 5])",
                                            "c = 40"]) 

    @pytest.mark.parametrize(
        argnames="repeat_num", 
        argvalues=[2, 2**2, 2**4, 2**8]
    )
    def test_subnodes(self, repeat_num) -> None:
        """Test the subnodes property is set and retrieved correctly"""
        
        metered_model = Meter(RepeatModel(repeat_nodes=repeat_num), device="cpu")
        assert len(metered_model.subnodes) == repeat_num + 2 # 2: root + modulelist
        
    def test_rebase(self) -> None:
        """Test the logic of rebase method""" 
        
        metered_model = Meter(ExampleModel())
        
        # rebase to root itself, return self directly
        with patch.object(Meter, "__init__", wraps=Meter.__init__) as mock_new: 
            rebase_model = metered_model.rebase("0")
            mock_new.assert_not_called()
            assert rebase_model is metered_model
        
        # rebase to child node
        rebase_model = metered_model.rebase("2.1")
        assert rebase_model.optree.root.type == "Linear"
        
        # invalid argument type
        with pytest.raises(TypeError):
            metered_model.rebase(0)
        
        # invalid argument value
        with pytest.raises(ValueError):
            metered_model.rebase("10")
    
    def test_stat_info(self) -> None:
        """Test the logic of stat_info method"""
        
        metered_model = Meter(ExampleModel())
        metered_model(torch_randn(1, 10))
        metered_model._Meter__has_nocall_nodes = False
        
        # verify output type
        # input a stat name
        with patch.object(ParamsMeter, "crucial_data", 
                          new_callable=PropertyMock) as mock_crucial_data:
            direct_res = metered_model.stat_info("param")
            mock_crucial_data.assert_called_once()
            assert isinstance(direct_res, Text)
        
        # input a stat obj
        with patch.object(CalMeter, "crucial_data", 
                          new_callable=PropertyMock) as mock_crucial_data:
            direct_res = metered_model.stat_info(metered_model.cal)
            mock_crucial_data.assert_called_once()
            assert isinstance(direct_res, Text)
        
        # invalid input type
        with pytest.raises(TypeError):
            metered_model.stat_info(["param", "cal"])
        
        # verify ittp special field
        with patch.object(IttpMeter, "crucial_data", 
                          new_callable=PropertyMock) as mock_crucial_data:
            direct_res = metered_model.stat_info("ittp")
            mock_crucial_data.assert_called_once()
            assert "Benchmark Times" in direct_res.plain
        
        # verify content is the crucial data of the specified stat
        with patch.object(MemMeter, "crucial_data", 
                          new_callable=PropertyMock) as mock_crucial_data:
            direct_res = metered_model.stat_info("mem")
            mock_crucial_data.assert_called_once()
    
    def test_stat_info_warning(self, monkeypatch) -> None:
        """Test the logic of generating warning info"""
        
        class NotSupportModel(nn.Module):
            def __init__(self) -> None:
                super(NotSupportModel, self).__init__()
                self.layer0 = nn.Linear(10, 5)
                self.layer1 = nn.AdaptiveAvgPool1d(1)

            def forward(self, x):
                return self.layer1(x)
        
        metered_model = Meter(NotSupportModel(), device="cpu")
        # set ittp_warmup and ittp_benchmark_time to a lower value to save time
        metered_model.ittp_warmup = 2
        metered_model.ittp_benchmark_time = 2
        metered_model(torch_randn(1, 10, 5))
        
        nocall_flag = lambda: metered_model._Meter__has_nocall_nodes
        notsupport_flag = lambda: metered_model._Meter__has_not_support_nodes
        
        assert nocall_flag() is None
        assert notsupport_flag() is None
        
        # only take effect when the stat is cal or mem
        metered_model.stat_info("param", show_warning=True)
        assert nocall_flag() is None
        assert notsupport_flag() is None
        
        metered_model.stat_info("ittp", show_warning=True)
        assert nocall_flag() is None
        assert notsupport_flag() is None
        
        metered_model.stat_info("mem", show_warning=True)
        assert nocall_flag() is True
        assert notsupport_flag() is None
        
        metered_model._Meter__has_nocall_nodes = None
        metered_model.stat_info("cal", show_warning=True)
        assert nocall_flag() is True
        assert notsupport_flag() is True
        
        # verify show_warning option
        metered_model._Meter__has_nocall_nodes = None
        metered_model._Meter__has_not_support_nodes = None
        metered_model.stat_info("cal", show_warning=False)
        assert nocall_flag() is None
        assert notsupport_flag() is None
                
        # verify __has_nocall_nodes flag is properly set &
        # verify cache of __has_nocall_nodes 
        with patch.object(MemMeter, "crucial_data",
                          new_callable=PropertyMock) as mock_crucial_data:
            # when there is no nocalled nodes (crucial_data is mocked and will raise error)
            metered_model.stat_info("mem", show_warning=True)
            assert mock_crucial_data.call_count == 4 # 1: provide info to info_ls; 3: traverse all 3 nodes
            assert nocall_flag() is False
            
            # when the second traversal node is no called
            mock_crucial_data.reset_mock()
            metered_model._Meter__has_nocall_nodes = None
            mock_crucial_data.side_effect = [{}, True, RuntimeError]
            metered_model.stat_info("mem", show_warning=True)
            assert mock_crucial_data.call_count == 3 # 1: provide info to info_ls; 2: traverse the leading 2 nodes
            assert nocall_flag() is True
            
            # verify cache of __has_nocall_nodes
            mock_crucial_data.reset_mock()
            mock_crucial_data.side_effect = [{}]
            metered_model.stat_info("mem", show_warning=True)
            mock_crucial_data.assert_called_once() # 1: provide info to info_ls; 0: no need to traverse due to the cache

        # verify __has_not_support_nodes flag is properly set &
        # verify cache of __has_not_support_nodes
        with patch.object(OperationNode, "cal", 
                          new_callable=PropertyMock) as mock_cal:
            
            mock_cal_instance = MagicMock(spec=CalMeter)
            type(mock_cal_instance).name = PropertyMock(return_value="cal")
            mock_cal.return_value = mock_cal_instance
            
            # when all nodes are supported
            mock_cal_instance.is_not_supported = False
            metered_model.stat_info("cal", show_warning=True)
            assert notsupport_flag() is False

            # when any node is not supported
            mock_cal_instance.is_not_supported = True
            metered_model._Meter__has_not_support_nodes = None
            metered_model.stat_info("cal", show_warning=True)
            assert notsupport_flag() is True
        
            # verify cache of __has_not_support_nodes
            mock_cal.reset_mock()
            metered_model._Meter__has_not_support_nodes = None
            metered_model.stat_info("cal", show_warning=True)
            assert mock_cal.call_count == 2 # 1: provide info to info_ls; 1: check each node.cal.is_not_supported
            
            mock_cal.reset_mock()
            metered_model.stat_info("cal", show_warning=True)
            assert mock_cal.call_count == 1 # 1: provide info to info_ls
        
        # verify warning info is added to info_ls correctly
        with patch.object(OperationNode, "cal", 
                          new_callable=PropertyMock) as mock_cal, \
             patch.object(CalMeter, "crucial_data",
                          new_callable=PropertyMock) as mock_crucial_data:
            
            mock_cal_instance = MagicMock(spec=CalMeter)
            type(mock_cal_instance).name = PropertyMock(return_value="cal")
            type(mock_cal_instance).crucial_data = mock_crucial_data
            mock_cal.return_value = mock_cal_instance
            
            # when there is no warning info, i.e. no nocalled nodes and not-supported nodes
            mock_crucial_data.side_effect = [dict()]
            mock_cal_instance.is_not_supported = False
            metered_model._Meter__has_nocall_nodes = None
            metered_model._Meter__has_not_support_nodes = None
            res = metered_model.stat_info("cal", show_warning=True).plain
            assert "Warning" not in res
            
            # when there are only nocall nodes, but all nodes are supported
            mock_crucial_data.side_effect = [dict(), RuntimeError]
            mock_cal_instance.is_not_supported = False
            metered_model._Meter__has_nocall_nodes = None
            metered_model._Meter__has_not_support_nodes = None
            res = metered_model.stat_info("cal", show_warning=True).plain
            assert "Warning" in res
            assert "not called" in res
            assert "don't support" not in res
            
            # when there are only not-supported nodes, but all nodes are called
            mock_crucial_data.side_effect = [dict()] * 10
            mock_cal_instance.is_not_supported = True
            metered_model._Meter__has_nocall_nodes = None
            metered_model._Meter__has_not_support_nodes = None
            res = metered_model.stat_info("cal", show_warning=True).plain
            assert "Warning" in res
            assert "not called" not in res
            assert "don't support" in res
            
            # when nocall nodes and not-supported nodes exist in the same time
            mock_crucial_data.side_effect = [dict(), RuntimeError]
            mock_cal_instance.is_not_supported = True
            metered_model._Meter__has_nocall_nodes = None
            metered_model._Meter__has_not_support_nodes = None
            res = metered_model.stat_info("cal", show_warning=True).plain
            assert "Warning" in res
            assert "not called" in res
            assert "don't support" in res
         
    def test_overview(self) -> None:
        """Test the logic of overview method"""
        
        from rich.panel import Panel
        from rich.columns import Columns
        
        metered_model = Meter(ExampleModel())
        # set ittp_warmup and ittp_benchmark_time to a lower value to save time
        metered_model.ittp_warmup = 2
        metered_model.ittp_benchmark_time = 2
        metered_model(torch_randn(1, 10))
        
        order_getter = lambda res: [p._title.plain.split(" INFO")[0].strip().lower() 
                                    for p in res.renderables]
        
        # verify output type
        res = metered_model.overview()
        assert isinstance(res, Columns)
        
        # verify default order is the order defined in OperationNode.statistics
        res_order = order_getter(res)
        assert res_order == ["model", *list(OperationNode.statistics)]
        
        # verify custom order
        res = metered_model.overview("param", "mem")
        res_order = order_getter(res)
        assert len(res.renderables) == 3
        assert res_order == ["model", "param", "mem"]
        
        # invalid stat name
        with pytest.raises(ValueError):
            metered_model.overview("invalid_stat")
        
        # verify content
        with patch.object(metered_model, "stat_info",
                          wraps=metered_model.stat_info) as mock_stat_info:
            # whether model info always exists, see the second section above
            
            # each item is a panel of stat_info
            res = metered_model.overview("mem", "cal")
            assert all(isinstance(p, Panel) for p in res.renderables)
            assert mock_stat_info.call_count == 2
            mock_stat_info.assert_any_call("mem", show_warning=True)
            mock_stat_info.assert_any_call("cal", show_warning=True)
            
            # default setting is True
            metered_model.overview("param", "cal")
            call_args_ls = mock_stat_info.call_args_list
            assert all(call_args.kwargs["show_warning"] for call_args in call_args_ls)
            
            # custom setting
            mock_stat_info.reset_mock()
            metered_model.overview("param", "cal", show_warning=False)
            call_args_ls = mock_stat_info.call_args_list
            assert all(not call_args.kwargs["show_warning"] for call_args in call_args_ls)
    
    def test_table_cols(self) -> None:
        """Test the logic of table_cols method"""
        
        from polars import DataFrame
        
        metered_model = Meter(ExampleModel())
        
        # invalid stat name
        with pytest.raises(KeyError):
            metered_model.table_cols("invalid_stat")
        
        # invalid input type
        with pytest.raises(TypeError):
            metered_model.table_cols(["param", "cal"])
        
        # verify the result got from a empty dict of dataframe
        metered_model.table_renderer.stats_data["param"] = DataFrame()
        cols = metered_model.table_cols("param")
        assert cols == ParamsMeter.detail_val_container._fields
        
        # verify the result got from a non-empty dict of dataframe
        metered_model.table_renderer.stats_data["cal"] = DataFrame({"test_A": [1, 2], "test_B": [1, 2]})
        cols = metered_model.table_cols("cal")
        assert cols == ("test_A", "test_B")

    def test_profile_iopt(self) -> None:
        """Test the type and content of input and output."""
        
        from polars import DataFrame
        from rich.table import Table
        
        metered_model = Meter(ExampleModel())
        
        # invalid input type
        with pytest.raises(TypeError):
            metered_model.profile(stat_name={"cal", "param"})
        
        # invalid input stat name
        with pytest.raises(AttributeError):
            metered_model.profile(stat_name="invalid_stat")

        # verify output
        output_a, output_b = metered_model.profile("param", show=False)
        assert isinstance(output_a, Table)
        assert isinstance(output_b, DataFrame)
    
    @patch("torchmeter.core.render_perline")
    def test_profile_option(self, mock_render, capsys) -> None:
        """Test the logic of different profile option."""

        lambda: capsys.readouterr().out.strip().split("\n")

        metered_model = Meter(ExampleModel())
        model_structure = metered_model.structure
        
        # show = False, no_tree = False
        mock_render.reset_mock()
        metered_model.profile("param", show=False, no_tree=False)
        mock_render.assert_not_called()
        
        # show = False, no_tree = True
        mock_render.reset_mock()
        metered_model.profile("param", show=False, no_tree=True)
        mock_render.assert_not_called()
        
        with patch.object(Meter, "structure", 
                          new_callable=PropertyMock,
                          return_value=model_structure) as mock_structure:
            # show = True, no_tree = False
            mock_render.reset_mock()
            mock_structure.reset_mock()
            metered_model.profile("param", show=True, no_tree=False)
            mock_structure.assert_called_once()
            mock_render.assert_called_once()
        
            # show = True, no_tree = True
            mock_render.reset_mock()
            mock_structure.reset_mock()
            metered_model.profile("param", show=True, no_tree=True)
            mock_structure.assert_not_called()
            mock_render.assert_called_once()
    
    @patch("torchmeter.core.render_perline")
    def test_profile_horizon_gap(self, mock_render) -> None:
        """Test the gap between tree and table is as same as the one in config"""
        
        origin_init = Layout.__init__

        def layout_init_wrapper(self, *args, **kwargs) -> None:
            origin_init(self, *args, **kwargs)  

        metered_model = Meter(ExampleModel())
        model_structure = metered_model.structure
        
        console = get_console()
        tree_width = console.measure(model_structure).maximum
        
        # negative gap
        with pytest.raises(ValueError):
            __cfg__.combine.horizon_gap = -10
            metered_model.profile("param", show=True, no_tree=False)

        # verify custom gap 
        __cfg__.combine.horizon_gap = 10
        with patch.object(Layout, "__init__", autospec=True, 
                          side_effect=layout_init_wrapper) as mock_init_layout:
            metered_model.profile("param", show=True, no_tree=False)
            kwargs_dict = mock_init_layout.call_args_list[1].kwargs
            assert kwargs_dict["size"] == tree_width + 10
    
    @patch("torchmeter.core.render_perline")
    def test_profile_content(self, mock_render) -> None:
        """Test the logic of generating the profile content."""
        
        from rich.rule import Rule
        from rich.table import Table
        from rich.columns import Columns
        
        origin_init = Layout.__init__

        def layout_init_wrapper(self, *args, **kwargs) -> None:
            origin_init(self, *args, **kwargs)  
        
        console = get_console()
        metered_model = Meter(ExampleModel())
        tree = metered_model.structure
        tree_width = console.measure(tree).maximum
        
        renderable_getter = lambda c: c.args[0]._renderable
        
        # verify main content generation
        with patch.object(Layout, "__init__", autospec=True, 
                          side_effect=layout_init_wrapper) as mock_init_layout,\
             patch.object(metered_model, "stat_info",
                          wraps=metered_model.stat_info) as mock_stat_info:
            # no tree, main content is a Table
            metered_model.profile("param", show=True, no_tree=True)
            main_content = renderable_getter(mock_init_layout.call_args_list[-2])
            
            assert mock_init_layout.call_count == 3
            assert isinstance(main_content, Table)
            
            # with tree, main content is a Layout with two columns
            mock_init_layout.reset_mock()
            tb, _ = metered_model.profile("param", show=True, no_tree=False)
            main_content = renderable_getter(mock_init_layout.call_args_list[-2])
            
            assert mock_init_layout.call_count == 6
            assert isinstance(main_content, Layout)
            assert len(main_content._children) == 2
            
            assert main_content["left"]._renderable is tree
            assert main_content["right"]._renderable is tb
            assert main_content["left"].size == tree_width + __cfg__.combine.horizon_gap
        
            # verify footer generation
            footer = renderable_getter(mock_init_layout.call_args_list[-1])
            assert isinstance(footer, Columns)
            assert len(footer.renderables) == 2
            assert all(isinstance(ctt, Text) for ctt in footer.renderables)
            mock_stat_info.assert_called_with(stat_or_statname=ANY, show_warning=False)
            
            assert isinstance(footer.title, Rule)
        
    @patch("torchmeter.core.render_perline")
    def test_profile_console_management(self, mock_render, monkeypatch) -> None:
        """Test the rendering interactive logic related to console size"""
        
        from rich.console import Console
        
        console = get_console()
        metered_model = Meter(ExampleModel())
        
        # verify auto show_lines when there is no enough space for table
        # when the table width is smaller than the terminal width
        monkeypatch.setattr(console, "width", float("inf"))
        tb, _ = metered_model.profile("param", show=True, no_tree=True)
        assert tb.show_lines is False
        
        # when the table width exceeds the terminal width
        monkeypatch.setattr(console, "width", console.measure(tb).maximum - 10)
        tb, _ = metered_model.profile("param", show=True, no_tree=False)
        assert tb.show_lines is True
        
        # verify minimal console width error
        monkeypatch.setattr(console, "width", 5)
        with pytest.raises(RuntimeError):
            metered_model.profile("param", show=True, no_tree=False)
                
        monkeypatch.setattr(console, "width", 1)
        with pytest.raises(RuntimeError):
            metered_model.profile("param", show=True, no_tree=False)
    
        # verify console size change and restore
        # init a large enough console with size 120x60
        monkeypatch.setattr(console, "width", 120)
        monkeypatch.setattr(console, "height", 60)
        origin_width, origin_height = console.width, console.height
        
        with patch.object(Console, "width", new_callable=PropertyMock,
                          return_value=origin_width) as mock_console_width, \
             patch.object(Console, "height", new_callable=PropertyMock,
                          return_value=origin_height) as mock_console_height, \
             patch("rich.layout.Layout.split_column", wraps=Layout().split_column) as mock_split_col:

            metered_model.profile("param", show=True, no_tree=True)
            upper_layout, down_layout = mock_split_col.call_args.args
            content_width = console.measure(upper_layout._renderable).maximum
            content_height = upper_layout.size + down_layout.size
            
            is_empty_call = lambda c: not len(c.args) and not len(c.kwargs)
            
            for mock_size_attr, origin_val, content_val in zip(
                [mock_console_width, mock_console_height],
                [origin_width, origin_height],
                [content_width, content_height]
            ):
                call_ls = mock_size_attr.call_args_list
                setter_calls = [(c_idx, c) for c_idx, c in enumerate(call_ls) 
                               if not is_empty_call(c)]
                # 1: set to canvas size; 1: restore
                assert len(setter_calls) == 2 
                
                # the restore happen right after it is set
                assert setter_calls[1][0] == setter_calls[0][0] + 1 
                
                # set to the canvas corresponding size, here the canvas only contains a table
                assert setter_calls[0][1].args[0] == content_val

                # verify if restore to the original size   
                assert setter_calls[1][1].args[0] == origin_val     

        # verify console size restore when the rendering is interrupted      
        mock_render.side_effect = KeyboardInterrupt("Simulated interrupt")
        
        with patch.object(Console, "width", new_callable=PropertyMock,
                          return_value=origin_width) as mock_console_width, \
             patch.object(Console, "height", new_callable=PropertyMock,
                          return_value=origin_height) as mock_console_height, \
             patch("rich.layout.Layout.split_column", wraps=Layout().split_column) as mock_split_col:
            
            with pytest.raises(KeyboardInterrupt):
                metered_model.profile("param", show=True, no_tree=True)
            upper_layout, down_layout = mock_split_col.call_args.args
            content_width = console.measure(upper_layout._renderable).maximum
            content_height = upper_layout.size + down_layout.size
            
            is_empty_call = lambda c: not len(c.args) and not len(c.kwargs)
            
            for mock_size_attr, origin_val, content_val in zip(
                [mock_console_width, mock_console_height],
                [origin_width, origin_height],
                [content_width, content_height]
            ):
                call_ls = mock_size_attr.call_args_list
                setter_calls = [(c_idx, c) for c_idx, c in enumerate(call_ls) 
                               if not is_empty_call(c)]
                assert len(setter_calls) == 2 
                assert setter_calls[1][0] == setter_calls[0][0] + 1 
                assert setter_calls[0][1].args[0] == content_val
                assert setter_calls[1][1].args[0] == origin_val
        