from __future__ import annotations
from typing import TYPE_CHECKING

import torch.nn as nn
from rich import get_console
from rich.columns import Columns
from torch import Tensor
from torch import device as tc_device

from torchmeter.config import get_config
from torchmeter.statistic import Statistics
from torchmeter.display import render_perline

if TYPE_CHECKING:
    import sys
    from typing import Any, Dict, List, Tuple, Union, Optional
    
    from rich.tree import Tree
    from rich.text import Text
    from rich.table import Table
    from polars import DataFrame

    from torchmeter.config import FlagNameSpace
    from torchmeter.statistic import ParamsMeter, CalMeter, MemMeter, IttpMeter
    
    if sys.version_info >= (3, 8):
        from typing import TypedDict
    else:
        from typing_extensions import TypedDict

    class IPT_TYPE(TypedDict):
        args: Tuple[Any, ...]
        kwargs: Dict[str, Any]

__all__ = ["Meter"]
__cfg__ = get_config()

class Meter:
    """A comprehensive instrumentation tool for PyTorch model performance analysis and visualization.
    
    The `Meter` class provides end-to-end measurement capabilities for neural networks, including 
    parameter statistics, computational cost analysis, memory usage tracking, inference time and 
    throughput analysis. It serves as a wrapper around PyTorch modules while maintaining full compatibility 
    with native model operations.

    Key Features: `easy-to-use`, `comprehensive`, and `flexible`
        1. **Zero-Intrusion Proxy**  
            - acts as drop-in decorator without any changes of the underlying model
            - Seamlessly integrates with PyTorch modules while preserving full compatibility (attributes and methods)

        2. **Full-Stack Model Analytics**: Holistic performance analytics across 5 dimensions: 
            - parameter distribution
            - calculation cost: FLOPs/MACs
            - memory access assessment
            - inference latency
            - throughput benchmarking
        
        3. **Rich visualization**  
            - Programmable tabular reports with real-time rendering 
            - Hierarchical operation tree with smart folding of repeated blocks for model structure insights

        4. **Fine-Grained Customization**  
            - Real-time hot-reload rendering: Dynamic adjustment of rendering configuration for operation trees, 
                                            report tables and their nested components
            - Progressive update: Namespace assignment + dictionary batch update

        5. **Config-Driven Runtime Management**  
            - Centralized control: Singleton-managed global configuration for dynamic behavior adjustment
            - Portable presets: Export/import YAML profiles for runtime behaviors, eliminating repetitive setup

        6. **Portability and Practicality**  
            - Decoupled pipeline: Separation of data collection and visualization
            - Automatic device synchronization: Maintains production-ready status by keeping model and data co-located
            - Dual-mode reporting with export flexibility: 
                * Measurement units mode vs. raw data mode
                * Multi-format export (`CSV`/`Excel`) for analysis integration

    Core Functionality
        1. Parameter Analysis 
            - Total/trainable parameter quantification
            - Layer-wise parameter distribution analysis
            - Gradient state tracking (requires_grad flags)
        
        2. Computational Profiling
            - FLOPs/MACs precision calculation
            - Operation-wise calculation distribution analysis
            - Dynamic input/output detection (number, type, shape, ...)
        
        3. Memory Diagnostics 
            - Input/output tensor memory mapping
            - Hierarchical memory consumption analysis
        
        4. Performance Benchmarking
            - Auto warm-up phase execution (eliminates cold-start bias)
            - Device-specific high-precision timing
            - Inference latency  & Throughput Benchmarking

        5. Visualization Engine
            - Centralized configuration management
            - Programmable tabular report
                1. Style customization and real-time rendering
                2. Dynamic table structure adjustment
                3. Real-time data analysis in programmable way
                4. Multi-format data export
            - Rich-text hierarchical structure tree rendering
                1. Style customization and real-time rendering
                2. Smart module folding based on structural equivalence detection
        
        6. Cross-Platform Support
            - Automatic model-data co-location
            - Seamless device transition (CPU/CUDA)

    Attributes:
        ipt (Dict[str, Any]): Input arguments for underlying model's `forward` method.
        device (torch.device): Current computation device for model and tensor data in input .
        model (nn.Module): The wrapped PyTorch model instance.
        optree (OperationTree): A backend hierarchical data structure of model operations.
        tree_renderer (TreeRenderer): A renderer for operation tree visualization.
        table_renderer (TabularRenderer): A renderer for programmable tabular reports.
        ittp_warmup (int): Number of warm-up(i.e., feed-forward inference) iterations before `ittp` measurement.
        ittp_benchmark_time (int): Number of benchmark iterations per operation in measuring `ittp`.
        tree_fold_repeat (bool): Whether to fold repeated blocks in the rendered tree structure.
        tree_levels_args (FlagNameSpace): Rendering configuration for various levels of rendered tree structure.
        tree_repeat_block_args (FlagNameSpace): Rendering configuration for repeated blocks of rendered tree structure.
        table_display_args (FlagNameSpace): Comprehensive rendering configuration for rendered tables.
        table_column_args (FlagNameSpace): Rendering configuration for all of the rendered tables' columns.
        structure (rich.tree.Tree): A stylized tree representation of the model's operation hierarchy.
        param (ParamsMeter): A ParamsMeter instance containing the measured parameter-related statistics.
        cal (CalMeter): A CalMeter instance containing the measured computational cost data.
        mem (MemMeter): A MemMeter instance containing the measured memory usage data.
        ittp (IttpMeter): A IttpMeter instance containing fresh inference time and throughput data.
        model_info (Text): A `rich.Text` object containing the formatted model information.
        subnodes (List[str]): A list of all nodes in the operation tree with their IDs and names.

    Methods:
        __call__: Execute model inference while maintaining input and model device synchronization.
        __getattr__: Transparently proxy attribute access to the underlying model when not found in Meter instance.
        __setattr__: Prioritize setting attributes on Meter instance first, falling back to the underlying model.
        __delattr__: Try to delete attributes from Meter instance first, fall back to underlying model if needed.
        to: Move the model to the specified device while keeping input and model device synchronization.
        profile: Render a tabular report of the specified statistics with rich visualization.
        table_cols: Get all column names of the backend dataframe for the specified statistics.
        stat_info: Generates a formatted summary of the specified statistics.
        overview: Generates an overview of all statistics in a formatted layout.
        rebase: Rebases the Meter instance to a specific node in the operation tree.
    
    Note:
        - Requires at least one forward pass before most measurements become available.
        - Implements lazy evaluation and cache for most statistics (i.e. `param`, `cal`, `mem`). 

    Example:
        ```python
        from torchmeter import Meter, get_config
        from torchvision import models

        # prepare your torch model
        model = models.resnet152()

        # wrap the model with Meter class
        metered_model = Meter(model, device='cuda')

        # Basic usage
        input_tensor = torch.randn(1, 3, 224, 224).cuda()
        output = meter(input_tensor)  # Standard model execution
        
        # Performance analysis
        print(meter.structure)  # Visualize model hierarchy
        print(meter.param)      # Show parameter statistics
        meter.profile('cal')    # Display computational cost table
        
        # Device management
        meter.to('cpu')
        meter(input_tensor.cpu())
        ```
    """
    
    def __init__(self, 
                 model: nn.Module,
                 device:Optional[Union[str, tc_device]]=None) -> None:
        """Initialize a Meter instance for model performance measurement and visualization.

        Args:
            model (nn.Module): PyTorch model to be instrumented for measurement
            device (Optional[Union[str, torch.device]]): Target device for model execution and measurement.
                                                         Accepts either device string (e.g., 'cuda:0') or 
                                                         torch.device object. If None, automatically detects 
                                                         model's current device via its parameters.

        Raises:
            TypeError: If provided model is not a nn.Module instance
            UserWarning: When device is not specified and model contains no parameters (fallback to CPU)

        Notes:
            Initialization performs following key operations:
            1. Device configuration:
                - Uses specified device or auto-detects via model parameters
                - Moves model to target device

            2. Measurement infrastructure setup:
                - Initializes input capture dictionary (`_ipt`)
                - Builds operation tree (`optree`) for model structure analysis
                - Prepares renderers for visualization (`tree_renderer`, `table_renderer`)

            3. Measurement state initialization:
                - Resets measurement flags (`param`/`cal`/`mem`)
                - Sets default benchmark parameters (`ittp_warmup`=50, `ittp_benchmark_time`=100)
                - Initializes accuracy warning trackers (`_has_nocall_nodes`, `_has_not_support_nodes`)
        
        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models
            
            model = models.resnet18()

            # auto detect device
            metered_model = Meter(model)

            # init a gpu model
            metered_model = Meter(model, device='cuda')
            metered_model = Meter(model, device='cuda:1')
            ```
        """
        
        from torchmeter.engine import OperationTree
        from torchmeter.display import TreeRenderer, TabularRenderer

        if not isinstance(model, nn.Module):
            raise TypeError(f"model must be a nn.Module, but got `{type(model).__name__}`.")
        
        device = device or self.__device_detect(model)
        self.__device = tc_device(device) if isinstance(device, str) else device
        self.model = model.to(self.__device)

        self._ipt:IPT_TYPE = {'args':tuple(), 'kwargs':dict()} # TODO: self.ipt_infer()

        self.optree = OperationTree(self.model)

        self.tree_renderer = TreeRenderer(self.optree.root)
        self.table_renderer = TabularRenderer(self.optree.root)

        self.__measure_param = False
        self.__measure_cal = False
        self.__measure_mem = False
        self.ittp_warmup = 50
        self.ittp_benchmark_time = 100

        self.__has_nocall_nodes:Optional[bool] = None
        self.__has_not_support_nodes:Optional[bool] = None

    def __call__(self, *args, **kwargs) -> Any:
        """Execute model inference while maintaining input and model device synchronization.

        This method performs three key operations in order:
        1. Captures input arguments of underlying model's `forward` method for measurement purposes
        2. Align the device where the input tensor is located with the device where the model on.
        3. Executes the underlying model's feed-forward inference

        Args:
            *args: Positional arguments of the underlying model's `forward` method
            **kwargs: Keyword arguments of the underlying model's `forward` method

        Returns:
            Any: Output from the underlying model's feed-forward inference

        Raises:
            RuntimeError: If input data is needed but not provided.
                          (triggered by `_ipt2device()` method).

        Notes:
            - From a macroscopic perspective, this is equivalent to direct model invocation: 
                `meter_instance(input)` == `model(input)`
                
            - You can safely input tensors from different devices; automatic synchronization is handled:
                - Moves all tensors in the input to current device via `_ipt2device()`
                - Ensures model is on current device before execution

            - Subsequent calls perform two key operations:
                1. Overwrite captured inputs, enabling `ipt` updates through normal model invocation
                2. Clear cached measurements when input differs (determined by `Meter.__is_ipt_changed()` rules)
            
            - If there exists tensor data, its dimensions might directly impact the measurement results 
              of multiple statistics (e.g. `cal`, `mem`, `ittp`). For consistent and comparable results, 
              we recommend using **a single sample** for measuring all statistics. This can be achieved 
              by passing in a single batch of sample data whenever you want. 

        Example:
            ```python
            import torch
            import torch.nn as nn
            from torchmeter import Meter
            
            class MyModel(nn.Module):
                def __init__(self):
                    super(MyModel, self).__init__()
                    self.conv = nn.Conv2d(3, 10, 3)
                def forward(self, x, y=1):
                    return self.conv(x) + y                

            model = MyModel()
            metered_model = Meter(model, device='cuda:0')
            
            # Standard invocation
            output = metered_model(torch.randn(1, 3, 224, 224))
            
            # Mixed argument types
            output = metered_model(torch.randn(1, 3, 224, 224), y=2)
            ```
        """

        new_ipt:IPT_TYPE = {"args": args, "kwargs": kwargs}
        if self.__is_ipt_changed(new_ipt):
            self.__measure_param = False
            self.__measure_cal = False
            self.__measure_mem = False
            
        self._ipt = new_ipt
        self._ipt2device()
        self.model.to(self.device)
        return self.model(*self._ipt['args'], **self._ipt['kwargs'])
    
    def __getattr__(self, name: str) -> Any:
        """Transparently proxy attribute access to the underlying model when not found in Meter instance

        This method enables seamless attribute access to the wrapped model while maintaining Meter's 
        own attributes. It follows these resolution rules:
        1. Directly returns Meter's own attributes if they exist
        2. For attributes prefixed with "ORIGIN_", returns the underlying model's attribute with the prefix removed
        3. Otherwise, returns the corresponding attribute from the wrapped model

        Args:
            name (str): Name of the attribute to retrieve

        Returns:
            Any: The value of the requested attribute from either Meter instance or underlying model

        Raises:
            AttributeError: 
                - When the attribute does not exist in both Meter instance and underlying model
                - When using "ORIGIN_" prefix with non-existent attribute in underlying model

        Notes:
            - Attribute resolution priority:
                Meter's own attributes > underlying model's attributes (unless "ORIGIN_" prefix is used)

            - To bypass Meter's attributes and directly access model's attributes with same name:
                Use "ORIGIN_" prefix (e.g., `meter.ORIGIN_param` maps to `model.param`)

            - This implementation ensures the Meter instance can be seamlessly used as a drop-in replacement 
              for the underlying model without requiring code modifications
        """

        try:
            # get the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            return super().__getattribute__(name)
        
        except AttributeError:
            return getattr(self.model, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Prioritize setting attributes on Meter instance first, falling back to the underlying model.

        This method ensures:
        1. Class attributes defined in `Meter` that cannot be modified are blocked
        2. Instance attributes are set first, falling back to model attributes if not present
        3. Attributes prefixed with "ORIGIN_" will set the underlying model attribute after removing prefix

        Args:
            name (str): Name of the attribute to assign
            value (Any): Value to be assigned to the attribute

        Raises:
            AttributeError:
                - When attempting to set non-modifiable Meter class attributes.
                - When attribute assignment fails for both Meter instance and the underlying model

                 For example, the attributes 
                  . All these attributes are
                  
        Notes:
            - When encountering conflicting attribute names between Meter instance and the model:
                The Meter instance's attribute will be prioritized for assignment by default.
                To assign the underlying model's attribute with same name, prepend "ORIGIN_" prefix.
                Example: `meter_instance.ORIGIN_param = 1` will set model's `param` attribute to 1

            - This implementation ensures the Meter instance can be seamlessly used as a drop-in replacement 
              for the underlying model without requiring code modifications

            - Non-modifiable Meter class attributes are attributes defined by `@property` but without a setter.
              include:
                1. `ipt`
                2. `structure`
                3. `param`
                4. `cal`
                5. `mem`
                6. `ittp`
                7. `model_info`
                8. `subnodes`
        """
        
        cls_attrs:Dict[str, bool] = self.__get_clsattr_with_settable_flag()
        notchange_cls_attrs = [k for k,v in cls_attrs.items() if not v]
        
        if name in notchange_cls_attrs:
            raise AttributeError(f"`{name}` could never be set.")
        
        try:
            # set the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            
            super().__setattr__(name, value)
            
        except AttributeError:
            setattr(self.model, name, value)
    
    def __delattr__(self, name:str) -> None:
        """Try to delete attributes from Meter instance first, fall back to underlying model if needed.

        This method ensures:
        1. Class attributes defined in `Meter` cannot be deleted
        2. Instance attributes are deleted along with corresponding model attributes (if exists)
        3. Attributes prefixed with "ORIGIN_" will delete the actual model attribute after removing prefix

        Args:
            name (str): Name of the attribute to delete

        Raises:
            AttributeError: 
                - When trying to delete Meter's class attributes
                - When attempting to delete non-existent attributes
                - When failed to delete attribute from both Meter instance and the underlying model
        
        Notes:
            - When encountering conflicting attribute names between Meter instance and the model:
                The Meter instance's attribute will be prioritized for deletion by default.
                To delete the underlying model's attribute with same name, prepend "ORIGIN_" prefix.
                Example: `del meter_instance.ORIGIN_param` will delete model's `param` attribute

            - This implementation ensures the Meter instance can be seamlessly used as a drop-in replacement 
              for the underlying model without requiring code modifications
        """
        
        cls_attrs:Dict[str, bool] = self.__get_clsattr_with_settable_flag()
        
        if name in cls_attrs:
            raise AttributeError(f"`{name}` could never be deleted.")
        
        try:
            # delete the property with same name defined in Meter from origin model
            if name.startswith("ORIGIN_"):
                name = name[7:]
                raise AttributeError
            
            super().__delattr__(name)
            
        except AttributeError:
            delattr(self.model, name)
    
    @property
    def ipt(self) -> IPT_TYPE:
        """Captured underlying model input dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the captured model input.

        Notes:
            - This property is read-only and cannot be directly modified

            - Returned dictionary containing:
                - 'args' (tuple): Positional arguments passed to the `forward()` of the underlying model.
                - 'kwargs' (dict): Keyword arguments passed to the `forward()` of the underlying model

            - Input can only be set/updated through `Meter` instance calls 
              (i.e., feed-forward inference of the origin model)
              
            - If there exists tensor data, its dimensions might directly impact the measurement results 
              of multiple statistics (e.g. `cal`, `mem`, `ittp`). For consistent and comparable results, 
              we recommend using **a single sample** for measuring all statistics. This can be achieved 
              by providing a single-sample forward pass to the meter instance whenever you want. 
        """

        return self._ipt
    
    @property
    def device(self) -> tc_device:
        """The device where the model and all input tensors are currently located.

        Returns:
            torch.device: Current device as a torch.device object.
        """

        return self.__device
    
    @device.setter
    def device(self, new_device:Union[str, tc_device]) -> None:
        """Moves the model and all tensors in captured input to the specified device.

        This setter updates the device for both the model and its input tensors (if available).

        Args:
            new_device (Union[str, torch.device]): The target device, which can be a string (e.g., "cpu" or "cuda:0") 
                                                   or a torch.device object.

        Notes:
            - The device property is updated to reflect the new device.
            - If any tensors are present in `self._ipt`, they will also be moved to the new device.
            - Moves the model to the new device using `model.to()` in PyTorch.
        """
        
        self.__device = tc_device(new_device)
        self.model.to(self.__device)
        if not self._is_ipt_empty():
            self._ipt2device()

    @property
    def tree_fold_repeat(self) -> bool:
        """Controls whether repeated tree blocks are rendered as collapsed panels.

        This property directly binds to the `tree_fold_repeat` property in the global configuration. 
        When enabled, repeated operation blocks are collapsed into a single panel during tree rendering 
        via `Meter.structure`.

        Returns:
            bool: True to collapse repeated blocks, False to expand them.
        
        Note:
            - Repeated blocks are identified only when two operations exhibit structural equivalence in:
                1. Their own parameter signatures 
                2. Their child operations' hierarchical parameters
                3. The execution order within the operation if it is a container.
            
            - The folding feature activates exclusively for such validated repetitive patterns. 
              All other structures render sequentially following their topological order.

            - If your model doesn't have the repeated blocks mentioned above (like `AlexNet`), 
              setting this property True or False won't affect the output.
        """
        
        return __cfg__.tree_fold_repeat
    
    @tree_fold_repeat.setter
    def tree_fold_repeat(self, enable:bool) -> None:
        """Control rendering of repeated tree blocks as a single collapsed panel.

        Args:
            enable (bool): Toggle whether repeated blocks are rendered as a collapsed panel.

        Raises:
            TypeError: If value is not a boolean.

        Notes: 
            This property is directly bound to the `tree_fold_repeat` property in the global configuration, 
            so any change will be directly synchronized to the global settings.
            
        Example:
            ```python
            from rich import print
            from torchmeter import Meter
            from torchvision import models

            model = models.vit_b_16()
            metered_model = Meter(model)

            # creating a panel for repeat blocks
            metered_model.tree_fold_repeat = True
            print(metered_model.structure)

            # not creating a panel for repeat blocks
            metered_model.tree_fold_repeat = False
            print(metered_model.structure)
            ```
        """

        if not isinstance(enable, bool):
            raise TypeError("The `tree_fold_repeat` property can only be rewritten with a boolean, " + \
                            f"but got `{type(enable).__name__}`.")
        __cfg__.tree_fold_repeat = enable

    @property
    def tree_levels_args(self) -> FlagNameSpace:
        """Gets rendering configuration for various levels of rendered tree structure.

        This property directly binds to `torchmeter.display.TreeRenderer.tree_levels_args` 
        to get rendering configuration (e.g., label, guide_style) for various levels of rendered 
        tree structure generated via `Meter.structure` property. The configuration persists across  
        all subsequent tree renderings until explicitly modified.

        Returns:
            FlagNameSpace: A nested namespace where the outer-layer keys are the specific tree levels, 
                           and the values are the configuration namespaces for the corresponding levels. 
                           In each configuration namespace, the keys contain the specific configuration names, 
                           which match the valid parameters of `rich.tree.Tree`.
        """

        return self.tree_renderer.tree_levels_args
    
    @tree_levels_args.setter
    def tree_levels_args(self, custom_args:Dict[str, Dict[str, Any]]) -> None:
        """Sets rendering configuration for various levels of rendered tree structure via a dictionary.

        This property is bound to the `tree_levels_args` attribute of the internal `TreeRenderer` instance. 
        It allows users to batch configure the rendering configuration (e.g., label, guide_style) for tree 
        structure generated through the `Meter.structure` property. The provided dictionary maps configuration 
        names to their values for fine-grained control over table rendering.

        Args:
            custom_args (Dict[str, Dict[str, Any]]): A nested dictionary where the keys of the outer dictionary 
                                                     are tree level names (such as 0, 1, default), and the values 
                                                     are the inner configuration dictionaries for the corresponding 
                                                     levels. In the inner dictionary, the keys are the configuration 
                                                     names and the values are the corresponding configuration values.

        Raises:
            UserWarning: If the input dictionary contains keys that are not valid level names, then the corresponding 
                        configuration will be ignored.
            TypeError: If the input is not a dictionary type. 
            KeyError:  If the input dictionary contains keys that are not valid arguments for `rich.tree.Tree`.
        
        Notes:
            - Specified configurations will be updated, while unspecified ones remain unchanged. Therefore, users 
            can pass a partially configured dictionary.
            
            - If the keys in outer dictionary are invalid, then the configuration in its value will be ignored. Valid 
              level names include (all are strings):
                1. non-negative integer: "0", "1", ... Used to specify the configuration for the corresponding level
                2. "default": The configuration applied when encountering a level with unspecified configuration during 
                              the rendering process.
                3. "all": The configuration will be used for all levels.
            
            - Supported configurations of inner configuration dictionary include:
                1. `label` (str): Node representation string, accept rich styling
                2. `guide_style` (str): Guide style of the node, execute `python -m rich.theme` to see more
                3. ... see more at https://rich.readthedocs.io/en/latest/reference/tree.html#rich.tree.Tree
            
        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models

            model = models.resnet18()
            metered_model = Meter(model)

            # check all configurations
            print(metered_model.tree_levels_args)

            # only update two configuration, other configuration remain unchanged.
            metered_model.tree_levels_args = {
                "default": {"guide_style": "red"},
                "1": {"guide_style": "yellow"}
            }
            print(metered_model.tree_levels_args)
            ```
        """

        self.tree_renderer.tree_levels_args = custom_args   # type: ignore

    @property
    def tree_repeat_block_args(self) -> FlagNameSpace:
        """Gets rendering configuration for repeated blocks of rendered tree structure.

        This property directly binds to `torchmeter.display.TreeRenderer.repeat_block_args` 
        to get rendering configuration (e.g., style, highlight) for repeated blocks of rendered 
        tree structure generated via `Meter.structure` property. The configuration persists across  
        all subsequent tree renderings until explicitly modified.

        Returns:
            FlagNameSpace: A namespace containing concrete configuration names. 
                           Accessible keys match valid arguments of `rich.panel.Panel`.
        """

        return self.tree_renderer.repeat_block_args
    
    @tree_repeat_block_args.setter
    def tree_repeat_block_args(self, custom_args:Dict[str, Any]) -> None:
        """Sets rendering configuration for repeated blocks of rendered tree structure via a dictionary.

        This property is bound to the `repeat_block_args` attribute of the internal `TreeRenderer` instance. 
        It allows users to batch configure the rendering configuration (e.g., style, highlight) for tree 
        structure generated through the `Meter.structure` property. The provided dictionary maps configuration 
        names to their values for fine-grained control over table rendering.

        Args:
            custom_args (Dict[str, Any]): A dictionary where keys are configuration names and values are 
                                          the corresponding values to be set. 

        Raises:
            TypeError: If the input is not a dictionary type.
            KeyError:  If the input dictionary contains keys that are not valid arguments for `rich.panel.Panel`.

        Notes:
            - Specified configurations will be updated, while unspecified ones remain unchanged. Therefore, users 
            can pass a partially configured dictionary.

            - Supported configuration include:
                1. `style` (str): Style of the repeat block, execute `python -m rich.theme` to see more
                2. `title` (str): Title of the repeat block, accept rich styling
                3. `title_align` (str): Title alignment, left, center, right
                4. ... see more at https://rich.readthedocs.io/en/latest/reference/panel.html#rich.panel.Panel

        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models

            model = models.resnet18()
            metered_model = Meter(model)

            # check all configurations
            print(metered_model.tree_repeat_block_args)

            # only update two configuration, other configuration remain unchanged.
            metered_model.tree_repeat_block_args = {
                "title": "This block repeats for [[b]<repeat_time>[/b]] Times",
                "title_align": "right"
            }
            print(metered_model.tree_repeat_block_args)
            ```
        """

        self.tree_renderer.repeat_block_args = custom_args # type: ignore

    @property
    def table_display_args(self) -> FlagNameSpace:
        """Gets comprehensive rendering configuration for rendered tables.

        This property directly binds to `torchmeter.display.TabularRenderer.tb_args` 
        to get rendering configuration (e.g., style, highlight) for tables generated 
        via `Meter.profile()`. The configuration persists across all subsequent table  
        renderings until explicitly modified.

        Returns:
            FlagNameSpace: A namespace containing concrete configuration names. 
                           Accessible keys match valid arguments of `rich.table.Table`.
        """

        return self.table_renderer.tb_args

    @table_display_args.setter
    def table_display_args(self, custom_args:Dict[str, Any]) -> None:
        """Sets comprehensive rendering configuration for rendered tables via a dictionary.

        This property is bound to the `tb_args` attribute of the internal `TabularRenderer` instance. 
        It allows users to batch configure the comprehensive rendering configuration (e.g., style, highlight) 
        for tables generated through the `Meter.profile()` method with a dictionary. The provided dictionary maps 
        configuration names to their values for fine-grained control over table rendering.

        Args:
            custom_args (Dict[str, Any]): A dictionary where keys are configuration names and values are 
                                          the corresponding values to be set. 

        Raises:
            TypeError: If the input is not a dictionary type.
            KeyError: If the input dictionary contains keys that are not valid arguments for `rich.table.Table`.

        Notes:
            - Specified configurations will be updated, while unspecified ones remain unchanged. Therefore, users 
            can pass a partially configured dictionary.

            - Supported configuration include:
                1. `style` (str): Style of the table, execute `python -m rich.theme` to see more
                2. `highlight` (bool): Whether to highlight the value (number, string...)
                3. `show_header` (bool): Whether to show the header row
                4. `show_lines` (bool): Whether to show lines between rows
                5. ... see more at https://rich.readthedocs.io/en/latest/reference/table.html#rich.table.Table

        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models

            model = models.resnet18()
            metered_model = Meter(model)

            # check all configurations
            print(metered_model.table_display_args)

            # only update two configuration, other configuration remain unchanged.
            metered_model.table_display_args = {
                "style": "red",
                "show_lines": True
            }
            print(metered_model.table_display_args)
            ```
        """
        
        self.table_renderer.tb_args = custom_args       # type: ignore

    @property
    def table_column_args(self) -> FlagNameSpace:
        """Gets column rendering configuration for rendered tables.

        This property directly binds to `torchmeter.display.TabularRenderer.col_args` 
        to get column-level rendering configuration (e.g., style, justify) for tables 
        generated via `Meter.profile()`. The configuration persists across all subsequent 
        table renderings until explicitly modified.

        Returns:
            FlagNameSpace: A namespace containing concrete configuration names. 
                           Accessible keys match valid arguments of `rich.table.Column`.
        """

        return self.table_renderer.col_args

    @table_column_args.setter
    def table_column_args(self, custom_args:Dict[str, Any]) -> None:
        """Sets column-level rendering configuration for rendered tables via a dictionary.

        This property is bound to the `col_args` attribute of the internal `TabularRenderer` instance. 
        It allows users to batch configure column-specific rendering configuration (e.g., style, justify) 
        for tables generated through the `Meter.profile()` method. The provided dictionary maps configuration 
        names to their values for fine-grained control over table rendering.

        Args:
            custom_args (Dict[str, Any]): A dictionary where keys are configuration names and values are 
                                          the corresponding values to be set. 

        Raises:
            TypeError: If the input is not a dictionary type.
            KeyError: If the input dictionary contains keys that are not valid arguments for `rich.table.Column`.

        Notes:
            - Configuration changes will be applied to **all** columns of the rendered table.

            - Specified configurations will be updated, while unspecified ones remain unchanged. Therefore, users 
              can pass a partially configured dictionary.

            - Supported configuration include:
                1. `style` (str): Style of the column, execute `python -m rich.theme` to see more
                2. `justify` (str): Justify of the column, left, center, right
                3. `no_wrap` (bool): Prevent wrapping of text within the column.
                4. ... see more at https://rich.readthedocs.io/en/latest/reference/table.html#rich.table.Column

        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models

            model = models.resnet18()
            metered_model = Meter(model)

            # check all configurations
            print(metered_model.table_column_args)

            # only update two configuration, other configuration remain unchanged.
            metered_model.table_column_args = {
                "style": "bold green",
                "justify": "left"
            }
            print(metered_model.table_column_args)
            ```
        """
        
        self.table_renderer.col_args = custom_args      # type: ignore

    @property
    def structure(self) -> Tree:
        """Generate a stylized tree representation of the model's operation hierarchy.

        This property renders the operation tree based on current configuration settings. 
        The rendering strategy (folded/unfolded) and customization options are determined 
        by the active configuration parameters. Caching is applied to optimize rendering 
        performance when configuration remains unchanged.

        Returns:
            Tree: A `rich.tree.Tree` object representing the hierarchical structure of model operations.
        
        Notes:
            - Configuration parameters influence rendering behavior, you can access them directly 
              by `metered_model.<param_name>`
                * `tree_fold_repeat`: Controls whether a repeated block is rendered as a single block. 
                                      Default to True.
                * `tree_levels_args`: Customizes rendering at different tree levels.
                * `tree_repeat_block_args`: Detailed parameters to control the rendering of the repeat blocks.
            
            - Caching mechanism: Reuses cached render result if all configuration parameters remain 
              unchanged since last render.
              
            - For information on repeated blocks identification and rendering, please refer to the 
              description of `Meter.tree_fold_repeat` property.

        Example:
            ```python
            from rich import print
            from torchmeter import Meter
            from torchvision import models
            
            model = models.vit_b_16()
            metered_model = Meter(model)
            
            # use the default configuration
            print(metered_model.structure)
            
            # reaccess the structure, will be quickly returned
            print(metered_model.structure)
            
            # use a custom configuration
            metered_model.tree_fold_repeat = False
            metered_model.tree_levels_args = {
                "default": {"guide_style": "red"}
            }
            print(metered_model.structure)
            ```
        """

        fold_repeat = __cfg__.tree_fold_repeat
        
        is_rpbk_change = __cfg__.tree_repeat_block_args.is_change()
        
        is_level_change = __cfg__.tree_levels_args.is_change()
        
        if fold_repeat:
            cache_res = self.tree_renderer.render_fold_tree if not is_rpbk_change else None
        else:
            cache_res = self.tree_renderer.render_unfold_tree
        cache_res = cache_res if not is_level_change else None
        
        rendered_tree = self.tree_renderer() if cache_res is None else cache_res
        
        if is_rpbk_change and fold_repeat:
            __cfg__.tree_repeat_block_args.mark_unchange()
        if is_level_change:
            __cfg__.tree_levels_args.mark_unchange()
        
        # render_perline(renderable=rendered_tree)
        return rendered_tree

    @property
    def param(self) -> ParamsMeter:
        """Measures the number of model parameters.

        This property calculates the parameter-related metrics (e.g., number of parameters, 
        trainable parameters) for each node in the operation tree. 

        Returns:
            ParamsMeter: A ParamsMeter instance containing the measured parameter-related statistics.

        Notes:
            The measurement is performed only once for each Meter instance. Subsequent accesses 
            will return the cached result.
        """
        
        if not self.__measure_param:
            list(map(lambda node: node.param.measure(), self.optree.all_nodes))
            self.__measure_param = True

        return self.optree.root.param
    
    @property
    def cal(self) -> CalMeter:
        """Measures the calculation cost of the model during inference.

        This property calculates the computational cost (i.e., FLOPs and MACs) for each node in the 
        operation tree during a feed-forward inference pass.

        Returns:
            CalMeter:  A CalMeter instance containing the measured computational cost data.

        Raises:
            RuntimeError: If no input data has been provided (i.e., `self._ipt` is empty).

        Notes:
            - You must first invoke the Meter instance (via a forward pass) before accessing this property.
            
            - The measurement is performed only once for each Meter instance. Subsequent accesses 
              will return the cached result.

            - The measurement results depend on the model input, and different input tensor sizes 
              will lead to varying calculation costs, which is **normal**. For consistent and comparable 
              results, we recommend using **a single sample** for measuring all statistics including `cal`.
              This can be achieved by providing a single-sample forward pass to the meter instance whenever 
              you want.
        """
    
        if not self.__measure_cal:
            if self._is_ipt_empty():
                raise RuntimeError("Input unknown! You should perform at least one feed-forward inference before measuring calculation!") 

            hook_ls = [node.cal.measure() for node in self.optree.all_nodes]

            # feed forwad
            self._ipt2device()
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove() if x is not None else None, hook_ls)) 

            self.__measure_cal = True
        
        return self.optree.root.cal

    @property
    def mem(self) -> MemMeter:
        """Measures the memory cost of the model during inference.

        This property calculates the memory usage for each node in the operation tree during a 
        feed-forward inference pass.

        Returns:
            MemMeter: A MemMeter instance containing the measured memory usage data.

        Raises:
            RuntimeError: If no input data has been provided (i.e., `self._ipt` is empty).

        Notes:
            - You must first invoke the Meter instance (via a forward pass) before accessing this property.
            
            - The measurement is performed only once for each Meter instance. Subsequent accesses 
              will return the cached result.
              
            - The measurement results depend on the model input, and different input tensor sizes 
              will lead to varying memory costs, which is **normal**. For consistent and comparable 
              results, we recommend using **a single sample** for measuring all statistics including 
              `mem`. This can be achieved by providing a single-sample forward pass to the meter instance 
              whenever you want.
        """
        
        if not self.__measure_mem:
            if self._is_ipt_empty():
                raise RuntimeError("Input unknown! You should perform at least one feed-forward inference " + \
                                   "before measuring the memory cost!") 

            hook_ls = [node.mem.measure() for node in self.optree.all_nodes]

            # feed forward
            self._ipt2device()
            self.model(*self.ipt['args'], **self.ipt['kwargs']) 

            # remove hooks after measurement
            list(map(lambda x:x.remove() if x is not None else None, hook_ls))

            self.__measure_mem = True

        return self.optree.root.mem

    @property
    def ittp(self) -> IttpMeter:
        """Measures the inference time and throughput of the model.

        This property calculates the inference time and throughput for each node in the operation tree. 
        It performs a warm-up phase followed by a benchmark phase to ensure accurate measurements. 
        The results are returned as an `IttpMeter` object.

        Returns:
            IttpMeter: A IttpMeter instance containing fresh inference time and throughput data.

        Raises:
            RuntimeError: If no input data has been provided (i.e., `self._ipt` is empty).
            TypeError: If `self.ittp_warmup` is not an integer.
            ValueError: If `self.ittp_warmup` is a negative integer.

        Notes:
            - You must first invoke the Meter instance (via a forward pass) before accessing this property.
            
            - The measurements are performed on the device specified by `meter_instance.device` !!!
            
            - The unit `IPS` means **Input Per Second**, which is the number of inferences with given input
              per second. 
            
            - Unlike other statistics, the measured result is **not** cached, so it will be
              re-measured every time `ittp` attribute is accessed.
              
            - The warm-up phase runs for `meter_instance.ittp_warmup` iterations to stabilize the measurements.
            
            - The benchmark phase runs for `meter_instance.ittp_benchmark_time` iterations per operation.
            
            - The measurement results depend on the model input, and different input tensor sizes will lead to 
              varying latencies and throughput, which is **normal**. For consistent and comparable results, we 
              recommend using **a single sample** for measuring all statistics including `ittp`. This can be 
              achieved by providing a single-sample forward pass to the meter instance whenever you want.
        """
        
        from tqdm import tqdm

        if self._is_ipt_empty():
            raise RuntimeError("Input unknown! " + \
                               "You should perform at least one feed-forward inference before measuring the inference time or throughput!") 
        if not isinstance(self.ittp_warmup, int):
            raise TypeError(f"ittp_warmup must be an integer, but got `{type(self.ittp_warmup).__name__}`")
        if self.ittp_warmup < 0:
            raise ValueError(f"ittp_warmup must be greater than or equal to 0, but got `{self.ittp_warmup}`.")
        
        self._ipt2device()

        for i in tqdm(range(self.ittp_warmup), desc='Warming Up'):
            self.model(*self.ipt['args'], **self.ipt['kwargs'])

        pb = tqdm(total=self.ittp_benchmark_time*len(self.optree.all_nodes), 
                  desc='Benchmark Inference Time & Throughput', 
                  unit='module')
        hook_ls = [node.ittp.measure(device=self.device, 
                                     repeat=self.ittp_benchmark_time,
                                     global_process=pb) 
                    for node in self.optree.all_nodes]

        # feed forwad
        self.model(*self.ipt['args'], **self.ipt['kwargs']) 

        # remove hooks after measurement
        list(map(lambda x:x.remove() if x is not None else None, hook_ls))

        del pb

        return self.optree.root.ittp

    @property
    def model_info(self) -> Text:
        """Generates a formatted summary of the model's basic information.

        This property provides a detailed summary of the model, including its name, device, 
        forward method signature, and structured input representation.

        Returns:
            Text: A `rich.Text` object containing the formatted model information.

        Notes:
            - If no input has been provided (i.e., `self._ipt` is empty), the input representation will 
            indicate that it is not provided.
            
            - Otherwise, all the values in `self._ipt` will correspond to the formal arguments of the 
            `forward` method, and a structured input representation with type prompts will be generated 
            through the `torchmeter.utils.data_repr` function.
        """
    
        from inspect import signature
        from torchmeter.utils import indent_str, data_repr

        forward_args:List[str] = list(signature(self.model.forward).parameters.keys())
        if self._is_ipt_empty():
            ipt_repr = "[dim]Not Provided\n(give an inference first)[/]"
        else:
            ipt_dict = {forward_args[args_idx]: anony_ipt for args_idx, anony_ipt in enumerate(self.ipt['args'])}
            ipt_dict.update(self.ipt['kwargs'])
            ipt_repr_ls = [f"{args_name} = {data_repr(args_val)}" for args_name, args_val in ipt_dict.items()] 
            ipt_repr = ',\n'.join(ipt_repr_ls) 

        forward_args = ["self"] + forward_args
        infos = '\n'.join([
            f"• [b]Model    :[/b] {self.optree.root.name}",
            f"• [b]Device   :[/b] {self.device}",
            f"• [b]Signature:[/b] forward({', '.join(forward_args)})",
            f"• [b]Input    :[/b] \n{indent_str(ipt_repr, indent=3, guideline=False)}"
        ])
        
        console = get_console()
        return console.render_str(infos)

    @property
    def subnodes(self) -> List[str]:
        """Retrieves a list of all nodes in the operation tree with their IDs and names.

        This property returns a formatted list of all nodes in the operation tree, where each node is 
        represented by its ID and name. This is useful for identifying specific nodes when rebasing or 
        inspecting the tree structure.

        Returns:
            List[str]: A list of strings, each formatted as `(node_id) node_name`, representing all nodes 
                       in the operation tree.
        """
        return [f"({node.node_id}) {node.name}" for node in self.optree.all_nodes]

    def to(self, new_device:Union[str, tc_device]) -> None:
        """Move the model to the specified device while keeping input and model device synchronization.

        Simulate the `to` method of pytorch model and use it to move model and all tensor data in 
        `self._ipt` to the specified device.

        Args:
            new_device (Union[str, torch.device]): Target device name or its corresponding torch.device object.
            
        Example:
            ```python
            import torch
            from torchmeter import Meter
            from torchvision import models
            
            model = models.resnet18()
            metered_model = Meter(model)
            
            # move to cuda:0
            metered_model.to("cuda:0")
            
            # move to cpu
            metered_model.to(torch.device("cpu"))
            ```
        """
        self.device = new_device # type: ignore

    def rebase(self, node_id:str) -> Meter:
        """Rebases the Meter instance to a specific node in the operation tree.

        This method allows the Meter instance to focus on a specific node in the operation tree,
        effectively treating that node as the new root of a new Meter instance. If the provided
        node ID is "0", the original Meter instance is returned unchanged.

        Args:
            node_id (str): The ID of the node to rebase to. Must be a valid node ID in the operation tree.

        Returns:
            Meter: A new Meter instance with the specified node as the root.

        Raises:
            TypeError: If `node_id` is not a string.
            ValueError: If `node_id` does not exist in the operation tree.

        Notes:
            - Use `Meter(your_model).subnodes` to retrieve a list of valid node IDs.
            - If `node_id` is "0", the original Meter instance is returned without modification.
            
        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models
            
            model = models.resnet18()
            metered_model = Meter(model)
            rebased_model = metered_model.rebase("5")
            
            print(metered_model) # Meter(model=0 ResNet: ResNet, device=cpu)
            print(rebased_model) # Meter(model=0 Sequential: Sequential, device=cpu)
            ```
        """
    
        if not isinstance(node_id, str):
            raise TypeError(f"node_id must be a string, but got `{type(node_id).__name__}`.")
        
        if node_id == "0":
            return self
        
        id_generator = ( (node_idx, node.node_id) for node_idx, node in enumerate(self.optree.all_nodes) )

        for idx, valid_id in id_generator:
            if node_id == valid_id:
                new_base = self.optree.all_nodes[idx]
                return self.__class__(new_base.operation, device=self.device)
        else:
            raise ValueError(f"Invalid node_id: {node_id}. Use `Meter(your_model).subnodes` to check valid ones.")

    def stat_info(self, stat_or_statname:Union[str, Statistics], *, show_warning:bool=True) -> Text:
        """Generates a formatted summary of the specified statistics.

        This method provides a summary of the given statistics, including its name and the crucial data
        about this statistics. However, sometimes there may exist some modules which is defined but not 
        explicitly called, or some modules that its calculation measurement logic is not defined in this 
        version. To prevent confusing user, we will show inaccuracies warnings in the summary. If you don't 
        want to see these warnings, you can set `show_warning` to `False` manually.

        Args:
            stat_or_statname (Union[str, Statistics]): The name of the statistics or the statistics object itself.
            show_warning (bool): Whether to display warnings about potential inaccuracies. Defaults to True.

        Returns:
            Text: A `rich.Text` object containing the formatted summary.

        Raises:
            TypeError: If `stat_or_statname` is neither a string nor a `Statistics` object.

        Notes:
            - The main content will be obtained from the `crucial_data` property of the statistics object, which is defined 
              in the corresponding statistics class.
              
            - For `ittp`, the number of repeated measurements, namely `Benchmark Times`, will be additionally displayed. 
              This value can be accessed or modified through the `ittp_benchmark_time' attribute.
              
            - `show_warning` option is keyword-only argument, so you should use it through its keyword name.
            
            - Warnings are only shown for the following two statistics: calculation (`cal`) and memory (`mem`). Because
              only these two statistics are affected by the no called modules or the not supported mudules.

        Example:
            ```python
            from torch import randn
            from torchmeter import Meter
            from torchvision import models
            
            from rich import print
            
            model = models.vit_b_16()
            metered_model = Meter(model)
            metered_model(randn(1, 3, 224, 224))
            
            # using statistics name
            print(metered_model.stat_info("param"))
            
            # using statistics object
            cal = metered_model.cal
            print(metered_model.stat_info(cal))
            
            # not show warnings 
            print(metered_model.stat_info("mem", show_warning=False))
            ```
        """
    
        if isinstance(stat_or_statname, str):
            stat = getattr(self, stat_or_statname)
        elif isinstance(stat_or_statname, Statistics):
            stat = stat_or_statname
        else:
            raise TypeError(f"Invalid type for stat_or_statname: `{type(stat_or_statname).__name__}`. " + \
                            "Please pass in the statistics name or the statistics object itself.")

        stat_name = stat.name
        infos_ls:List[str] = [f"• [b]Statistics:[/b] {stat_name}"]
        
        if stat_name == 'ittp':
            infos_ls.append(f"• [b]Benchmark Times:[/b] {self.ittp_benchmark_time}")
            
        infos_ls.extend([
            f"• [b]{k}:[/b] {v}" for k, v in stat.crucial_data.items()
        ])
        
        ## warning field, only works when stat is "cal" or "mem"
        if show_warning and stat_name not in ("param", "ittp"):
            # cache for __has_nocall_nodes
            if self.__has_nocall_nodes is None:
                from operator import attrgetter
                
                crucial_data_getter = attrgetter(f"{stat_name}.crucial_data")
                try:
                    list(map(crucial_data_getter, self.optree.all_nodes))
                    self.__has_nocall_nodes = False
                except RuntimeError:
                    self.__has_nocall_nodes = True  
            
            # cache for __has_not_support_nodes
            if stat_name == "cal" and self.__has_not_support_nodes is None:
                self.__has_not_support_nodes = any(n.cal.is_not_supported 
                                                   for n in self.optree.all_nodes)
            
            warns_ls = []
            if self.__has_nocall_nodes:
                warns_ls.append(" "*2 + "[dim yellow]:arrow_forward:  Some nodes are defined but not called explicitly.[/]")
            if stat_name == "cal" and self.__has_not_support_nodes:
                warns_ls.append(" "*2 + "[dim yellow]:arrow_forward:  Some modules don't support calculation measurement yet.[/]")
            if warns_ls:
                warns_ls.insert(0, "[dim yellow]:warning:  Warning: the result may be inaccurate, cause:[/]")
                warns_ls.append(" "*2 + f"[dim cyan]:ballot_box_with_check:  use `Meter(your_model).profile('{stat_name}')` to see more.[/]")
            
            infos_ls.extend(warns_ls)
                    
        infos = '\n'.join(infos_ls)
        
        console = get_console()
        return console.render_str(infos)

    def overview(self, *order:str, show_warning:bool=True) -> Columns:
        """Generates an overview of all statistics in a formatted layout.

        This method creates a visual overview of model statistics, including basic model 
        information and core data of each specified statistic. You can customize the statistics 
        contained in the rendering results and their order by passing in the statistics you want 
        in the order you prefer.

        Args:
            *order (str): The names of the statistics to include in the overview. If not provided,
                        all available statistics are included.
            show_warning (bool): Whether to display warnings for potentially inaccurate results.
                                Defaults to True.

        Returns:
            Columns: A `rich.Columns` object containing the formatted overview.

        Raises:
            ValueError: If any of the provided statistics names are invalid.
        
        Example:
            ```python
            from torch import randn
            from torchmeter import Meter
            from torchvision import models
            
            model = models.resnet18()
            metered_model = Meter(model)
            metered_model(randn(1, 3, 224, 224))

            # overview all statistics (i.e. param, cal, mem, ittp)
            metered_model.overview() 
            
            # only overview `cal` and `param`
            # and the order is `cal` then `param`
            metered_model.overview("cal", "param") 
            ```
        """
        
        from functools import partial
        from rich.panel import Panel
        from rich.box import HORIZONTALS

        order = order or self.optree.root.statistics
        
        invalid_stat = tuple(filter(lambda x: x not in self.optree.root.statistics, order))
        if len(invalid_stat) > 0:
            raise ValueError(f"Invalid statistics: {invalid_stat}")
        
        container = Columns(expand=True, align='center')
        format_cell = partial(Panel, safe_box=True, expand=False, highlight=True, box=HORIZONTALS)
        
        container.add_renderable(format_cell(self.model_info, title='[b]Model INFO[/]', border_style='orange1'))
        container.renderables.extend([format_cell(self.stat_info(stat_name, show_warning=show_warning), 
                                                  title=f"[b]{stat_name.capitalize()} INFO[/]",
                                                  border_style='cyan') 
                                      for stat_name in order])
        
        return container

    def table_cols(self, stat_name:str) -> Tuple[str, ...]:
        """Get all column names of the backend dataframe for the specified statistics.
        
        This method returns the column names of the backend dataframe associated with the given statistics. 
        If the dataframe is empty(i.e. the `profile` is not called yet), it falls back to the values of the
        `tb_fields` property of corresponding statistics class.

        Args:
            stat_name (str): The name of the statistics for which to retrieve the columns.

        Returns:
            Tuple[str, ...]: A tuple of column names for the specified statistics backend dataframe.

        Raises:
            TypeError: If `stat_name` is not a string.
            KeyError: If `stat_name` is not found in the available statistics (i.e. `param`, `cal`, `mem`, `ittp`).
        
        Notes:
            default column names for each statistics:
                - param: ("Operation_Id", "Operation_Name", "Operation_Type", 
                          "Param_Name", "Requires_Grad", "Numeric_Num")
                
                - cal: ("Operation_Id", "Operation_Name", "Operation_Type", 
                        "Kernel_Size", "Bias", "Input", "Output", "MACs", "FLOPs")
                
                - mem: ("Operation_Id", "Operation_Name", "Operation_Type", 
                        "Param_Cost", "Buffer_Cost", "Output_Cost", "Total")
                
                - ittp: ("Operation_Id", "Operation_Name", "Operation_Type", 
                         "Infer_Time", "Throughput")
            
        Example:
            ```python
            from torchmeter import Meter
            from torchvision import models
            
            model = models.resnet18()
            metered_model = Meter(model)
            
            metered_model.table_cols("param")
            # ('Operation_Id',
            #  'Operation_Name',
            #  'Operation_Type',
            #  'Param_Name',
            #  'Requires_Grad',
            #  'Numeric_Num')
            
            metered_model.table_cols("cal")
            # ('Operation_Id',
            #  'Operation_Name',
            #  'Operation_Type',
            #  'Kernel_Size',
            #  'Bias',
            #  'Input',
            #  'Output',
            #  'MACs',
            #  'FLOPs')
            ```
        """
        
        if not isinstance(stat_name, str):
            raise TypeError(f"stat_name must be a string, but got `{type(stat_name).__name__}`.")
        
        stats_data_dict:Dict[str, DataFrame] = self.table_renderer.stats_data
        
        if stat_name not in stats_data_dict:
            raise KeyError(f"Statistics `{stat_name}` not in {tuple(stats_data_dict.keys())}.")
        
        stat_data:DataFrame = stats_data_dict[stat_name]
        
        if stat_data.is_empty():
            cols:Tuple[str, ...] = getattr(self.optree.root, stat_name).tb_fields
        else:
            cols = tuple(stat_data.columns)
        
        return cols
    
    def profile(self, 
                stat_name:str, 
                show:bool=True, no_tree:bool=False, 
                **tb_kwargs) -> Tuple[Table, DataFrame]:
        """Render a tabular report of the specified statistics with rich visualization.

        This method generates an interactive table visualization for the given statistical data,
        optionally combined with the model's operation tree structure. The rendering supports
        real-time customization through keyword arguments and can export data to multiple formats.

        Args:
            stat_name (str): Name of the statistics to profile (i.e., 'param', 'cal', 'mem', 'ittp').
            
            show (bool, optional): Whether to immediately render the visualization and display in terminal.
                                   Defaults to True.
            
            no_tree (bool, optional): Not to display the rendered tree when set to True. Defaults to False.
            
            **tb_kwargs: Additional table customization options:
                - raw_data (bool): Use raw numerical data instead of formatted values with unit. 
                                   Defaults to False.
                - pick_cols (Sequence[str]): Whitelist of columns to display. Defaults to [].
                - exclude_cols (Sequence[str]): Blacklist of columns to hide. Defaults to [].
                - custom_cols (Dict[str, str]): Column rename mappings (original: new). Defaults to {}.
                - keep_custom_name (bool): Whether to keep custom names after this call. Defaults to False.
                - newcol_name (str): Name for new computed column. Defaults to ''.
                - newcol_func (Callable[[DataFrame], ArrayLike]): Function to compute new column values. 
                                                                  Defaults to lambda df: [None]*len(df).
                - newcol_type (Optional[PolarsDataType]): Explicit data type for new column. Defaults to None.
                - newcol_idx (int): Insertion position for new column (-1=append). Defaults to -1.
                - keep_new_col (bool): Retain new columns in backend dataframe and subsequent renders. 
                                       Defaults to False.
                - save_to (Optional[str]): File path for data export, not None to trigger export. Defaults to None.
                - save_format (Optional[str]): Export format, None to use the value in `save_to`. 
                                               Now we only support 'csv' or 'xlsx' file. Defaults to None.

        Returns:
            Tuple[rich.table.Table, polars.DataFrame]: The rendered `rich.table.Table` object and 
                                                       underlying polars DataFrame.

        Raises:
            RuntimeWarning: If your model has some modules defined but not explicitly called.
            
            AttributeError: If `stat_name` is not a valid statistics name.
            
            ValueError: 
                - If horizontal gap defined in global config is negative when disable `no_tree`.
                - If you specify any not existing column name to `pick_cols` when enable `show` and `pick_cols`.
                - If you pass in a directory path as `save_to` but not specify `save_format`.
                - If you pass in a non csv or xlsx file path as `save_to`.
                - If you pass in a non-supported export format as `save_format`.
                - If `newcol_name` already exists in the backend dataframe.
            
            RuntimeError: 
                - If terminal width is insufficient for display when enable `show`.
                - If no input data has been provided (i.e., `ipt` property is empty) and `stat_name` is 
                  one of `cal`, `mem`, or `ittp`.
                - If no module is called (e.g. the underlying model's `forward` method is not empty).
                - If the whole model is empty and has no sublayers.
                - If using a single layer as a model
                - If `newcol_func` returns values with length mismatch to the underlying dataframe's row count
                  
            TypeError: 
                - If `stat_name` is not a string
                - If `pick_cols` is not a list, tuple or set.
                - If `exclude_cols` is not a list, tuple or set.
                - If `custom_cols` is not a dict.
                - If `newcol_name` is not a string.
                - If `newcol_func` is uncallable 
                - If `newcol_func` doesn't have exactly **1** formal parameter
                - If return value of `newcol_func` is not array-like
                - If `newcol_idx` is not an integer.
                - If `newcol_type` is not a valid Polars data type.
                - If `save_to` is not a string, neither None.
                - If `save_format` is not a string, neither None.

        Notes:
            1. Ensure at least one forward pass has been executed before accessing `cal`/`mem`/`ittp` statistics to 
               guarantee valid input capture.

            2. Table and tree rendering styles can be preconfigured through the properties:
                - `table_display_args`
                - `table_column_args`
                - `tree_fold_args`
                - `tree_levels_args`
                - `tree_repeat_block_args`
            
            3. The rendering result will be progressively displayed line-by-line with a time interval. 
               You can configure this interval through the following steps (must be non-negative):
                ```python
                from torchmeter import get_config
                cfg = get_config()
                cfg.render_interval = 0.5 # unit second, should be non-negative
                ```
            
            4. Disable rendering (`show=False`) when only exporting data to reduce computational overhead.

            5. Enable `no_tree` to:
                - Enable focused data analysis
                - Hide the operation tree for narrow terminals
                - Default layout shows tree left + table right (may enforce row separators if space constrained)

            6. Horizontal spacing between tree and table is controlled by `combine.horizon_gap` in global config.
               You should promise the value is non-negative.

            7. When `raw_data=True` displays unformatted values:
                - `param`: Parameter counts
                - `cal`: FLOPs/MACs counts  
                - `mem`: Bytes consumed
                - `ittp`: Median inference time (seconds) and inferences per second per module
            
            8. Column management:
                - Use `pick_cols` to reorder columns (validate column names via 
                  `metered_instance.table_cols(stat_name)`)
                - Processing order: `pick_cols` -> `exclude_cols` -> `custom_cols` -> `newcol`
                - Conflicts: 
                    - picked columns override custom/newcol names
                    - exclusions override picks
            
            9. About `newcol_func`:
                - must have exactly **1** formal parameter (name irrelevant) that will receive the 
                  underlying `polars.DataFrame` of specified statistics.
                - Implement logic using the incoming dataframe to return new column values (must be 1D array-like data
                  such as `Series`, `lists`, `ndarrays`, etc.). Note that you can use `val` property to access the 
                  raw data for all statistics (for `ittp`, the return will be a tuple made up of the median and iqr of 
                  the measurement data sequence).
                - The example below demonstrates adding a percentage column of the `cal` statistics. Refer to 
                  https://docs.pola.rs/api/python/stable/reference/dataframe/index.html for using `polars.Dataframe`.
                    
            10. The `newcol_idx` parameter mostly follows Python list insertion semantics:
                - Negative values count backward from end (`-1`=`append`)
                - `0` inserts at beginning
                - Values exceeding column count clamp to nearest valid position:
                  * Negative abs values > column count → insert at start
                  * Positive values > column count → append at end

            12. Session persistence:
                - `keep_new_col` retains created columns
                - `keep_custom_name` preserves renamed columns
            
            13. Export paths:
                - Directory paths require explicit `save_format`
                - File paths auto-detect format from extension unless `save_format` overrides
            
        Example:
            ```python
            import torch
            from torchmeter import Meter
            from torchvision import models
            
            # wrap your model with Meter
            model = models.alexnet()
            metered_model = Meter(model)

            # execute a forward inference (necessary, to provide input data)
            input = torch.randn(1, 3, 224, 224)
            metered_model(input)

            # check column names of cal tabel
            print(metered_model.table_cols('cal'))
            # ('Operation_Id', 'Operation_Name', 'Operation_Type', 'Kernel_Size', 'Bias', 
            # 'Input', 'Output', 'MACs', 'FLOPs')

            def newcol_logic(df):
                flops_col = df['FLOPs']
                return flops_col.map_elements(
                    lambda x: f"{100 * x / metered_model.cal.Flops:.4f} %"
                )

            # Customized profile with column operations
            metered_model.profile(
                'cal',

                # render and display immediately
                show=True,                                           
                no_tree=True,
                raw_data=False, 

                # columns management
                exclude_cols=['Kernel_Size', 'Bias'],     
                custom_cols={'Operation_Id': 'ID', 'Operation_Name': 'Module Name', 'Operation_Type': 'Module Type'},  
                newcol_name='Percentage',                          
                newcol_func=newcol_logic,
                newcol_type=str,
                newcol_idx=-1,

                # export
                save_to='./cal_profile.xlsx',                       
                save_format='xlsx',
            )
            ```
        """

        from rich.rule import Rule
        from rich.layout import Layout

        # the horizontal gap between tree and table
        TREE_TABLE_GAP = __cfg__.combine.horizon_gap

        if not isinstance(stat_name, str):
            raise TypeError(f"stat_name must be a string, but got `{type(stat_name).__name__}`.") 

        if TREE_TABLE_GAP < 0:
            raise ValueError("The gap between the rendered tree and the rendered table should be non-negative, " + \
                             f"but got `{TREE_TABLE_GAP}`.")
        
        stat = getattr(self, stat_name)
        tb, data = self.table_renderer(stat_name=stat_name, **tb_kwargs)
        
        if not show:
            return tb, data
        
        tree = None if no_tree else self.structure
        
        console = get_console()
        tree_width = console.measure(tree).maximum if not no_tree else 0 # type: ignore
        desirable_tb_width = console.measure(tb).maximum
        actual_tb_width = min(desirable_tb_width, console.width - tree_width - TREE_TABLE_GAP)
        
        if actual_tb_width <= 5: # 5 is the minimum width of table
            raise RuntimeError("The width of the terminal is too small, try to maximize the window or " + \
                               "set a smaller `horizon_gap` value in config and try again.")
        
        # when some cells in the table is overflown, we need to show a line between rows
        if actual_tb_width < desirable_tb_width:
            tb.show_lines = True 
        
        # get main content(i.e. tree & statistics table)
        if no_tree:
            main_content = tb
            tree_height = 0
        else:
            main_content = Layout()
            main_content.split_row(Layout(tree, name='left', size=tree_width + TREE_TABLE_GAP),
                                   Layout(tb, name='right', size=actual_tb_width))
            tree_height = len(console.render_lines(tree)) # type: ignore
        
        temp_options = console.options.update_width(actual_tb_width) 
        tb_height = len(console.render_lines(tb, options=temp_options))
        main_content_height = max(tree_height, tb_height)
        main_content_width = tree_width + actual_tb_width + (0 if no_tree else TREE_TABLE_GAP)

        # get footer content
        footer = Columns(title=Rule('[gray54]s u m m a r y[/]', characters='-', style='gray54'), # type: ignore
                         padding=(1,1),
                         equal=True, 
                         expand=True)
        
        model_info = self.model_info
        stat_info = self.stat_info(stat_or_statname=stat, show_warning=False)
        model_info.style = 'dim'
        stat_info.style = 'dim'
        footer.add_renderable(model_info)
        footer.add_renderable(stat_info)

        temp_options = console.options.update_width(main_content_width)
        footer_height = len(console.render_lines(footer, options=temp_options))
        
        # render profile
        canvas = Layout()
        canvas.split_column(Layout(main_content, name='top', size=main_content_height),
                            Layout(footer, name='down', size=footer_height))
        
        origin_width = console.width
        origin_height = console.height
        console.width = main_content_width
        console.height = main_content_height + footer_height
        
        try: 
            render_perline(renderable=canvas)
        finally:
            # if user interupts the rendering when render_interval > 0
            # still restore the console size
            console.width = origin_width
            console.height = origin_height
        
        return tb, data

    def _is_ipt_empty(self) -> bool:
        """Determine whether the model input has been provided

        Returns:
            bool: whether the input required for a feed-forward is clear
        """
        return not self._ipt['args'] and not self._ipt['kwargs']
        
    def _ipt2device(self) -> None:
        """Moves all input tensors to the specified device.

        This method checks if the input tensors are already on the specified device. 
        If not, it moves them to the device set in the Meter instance.

        Raises:
            RuntimeError: If input data is needed but not provided (i.e., `self._ipt` is empty).

        Notes:
            - The method only processes tensors in the input.
            - Non-tensor inputs remain unchanged.
        """

        from inspect import signature
        forward_args = signature(self.model.forward).parameters

        if len(forward_args) and self._is_ipt_empty():
            raise RuntimeError("No input data provided.")

        devices = set(arg.device for arg in self._ipt['args'] if isinstance(arg, Tensor))
        devices.update(kwargs.device for kwargs in self._ipt['kwargs'].values() if isinstance(kwargs, Tensor))

        if not len(devices):
            return
        
        if len(devices) == 1 and next(iter(devices)) == self.device:
            return

        self._ipt = {
            'args': tuple(x.to(self.device) if isinstance(x, Tensor) else x 
                          for x in self._ipt['args']),
            'kwargs': {k: (v.to(self.device) if isinstance(v, Tensor) else v) 
                       for k, v in self._ipt['kwargs'].items()}
        }

    def __device_detect(self, model) -> Union[str, tc_device]:
        """Detects the device where the model are located via model's parameters.

        This method detects the model's device by checking its parameters' location. 
        If no parameters are found, it will raise a warning and move the model to CPU by default.

        Args:
            model (nn.Module): The model whose device is to be detected.

        Returns:
            Union[str, torch.device]: The device where the model's parameters are located. If no parameters are found, 
            returns 'cpu' as the default device.

        Raises:
            UserWarning: If the model has no parameters, a warning is issued indicating that the model will be moved 
            to CPU for subsequent analysis.
        """
        
        import warnings
        
        try:
            model_first_param = next(model.parameters())
            return model_first_param.device
        
        except StopIteration:
            warnings.warn(category=UserWarning, message=\
                "We can't detect the device where your model is located because no parameter was found in your model. " + \
                "We'll move your model to CPU and do all subsequent analysis based on this CPU version. " + \
                "If this isn't what you want, set a specific device when initializing the `Meter` class, " + \
                "e.g. `Meter(your_model, device='cuda:0')`.")
                          
            return "cpu"
        
    def __is_ipt_changed(self, new_ipt:IPT_TYPE) -> bool:
        """Determines if the new input differs from the current captured input.

        Compares both positional arguments (args) and keyword arguments (kwargs) between current and new input:
        - For Tensor arguments: Checks shape and dtype equivalence
        - For non-Tensor arguments: Performs value equality check
        - Verifies argument structure consistency (same length for args, same keys for kwargs)

        Args:
            new_ipt: New input arguments to compare against currently stored input. 
                     It is a dictionary with two keys:
                        - `args`: A tuple containing all positional arguments.
                        - `kwargs`: A dictionary containing all keyword arguments.

        Returns:
            bool: `True` if any of following conditions met:
                   1. Current input is empty (first-time input)
                   2. Positional arguments differ in length/value type/shape (for Tensors)
                   3. Keyword arguments have different keys or values
                   4. Any argument value differs (non-Tensor) or tensor properties differ (Tensor)
        """
        
        if self._is_ipt_empty():
            return True
        
        is_changed = False
        
        if len(self._ipt["args"]) == len(new_ipt["args"]):
            for origin, new in zip(self._ipt["args"], new_ipt["args"]): 
                if type(origin) is not type(new):
                    is_changed = True
                elif isinstance(origin, Tensor):
                    is_changed = origin.shape != new.shape or origin.dtype != new.dtype
                else:
                    is_changed = origin != new   
                
                if is_changed:
                    return True
        else:
            return True

        if set(self._ipt["kwargs"].keys()) == set(new_ipt["kwargs"].keys()):
            for k, origin in self._ipt["kwargs"].items():
                new = new_ipt["kwargs"][k]
                
                if type(origin) is not type(new):
                    is_changed = True
                elif isinstance(origin, Tensor):
                    is_changed = origin.shape != new.shape or origin.dtype != new.dtype
                else:
                    is_changed = origin != new   
                
                if is_changed:
                    return True
        else:
            return True
        
        return False
        
    def __repr__(self) -> str:
        return f"Meter(model={self.optree}, device={self.device})"

    @classmethod
    def __get_clsattr_with_settable_flag(cls) -> Dict[str, bool]:
        """Determines which class attributes have setter methods defined.

        This method iterates over all properties of the class and checks if a setter method
        is defined for each property. It returns a dictionary mapping attribute names to a
        boolean indicating whether the attribute is settable.

        Returns:
            Dict[str, bool]: A dictionary where keys are attribute names and values indicate
            whether the attribute has a setter method (True if settable, False otherwise).
        """
        
        return {k:v.fset is not None for k,v in cls.__dict__.items() 
                if isinstance(v, property)}
        