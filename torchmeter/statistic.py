from time import perf_counter
from collections import namedtuple
from abc import ABC, abstractmethod
from operator import attrgetter, mul
from functools import reduce, partial
from enum import Enum, IntEnum, IntFlag, unique
from typing import Any, Callable, List, NamedTuple, Optional, TypeVar, Tuple, Union

import numpy as np
import torch.nn as nn
from torch import no_grad
from torch.cuda import Event as cuda_event
from torch.cuda import synchronize as cuda_sync

OPN_TYPE = TypeVar("OperationNode")

@unique
class DecimalUnit(IntEnum):
    T:int = 1e12
    G:int = 1e9
    M:int = 1e6
    K:int = 1e3
    B:int = 1e0

@unique
class BinaryUnit(IntFlag):
    TiB:int = 2**40
    GiB:int = 2**30
    MiB:int = 2**20
    KiB:int = 2**10
    B:int   = 2**0

@unique
class TimeUnit(Enum):
    h:int  = 60**2
    min:int = 60**1
    s:int  = 60**0
    ms:float = 1e-3
    us:float = 1e-6
    ns:float = 1e-9

@unique
class SpeedUnit(IntEnum):
    TSamPS:int = 1e12
    GSamPS:int = 1e9
    MSamPS:int = 1e6
    KSamPS:int = 1e3
    SamPS:int  = 1e0

UNIT_TYPE = Union[DecimalUnit, BinaryUnit, TimeUnit, SpeedUnit]

def auto_unit(val:Union[int, float], unit_system=DecimalUnit) -> Union[str, None]:
    for unit in list(unit_system):
        if val >= unit.value:
            return f'{val / unit.value:.2f} {unit.name}'
    return None

class UpperLinkData:

    __slots__ = ['val', '__parent_data']

    def __init__(self, val:int=0, parent_data:Optional["UpperLinkData"]=None):
        self.val = val
        self.__parent_data = parent_data    
    
    def __iadd__(self, other):
        self.val += other
        self.__upper_update(other)
        return self
    
    def __upper_update(self, other:int):
        if self.__parent_data is not None:
            self.__parent_data += other
    
    def __repr__(self):
        return str(self.val)

class MetricsData:

    __slots__ = ['vals',
                 'reduce_func',
                 'unit_sys']

    def __init__(self, reduce_func:Optional[Callable]=np.mean, unit_system:Optional[UNIT_TYPE]=DecimalUnit):
        self.vals = np.array([])
        self.reduce_func = reduce_func if reduce_func is not None else lambda x:x
        self.unit_sys = unit_system

    @property
    def metrics(self):
        return self.reduce_func(self.vals) if self.vals.any() else 0.
    
    @property
    def iqr(self):
        if self.vals.any():
            return np.percentile(self.vals, 75) - np.percentile(self.vals, 25)
        else:
            return 0.
    
    def append(self, new_val:Any):
        self.vals = np.append(self.vals, new_val)

    def clear(self):
        self.vals = np.array([])

    def __repr__(self):
        if self.unit_sys is not None:
            return f"{auto_unit(self.metrics, self.unit_sys)}" + ' ± ' + \
                   f"{auto_unit(self.iqr, self.unit_sys)}"
        else:
            return f"{self.metrics} ± {self.iqr}"

