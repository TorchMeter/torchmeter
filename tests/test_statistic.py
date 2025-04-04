import warnings
from collections import namedtuple
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import numpy as np
import torch.nn as nn
from pympler.asizeof import asizeof
from torch import ones as torch_ones
from torch import randn as torch_randn
from torch import device as torch_device
from torch.cuda import is_available as is_cuda
from torch import (
    float16 as torch_float16, 
    float64 as torch_float64, 
    int16 as torch_int16, 
    int64 as torch_int64, 
    int8 as torch_int8
)

from torchmeter.engine import (
    OperationNode,
    OperationTree
)
from torchmeter.statistic import (
    UpperLinkData, MetricsData,
    BinaryUnit, CountUnit, TimeUnit, SpeedUnit,
    Statistics, ParamsMeter, CalMeter, MemMeter, IttpMeter
)

pytestmark = pytest.mark.vital
STAT_TESTED_NOW = ""

@pytest.fixture
def empty_model_root():
    model = nn.Sequential()
    optree = OperationTree(model)
    return model, optree.root

@pytest.fixture
def simple_model_root():
    from torch import mean as torch_mean
    
    class SimpleModel(nn.Module):
        def __init__(self):
            super(SimpleModel, self).__init__()
            self.conv = nn.Conv2d(3, 16, 3)
            self.linear = nn.Linear(16, 10)
        
        def forward(self, x):
            conv_res = self.conv(x)
            pool_res = torch_mean(conv_res, dim=(2, 3))
            return self.linear(pool_res)

    model = SimpleModel()
    for param in model.parameters():
        param.requires_grad = False
    model.conv.weight.requires_grad = True
    
    optree = OperationTree(model)
    return model, optree.root

@pytest.fixture
def measured_simple_model(simple_model_root):
    simple_model, simple_oproot = simple_model_root
    stat = getattr(simple_oproot, STAT_TESTED_NOW)
    device = torch_device("cpu")

    if STAT_TESTED_NOW == "ittp":
        repeat = 2
        for child in simple_oproot.childs.values():
            getattr(child, STAT_TESTED_NOW).measure(device=device, repeat=repeat)
        stat.measure(device=device, repeat=repeat)
    else:
        for child in simple_oproot.childs.values():
            getattr(child, STAT_TESTED_NOW).measure()
        stat.measure()

    simple_model(torch_randn(1,3,64,64))

    return simple_model, simple_oproot, stat

@pytest.fixture()
def toggle_to_cal():
    global STAT_TESTED_NOW
    STAT_TESTED_NOW = "cal"
    yield
    STAT_TESTED_NOW = ""

@pytest.fixture()
def toggle_to_mem():
    global STAT_TESTED_NOW
    STAT_TESTED_NOW = "mem"
    yield
    STAT_TESTED_NOW = ""

@pytest.fixture()
def toggle_to_ittp():
    global STAT_TESTED_NOW
    STAT_TESTED_NOW = "ittp"
    yield
    STAT_TESTED_NOW = ""

class ConcreteStat(Statistics):
    detail_val_container = namedtuple('Detail',  # type: ignore
                                      ['field1', 'field2'])  
    overview_val_container = namedtuple('Overview', # type: ignore
                                        ['summary', 'other_field'])    

    def __init__(self) -> None:
        self.StatVal = UpperLinkData(val=50)
    
    @property
    def name(self) -> str:
        return "con_stat"

    @property
    def val(self):
        return self.overview_val_container(summary=100,
                                           other_field=200)

    @property
    def detail_val(self):
        return [self.detail_val_container(1, 2)]

    @property
    def crucial_data(self):
        return {"key": "value"}

    def measure(self): ...


class TestStatistics:
    def test_mandatory_attributes_check(self):
        """Test whether the necessary class properties are implemented."""
        class MissingAll(Statistics):...
        with pytest.raises(AttributeError) as e1:
            MissingAll()
        assert "detail_val_container" in str(e1.value)
        
        class MissingOverviewContainer(Statistics):
            detail_val_container = namedtuple('Detail', ['a'])
        with pytest.raises(AttributeError) as e2:
            MissingOverviewContainer()
        assert "overview_val_container" in str(e2.value)
        
        class MissingDetailContainer(Statistics):
            overview_val_val_container = namedtuple('Detail', ['a'])
        with pytest.raises(AttributeError) as e3:
            MissingDetailContainer()
        assert "detail_val_container" in str(e3.value)
        
    def test_required_method_property(self):
        """Test whether all abstract methods and property are implemented"""
        class InvalidSubclass(Statistics):
            detail_val_container = namedtuple('Detail', ['a'])
            overview_val_container = namedtuple('Overview', ['b'])

        with pytest.raises(TypeError) as e:
            InvalidSubclass()
        
        required = ["name", "val", "detail_val", "crucial_data", "measure"]
        assert all(method in str(e.value) for method in required)

    def test_init_linkdata(self):
        """Test init_linkdata method"""
        # init a upperlinkdata without parent 
        linked_data = ConcreteStat().init_linkdata("StatVal", init_val=100)
        assert linked_data.val == 100
        assert linked_data._UpperLinkData__parent_data is None

        # init a upperlinkdata with parent
        mock_opnode = MagicMock(con_stat=ConcreteStat()) # val=50
        mock_opnode.parent = MagicMock(con_stat=ConcreteStat()) # val=50
        linked_data = mock_opnode.con_stat.init_linkdata("StatVal", init_val=100, 
                                                         opparent=mock_opnode.parent)
        assert linked_data.val == 100
        assert linked_data._UpperLinkData__parent_data is mock_opnode.parent.con_stat.StatVal
        
        linked_data += 50
        assert mock_opnode.parent.con_stat.StatVal.val == 100 # 50 + 50

    def test_repr(self):
        """Test correct representation"""
        # without upperlinkdata 
        stat = ConcreteStat()
        output = repr(stat)
        assert output == (
            "Overview\n"
            "•     summary = 100\n"
            "• other_field = 200\n"
        )
        
        # with upperlinkdata
        with patch.object(ConcreteStat, 'val', 
                          new_callable=PropertyMock) as mock_val:
            mock_val.return_value = stat.overview_val_container(summary=100,
                                                                other_field=stat.StatVal)
            output = repr(stat)
            assert output == (
                "Overview\n"
                "•     summary = 100\n"
                "• other_field = 50.00 = 50.0\n"
            )

            assert mock_val.call_count == 3 # title + 2 fields
        
        # with invalid field
        with patch.object(ConcreteStat, 'ov_fields', 
                          new_callable=PropertyMock) as mock_val:
            mock_val.return_value = ("summary", "invalid_field")

            output = repr(stat)
            assert output == (
                "Overview\n"
                "•       summary = 100\n"
                "• invalid_field = N/A\n"
            )

            assert mock_val.call_count == 2 # max_len + for loop

    def test_tbov_fields(self):
        """Test tb_fields and ov_fields are set correctly"""
        stat = ConcreteStat()
        assert stat.tb_fields == ("field1", "field2")
        assert stat.ov_fields == ("summary","other_field")

    def test_crucial_data(self):
        """Test crucial_data is set correctly"""
        stat = ConcreteStat()
        data = stat.crucial_data
        assert data == {"key":"value"}

