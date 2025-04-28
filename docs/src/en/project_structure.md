# Project Structure Documentation

This document outlines the architecture of `torchmeter`'s codebase, detailing each module's purpose and functionality.

Hoping this helps you quickly understand the structure of `torchmeter` and boosts your contribution efficiency.

## ① **Structure Overview**

```text
torchmeter
├── __init__.py         # Package initialization & metadata  
├── __cli__.py          # CLI tool implementation (not implemented) 
├── py.typed            # PEP-561 type hinting marker
├── _stat_numeric.py    # Numeric data structures for metric tracking  
├── unit.py             # Unit systems and automatic unit conversion  
├── utils.py            # Utility functions/classes for common tasks  
├── core.py             # Central analytics engine for PyTorch model analysis  
├── config.py           # Configuration management with YAML and singleton patterns  
├── engine.py           # Hierarchical operation trees for model structure analysis 
├── display.py          # Visualization components for model architecture and metrics  
└── statistic.py        # Modular meters for model parameter/computation/memory/inference-time/thoughput analysis   
```

## ② **Detailed Introduction**

### 1. `__init__.py`

1. **Purpose**: Implements package initialization, defining metadata, versioning, and public API declarations.  

2. **Global Variables**  
   - `__version__`: Package version identifier.  
   - `__all__`: Explicitly declares public API exports.  

3. **Functions**: *None*  

4. **Classes**: *None*  

---

### 2. `__cli__.py`

> Not implemented yet  

1. **Purpose**: Implements command-line interface (CLI) tool logic.  

2. **Global Variables**: *None*  

3. **Functions**: 
   - `main`: Main entry point for CLI tool.

4. **Classes**: *None*  

---

### 3. `py.typed`

1. **Purpose**: Serves as a PEP 561 type hinting marker for static type checking.  

---

### 4. `_stat_numeric.py`

1. **Purpose**: Implements numeric data structures for metric tracking and statistical aggregation 

2. **Global Variables**: *None*

3. **Functions**: *None*

4. **Classes**:  
    - `NumericData` (ABC) An abstract class for numeric data operations  
    - `UpperLinkData`: Implement hierarchical metric tracking with parent-child relationships  
    - `MetricsData`: Implement batch metric collection and statistical analysis  

---

### 5. `unit.py`

1. **Purpose**: Implements unit systems and automatic unit conversion for numeric values  

2. **Global Variables**:  
    - `__all__`: Public API exports (`CountUnit`, `BinaryUnit`, `TimeUnit`, `SpeedUnit`, `auto_unit`)  

3. **Functions**:  
   - `auto_unit`: Automatically selects appropriate unit based on value magnitude and formats as string  

4. **Classes**:  
    - `CountUnit` (Enum): Decimal-based unit system (K/M/G/T for 1e3/1e6/1e9/1e12)  
    - `BinaryUnit` (IntFlag): Binary-based unit system (KiB/MiB/GiB/TiB for 2^10/20/30/40)  
    - `TimeUnit` (Enum): Time unit system (h/min/s/ms/us/ns)  
    - `SpeedUnit` (Enum): Operational speed unit system (Input Per Second, IPS/KIPS/MIPS/GIPS/TIPS)  

---

### 6. `utils.py`

1. **Purpose**: Provides utility functions or classes for common tasks such as file io, string formatting etc.

2. **Global Variables**:  
    - `__all__`: Public API exports (`dfs_task`, `data_repr`, `Timer`)  

3. **Functions**:  
    - `resolve_savepath`: Decouples save path into dir and filename, and allows customizable filenames, validates file extensions. 
    - `hasargs`: Validates required arguments exist in a function signature  
    - `dfs_task`: Executes depth-first search tasks on hierarchical data structures  
    - `indent_str`: Formats text with customizable indentation and guidelines  
    - `data_repr`: Generates rich-formatted string representations for data structures  
    - `match_polars_type`: Infers Polars data types from Python/Numpy objects  

4. **Classes**:  
    - **`Timer` (Status)**: Context manager for tracking and displaying execution time  

---

### 7. `core.py`

1. **Purpose**: Provides a central analytics engine for `PyTorch` model performance analysis and visualization.  

