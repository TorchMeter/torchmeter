<!-- logo -->
<p align="center">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://github.com/TorchMeter/assets/blob/master/banner/banner_white.png?raw=true">
        <img src="https://github.com/TorchMeter/assets/blob/master/banner/banner_black.png?raw=true" alt="TorchMeter Banner">
    </picture>
</p>

<!-- caption -->
<p align="center">
    🚀 <ins>𝒀𝒐𝒖𝒓 𝑨𝒍𝒍-𝒊𝒏-𝑶𝒏𝒆 𝑻𝒐𝒐𝒍 𝒇𝒐𝒓 𝑷𝒚𝒕𝒐𝒓𝒄𝒉 𝑴𝒐𝒅𝒆𝒍 𝑨𝒏𝒂𝒍𝒚𝒔𝒊𝒔</ins> 🚀
</p>

<!-- badge -->
<p align="center">
    <a href="https://pypi.org/project/torchmeter/"><img alt="PyPI-Version" src="https://img.shields.io/pypi/v/torchmeter?logo=pypi&logoColor=%23ffffff&label=PyPI&color=%230C7EBF"></a>
    <a href="https://www.python.org/"><img alt="Python-Badge" src="https://img.shields.io/badge/Python-%3E%3D3.8-white?logo=python&logoColor=%232EA9DF&color=%233776AB"></a>
    <a href="https://pytorch.org/"><img alt="Pytorch-Badge" src="https://img.shields.io/badge/Pytorch-%3E%3D1.7.0-white?logo=pytorch&logoColor=%23EB5F36&color=%23EB5F36"></a>
    <a href="https://github.com/astral-sh/ruff"><img alt="Ruff-Badge" src="https://img.shields.io/badge/Ruff-Lint_%26_Format-white?logo=ruff&color=%238B70BA"></a>
    <a href="https://github.com/TorchMeter/torchmeter/blob/master/LICENSE"><img alt="Static Badge" src="https://img.shields.io/badge/License-AGPL--3.0-green"></a>
</p>

<!-- simple introduction -->

- **Docs**: https://torchmeter.github.io/docs/vers/latest/
- **Intro**: Provides comprehensive measurement of Pytorch model's `Parameters`, `FLOPs/MACs`, `Memory-Cost`, `Inference-Time` and `Throughput` with highly customizable result display ✨

## 𝒜. 𝐻𝒾𝑔𝒽𝓁𝒾𝑔𝒽𝓉𝓈

<details>
<summary>① 𝒁𝒆𝒓𝒐-𝑰𝒏𝒕𝒓𝒖𝒔𝒊𝒐𝒏 𝑷𝒓𝒐𝒙𝒚</summary>

- Acts as drop-in decorator **without** any changes of the underlying model
- Seamlessly integrates with `Pytorch` modules while preserving **full** compatibility (attributes and methods)

</details>

<details>
<summary>② 𝑭𝒖𝒍𝒍-𝑺𝒕𝒂𝒄𝒌 𝑴𝒐𝒅𝒆𝒍 𝑨𝒏𝒂𝒍𝒚𝒕𝒊𝒄𝒔</summary>

Holistic performance analytics across **5** dimensions: 

1. **Parameter Analysis**
    - Total/trainable parameter quantification
    - Layer-wise parameter distribution analysis
    - Gradient state tracking (requires_grad flags)
  
2. **Computational Profiling**
    - FLOPs/MACs precision calculation
    - Operation-wise calculation distribution analysis
    - Dynamic input/output detection (number, type, shape, ...)
  
3. **Memory Diagnostics** 
    - Input/output tensor memory awareness
    - Hierarchical memory consumption analysis

4. **Inference latency** & 5. **Throughput benchmarking**
    - Auto warm-up phase execution (eliminates cold-start bias)
    - Device-specific high-precision timing
    - Inference latency  & Throughput Benchmarking

</details>    

<details>
<summary>③ 𝑹𝒊𝒄𝒉 𝒗𝒊𝒔𝒖𝒂𝒍𝒊𝒛𝒂𝒕𝒊𝒐𝒏</summary>

1. **Programmable tabular report**
    - Dynamic table structure adjustment
    - Style customization and real-time rendering
    - Real-time data analysis in programmable way

2. **Rich-text hierarchical operation tree**
    - Style customization and real-time rendering
    - Smart module folding based on structural equivalence detection for intuitive model structure insights