class TestParamsMeter:
    def test_cls_variable(self):
        """Test detail_val_container and overview_val_container settings"""
        assert hasattr(ParamsMeter, "detail_val_container")
        dc = ParamsMeter.detail_val_container
        assert all(v is None for v in dc._field_defaults.values())
        
        assert hasattr(ParamsMeter, "overview_val_container")
        oc = ParamsMeter.overview_val_container
        assert all(v is None for v in oc._field_defaults.values())
    
    def test_valid_init(self, simple_model_root):
        """Test valid initialization"""
        model, oproot = simple_model_root
        
        param_meter = oproot.param
        assert param_meter._opnode == oproot
        assert param_meter._model is model
        assert not param_meter.is_measured
        assert not param_meter._ParamsMeter__stat_ls
        
        assert param_meter.name == "param"    
        assert hasattr(param_meter, "RegNum")
        assert isinstance(param_meter.RegNum, UpperLinkData)
        assert param_meter.RegNum.val == 0
        assert param_meter.RegNum._UpperLinkData__parent_data is None
        assert param_meter.RegNum._UpperLinkData__unit_sys is CountUnit
        
        assert hasattr(param_meter, "TotalNum")
        assert isinstance(param_meter.TotalNum, UpperLinkData)
        assert param_meter.TotalNum.val == 0
        assert param_meter.TotalNum._UpperLinkData__parent_data is None
        assert param_meter.TotalNum._UpperLinkData__unit_sys is CountUnit

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            ParamsMeter(opnode="0")

    def test_val_property(self, simple_model_root):
        """Test whether the val property is properly set"""
        simple_model, simple_oproot = simple_model_root
        param_meter = simple_oproot.param
        for child in simple_oproot.childs.values():
            child.param.measure()
        param_meter.measure()
        
        overview = param_meter.val
        assert isinstance(overview, ParamsMeter.overview_val_container)
        assert overview.Operation_Id == "0"
        assert overview.Operation_Name == "SimpleModel"
        assert overview.Operation_Type == "SimpleModel"
        assert overview.Total_Params is param_meter.TotalNum
        assert overview.Learnable_Params is param_meter.RegNum

    def test_crucial_data_format(self, simple_model_root):
        """Test whether the crucial_data is return in correct format"""
        simple_model, simple_oproot = simple_model_root
        param_meter = simple_oproot.param
        crucial_data = param_meter.crucial_data
        assert isinstance(crucial_data, dict)
                
        # verify align
        keys = list(crucial_data.keys())
        assert all(isinstance(k, str) for k in crucial_data.keys())
        assert all(len(k) == len(keys[0]) for k in keys[1:])
        
        # verify value
        assert all(isinstance(v,str) for v in crucial_data.values())

    def test_param_measure(self, empty_model_root, simple_model_root):
        """Test whether the measure method works well"""
        # model without parameters
        empty_model, empty_oproot = empty_model_root
        empty_pm = empty_oproot.param
        empty_pm.measure()
        
        assert empty_pm.is_measured
        assert empty_pm.RegNum.val == 0
        assert empty_pm.TotalNum.val == 0
        
        assert len(empty_pm.detail_val) == 1 
        record = empty_pm.detail_val[0]
        assert record.Operation_Id == "0"
        assert record.Operation_Name == "Sequential"
        assert record.Operation_Type == "Sequential"
        assert record.Numeric_Num.val == 0
        
        # model with parameters
        simple_model, simple_oproot = simple_model_root
        param_meter = simple_oproot.param
        for child in simple_oproot.childs.values():
            child.param.measure()
        param_meter.measure()
        
        assert param_meter.is_measured
        assert all(c.param.is_measured for c in simple_oproot.childs.values())
        
        assert param_meter.RegNum.val == simple_model.conv.weight.numel()
        assert param_meter.TotalNum.val == sum([simple_model.conv.weight.numel(),
                                              simple_model.conv.bias.numel(),
                                              simple_model.linear.weight.numel(),
                                              simple_model.linear.bias.numel()])
        
        assert len(param_meter.detail_val) == 1  # empty record
        assert len(simple_oproot.childs["1"].param.detail_val) == 2  # Conv2d: weight+bias
        assert len(simple_oproot.childs["2"].param.detail_val) == 2  # Linear: weight+bias
        
        records = param_meter.detail_val
        records.extend(simple_oproot.childs["1"].param.detail_val)
        records.extend(simple_oproot.childs["2"].param.detail_val)
        for record in records:
            if record.Param_Name is not None:
                if "weight" in record.Param_Name:
                    assert record.Requires_Grad == ("Conv2d" in record.Operation_Type)
                else:
                    assert record.Requires_Grad is False

    def test_measure_cache(self):
        """Test whether the measure method will be revisited after the first call"""        
        model = nn.Linear(10, 5)
        opnode = OperationNode(module=model)
        pm = ParamsMeter(opnode)
        
        pm.measure()
        initial_total = pm.TotalNum.val
        
        model.weight = nn.Parameter(torch_randn(5, 20))  
        pm._model = model
        pm.measure()
        
        assert pm.TotalNum.val == initial_total

    def test_none_parameter_handling(self):
        """Test whether the None parameter is skipped correctly"""
        
        class BadModule(nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = nn.Parameter(torch_randn(10, 10))
                self.bias = None
        
        mock_opnode = OperationNode(module=BadModule())
        pm = ParamsMeter(mock_opnode)
        
        pm.measure()

        assert len(pm.detail_val) == 1
        assert pm.detail_val[0].Param_Name == "weight"

@pytest.mark.usefixtures("toggle_to_cal")
class TestCalMeter:
    def test_cls_variable(self):
        """Test detail_val_container and overview_val_container settings"""
        assert hasattr(CalMeter, "detail_val_container")
        dc = CalMeter.detail_val_container
        assert all(v is None for v in dc._field_defaults.values())
        
        assert hasattr(CalMeter, "overview_val_container")
        oc = CalMeter.overview_val_container
        assert all(v is None for v in oc._field_defaults.values())
    
    def test_valid_init(self, simple_model_root):
        """Test valid initialization"""
        model, oproot = simple_model_root
        
        cal_meter = oproot.cal
        assert cal_meter._opnode == oproot
        assert cal_meter._model is model
        assert not cal_meter.is_measured
        assert not cal_meter._CalMeter__is_not_supported
        assert not cal_meter._CalMeter__stat_ls
        
        assert cal_meter.name == "cal"   
        
        assert hasattr(cal_meter, "is_not_supported")
        assert not cal_meter.is_not_supported 
        
        assert hasattr(cal_meter, "Macs")
        assert isinstance(cal_meter.Macs, UpperLinkData)
        assert cal_meter.Macs.val == 0
        assert cal_meter.Macs._UpperLinkData__parent_data is None
        assert cal_meter.Macs._UpperLinkData__unit_sys is CountUnit
        assert cal_meter.Macs.none_str == "Not Supported"
        
        assert hasattr(cal_meter, "Flops")
        assert isinstance(cal_meter.Flops, UpperLinkData)
        assert cal_meter.Flops.val == 0
        assert cal_meter.Flops._UpperLinkData__parent_data is None
        assert cal_meter.Flops._UpperLinkData__unit_sys is CountUnit
        assert cal_meter.Flops.none_str == "Not Supported"

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            CalMeter(opnode="0")

    def test_val_property(self, measured_simple_model):
        """Test whether the val property is properly set"""
        *_, cal_meter = measured_simple_model
        
        overview = cal_meter.val
        assert isinstance(overview, CalMeter.overview_val_container)
        assert overview.Operation_Id == "0"
        assert overview.Operation_Name == "SimpleModel"
        assert overview.Operation_Type == "SimpleModel"
        assert overview.MACs is cal_meter.Macs
        assert overview.FLOPs is cal_meter.Flops

    def test_crucial_data_format(self, measured_simple_model):
        """Test whether the crucial_data is return in correct format"""
        *_, cal_meter = measured_simple_model
        crucial_data = cal_meter.crucial_data
        assert isinstance(crucial_data, dict)
                
        # verify align
        keys = list(crucial_data.keys())
        assert all(isinstance(k,str) for k in crucial_data.keys())
        assert all(len(k) == len(keys[0]) for k in keys[1:])
        
        # verify value
        assert all(isinstance(v,str) for v in crucial_data.values())

    @pytest.mark.parametrize(
        argnames=("module", "target_hook"), 
        argvalues=[
            (nn.Sequential(nn.Identity()), "__container_hook"),
            (nn.ModuleList([nn.Identity()]), "__container_hook"), 
            (nn.ModuleDict({"example":nn.Identity()}), "__container_hook"), 

            (nn.Conv1d(10, 5, 3), "__conv_hook"), 
            (nn.Conv2d(10, 5, 3), "__conv_hook"), 
            (nn.Conv3d(10, 5, 3), "__conv_hook"), 

            (nn.Linear(10, 5), "__linear_hook"), 
            
            (nn.BatchNorm1d(10), "__BN_hook"), 
            (nn.BatchNorm2d(10), "__BN_hook"), 
            (nn.BatchNorm3d(10), "__BN_hook"), 
            
            (nn.MaxPool1d(3), "__pool_hook"), 
            (nn.MaxPool2d(3), "__pool_hook"), 
            (nn.MaxPool3d(3), "__pool_hook"),
            (nn.AvgPool1d(3), "__pool_hook"), 
            (nn.AvgPool2d(3), "__pool_hook"), 
            (nn.AvgPool3d(3), "__pool_hook"), 

            (nn.Sigmoid(), "__activate_hook"), 
            (nn.Tanh(), "__activate_hook"),
            (nn.ReLU(), "__activate_hook"),
            (nn.ReLU6(), "__activate_hook"),
            (nn.SiLU(), "__activate_hook"),
            (nn.PReLU(), "__activate_hook"),
            (nn.RReLU(), "__activate_hook"),
            (nn.LeakyReLU(), "__activate_hook"),
            
            (nn.Dropout(0.5), "__not_support_hook"), 
            (nn.AdaptiveAvgPool1d(1), "__not_support_hook"), 
            (nn.Identity(), "__not_support_hook"), 
        ]
    )
    def test_cal_measure(self, module, target_hook):
        """Test whether the measure method works well"""
        opnode = OperationNode(module=module)
        cal_meter = opnode.cal
        cal_meter.measure()
        
        assert cal_meter.is_measured
        assert len(module._forward_hooks) == 1
        assert next(iter(module._forward_hooks.values())).__name__ == target_hook
        
    def test_measure_cache(self, simple_model_root):
        """Test whether the measure method will be revisited after the first call"""
        model, oproot = simple_model_root
        cal_meter = oproot.cal
        
        res = cal_meter.measure()
        assert res is not None
        
        res = cal_meter.measure()
        assert res is None

    def test_valid_access(self, simple_model_root):
        """Test whether the invalid access will be blocked"""
        model, oproot = simple_model_root
        cal_meter = oproot.cal
        
        # access property before measure
        with pytest.raises(AttributeError) as e:
            cal_meter.detail_val
        assert "cal" in str(e.value)
        
        with pytest.raises(AttributeError) as e:
            cal_meter.val
        assert "cal" in str(e.value)

        with pytest.raises(AttributeError) as e:
            cal_meter.crucial_data
        assert "cal" in str(e.value)
            
        # access skipped module after measure
        cal_meter.measure()
        with pytest.raises(RuntimeError):
            cal_meter.detail_val
        
        with pytest.raises(RuntimeError):
            cal_meter.val
        
        with pytest.raises(RuntimeError):
            cal_meter.crucial_data
    
    @pytest.mark.parametrize(
        argnames=("iopt", "expected"),
        argvalues=[
            (torch_randn(3,4,5), "[3, 4, 5]"),
            
            (None, "None"),
            (123, "int"),
            (1.5, "float"),
            (np.array([1,2,3]), "ndarray"),
            
            ((torch_randn(1,2,3),), "[1, 2, 3]"),
            ([torch_randn(4,5,6)], "[4, 5, 6]"),
            ({torch_randn(7,8,9)}, "[7, 8, 9]"),
            ({"k":torch_randn(2,4,6)}, "{str: [2, 4, 6]}"),
            
            ((torch_randn(2,3),)*3, ("([2, 3],\n" 
                                     " [2, 3],\n"
                                     " [2, 3])")),
            ([torch_randn(3,4)]*3, ("([3, 4],\n" 
                                    " [3, 4],\n"
                                    " [3, 4])")),
            ({"k":torch_randn(2,3),
              "l":torch_randn(4,5),
              "m":torch_randn(6,7)}, ("{str: [2, 3],\n"
                                      " str: [4, 5],\n"
                                      " str: [6, 7]}")),
        ]
    ) 
    def test_iopt_repr(self, iopt, expected):
        """Test whether the __iopt_repr method works well"""
        oproot = OperationNode(module=nn.Identity())
        cal_meter = oproot.cal
        iopt_repr = cal_meter._CalMeter__iopt_repr
        
        assert iopt_repr(iopt) == expected        

    @pytest.mark.parametrize(
        argnames=("module", "ipt_shape"),
        argvalues=[
            (nn.Sequential(nn.Identity()), (1, 10)),
            
            (nn.Linear(10, 5), (1, 10)),
            
            (nn.Conv1d(10, 5, 3), (1, 10, 32)),
            (nn.Conv2d(10, 5, 3), (1, 10, 32, 32)),
            (nn.Conv3d(10, 5, 3), (1, 10, 32, 32, 32)),
            
            (nn.MaxPool1d(3), (1, 10, 32)),
            (nn.MaxPool2d(3), (1, 10, 32, 32)),
            (nn.MaxPool3d(3), (1, 10, 32, 32, 32)),
            (nn.AvgPool1d(3), (1, 10, 32)),
            (nn.AvgPool2d(3), (1, 10, 32, 32)),
            (nn.AvgPool3d(3), (1, 10, 32, 32, 32)),
            
            (nn.BatchNorm1d(10), (1, 10, 32)),
            (nn.BatchNorm2d(10), (1, 10, 32, 32)),
            (nn.BatchNorm3d(10), (1, 10, 32, 32, 32)),
            
            (nn.Sigmoid(), (1, 10)),
            (nn.Tanh(), (1, 10)),
            (nn.ReLU(), (1, 10)),
            (nn.ReLU6(), (1, 10)),
            (nn.SiLU(), (1, 10)),
            (nn.PReLU(), (1, 10)),
            (nn.RReLU(), (1, 10)),
            (nn.LeakyReLU(), (1, 10)),
            
            (nn.Dropout(0.5), (1, 10)), 
            (nn.AdaptiveAvgPool1d(1), (1, 32, 8)), 
            (nn.Identity(), (1, 10)), 
        ]
    )
    def test_reaccess_module(self, module, ipt_shape):
        """Test reaccess handling"""
        oproot = OperationTree(module).root
        cal_meter = oproot.cal
        
        cal_meter.measure()
        if not oproot.is_leaf:
            list(map(lambda x:x.cal.measure(), oproot.childs.values()))
        module(torch_randn(*ipt_shape))
        
        assert cal_meter.Macs._UpperLinkData__access_cnt == 1
        assert cal_meter.Flops._UpperLinkData__access_cnt == 1
        
        hook_func = next(iter(module._forward_hooks.values())).__name__
        if "not_support_hook" not in hook_func:
            module(torch_randn(*ipt_shape))
            assert cal_meter.Macs._UpperLinkData__access_cnt == 2
            assert cal_meter.Flops._UpperLinkData__access_cnt == 2
        else:
            assert cal_meter.Macs._UpperLinkData__access_cnt == 1
            assert cal_meter.Flops._UpperLinkData__access_cnt == 1

    @pytest.mark.parametrize(
        argnames=("module", "ipt_shape", "expected_opt_shape",
                  "expected_macs", "expected_flops"),
        argvalues=[
            (nn.Sequential(nn.Identity()), (1, 10), (1, 10), 0, 0),
            (nn.Sequential(nn.Conv2d(3,10,3),
                           nn.Conv2d(10,30,1)), (1, 3, 32, 32), (1, 30, 30, 30), 30**2*10*27+30**3*10, 30**2*20*27+30**3*20),
            
            (nn.Linear(10, 5, bias=True), (1, 10), (1, 5), 5*10, 5*10*2),
            (nn.Linear(10, 5, bias=False), (1, 10), (1, 5), 5*10, 5*10*2-5),
            
            (nn.Conv1d(10, 5, 3, bias=True), (1, 10, 32), (1, 5, 30), 150*30, 150*30*2),
            (nn.Conv1d(10, 5, 3, bias=False), (1, 10, 32), (1, 5, 30), 150*30, 150*30*2-150),
            (nn.Conv2d(10, 5, 3, bias=True), (1, 10, 32, 32), (1, 5, 30, 30), 4500*90, 4500*2*90),
            (nn.Conv2d(10, 5, 3, bias=False), (1, 10, 32, 32), (1, 5, 30, 30), 4500*90, 4500*2*90-4500),
            (nn.Conv3d(10, 5, 3, bias=True), (1, 10, 32, 32, 32), (1, 5, 30, 30, 30), 135000*270, 135000*270*2),
            (nn.Conv3d(10, 5, 3, bias=False), (1, 10, 32, 32, 32), (1, 5, 30, 30, 30), 135000*270, 135000*270*2-135000),
            
            (nn.MaxPool1d(3, ceil_mode=False), (1, 10, 32), (1, 10, 10), 2*100, 2*100),
            (nn.MaxPool2d(3, ceil_mode=False), (1, 10, 32, 32), (1, 10, 10, 10), 8*10**3, 8*10**3),
            (nn.MaxPool3d(3, ceil_mode=False), (1, 10, 32, 32, 32), (1, 10, 10, 10, 10), 26*10**4, 26*10**4),
            (nn.MaxPool1d(3, ceil_mode=True), (1, 10, 32), (1, 10, 11), 2*110, 2*110),
            (nn.MaxPool2d(3, ceil_mode=True), (1, 10, 32, 32), (1, 10, 11, 11), 80*11**2, 80*11**2),
            (nn.MaxPool3d(3, ceil_mode=True), (1, 10, 32, 32, 32), (1, 10, 11, 11, 11), 260*11**3, 260*11**3),
            (nn.AvgPool1d(3, ceil_mode=False), (1, 10, 32), (1, 10, 10), 2*100, 5*100),
            (nn.AvgPool2d(3, ceil_mode=False), (1, 10, 32, 32), (1, 10, 10, 10), 8*10**3, 17*10**3),
            (nn.AvgPool3d(3, ceil_mode=False), (1, 10, 32, 32, 32), (1, 10, 10, 10, 10), 26*10**4, 53*10**4),
            (nn.AvgPool1d(3, ceil_mode=True), (1, 10, 32), (1, 10, 11), 2*110, 5*110),
            (nn.AvgPool2d(3, ceil_mode=True), (1, 10, 32, 32), (1, 10, 11, 11), 80*11**2, 170*11**2),
            (nn.AvgPool3d(3, ceil_mode=True), (1, 10, 32, 32, 32), (1, 10, 11, 11, 11), 260*11**3, 530*11**3),
            
            (nn.BatchNorm1d(10), (1, 10, 32), (1, 10, 32), 320*2, 320*4),
            (nn.BatchNorm2d(10), (1, 10, 32, 32), (1, 10, 32, 32), 32*32*20, 32*32*40),
            (nn.BatchNorm3d(10), (1, 10, 32, 32, 32), (1, 10, 32, 32, 32), 32**3*20, 32**3*40),
            
            (nn.Sigmoid(), (1, 10), (1, 10), 20, 40),
            (nn.Tanh(), (1, 10), (1, 10), 50, 90),
            (nn.ReLU(), (1, 10), (1, 10), 10, 10),
            (nn.ReLU6(), (1, 10), (1, 10), 10, 10),
            (nn.SiLU(), (1, 10), (1, 10), 30, 50),
            (nn.PReLU(), (1, 10), (1, 10), 20, 40),
            (nn.RReLU(), (1, 10), (1, 10), 20, 40),
            (nn.LeakyReLU(), (1, 10), (1, 10), 20, 40),
            
            (nn.Dropout(0.5), (1, 10), (1, 10), 0, 0),
            (nn.AdaptiveAvgPool1d(1), (1, 32, 8), (1, 32, 1), 0, 0), 
            (nn.Identity(), (1, 10), (1, 10), 0, 0), 
        ]
    )
    def test_module_measurement_logic(self, module, ipt_shape, expected_opt_shape, 
                                      expected_macs, expected_flops):
        """Test whether the measurement logic is true"""
        oproot = OperationTree(module).root
        cal_meter = oproot.cal
        
        assert not cal_meter._CalMeter__stat_ls
        cal_meter.measure()
        if not oproot.is_leaf:
            list(map(lambda x:x.cal.measure(), oproot.childs.values()))
        opt = module(torch_randn(*ipt_shape))
        assert tuple(opt.shape) == expected_opt_shape
        assert len(cal_meter._CalMeter__stat_ls) == 1
        
        assert cal_meter.Macs.val == expected_macs    
        assert cal_meter.Flops.val == expected_flops

    def test_not_supported_flag(self):
        """Test the is_not_supported property is set and retrieved correctly"""
        
        model = nn.Identity()
        opnode = OperationNode(module=model)
        cal_meter = opnode.cal
        
        # retrieve
        assert not cal_meter.is_not_supported
        
        # valid set
        model.register_forward_hook(cal_meter._CalMeter__not_support_hook)
        model(torch_randn(1, 10))
        
        assert cal_meter.is_not_supported
        
        # invalid set
        with pytest.raises(AttributeError):
            del cal_meter.is_not_supported

@pytest.mark.usefixtures("toggle_to_mem")
class TestMemMeter:
    def test_cls_variable(self):
        """Test detail_val_container and overview_val_container settings"""
        assert hasattr(MemMeter, "detail_val_container")
        dc = MemMeter.detail_val_container
        assert all(v is None for v in dc._field_defaults.values())
        
        assert hasattr(MemMeter, "overview_val_container")
        oc = MemMeter.overview_val_container
        assert all(v is None for v in oc._field_defaults.values())
    
    def test_valid_init(self, simple_model_root):
        """Test valid initialization"""
        model, oproot = simple_model_root
        
        mem_meter = oproot.mem
        assert mem_meter._opnode == oproot
        assert mem_meter._model is model
        assert not mem_meter.is_measured
        assert not mem_meter._MemMeter__stat_ls
        
        assert mem_meter.name == "mem"    
        assert hasattr(mem_meter, "ParamCost")
        assert isinstance(mem_meter.ParamCost, UpperLinkData)
        assert mem_meter.ParamCost.val == 0
        assert mem_meter.ParamCost._UpperLinkData__parent_data is None
        assert mem_meter.ParamCost._UpperLinkData__unit_sys is BinaryUnit
        
        assert hasattr(mem_meter, "BufferCost")
        assert isinstance(mem_meter.BufferCost, UpperLinkData)
        assert mem_meter.BufferCost.val == 0
        assert mem_meter.BufferCost._UpperLinkData__parent_data is None
        assert mem_meter.BufferCost._UpperLinkData__unit_sys is BinaryUnit
        
        assert hasattr(mem_meter, "OutputCost")
        assert isinstance(mem_meter.OutputCost, UpperLinkData)
        assert mem_meter.OutputCost.val == 0
        assert mem_meter.OutputCost._UpperLinkData__parent_data is None
        assert mem_meter.OutputCost._UpperLinkData__unit_sys is BinaryUnit
        
        assert hasattr(mem_meter, "TotalCost")
        assert isinstance(mem_meter.TotalCost, UpperLinkData)
        assert mem_meter.TotalCost.val == 0
        assert mem_meter.TotalCost._UpperLinkData__parent_data is None
        assert mem_meter.TotalCost._UpperLinkData__unit_sys is BinaryUnit

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            MemMeter(opnode="0")

    def test_val_property(self, measured_simple_model):
        """Test whether the val property is properly set"""
        *_, mem_meter = measured_simple_model
        
        overview = mem_meter.val
        assert isinstance(overview, MemMeter.overview_val_container)
        assert overview.Operation_Id == "0"
        assert overview.Operation_Name == "SimpleModel"
        assert overview.Operation_Type == "SimpleModel"
        assert overview.Param_Cost is mem_meter.ParamCost
        assert overview.Buffer_Cost is mem_meter.BufferCost
        assert overview.Output_Cost is mem_meter.OutputCost
        assert overview.Total is mem_meter.TotalCost

    def test_crucial_data_format(self, measured_simple_model):
        """Test whether the crucial_data is return in correct format"""
        *_, mem_meter = measured_simple_model
        crucial_data = mem_meter.crucial_data
        assert isinstance(crucial_data, dict)
                
        # verify align
        keys = list(crucial_data.keys())
        assert all(isinstance(k,str) for k in crucial_data.keys())
        assert all(len(k) == len(keys[0]) for k in keys[1:])
        
        # verify value
        assert all(isinstance(v,str) for v in crucial_data.values())

    def test_mem_measure(self):
        """Test whether the measure method works well"""
        module = nn.Identity()
        opnode = OperationNode(module)
        mem_meter = opnode.mem
        mem_meter.measure()
        
        assert mem_meter.is_measured
        assert len(module._forward_hooks) == 1
        assert next(iter(module._forward_hooks.values())).__name__ == "__hook_func"
        
    def test_measure_cache(self, simple_model_root):
        """Test whether the measure method will be revisited after the first call"""
        model, oproot = simple_model_root
        mem_meter = oproot.mem
        
        res = mem_meter.measure()
        assert res is not None
        
        res = mem_meter.measure()
        assert res is None

    def test_valid_access(self, simple_model_root):
        """Test whether the invalid access will be blocked"""
        model, oproot = simple_model_root
        mem_meter = oproot.mem
        
        # access property before measure
        with pytest.raises(AttributeError) as e:
            mem_meter.detail_val
        assert "mem" in str(e.value)
        
        with pytest.raises(AttributeError) as e:
            mem_meter.val
        assert "mem" in str(e.value)

        with pytest.raises(AttributeError) as e:
            mem_meter.crucial_data
        assert "mem" in str(e.value)
            
        # access skipped module after measure
        mem_meter.measure()
        with pytest.raises(RuntimeError):
            mem_meter.detail_val
        
        with pytest.raises(RuntimeError):
            mem_meter.val
        
        with pytest.raises(RuntimeError):
            mem_meter.crucial_data
    
    @pytest.mark.parametrize(
        argnames=("module", "ipt_shape", "is_inplace"),
        argvalues=[
            (nn.ReLU(), (1, 10), False),
            (nn.ReLU6(), (1, 10), False),
            (nn.SiLU(), (1, 10), False),
            (nn.RReLU(), (1, 10), False),
            (nn.LeakyReLU(), (1, 10), False),
            (nn.SELU(), (1, 10), False),
            (nn.Mish(), (1, 10), False),
            (nn.Dropout(0.5), (1, 10), False),
            (nn.Threshold(0.1, 20), (1, 10), False),

            (nn.ReLU(inplace=True), (1, 10), True),
            (nn.ReLU6(inplace=True), (1, 10), True),
            (nn.SiLU(inplace=True), (1, 10), True),
            (nn.RReLU(inplace=True), (1, 10), True),
            (nn.LeakyReLU(inplace=True), (1, 10), True),
            (nn.SELU(inplace=True), (1, 10), True),
            (nn.Mish(inplace=True), (1, 10), True),
            (nn.Dropout(0.5, inplace=True), (1, 10), True),
            (nn.Threshold(0.1, 20, inplace=True), (1, 10), True),

            (nn.GELU(), (1, 10), False),
            (nn.PReLU(), (1, 10), False),
            (nn.Sigmoid(), (1, 10), False),
            (nn.Tanh(), (1, 10), False),
            (nn.Conv1d(10,5,3), (1, 10, 32), False),
            (nn.Linear(10, 5), (1, 10), False),
            (nn.BatchNorm1d(10), (1, 10, 32), False),
            (nn.AvgPool1d(3), (1, 10, 32), False),
            (nn.MaxPool1d(3), (1, 10, 32), False),
            (nn.Identity(), (1, 10), False),
            (nn.Sequential(), (1, 10), False),
            (nn.Sequential(nn.Identity()), (1, 10), False),
        ]
    )
    def test_inplace_module_handling(self, module, ipt_shape, is_inplace):
        """Test whether the inplace module will be handled properly"""
        opnode = OperationNode(module)
        mem_meter = opnode.mem
        assert mem_meter.is_inplace is is_inplace
        mem_meter.measure()
        
        module(torch_randn(*ipt_shape))
        
        record = mem_meter.detail_val[0]
        if is_inplace:
            assert record.Operation_Type.endswith("(inplace)")
            assert mem_meter.OutputCost.val == 0   
        else:
            assert not record.Operation_Type.endswith("(inplace)")
            if opnode.is_leaf:
                assert mem_meter.OutputCost.val > 0

    @pytest.mark.parametrize(
        argnames=("opts", "expected_opt_cost"),
        argvalues=[
            (1, 32),  
            (1., 24), # python default size for float

            ("1", 49 + 1),
            ("-"*50, 49 + 50),

            (None, 16), # python default size for None

            (tuple(), 0),
            ((1,2,3), 32*3),
            
            # value change between python version
            (list(), asizeof([])),
            ([1,2,3], asizeof([1,2,3])), 

            (set(), 216),
            ({1,2,3}, 216 + 32*3),

            # hard to resolve the component
            (dict(), asizeof(dict())), 
            ({"a":1, "b":2}, asizeof({"a":1, "b":2})), 
            ({"a":1., "b":2.}, asizeof({"a":1., "b":2.})),

            (np.array([1,2,3], dtype=np.int8), 1*3),
            (np.array([1,2,3], dtype=np.int16), 2*3),
            (np.array([1,2,3], dtype=np.int64), 8*3),
            (np.array([1,2,3], dtype=np.float16), 2*3),
            (np.array([1,2,3], dtype=np.float64), 8*3),

            (torch_randn(1,2,3), 6*4),
            (torch_randn(1,2,3, dtype=torch_float16), 6*2),
            (torch_randn(1,2,3, dtype=torch_float64), 6*8),
            (torch_ones(1,2,3, dtype=torch_int8), 6*1),
            (torch_ones(1,2,3, dtype=torch_int16), 6*2),
            (torch_ones(1,2,3, dtype=torch_int64), 6*8)
        ]
    )
    def test_multitype_output_handling(self, opts, expected_opt_cost):
        """Test whether the different types' output will be handled properly"""
        class MultiOutputModel(nn.Module):
            def __init__(self):
                super(MultiOutputModel, self).__init__()

            def forward(self):
                return opts
        
        model = MultiOutputModel()
        opnode = OperationNode(model)
        mem_meter = opnode.mem

        mem_meter.measure()
        model()

        assert mem_meter.OutputCost.val == expected_opt_cost

    @pytest.mark.parametrize(
        argnames=("opts", "expected_opt_cost"),
        argvalues=[
            ((1, 1.), 32 + 24), 
            ((1, "1"), 32 + 50),
            ((1, None), 32 + 16),  
            ((1, ()), 32 + 40),
            ((1, (1,2,3)), 32 + 40*4),
            ((1, [1,2,3]), 32 + asizeof([1,2,3])),
            ((1, {1,2,3}), 32 + 216 + 32*3),
            ((1, {"a":1, "b":2}), 32 + asizeof({"a":1, "b":2})),

            (("1", "2."), 50 + 51),
            (("1", 2.), 50 + 24),
            (("1", None), 50 + 16),

            ((None, None), 16 + 16),
            ((None, 2.), 16 + 24),

            ((1, np.array([1,2,3], dtype=np.int8)), 32 + 1*3),
            ((1, torch_ones(1,2,3, dtype=torch_int8)), 32 + 1*6),
            ((torch_randn(1,2,3, dtype=torch_float64), None), 6*8 + 16),

            ((torch_randn(1,2,3, dtype=torch_float16), 
              np.array([1,2,3], dtype=np.int8)), 6*2 + 1*3),

            ((torch_randn(1,2,3, dtype=torch_float64),
              torch_ones(1,2,3, dtype=torch_int64)), 6*8 + 6*8)
        ]
    )
    def test_multi_output_handling(self, opts, expected_opt_cost):
        """Test whether the multi output module will be handled properly"""
        class MultiOutputModel(nn.Module):
            def __init__(self):
                super(MultiOutputModel, self).__init__()

            def forward(self):
                return opts
        
        model = MultiOutputModel()
        opnode = OperationNode(model)
        mem_meter = opnode.mem

        mem_meter.measure()
        model()

        assert mem_meter.OutputCost.val == expected_opt_cost

    @pytest.mark.parametrize(
        argnames=("module", "ipt_shape"),
        argvalues=[
            (nn.Sequential(nn.Identity()), (1, 10)),
            
            (nn.Linear(10, 5), (1, 10)),
            
            (nn.Conv1d(10, 5, 3), (1, 10, 32)),
            (nn.Conv2d(10, 5, 3), (1, 10, 32, 32)),
            (nn.Conv3d(10, 5, 3), (1, 10, 32, 32, 32)),
            
            (nn.MaxPool1d(3), (1, 10, 32)),
            (nn.MaxPool2d(3), (1, 10, 32, 32)),
            (nn.MaxPool3d(3), (1, 10, 32, 32, 32)),
            (nn.AvgPool1d(3), (1, 10, 32)),
            (nn.AvgPool2d(3), (1, 10, 32, 32)),
            (nn.AvgPool3d(3), (1, 10, 32, 32, 32)),
            
            (nn.BatchNorm1d(10), (1, 10, 32)),
            (nn.BatchNorm2d(10), (1, 10, 32, 32)),
            (nn.BatchNorm3d(10), (1, 10, 32, 32, 32)),
            
            (nn.Sigmoid(), (1, 10)),
            (nn.Tanh(), (1, 10)),
            (nn.ReLU(), (1, 10)),
            (nn.ReLU6(), (1, 10)),
            (nn.SiLU(), (1, 10)),
            (nn.PReLU(), (1, 10)),
            (nn.RReLU(), (1, 10)),
            (nn.LeakyReLU(), (1, 10)),
            
            (nn.Dropout(0.5), (1, 10)), 
            (nn.AdaptiveAvgPool1d(1), (1, 32, 8)), 
            (nn.Identity(), (1, 10)), 
        ]
    )
    def test_reaccess_module(self, module, ipt_shape):
        """Test reaccess handling"""
        opnode = OperationNode(module)
        mem_meter = opnode.mem
        
        mem_meter.measure()
        module(torch_randn(*ipt_shape))
        
        assert mem_meter.ParamCost._UpperLinkData__access_cnt == 1
        assert mem_meter.BufferCost._UpperLinkData__access_cnt == 1
        assert mem_meter.OutputCost._UpperLinkData__access_cnt == 1
        assert mem_meter.TotalCost._UpperLinkData__access_cnt == 1
        origin_paramcost = mem_meter.ParamCost.val
        origin_buffercost = mem_meter.BufferCost.val
        origin_outputcost = mem_meter.OutputCost.val
        origin_totalcost = mem_meter.TotalCost.val

        # revisit
        module(torch_randn(*ipt_shape))
        assert mem_meter.ParamCost._UpperLinkData__access_cnt == 1
        assert mem_meter.BufferCost._UpperLinkData__access_cnt == 1
        assert mem_meter.OutputCost._UpperLinkData__access_cnt == 2 # revisit will only take output into account
        assert mem_meter.TotalCost._UpperLinkData__access_cnt == 1
        assert mem_meter.ParamCost.val == origin_paramcost
        assert mem_meter.BufferCost.val == origin_buffercost
        assert mem_meter.OutputCost.val == origin_outputcost * 2
        assert mem_meter.TotalCost.val == origin_totalcost + origin_outputcost

    @pytest.mark.parametrize(
        argnames=("module", "ipt_shape", "expected_param_cost",
                  "expected_buffer_cost", "expected_output_cost"),
        argvalues=[
            (nn.Sequential(nn.Identity()), (1, 10), 0, 0, 10*4),
            (nn.Sequential(nn.Conv2d(3,10,3),
                           nn.Conv2d(10,30,1)), (1, 3, 32, 32), 610*4, 0, 9000*4+27000*4),
            
            (nn.Linear(10, 5, bias=True), (1, 10), 55*4, 0, 5*4),
            (nn.Linear(10, 5, bias=False), (1, 10), 50*4, 0, 5*4),
            
            (nn.Conv1d(10, 5, 3, bias=True), (1, 10, 32), 155*4, 0, 150*4),
            (nn.Conv1d(10, 5, 3, bias=False), (1, 10, 32), 150*4, 0, 150*4),
            (nn.Conv2d(10, 5, 3, bias=True), (1, 10, 32, 32), 455*4, 0, 4500*4),
            (nn.Conv2d(10, 5, 3, bias=False), (1, 10, 32, 32), 450*4, 0, 4500*4),
            (nn.Conv3d(10, 5, 3, bias=True), (1, 10, 32, 32, 32), 1355*4, 0, 135000*4),
            (nn.Conv3d(10, 5, 3, bias=False), (1, 10, 32, 32, 32), 1350*4, 0, 135000*4),
            
            (nn.MaxPool1d(3), (1, 10, 32), 0, 0, 4*1e2),
            (nn.MaxPool2d(3), (1, 10, 32, 32), 0, 0, 4*1e3),
            (nn.MaxPool3d(3), (1, 10, 32, 32, 32), 0, 0, 4*1e4),
            (nn.AvgPool1d(3), (1, 10, 32), 0, 0, 4*1e2),
            (nn.AvgPool2d(3), (1, 10, 32, 32), 0, 0, 4*1e3),
            (nn.AvgPool3d(3), (1, 10, 32, 32, 32), 0, 0, 4*1e4),
            
            (nn.BatchNorm1d(10), (1, 10, 32), 80, 88, 32*40),
            (nn.BatchNorm2d(10), (1, 10, 32, 32), 80, 88, 32*32*40),
            (nn.BatchNorm3d(10), (1, 10, 32, 32, 32), 80, 88, 32**3*40),
            
            (nn.Sigmoid(), (1, 10), 0, 0, 40),
            (nn.Tanh(), (1, 10), 0, 0, 40),
            (nn.ReLU(), (1, 10), 0, 0, 40),
            (nn.ReLU6(), (1, 10), 0, 0, 40),
            (nn.SiLU(), (1, 10), 0, 0, 40),
            (nn.PReLU(), (1, 10), 4, 0, 40),
            (nn.RReLU(), (1, 10), 0, 0, 40),
            (nn.LeakyReLU(), (1, 10), 0, 0, 40),

            (nn.ReLU(inplace=True), (1, 10), 0, 0, 0),
            (nn.ReLU6(inplace=True), (1, 10), 0, 0, 0),
            (nn.SiLU(inplace=True), (1, 10), 0, 0, 0),
            (nn.RReLU(inplace=True), (1, 10), 0, 0, 0),
            (nn.LeakyReLU(inplace=True), (1, 10), 0, 0, 0),
            (nn.SELU(inplace=True), (1, 10), 0, 0, 0),
            (nn.Mish(inplace=True), (1, 10), 0, 0, 0),
            (nn.Dropout(0.5, inplace=True), (1, 10), 0, 0, 0),
            (nn.Threshold(0.1, 20, inplace=True), (1, 10), 0, 0, 0),
            
            (nn.Dropout(0.5), (1, 10), 0, 0, 40),
            (nn.AdaptiveAvgPool1d(1), (1, 32, 8), 0, 0, 32*4), 
            (nn.Identity(), (1, 10), 0, 0, 40), 
        ]
    )
    def test_module_measurement_logic(self, module, ipt_shape, 
                                      expected_param_cost, expected_buffer_cost, expected_output_cost):
        """Test whether the measurement logic is true"""
        oproot = OperationTree(module).root
        mem_meter = oproot.mem
        
        assert not mem_meter._MemMeter__stat_ls
        mem_meter.measure()
        if not oproot.is_leaf:
            list(map(lambda x: x.mem.measure(), oproot.childs.values()))
        module(torch_randn(*ipt_shape))
        assert len(mem_meter._MemMeter__stat_ls) == 1
        
        assert mem_meter.ParamCost.val == expected_param_cost    
        assert mem_meter.BufferCost.val == expected_buffer_cost
        assert mem_meter.OutputCost.val == expected_output_cost  
        assert mem_meter.TotalCost.val == expected_param_cost + \
                                          expected_buffer_cost  + \
                                          expected_output_cost

        record = mem_meter._MemMeter__stat_ls[0]
        if not oproot.is_leaf:
            assert all(isinstance(getattr(record, field), UpperLinkData)
                       for field in ["Param_Cost", "Buffer_Cost", "Output_Cost", "Total"])
        else:
            for expected_val, field_name in zip([expected_param_cost, expected_buffer_cost, 
                                                 expected_output_cost, mem_meter.TotalCost.val], 
                                                ["Param_Cost", "Buffer_Cost", "Output_Cost", "Total"]):
                field_val = getattr(record, field_name)
                if not expected_val:
                    assert field_val is None
                else:
                    assert isinstance(field_val, UpperLinkData)

@pytest.mark.usefixtures("toggle_to_ittp")
class TestIttpMeter:
    def test_cls_variable(self):
        """Test detail_val_container and overview_val_container settings"""
        assert hasattr(IttpMeter, "detail_val_container")
        dc = MemMeter.detail_val_container
        assert all(v is None for v in dc._field_defaults.values())
        
        assert hasattr(IttpMeter, "overview_val_container")
        oc = MemMeter.overview_val_container
        assert all(v is None for v in oc._field_defaults.values())
    
    def test_valid_init(self, simple_model_root):
        """Test valid initialization"""
        model, oproot = simple_model_root
        
        ittp_meter = oproot.ittp
        assert ittp_meter._opnode == oproot
        assert ittp_meter._model is model
        assert not ittp_meter.is_measured
        assert not ittp_meter._IttpMeter__stat_ls
        
        assert ittp_meter.name == "ittp"    
        assert hasattr(ittp_meter, "InferTime")
        assert isinstance(ittp_meter.InferTime, MetricsData)
        assert not len(ittp_meter.InferTime.vals)
        assert ittp_meter.InferTime._MetricsData__reduce_func is np.median
        assert ittp_meter.InferTime._MetricsData__unit_sys is TimeUnit
        
        assert ittp_meter.name == "ittp"    
        assert hasattr(ittp_meter, "Throughput")
        assert isinstance(ittp_meter.Throughput, MetricsData)
        assert not len(ittp_meter.Throughput.vals)
        assert ittp_meter.Throughput._MetricsData__reduce_func is np.median
        assert ittp_meter.Throughput._MetricsData__unit_sys is SpeedUnit

    def test_invalid_init(self):
        """Test invalid initialization"""
        with pytest.raises(TypeError):
            IttpMeter(opnode="0")

    def test_val_property(self, measured_simple_model):
        """Test whether the val property is properly set"""
        *_, ittp_meter = measured_simple_model
        
        overview = ittp_meter.val
        assert isinstance(overview, IttpMeter.overview_val_container)
        assert overview.Operation_Id == "0"
        assert overview.Operation_Name == "SimpleModel"
        assert overview.Operation_Type == "SimpleModel"
        assert overview.Infer_Time is ittp_meter.InferTime
        assert overview.Throughput is ittp_meter.Throughput

    def test_crucial_data_format(self, measured_simple_model):
        """Test whether the crucial_data is return in correct format"""
        *_, ittp_meter = measured_simple_model
        crucial_data = ittp_meter.crucial_data
        assert isinstance(crucial_data, dict)
                
        # verify align
        keys = list(crucial_data.keys())
        assert all(isinstance(k,str) for k in crucial_data.keys())
        assert all(len(k) == len(keys[0]) for k in keys[1:])
        
        # verify value
        assert all(isinstance(v,str) for v in crucial_data.values())

    def test_ittp_measure(self):
        """Test whether the measure method works well"""
        module = nn.Identity()
        opnode = OperationNode(module)
        ittp_meter = opnode.ittp
        ittp_meter.measure(device=torch_device("cpu"))

        assert ittp_meter.is_measured
        assert len(module._forward_hooks) == 1
        assert next(iter(module._forward_hooks.values())).func.__name__ == "__hook_func"
        
    def test_no_measure_cache(self, simple_model_root):
        """Test whether the measure method will be revisited after the first call"""
        model, oproot = simple_model_root
        ittp_meter = oproot.ittp
        
        res = ittp_meter.measure(device=torch_device("cpu"))
        assert res is not None
        
        res = ittp_meter.measure(device=torch_device("cpu"))
        assert res is not None

    @pytest.mark.skipif(not is_cuda(), reason="No GPUs detected")
    def test_model_device_dismatch(self):
        """Test whether the measure method works well 
           when model's device is the same with given argument"""
        model = nn.Linear(10, 5)
        opnode = OperationNode(model)
        ittp_meter = opnode.ittp

        assert not len(model._forward_hooks)
        ittp_meter.measure(device=torch_device("cuda:0"), repeat=1)
        assert len(model._forward_hooks) == 1

    def test_measure_on_different_device(self):
        """Test whether the measure method works well for model on different device"""
        model = nn.Linear(10, 5)
        opnode = OperationNode(model)
        ittp_meter = opnode.ittp

        # cpu
        ittp_meter.measure(device=torch_device("cpu"), repeat=1)
        with patch("torchmeter.statistic.perf_counter") as cpu_timer, \
             patch("torchmeter.statistic.cuda_event.elapsed_time") as gpu_timer:
            cpu_timer.side_effect = [1, 2]
            gpu_timer.side_effect = [1, 2]
            model(torch_randn(1, 10, device=torch_device("cpu")))
            assert cpu_timer.call_count == 2
            assert gpu_timer.call_count == 0
        
        # gpu
        if is_cuda():
            ittp_meter.measure(device=torch_device("cuda:0"), repeat=1)
            with patch("torchmeter.statistic.perf_counter") as cpu_timer, \
                 patch("torchmeter.statistic.cuda_event.elapsed_time") as gpu_timer:
                cpu_timer.side_effect = [1, 2]
                gpu_timer.side_effect = [1, 2]
                model(torch_randn(1, 10, device=torch_device("cuda:0")))
                assert cpu_timer.call_count == 0
                assert gpu_timer.call_count == 1
        else:
            warnings.warn(message="No Nvidia GPU detected on this device, the test of measuring ittp of model on GPU will be skipped.", 
                          category=UserWarning)

    @pytest.mark.parametrize(
        argnames="repeat_time",
        argvalues=range(10,101,10),
        ids=lambda x: f"repeat measurement {x} times"        
    )
    def test_repeat_measure(self, repeat_time):
        """Test whether the repeat setting works well"""
        model = nn.Linear(10, 5)
        opnode = OperationNode(model)
        ittp_meter = opnode.ittp
        ittp_meter.measure(device=torch_device("cpu"), repeat=repeat_time)

        model(torch_randn(1, 10))

        assert len(ittp_meter.InferTime.vals) == repeat_time
        assert len(ittp_meter.Throughput.vals) == repeat_time   

    def test_valid_access(self, simple_model_root):
        """Test whether the invalid access will be blocked"""
        model, oproot = simple_model_root
        ittp_meter = oproot.ittp
        
        # access property before measure
        with pytest.raises(AttributeError) as e:
            ittp_meter.detail_val
        assert "ittp" in str(e.value)
        
        with pytest.raises(AttributeError) as e:
            ittp_meter.val
        assert "ittp" in str(e.value)

        with pytest.raises(AttributeError) as e:
            ittp_meter.crucial_data
        assert "ittp" in str(e.value)
            
        # access skipped module after measure
        ittp_meter.measure(device=torch_device("cpu"))
        with pytest.raises(RuntimeError):
            ittp_meter.detail_val
        
        with pytest.raises(RuntimeError):
            ittp_meter.val
        
        with pytest.raises(RuntimeError):
            ittp_meter.crucial_data

    def test_reaccess_module(self):
        """Test reaccess handling"""
        model = nn.Linear(10, 5)
        opnode = OperationNode(model)
        ittp_meter = opnode.ittp
        
        assert not len(model._forward_hooks)
        ittp_meter.measure(device=torch_device("cpu"))
        assert len(model._forward_hooks) == 1
        
        model(torch_randn(1, 10))
        assert not len(model._forward_hooks)
        
        # reaccess
        it_val = ittp_meter.InferTime.metrics
        tp_val = ittp_meter.Throughput.metrics
        model(torch_randn(1, 10))
        assert it_val == ittp_meter.InferTime.metrics 
        assert tp_val == ittp_meter.Throughput.metrics

    @pytest.mark.parametrize(
        argnames=("repeat_time", "expected_it", "expected_tp"),
        argvalues=[
            (11, 6, 1/6),
            (21, 11, 1/11),
            (31, 16, 1/16),
            (41, 21, 1/21),
            (51, 26, 1/26)
        ],
        ids=lambda x: f"{x}" if isinstance(x, int) else f"{x:g}"
    )
    def test_module_measurement_logic(self, repeat_time, 
                                      expected_it, expected_tp):
        """Test whether the measurement logic is true"""
        model = nn.Linear(10, 5)
        opnode = OperationNode(model)
        ittp_meter = opnode.ittp
        ittp_meter._IttpMeter__reduce_func = np.median
        
        # cpu
        ittp_meter.measure(device=torch_device("cpu"), repeat=repeat_time)
        with patch("torchmeter.statistic.perf_counter") as cpu_timer:
            se_time_vals = []
            for sub_res in range(1, repeat_time+1):
                se_time_vals.extend([0, sub_res])
            cpu_timer.side_effect = se_time_vals
            model(torch_randn(1, 10, device=torch_device("cpu")))
            assert ittp_meter.InferTime.metrics == expected_it
            assert ittp_meter.Throughput.metrics == pytest.approx(expected_tp)
        
        # gpu
        if is_cuda():
            ittp_meter.measure(device=torch_device("cuda:0"), repeat=repeat_time)
            with patch("torchmeter.statistic.cuda_event.elapsed_time") as gpu_timer:
                gpu_timer.side_effect = map(lambda x:int(x*1e3), range(1, repeat_time+1))
                model(torch_randn(1, 10, device=torch_device("cuda:0")))
                assert ittp_meter.InferTime.metrics == expected_it
                assert ittp_meter.Throughput.metrics == pytest.approx(expected_tp)
        else:
            warnings.warn(message="No Nvidia GPU detected on this device, the test of ittp measuring logic on GPU will be skipped.", 
                          category=UserWarning)
            
    
