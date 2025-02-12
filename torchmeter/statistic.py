from functools import reduce
from enum import IntFlag, unique
from collections import namedtuple
from abc import ABC, abstractmethod
from operator import attrgetter, mul
from typing import List, NamedTuple, Optional, TypeVar, Tuple, Union

import torch.nn as nn

OPN_TYPE = TypeVar("OperationNode")

@unique
class Unit(IntFlag):
    T:int = 2**40
    G:int = 2**30
    M:int = 2**20
    K:int = 2**10

def auto_unit(val:Union[int, float], suffix:str='') -> str:
    for unit in list(Unit):
        if val >= unit:
            return f'{val / unit:.2f} {unit.name + suffix}'

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
                repr_str += '• ' + f"{field.rjust(max_len)} = {field_val} = {auto_unit(field_val)}\n"
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
# ----------------------------------------------------------------------
'''
def count_memory(self, optimizer_type, print_tb=True, save_path=None):  # to calculate MAC
    if save_path:
        assert save_path[-4:]=='.csv','Strongly recommend using csv format!'

    tb_module_fields=['Module','Output Shape','Memory/MB']
    tb_param_fields=['Param Id','Param(Requires_Grad)','Floats Num','Memory/MB']
    tb_buffer_fields=['Buffer Id','Buffer','Floats Num','Memory/MB']
    tb_optim_fields=['Item Id','Optimizer Item','Params Num(Shared)','Memory/MB'] # Params Num为不共享内存的参数，Shared为共享参数，总参数等于两者之和
    tb_title='Input: tensor({},dtype=\'{}\')'.format(list(self.input.shape),str(self.input.dtype))
    self.clear_data()

    for module_name,module in self.model.named_children():
        if module._modules:
            self.modules_dict.update(self.unfold_layer(module,module_name))
        else:
            self.modules_dict.update({str(id(module)):(module_name,module)})  # 展开模型所有sequential、modulelist、moduledict等，以 {层地址:(层名，层)}的形式存为字典

    for no,(name, parameter) in enumerate(self.model.named_parameters()): 
        p_ptr=parameter.data_ptr()
        if p_ptr in self.param_ptr:
            self.neglect_id.append(id)
            continue
        
        self.param_ptr.append(p_ptr)
        p_num=parameter.numel()
        p_memory=p_num*self.element_byte # 计算各参数的字节数
        self.param_memory+=p_memory
        p_reg=True if parameter.requires_grad else False
        self.params_data.append([no+1,name+f'({p_reg})',p_num,'{:.4f}'.format(p_memory/1e6)])

    def hook_func(module,input,output):
        module_id=str(id(module))
        module_name=self.modules_dict[module_id][0]
        out_memory=output.numel()*self.element_byte # 计算中间层输出的字节数
        self.feat_memory+=out_memory
        self.modules_data.append([module_name,list(output.shape),'{:.4f}'.format(out_memory/1e6)])

    handle_list=list(map(lambda x:x[1].register_forward_hook(hook_func),self.modules_dict.values()))
    logits=self.model(self.input)
    list(map(lambda x:x.remove(),handle_list))

    for no,(name, buffer) in enumerate(self.model.named_buffers()): 
        b_num=buffer.numel()
        b_memory=b_num*self.element_byte # 计算各缓存参数的字节数
        self.buffer_memory+=b_memory
        self.buffers_data.append([no+1,name,b_num,'{:.4f}'.format(b_memory/1e6)])

    optimizer=optimizer_type(self.model.parameters(),lr=1e-4)
    optimizer.zero_grad()
    logits.max().backward()
    optimizer.step()
    for param_group in optimizer.param_groups:
        for param in param_group['params']:
            if param.data_ptr() in self.param_ptr: 
                self.shared_num+=1
                continue
            self.param_ptr.append(param.data_ptr())
            self.op_param_num+=param.numel()
            self.op_param_memory+=self.op_param_num*self.element_byte
    self.op_data.append([1,'Param Groups',f'{self.op_param_num}({self.shared_num})','{:.4f}'.format(self.op_param_memory/1e6)])

    self.shared_num=0
    for param, state_dict in optimizer.state.items():
        if param.data_ptr() in self.param_ptr: 
            self.shared_num+=1
        else:
            self.param_ptr.append(param.data_ptr())
            self.state_memory+=param.numel()*self.element_byte
        for name,state_data in state_dict.items():
            if isinstance(state_data,torch.Tensor):
                self.state_num+=1
                self.state_memory+=state_data.numel()*self.element_byte
    self.op_data.append([2,'State',f'{self.state_num}({self.shared_num})','{:.4f}'.format(self.state_memory/1e6)])

    tb=self.draw_table(tb_module_fields,self.modules_data)
    tb.title=tb_title
    tb.add_autoindex('Forward Step')

    divider=['─'*len('Forward Step'),'─'*(len('Param(Requires_Grad)')+3),'─'*len('Param(Output Shape)'),'─'*len('Memory/MB)')]
    tb.add_row(divider)
    tb.add_row(tb_param_fields)
    tb.add_row(divider)
    tb.add_rows(self.params_data)
    
    tb.add_row(divider)
    tb.add_row(tb_buffer_fields)
    tb.add_row(divider)
    if self.buffers_data:
        tb.add_rows(self.buffers_data)
    else:
        tb.add_row(['None','None','None','None'])

    tb.add_row(divider)
    tb.add_row(tb_optim_fields)
    tb.add_row(divider)
    tb.add_rows(self.op_data)

    if print_tb:
        print(tb)

    if save_path:
        with open(save_path,'w') as w:
            w.writelines(tb.get_csv_string().replace('\n',''))

    word_length=len('Optimizer Params Memory')
    print('# '+'Model Params Memory'.rjust(word_length)+' : {:e} MB'.format(self.param_memory/1e6)) # 参数+梯度的内存
    print('# '+'Model Buffers Memory'.rjust(word_length)+' : {:e} MB'.format(self.buffer_memory/1e6))
    print('# '+'Features Memory'.rjust(word_length)+' : {:e} MB'.format(self.feat_memory/1e6))
    print('# '+'Optimizer Params Memory'.rjust(word_length)+' : {:e} MB'.format(self.op_param_memory/1e6)) 
    print('# '+'Optimizer State Memory'.rjust(word_length)+' : {:e} MB'.format(self.state_memory/1e6))
    print('# '+'Gradian Memory'.rjust(word_length)+' : {:e} MB'.format(self.param_memory/1e6))
    print('# '+'Total Memory'.rjust(word_length)+' : {:e} MB'.format((self.feat_memory+self.op_param_memory+self.state_memory+self.param_memory*2+self.buffer_memory)/1e6))

def cal_ITTP(self, pick_device='cpu', warmup_iters=50, repeat=50): # to measure IT and TP
    """
    input_shape: (bs,channel,h,w) \n
    warmup_iters: 预热时的前向传播数 \n
    repeat: 重复测量多少次
    """
    device=torch.device(pick_device)
    self.model.to(device)
    input = torch.randn(self.input.shape).to(device)

    for _ in tqdm(range(warmup_iters),desc='Warming Up'):  # warm up
        self.model(input)

    IT_list=np.zeros(repeat)  # measure
    if device.type!='cpu':
        starter, ender = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    with torch.no_grad():
        for rep in tqdm(range(repeat),desc='Measuring'):
            if device.type=='cpu':
                start_time=time()
            else:
                starter.record()
            self.model(input)
            if device.type=='cpu':
                end_time=time()
            else:
                ender.record() 
                torch.cuda.synchronize()  # WAIT FOR GPU SYNC

        IT_list[rep] = end_time-start_time if device.type=='cpu' else (starter.elapsed_time(ender))*1e-3 # 后者计时单位为ms

    IT=IT_list.mean()
    TP=1/IT
    print('-'*15+'Result'+'-'*15)
    print(f'Device: {pick_device}\nSample Shape: {self.input.shape}')
    print('IT(Inference Time): {:.6f} s'.format(IT))
    print('TP(Throughput): {:.6f} samples/s'.format(TP))
'''