2. **Global Variables**:  
    - `__all__`: Public API exports (`Meter`)  
    - `__cfg__`: Global configuration  

3. **Functions**: *None*  

4. **Classes**:  
    - **`Meter`**: Provides end-to-end measurement capabilities for neural networks, including 
    parameter statistics, computational cost analysis, memory usage tracking, inference time and 
    throughput analysis. It serves as a wrapper around `PyTorch` modules while maintaining full compatibility 
    with native model operations.

---

### 8. `config.py`

1. **Purpose**: Provides centralized configuration management for visualization parameters and layout presets through YAML parsing, singleton pattern enforcement, and reactive change tracking. 

2. **Global Variables**  
    - `__all__`: Public API exports (`get_config`, `Config`)
    - `DEFAULT_CFG`: Stores default YAML configurations for rendering intervals, tree/table styling, and layout parameters.  

3. **Functions**  
    - `list_to_callbacklist`: Wraps lists with mutation callbacks for state tracking.  
    - `dict_to_namespace`: Converts dictionaries to observable `FlagNameSpace` objects recursively.  
    - `namespace_to_dict`: Serializes `FlagNameSpace` back to dictionaries for persistence.  
    - `get_config`: Ensures thread-safe singleton access to configuration instances with environment/file override support.  

4. **Classes**  
    - `ConfigMeta`: Enforces singleton pattern via metaclass for global configuration consistency.  
    - `Config`: Central configuration manager handling YAML loading, validation, and dynamic updates.  
    - `FlagNameSpace`: Extends `SimpleNamespace` with nested change tracking.  
    - `CallbackList/CallbackSet`: Collection proxies that propagate modification events through callback chains

---

### 9. `engine.py`

1. **Purpose**: Constructs hierarchical operation trees for `PyTorch` models to track parameters, computational costs, memory usage, and inference time metrics.  

2. **Global Variables**  
    - `__all__`: Public API exports (`OperationNode`, `OperationTree`).  

3. **Functions**: *None*  

4. **Classes**  
    - `OperationNode`: Represents individual model components with hierarchical relationships, stores module meta info, statistical metrics (parameters, computation, memory, throughput), and tracks module repetitions.  
    - `OperationTree`: Constructs the structural and display trees simultaneously through depth-first traversal, and identifying repeated modules to implement smart folding of repeated blocks.

---

### 10. `display.py`

1. **Purpose**: Implements visualization components for rendering `PyTorch` model architecture as rich text tree and performance metrics as programmable tabular reports, supporting configuration-driven styling and data export capabilities.  

2. **Global Variables** 
    - `__all__`: Public API exports (`render_perline`, `TreeRenderer`, `TabularRenderer`).  
    - `__cfg__`: Global configuration.

3. **Functions**  
    - `apply_setting`: Dynamically applies configuration in tree or tabular report rendering process.
    - `render_perline`: Implements progressive rendering with configurable delay for terminal animation effects.  

4. **Classes**  
    - `TreeRenderer`: Generates collapsible tree visualizations with loop algebra notation for repeated modules through depth-first traversal and configuration inheritance.  
    - `TabularRenderer`: Produces customizable metric tables with column filtering/renaming, dynamic column management(rename, insert, delete and interact), and CSV/XLSX export functionality.  

---

### 11. `statistic.py`

1. **Purpose**: Implements metering tools for comprehensive PyTorch model analysis across parameters, computation, memory, and inference performance through modular measurement components.  

2. **Global Variables**  
   - `__all__`: Public API exports (`ParamsMeter`, `CalMeter`, `MemMeter`, `IttpMeter`).  

3. **Functions**: *None*  

4. **Classes**  
    - `Statistics`: Abstract base class defining common interfaces and properties for all specialized metric calculators.  
    - `ParamsMeter`: Quantifies total/learnable parameters across model layers with hierarchical aggregation capabilities.  
    - `CalMeter`: Calculates floating-point operations (FLOPs/MACS) using layer-specific forward hooks and kernel analysis.  
    - `MemMeter`: Measures parameter/buffer/memory overhead in binary units via deep object size inspection.  
    - `IttpMeter`: Benchmarks inference latency/throughput using device-optimized timing (CPU wall-clock/CUDA events)
