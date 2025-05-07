# Copyright (C) 2024 TorchMeter, Ahzyuan. - All Rights Reserved
# You may use, distribute and modify this code under the terms of the AGPL-3.0 license.

"""
torchmeter 🚀
------------------------------------------------------------------------------------------------------------
An `all-in-one` tool for `Pytorch` model analysis, providing end-to-end measurement capabilities, including:
  - parameter statistics
  - computational cost analysis
  - memory usage tracking
  - inference time
  - throughput analysis

------------------------------------------------------------------------------------------------------------
Core Functionality:
  1. Parameter Analysis
    - Total/trainable parameter quantification
    - Layer-wise parameter distribution analysis
    - Gradient state tracking (requires_grad flags)

  2. Computational Profiling
    - FLOPs/MACs precision calculation
    - Operation-wise calculation distribution analysis
    - Dynamic input/output detection (number, type, shape, ...)

  3. Memory Diagnostics
    - Input/output tensor memory awareness
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
------------------------------------------------------------------------------------------------------------
Author: Ahzyuan
Project: https://github.com/TorchMeter/torchmeter
"""

__version__ = "0.1.0"

from torchmeter.core import Meter
from torchmeter.config import get_config

__all__ = ["Meter", "get_config"]