class Statistics(ABC):

    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'detail_val_container'), f"Class '{cls.__name__}' must have the class attribute 'detail_val_container', \
                                               which should be a NamedTuple"
        assert hasattr(cls, 'overview_val_container'), f"Class '{cls.__name__}' must have the class attribute 'overview_val_container', \
                                            which should be a NamedTuple"
        return super().__new__(cls)        

    @property
    @abstractmethod
    def name(self) -> str:
        """The registered name of the statistics in OperationNode"""
        ...

    @property
    @abstractmethod
    def val(self) -> NamedTuple:
        """A namedtuple which contains all the necessary information of the statistics"""
        ...
    
    @property
    @abstractmethod
    def detail_val(self) -> List[NamedTuple]:
        """The list of namedtuple which will be rendered in table"""
        ...

    @abstractmethod
    def measure(self):
        """To measure the statistics"""
        ...

    @property
    def tb_fields(self) -> Tuple[str]:
        return self.detail_val_container._fields
    
    @property
    def ov_fields(self) -> Tuple[str]:
        return self.overview_val_container._fields
    
    def init_linkdata(self,
                      attr_name:str,
                      init_val:int=0,
                      opparent:Optional["OperationNode"]=None): # noqa # type: ignore
        if opparent is None:
            link_data = UpperLinkData(val=init_val)
        else:
            upper_getter = attrgetter(f'{self.name}.{attr_name}')
            link_data = UpperLinkData(val=init_val, 
                                      parent_data=upper_getter(opparent))
        return link_data

    def __repr__(self):
        repr_str = self.val.__class__.__name__ + '\n'

        max_len = max((len(f) for f in self.ov_fields))

        for field in self.ov_fields:
            field_val = getattr(self.val, field, 'N/A')
            if isinstance(field_val, UpperLinkData):
                field_val = float(field_val.val) # get the value
                unit_system = BinaryUnit if repr_str.startswith('Memory') else DecimalUnit
                repr_str += '• ' + f"{field.rjust(max_len)} = {field_val} = {auto_unit(field_val, unit_system)}\n"
            else:
                repr_str += '• ' + f"{field.rjust(max_len)} = {field_val}\n"

        return repr_str

class ParamsMeter(Statistics):

    detail_val_container:NamedTuple = namedtuple(typename='Params_INFO', 
                                                 defaults=(None,)*5,
                                                 field_names=['Operation_Id', 
                                                              'Operation_Type',
                                                              'Param_Name', 
                                                              'Requires_Grad', 
                                                              'Numeric_Num'],)
    
    overview_val_container:NamedTuple = namedtuple(typename='Params_INFO', 
                                                   defaults=(None,)*5,
                                                   field_names=['Operation_Id', 
                                                                'Operation_Type',
                                                                'Operation_Name', 
                                                                'Total_Params', 
                                                                'Learnable_Params'])

    def __init__(self, opnode: OPN_TYPE):
        self._opnode = opnode
        self._model = opnode.operation
        
        self.__stat_ls = [] # record all parameters' information
        self.is_measured = True if self._model._modules else False # only measure the leaf nodes

        _opparent = opnode.parent
        self.__RegNum = self.init_linkdata(attr_name='RegNum', init_val=0, opparent=_opparent)
        self.__TotalNum = self.init_linkdata(attr_name='TotalNum', init_val=0, opparent=_opparent)

    @property
    def name(self) -> str:
        return 'param'

    @property
    def RegNum(self) -> UpperLinkData :
        return self.__RegNum
    
    @property
    def TotalNum(self) -> UpperLinkData:
        return self.__TotalNum

    @property
    def detail_val(self) -> List[NamedTuple]:
        self.measure()
        return self.__stat_ls
    
    @property
    def val(self) -> NamedTuple:
        self.measure()
        return self.overview_val_container(Operation_Id=self._opnode.node_id,
                                           Operation_Type=self._opnode.type,
                                           Operation_Name=self._opnode.name,
                                           Total_Params=self.TotalNum,
                                           Learnable_Params=self.RegNum)

    def measure(self) -> None:
        if self.is_measured:
            return
        
        if not self._model._parameters:
            self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                            Operation_Type=self._opnode.type,
                                                            Numeric_Num=0))
        else:
            for param_name, param_val in self._model.named_parameters(): 
                p_num = param_val.numel()
                
                p_reg = False
                if param_val.requires_grad:
                    p_reg = True
                    self.__RegNum += p_num

                self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                                Operation_Type=self._opnode.type,
                                                                Param_Name=param_name,
                                                                Requires_Grad=p_reg,
                                                                Numeric_Num=p_num))
                
                self.__TotalNum += p_num
        
        self.is_measured = True