</details>  

<details>
<summary>④ 𝑭𝒊𝒏𝒆-𝑮𝒓𝒂𝒊𝒏𝒆𝒅 𝑪𝒖𝒔𝒕𝒐𝒎𝒊𝒛𝒂𝒕𝒊𝒐𝒏</summary>

- **Real-time hot-reload rendering**: Dynamic adjustment of rendering configuration for operation trees, report tables and their nested components
- **Progressive update**: Namespace assignment + dictionary batch update

</details>  

<details>
<summary>⑤ 𝑪𝒐𝒏𝒇𝒊𝒈-𝑫𝒓𝒊𝒗𝒆𝒏 𝑹𝒖𝒏𝒕𝒊𝒎𝒆 𝑴𝒂𝒏𝒂𝒈𝒆𝒎𝒆𝒏𝒕</summary>

- **Centralized control**: Singleton-managed global configuration for dynamic behavior adjustment
- **Portable presets**: Export/import YAML profiles for runtime behaviors, eliminating repetitive setup

</details>

<details>
<summary>⑥ 𝑷𝒐𝒓𝒕𝒂𝒃𝒊𝒍𝒊𝒕𝒚 𝒂𝒏𝒅 𝑷𝒓𝒂𝒄𝒕𝒊𝒄𝒂𝒍𝒊𝒕𝒚</summary>

- **Decoupled pipeline**: Separation of data collection and visualization
- **Automatic device synchronization**: Maintains production-ready status by keeping model and data co-located
- **Dual-mode reporting** with export flexibility: 
    * Measurement units mode vs. raw data mode
    * Multi-format export (`CSV`/`Excel`) for analysis integration

</details>

## ℬ. 𝐼𝓃𝓈𝓉𝒶𝓁𝓁𝒶𝓉𝒾𝑜𝓃

> [!NOTE] 
> 𝑪𝒐𝒎𝒑𝒂𝒕𝒊𝒃𝒊𝒍𝒊𝒕𝒚
> - OS: `windows` /  `linux` / `macOS`    
> - `Python`: >= 3.8   
> - `Pytorch`: >= 1.7.0

<details>
<summary>① 𝑻𝒉𝒓𝒐𝒖𝒈𝒉 𝑷𝒚𝒕𝒉𝒐𝒏 𝑷𝒂𝒄𝒌𝒂𝒈𝒆 𝑴𝒂𝒏𝒂𝒈𝒆𝒓</summary>

> the most convenient way, suitable for installing the released **latest stable** version

```bash
# pip series
pip/pipx/pipenv install torchmeter

# Or via conda
conda install torchmeter

# Or via uv
uv add torchmeter

# Or via poetry
poetry add torchmeter

# Other managers' usage please refer to their own documentation
```

</details>

<details>
<summary>② 𝑻𝒉𝒓𝒐𝒖𝒈𝒉 𝑩𝒊𝒏𝒂𝒓𝒚 𝑫𝒊𝒔𝒕𝒓𝒊𝒃𝒖𝒕𝒊𝒐𝒏</summary>

> Suitable for installing released historical versions