class CalMeter(Statistics):

    detail_val_container:NamedTuple = namedtuple(typename='Calculation_INFO', 
                                                 defaults=(None,)*9,
                                                 field_names=['Operation_Id', 
                                                              'Operation_Name', 
                                                              'Operation_Type',
                                                              'Kernel_Size',  # Kernel_Size([H,W])
                                                              'Bias', 
                                                              'Input_Shape',  # Input_Shape([B,C,H,W])'
                                                              'Output_Shape',  # Output_Shape([B,C,H,W])'
                                                              'MACs', 
                                                              'FLOPs'])
    
    overview_val_container:NamedTuple = namedtuple(typename='Calculation_INFO', 
                                                   defaults=(None,)*5,
                                                   field_names=['Operation_Id', 
                                                                'Operation_Type',
                                                                'Operation_Name', 
                                                                'MACs', 
                                                                'FLOPs'])

    def __init__(self, opnode: OPN_TYPE):
        self._opnode = opnode
        self._model = opnode.operation
        
        self.__stat_ls = [] # record the flops and macs information of each operation
        self.is_measured = True if self._model._modules else False # only measure the leaf nodes

        _opparent = opnode.parent
        self.__Macs = self.init_linkdata(attr_name='Macs', init_val=0, opparent=_opparent)
        self.__Flops = self.init_linkdata(attr_name='Flops', init_val=0, opparent=_opparent)

    @property
    def name(self) -> str:
        return 'cal'

    @property
    def Macs(self) -> UpperLinkData :
        return self.__Macs
    
    @property
    def Flops(self) -> UpperLinkData:
        return self.__Flops

    @property
    def detail_val(self) -> List[NamedTuple]:
        self.measure()
        return self.__stat_ls
    
    @property
    def val(self) -> NamedTuple:
        self.measure()
        return self.overview_val_container(Operation_Id=self._opnode.node_id,
                                           Operation_Type=self._opnode.type,
                                           Operation_Name=self._opnode.name,
                                           MACs=self.Macs,
                                           FLOPs=self.Flops)

    def measure(self):
        if self.is_measured:
            return
        
        hook = self.__regist_hook(self._model) # torch.utils.hooks.RemovableHandle

        self.is_measured = True

        return hook

    def __regist_hook(self, module):
        if isinstance(module, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
            h = module.register_forward_hook(self.__conv_hook)

        elif isinstance(module, (nn.Sigmoid, nn.Tanh, nn.ReLU, nn.ReLU6, nn.SiLU, nn.PReLU, nn.RReLU, nn.LeakyReLU)):
            h = module.register_forward_hook(self.__activate_hook)

        elif isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
            h = module.register_forward_hook(self.__BN_hook)

        elif isinstance(module, nn.Linear):
            h = module.register_forward_hook(self.__linear_hook)

        elif isinstance(module, (nn.MaxPool1d, nn.AvgPool1d, nn.MaxPool2d, nn.AvgPool2d, nn.MaxPool3d, nn.AvgPool3d)):
            h = module.register_forward_hook(self.__pool_hook)

        else:
            h = module.register_forward_hook(self.__not_support_hook)

        return h
    
    def __conv_hook(self, module, input, output):
        c_in = input[0].shape[1]
        n = c_in * reduce(mul, module.kernel_size)
        m = output.numel()
        is_bias = 1 if module.bias is not None else 0

        FLOPs = m*(2*n-1+is_bias)
        MACs = m*n
        self.__Macs += MACs
        self.__Flops += FLOPs
        
        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Kernel_Size=list(module.kernel_size),
                                                        Bias=bool(is_bias),
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape),
                                                        MACs=self.Macs.val,
                                                        FLOPs=self.Flops.val)
        )
    
    def __linear_hook(self, module, input, output):
        k = module.in_features
        l = module.out_features # noqa
        is_bias = 1 if module.bias is not None else 0
        n = k

        FLOPs = l*(2*n-1 + is_bias)
        MACs = l*n
        self.__Macs += MACs
        self.__Flops += FLOPs

        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Bias=bool(is_bias),
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape),
                                                        MACs=self.Macs.val,
                                                        FLOPs=self.Flops.val)
        )

    def __BN_hook(self, module, input, output):
        FLOPs = 4*input[0].numel()
        MACs = 0.5*FLOPs
        self.__Macs += MACs
        self.__Flops += FLOPs

        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape),
                                                        MACs=self.Macs.val,
                                                        FLOPs=self.Flops.val)
        )

    def __activate_hook(self, module, input, output):
        k = input[0].numel()
        if isinstance(module, (nn.Sigmoid, nn.PReLU, nn.RReLU, nn.LeakyReLU)):
            FLOPs = 4*k
            MACs = 2*k

        elif isinstance(module, nn.Tanh):
            FLOPs = 9*k
            MACs = 5*k

        elif isinstance(module, (nn.ReLU, nn.ReLU6)):
            FLOPs = k
            MACs = k

        else: # SiLU
            FLOPs = 5*k
            MACs = 3*k

        self.__Macs += MACs
        self.__Flops += FLOPs

        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape),
                                                        MACs=self.Macs.val,
                                                        FLOPs=self.Flops.val)
        )

    def __pool_hook(self, module, input, output):
        k = module.kernel_size
        k = (k,) if isinstance(k, int) else k
        n = reduce(mul, k)-1
        m = output.numel()

        if isinstance(module, (nn.MaxPool1d, nn.MaxPool2d, nn.MaxPool3d)):
            FLOPs = n*m
        else: # avgpool
            FLOPs = (2*n+1)*m
        MACs = n*m

        self.__Macs += MACs
        self.__Flops += FLOPs

        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Kernel_Size=list(k) if len(k)>1 else [k[0]]*2,
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape),
                                                        MACs=self.Macs.val,
                                                        FLOPs=self.Flops.val)
        )

    def __not_support_hook(self, module, input, output):
        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Input_Shape=list(input[0].shape),
                                                        Output_Shape=[len(output)]+list(output[0].shape))
        )

class MemMeter(Statistics):

    detail_val_container:NamedTuple = namedtuple(typename='Memory_INFO', 
                                                 defaults=(None,)*7,
                                                 field_names=['Operation_Id', 
                                                              'Operation_Name', 
                                                              'Operation_Type',
                                                              'Param_Cost', 
                                                              'Buffer_Cost', 
                                                              'FeatureMap_Cost',  
                                                              'Total'])
    
    overview_val_container:NamedTuple = namedtuple(typename='Memory_INFO', 
                                                   defaults=(None,)*7,
                                                   field_names=['Operation_Id', 
                                                                'Operation_Type',
                                                                'Operation_Name', 
                                                                'Param_Cost', 
                                                                'Buffer_Cost', 
                                                                'FeatureMap_Cost',  
                                                                'Total'])

    def __init__(self, opnode: OPN_TYPE):
        self._opnode = opnode
        self._model = opnode.operation
        
        self.__stat_ls = [] # record the memory cost of each operation
        self.is_measured = True if self._model._modules else False # only measure the leaf nodes

        _opparent = opnode.parent
        self.__ParamCost = self.init_linkdata(attr_name='ParamCost', init_val=0, opparent=_opparent)
        self.__BufferCost = self.init_linkdata(attr_name='BufferCost', init_val=0, opparent=_opparent)
        self.__FeatureMapCost = self.init_linkdata(attr_name='FeatureMapCost', init_val=0, opparent=_opparent)
        self.__TotalCost = self.init_linkdata(attr_name='TotalCost', init_val=0, opparent=_opparent)

    @property
    def name(self) -> str:
        return 'mem'

    @property
    def ParamCost(self) -> UpperLinkData :
        return self.__ParamCost
    
    @property
    def BufferCost(self) -> UpperLinkData:
        return self.__BufferCost

    @property
    def FeatureMapCost(self) -> UpperLinkData:
        return self.__FeatureMapCost
    
    @property
    def TotalCost(self) -> UpperLinkData:
        return self.__TotalCost
    
    @property
    def detail_val(self) -> List[NamedTuple]:
        self.measure()
        return self.__stat_ls
    
    @property
    def val(self) -> NamedTuple:
        self.measure()
        return self.overview_val_container(Operation_Id=self._opnode.node_id,
                                           Operation_Type=self._opnode.type,
                                           Operation_Name=self._opnode.name,
                                           Param_Cost=self.__ParamCost,
                                           Buffer_Cost=self.__BufferCost,
                                           FeatureMap_Cost=self.__FeatureMapCost,
                                           Total=self.__TotalCost)

    def measure(self):
        if self.is_measured:
            return
        
        hook = self._model.register_forward_hook(self.__hook_func)
        # TODO: measure backward cost (deal with the gradient)
        
        self.is_measured = True

        return hook

    def __hook_func(self, module, input, output):
        param_cost = 0 # byte
        for param in module.parameters():
            param_cost += param.numel() * param.element_size()
        self.__ParamCost += param_cost
        
        buffer_cost = 0 # byte
        for buffer in module.buffers():
            buffer_cost += buffer.numel() * buffer.element_size()
        self.__BufferCost += buffer_cost
        
        feat_cost = output.numel() * output.element_size() # byte
        self.__FeatureMapCost += feat_cost
        
        self.__TotalCost += param_cost + buffer_cost + feat_cost
        
        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Param_Cost=auto_unit(param_cost,unit_system=BinaryUnit), 
                                                        Buffer_Cost=auto_unit(buffer_cost,unit_system=BinaryUnit), 
                                                        FeatureMap_Cost=auto_unit(feat_cost,unit_system=BinaryUnit), 
                                                        Total=auto_unit(param_cost + buffer_cost + feat_cost,
                                                                        unit_system=BinaryUnit)))