1. Download `.whl` from [PyPI](https://pypi.org/project/torchmeter/#files) or [Github Releases](https://github.com/TorchMeter/torchmeter/releases).

2. Install locally:

    ```bash
    # Replace x.x.x with actual version
    pip install torchmeter-x.x.x.whl  
    ```

</details>

<details>
<summary>③ 𝑻𝒉𝒓𝒐𝒖𝒈𝒉 𝑺𝒐𝒖𝒓𝒄𝒆 𝑪𝒐𝒅𝒆</summary>

> Suitable for who want to try out the upcoming features (may has unknown bugs).

```bash
git clone https://github.com/TorchMeter/torchmeter.git
cd torchmeter

# If you want to install the released stable version, use this: 
# Don't forget to eplace x.x.x with actual version
git checkout vx.x.x  # Stable

# If you want to try the latest development version(alpha/beta), use this:
git checkout master  # Development version

pip install .
```

</details>

## 𝒞. 𝒢𝑒𝓉𝓉𝒾𝓃𝑔 𝓈𝓉𝒶𝓇𝓉𝑒𝒹

<!-- screenshot / gif -->
<p align="center">
    <img src="https://github.com/TorchMeter/assets/blob/master/demo/demo.gif?raw=true" alt="TorchMeter Demo">
    <font color="gray">Refer to <a href="https://torchmeter.github.io/docs/vers/latest/demo">tutorials</a> for all scenarios</font>
</p>

<details>
<summary>‌① 𝑫𝒆𝒍𝒆𝒈𝒂𝒕𝒆 𝒚𝒐𝒖𝒓 𝒎𝒐𝒅𝒆𝒍 𝒕𝒐 𝒕𝒐𝒓𝒄𝒉𝒎𝒆𝒕𝒆𝒓</summary>

> <details>
> <summary>Implementation of ExampleNet</summary>
> 
> ```python
> import torch.nn as nn
> 
> class ExampleNet(nn.Module):
>     def __init__(self):
>         super(ExampleNet, self).__init__()
>         
>         self.backbone = nn.Sequential(
>             self._nested_repeat_block(2),
>             self._nested_repeat_block(2)
>         )
> 
>         self.gap = nn.AdaptiveAvgPool2d(1)
> 
>         self.classifier = nn.Linear(3, 2)
>     
>     def _inner_net(self):
>         return nn.Sequential(
>             nn.Conv2d(10, 10, 1),
>             nn.BatchNorm2d(10),
>             nn.ReLU(),
>         )
> 
>     def _nested_repeat_block(self, repeat:int=1):
>         inners = [self._inner_net() for _ in range(repeat)]
>         return nn.Sequential(
>             nn.Conv2d(3, 10, 3, stride=1, padding=1),
>             nn.BatchNorm2d(10),
>             nn.ReLU(),
>             *inners,
>             nn.Conv2d(10, 3, 1),
>             nn.BatchNorm2d(3),
>             nn.ReLU()
>         )
> 
>     def forward(self, x):
>         x = self.backbone(x)
>         x = self.gap(x)
>         x = x.squeeze(dim=(2,3))
>         return self.classifier(x)
> ```
> 
> </details>

```python
import torch.nn as nn
from torchmeter import Meter
from torch.cuda import is_available as is_cuda

# 1️⃣ Prepare your pytorch model, here is a simple examples
underlying_model = ExampleNet() # see above for implementation of `ExampleNet`

# Set an extra attribute to the model to show 
# how torchmeter acts as a zero-intrusion proxy later
underlying_model.example_attr = "ABC"

# 2️⃣ Wrap your model with torchmeter
model = Meter(underlying_model)

# 3️⃣ Validate the zero-intrusion proxy

# Get the model's attribute
print(model.example_attr)

# Get the model's method
# `_inner_net` is a method defined in the ExampleNet
print(hasattr(model, "_inner_net")) 

# Move the model to other device (now on cpu)
print(model)
if is_cuda():
    model.to("cuda")
    print(model) # now on cuda
```

</details>

<details>
<summary>② 𝑮𝒆𝒕 𝒊𝒏𝒔𝒊𝒈𝒉𝒕𝒔 𝒊𝒏𝒕𝒐 𝒕𝒉𝒆 𝒎𝒐𝒅𝒆𝒍 𝒔𝒕𝒓𝒖𝒄𝒕𝒖𝒓𝒆</summary>

```python
from rich import print

print(model.structure)
```

</details>

<details>
<summary>③ 𝑸𝒖𝒂𝒏𝒕𝒊𝒇𝒚 𝒎𝒐𝒅𝒆𝒍 𝒑𝒆𝒓𝒇𝒐𝒓𝒎𝒂𝒏𝒄𝒆 𝒇𝒓𝒐𝒎 𝒗𝒂𝒓𝒊𝒐𝒖𝒔 𝒅𝒊𝒎𝒆𝒏𝒔𝒊𝒐𝒏𝒔</summary>

```python
# Parameter Analysis
# Suppose that the `backbone` part of ExampleNet is frozen
_ = model.backbone.requires_grad_(False)
print(model.param)
tb, data = model.profile('param', no_tree=True)

# Before measuring calculation you should first execute a feed-forward
# you do **not** need to concern about the device mismatch, 
# just feed the model with the input.
import torch
input = torch.randn(1, 3, 32, 32)
output = model(input) 

# Computational Profiling
print(model.cal) # `cal` for calculation
tb, data = model.profile('cal', no_tree=True)

# Memory Diagnostics
print(model.mem) # `mem` for memory
tb, data = model.profile('mem', no_tree=True)

# Performance Benchmarking
print(model.ittp) # `ittp` for inference time & throughput
tb, data = model.profile('ittp', no_tree=True)

# Overall Analytics
print(model.overview())
```

</details>

<details>
<summary>④ 𝑬𝒙𝒑𝒐𝒓𝒕 𝒓𝒆𝒔𝒖𝒍𝒕𝒔 𝒇𝒐𝒓 𝒇𝒖𝒓𝒕𝒉𝒆𝒓 𝒂𝒏𝒂𝒍𝒚𝒔𝒊𝒔</summary>

```python
# export to csv
model.profile('param', show=False, save_to="params.csv")

# export to excel
model.profile('cal', show=False, save_to="../calculation.xlsx")
```

</details>

<details>
<summary>⑤ 𝑨𝒅𝒗𝒂𝒏𝒄𝒆𝒅 𝒖𝒔𝒂𝒈𝒆</summary>

1. [Attributes/methods access of underlying model](https://torchmeter.github.io/docs/vers/latest/demo/#b-zero-intrusion-proxy)
2. [Automatic device synchronization](https://torchmeter.github.io/docs/vers/latest/demo/#c-automatic-device-synchronization)
3. [Smart module folding](https://torchmeter.github.io/docs/vers/latest/demo/#d-model-structure-analysis)
4. [Performance gallery](https://torchmeter.github.io/docs/vers/latest/demo/#eb-overall-report)
5. Customized visulization 
    - [for statistics overview](https://torchmeter.github.io/docs/vers/latest/demo/#fa-customization-of-statistics-overview)
    - [for operation tree](https://torchmeter.github.io/docs/vers/latest/demo/#fb-customization-of-rich-text-operation-tree)
    - [for tabular report](https://torchmeter.github.io/docs/vers/latest/demo/#fc-customization-of-tabular-report)
6. Best practice of programmable tabular report
    - [Real-time structure adjustment](https://torchmeter.github.io/docs/vers/latest/demo/#fc3-customize-tabular-report-structure)   
    - [Real-time data analysis](https://torchmeter.github.io/docs/vers/latest/demo/#fc34-add-a-new-column)
7. [Instant export and postponed export](https://torchmeter.github.io/docs/vers/latest/demo/#gb-postponed-export)
8. [Centralized configuration management](https://torchmeter.github.io/docs/vers/latest/demo/#h-centralized-configuration-management)
9. [Submodule exploration](https://torchmeter.github.io/docs/vers/latest/demo/#i4-submodule-explore)

</details>

## 𝒟. 𝒞𝑜𝓃𝓉𝓇𝒾𝒷𝓊𝓉𝑒

Thank you for wanting to make `TorchMeter` even better!

There are several ways to make a contribution:

- 💬 [Start/join discussions](CONTRIBUTING.md#-discussions--lets-collaborate--innovate)
- 🚨 [Report issues](CONTRIBUTING.md#-issues--lets-report--enhance)
- 👨‍💻 [Create pull requests (PRs)](CONTRIBUTING.md#-pull-requests--lets-squash-bugs--build-features)

Before jumping in, let's ensure smooth collaboration by reviewing our 📋 [**contribution guidelines**](CONTRIBUTING.md) first. 

Thanks again !

> [!NOTE]
> `@Ahzyuan`: I'd like to say sorry in advance. Due to my master's studies and job search, I may be too busy in the coming year to address contributions promptly. I'll do my best to handle them as soon as possible. Thanks a lot for your understanding and patience!

## ℰ. 𝒞𝑜𝒹𝑒 𝑜𝒻 𝒞𝑜𝓃𝒹𝓊𝒸𝓉

> Refer to official [code-of-conduct file](CODE_OF_CONDUCT.md) for more details.

- `TorchMeter` is an open-source project built by developers worldwide. We're committed to fostering a **friendly, safe, and inclusive** environment for all participants. 

- This code applies to all community spaces including but not limited to GitHub repositories, community forums, etc.

## ℱ. 𝐿𝒾𝒸𝑒𝓃𝓈𝑒

`TorchMeter` is released under the **AGPL-3.0 License**, see the [LICENSE](LICENSE) file for the full text. Please carefully review the terms in the [LICENSE](LICENSE) file before using or distributing `TorchMeter`. Ensure compliance with the licensing conditions, especially when integrating this project into larger systems or proprietary software.