class ITTPMeter(Statistics):

    detail_val_container:NamedTuple = namedtuple(typename='InferTime_Throughput_INFO', 
                                                 defaults=(None,)*5,
                                                 field_names=['Operation_Id', 
                                                              'Operation_Name', 
                                                              'Operation_Type',
                                                              'Infer_Time', 
                                                              'Throughput'])
    
    overview_val_container:NamedTuple = namedtuple(typename='InferTime_Throughput_INFO', 
                                                   defaults=(None,)*5,
                                                   field_names=['Operation_Id', 
                                                                'Operation_Name',
                                                                'Operation_Type',
                                                                'Infer_Time', 
                                                                'Throughput'])
                                                                
    def __init__(self, opnode: OPN_TYPE):
        self._opnode = opnode
        self._model = opnode.operation
        
        self.__stat_ls = [] # record the inference time and throughput of each operation

        self.__InferTime = MetricsData(reduce_func=np.median, unit_system=TimeUnit)
        self.__Throughput = MetricsData(reduce_func=np.median, unit_system=SpeedUnit)

    @property
    def name(self) -> str:
        return 'ittp'

    @property
    def InferTime(self) -> MetricsData :
        return self.__InferTime
    
    @property
    def Throughput(self) -> MetricsData:
        return self.__Throughput

    @property
    def detail_val(self) -> List[NamedTuple]:
        return self.__stat_ls
    
    @property
    def val(self) -> NamedTuple:
        return self.overview_val_container(Operation_Id=self._opnode.node_id,
                                           Operation_Type=self._opnode.type,
                                           Operation_Name=self._opnode.name,
                                           Infer_Time=self.__InferTime,
                                           Throughput=self.__Throughput)

    def measure(self, device, repeat:int=50, global_process=None):
        
        hook = self._model.register_forward_hook(partial(self.__hook_func, 
                                                         device=device, 
                                                         repeat=repeat,
                                                         global_process=global_process))
        
        return hook

    def __hook_func(self, module, input, output, device, repeat:int=50, global_process=None):
        self.__InferTime.clear()
        self.__Throughput.clear()
        self.__stat_ls.clear()
    
        module._forward_hooks.clear()
        module.eval()

        start_timer = perf_counter if device.type=='cpu' else cuda_event(enable_timing=True)
        end_timer = perf_counter if device.type=='cpu' else cuda_event(enable_timing=True)
                    
        with no_grad():
            for _ in range(repeat):
                start_time = start_timer() if device.type == 'cpu' else start_timer.record()

                module(*input)

                end_time = end_timer() if device.type == 'cpu' else end_timer.record()

                if device.type == 'cpu':
                    it = end_time-start_time
                else:
                    cuda_sync()  # WAIT FOR GPU SYNC
                    it = start_timer.elapsed_time(end_timer)*1e-3 # ms -> s

                tp = input[0].shape[0]/it
                self.__InferTime.append(it) 
                self.__Throughput.append(tp)

                if global_process is not None:
                    global_process.update(1)

        self.__stat_ls.append(self.detail_val_container(Operation_Id=self._opnode.node_id,
                                                        Operation_Name=self._opnode.name,
                                                        Operation_Type=self._opnode.type,
                                                        Infer_Time=str(self.__InferTime),
                                                        Throughput=str(self.__Throughput)))


