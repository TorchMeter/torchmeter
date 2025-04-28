---
hide:
  - toc
  - navigation
---

<!-- logo -->
![TorchMeter Banner](assets/banner/banner_black.png#only-light)
![TorchMeter Banner](assets/banner/banner_white.png#only-dark)

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

- **Repo**: https://github.com/TorchMeter/torchmeter
- **Intro**: Provides {++comprehensive++} measurement of `Pytorch` model's `Parameters`, `FLOPs/MACs`, `Memory-Cost`, `Inference-Time` and `Throughput` with {++highly customizable++} result display ✨

## 𝒜. 𝐻𝒾𝑔𝒽𝓁𝒾𝑔𝒽𝓉𝓈

??? tip ":material-numeric-1-circle-outline: 𝚉𝚎𝚛𝚘-𝙸𝚗𝚝𝚛𝚞𝚜𝚒𝚘𝚗 𝙿𝚛𝚘𝚡𝚢"

    - [x] Acts as ^^drop-in^^ decorator {++without++} any changes of the underlying model
    - [x] Seamlessly integrates with `Pytorch` modules while preserving {++full++} compatibility (attributes and methods)

??? tip ":material-numeric-2-circle-outline: 𝙵𝚞𝚕𝚕-𝚂𝚝𝚊𝚌𝚔 𝙼𝚘𝚍𝚎𝚕 𝙰𝚗𝚊𝚕𝚢𝚝𝚒𝚌𝚜"

    Holistic performance analytics across {++5++} dimensions: 

    - [x] {++Parameter Analysis++}
        - Total/trainable parameter quantification
        - Layer-wise parameter distribution analysis
        - Gradient state tracking (requires_grad flags)
    
    - [x] {++Computational Profiling++}
        - FLOPs/MACs precision calculation
        - Operation-wise calculation distribution analysis
        - Dynamic input/output detection (number, type, shape, ...)
    
    - [x] {++Memory Diagnostics++} 
        - Input/output tensor memory awareness
        - Hierarchical memory consumption analysis

    - [x] {++Inference latency & 5. Throughput benchmarking++}
        - Auto warm-up phase execution (eliminates cold-start bias)
        - Device-specific high-precision timing
        - Inference latency  & Throughput Benchmarking

??? tip ":material-numeric-3-circle-outline: 𝚁𝚒𝚌𝚑 𝚅𝚒𝚜𝚞𝚊𝚕𝚒𝚣𝚊𝚝𝚒𝚘𝚗"

    - [x] {++Programmable tabular report++}
        - Dynamic table structure adjustment
        - Style customization and real-time rendering
        - Real-time data analysis in programmable way

    - [x] {++Rich-text hierarchical operation tree++}
        - Style customization and real-time rendering
        - Smart module folding based on structural equivalence detection for intuitive model structure insights

??? tip ":material-numeric-4-circle-outline: 𝙵𝚒𝚗𝚎-𝙶𝚛𝚊𝚒𝚗𝚎𝚍 𝙲𝚞𝚜𝚝𝚘𝚖𝚒𝚣𝚊𝚝𝚒𝚘𝚗"

    - [x] {++Real-time hot-reload rendering++}: <br> Dynamic adjustment of rendering configuration for operation trees, report tables and their nested components <br>

    - [x] {++Progressive update++}: <br>Namespace assignment + dictionary batch update

??? tip ":material-numeric-5-circle-outline: 𝙲𝚘𝚗𝚏𝚒𝚐-𝙳𝚛𝚒𝚟𝚎𝚗 𝚁𝚞𝚗𝚝𝚒𝚖𝚎 𝙼𝚊𝚗𝚊𝚐𝚎𝚖𝚎𝚗𝚝"

    - [x] {++Centralized control++}: <br>Singleton-managed global configuration for dynamic behavior adjustment <br>

    - [x] {++Portable presets++}: <br>Export/import YAML profiles for runtime behaviors, eliminating repetitive setup

??? tip ":material-numeric-6-circle-outline: 𝙿𝚘𝚛𝚝𝚊𝚋𝚒𝚕𝚒𝚝𝚢 𝚊𝚗𝚍 𝙿𝚛𝚊𝚌𝚝𝚒𝚌𝚊𝚕𝚒𝚝𝚢"

    - [x] {++Decoupled pipeline++}: <br>Separation of data collection and visualization <br>

    - [x] {++Automatic device synchronization++}: <br>Maintains production-ready status by keeping model and data co-located <br>

    - [x] {++Dual-mode reporting++} with export flexibility: 
        - Measurement units mode vs. raw data mode
        - Multi-format export (`CSV`/`Excel`) for analysis integration

## ℬ. 𝐼𝓃𝓈𝓉𝒶𝓁𝓁𝒶𝓉𝒾𝑜𝓃

???+ example "𝙲𝚘𝚖𝚙𝚊𝚝𝚒𝚋𝚒𝚕𝚒𝚝𝚢"

    - **OS**: `windows` / `linux` / `macOS`    
    - **Python**: >= 3.8   
    - **Pytorch**: >= 1.7.0

??? abstract "𝚃𝚑𝚛𝚘𝚞𝚐𝚑 𝙿𝚢𝚝𝚑𝚘𝚗 𝙿𝚊𝚌𝚔𝚊𝚐𝚎 𝙼𝚊𝚗𝚊𝚐𝚎𝚛"

    > the most convenient way, suitable for installing the released **latest stable** version

    ```{ .bash .no-copy title="" linenums="1" hl_lines="2 5 8 11" } 
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

??? abstract "𝚃𝚑𝚛𝚘𝚞𝚐𝚑 𝙱𝚒𝚗𝚊𝚛𝚢 𝙳𝚒𝚜𝚝𝚛𝚒𝚋𝚞𝚝𝚒𝚘𝚗"

    > Suitable for installing released historical versions

    1. Download `.whl` from [PyPI](https://pypi.org/project/torchmeter/#files) or [Github Releases](https://github.com/TorchMeter/torchmeter/releases).

    2. Install locally:

        ```{.bash title=""}
        pip install torchmeter-x.x.x.whl # (1)
        ```
        
        1.    :man_raising_hand: Replace `x.x.x` with actual version

??? abstract "𝚃𝚑𝚛𝚘𝚞𝚐𝚑 𝚂𝚘𝚞𝚛𝚌𝚎 𝙲𝚘𝚍𝚎"

    > Suitable for who want to try out the upcoming features (may has unknown bugs).

    ```{.bash  title=""}
    git clone https://github.com/TorchMeter/torchmeter.git
    cd torchmeter

    # If you want to install the released stable version, use this: 
    git checkout vx.x.x # Stable (1)

    # If you want to try the latest development version(alpha/beta), use this:
    git checkout master  # Development version

    pip install .
    ```

    1.    :man_raising_hand: Don't forget to eplace `x.x.x` with actual version. You can check all available versions with `git tag -l`

## 𝒞. 𝒢𝑒𝓉𝓉𝒾𝓃𝑔 𝓈𝓉𝒶𝓇𝓉𝑒𝒹

<!-- screenshot / gif -->
<p align="center">
    <img src="assets/demo/demo.gif" alt="TorchMeter Demo">
    <font color="gray">Refer to <a href="examples/demo.ipynb">demo notebook</a> for all scenarios</font>
</p>

??? success ":material-numeric-1-circle-outline: 𝙳𝚎𝚕𝚎𝚐𝚊𝚝𝚎 𝚢𝚘𝚞𝚛 𝚖𝚘𝚍𝚎𝚕 𝚝𝚘 𝚝𝚘𝚛𝚌𝚑𝚖𝚎𝚝𝚎𝚛"

    ??? info "Implementation of ExampleNet"

        ```python
        import torch.nn as nn

        class ExampleNet(nn.Module):
            def __init__(self):
                super(ExampleNet, self).__init__()
                
                self.backbone = nn.Sequential(
                    self._nested_repeat_block(2),
                    self._nested_repeat_block(2)
                )

                self.gap = nn.AdaptiveAvgPool2d(1)

                self.classifier = nn.Linear(3, 2)
            
            def _inner_net(self):
                return nn.Sequential(
                    nn.Conv2d(10, 10, 1),
                    nn.BatchNorm2d(10),
                    nn.ReLU(),
                )

            def _nested_repeat_block(self, repeat:int=1):
                inners = [self._inner_net() for _ in range(repeat)]
                return nn.Sequential(
                    nn.Conv2d(3, 10, 3, stride=1, padding=1),
                    nn.BatchNorm2d(10),
                    nn.ReLU(),
                    *inners,
                    nn.Conv2d(10, 3, 1),
                    nn.BatchNorm2d(3),
                    nn.ReLU()
                )

            def forward(self, x):
                x = self.backbone(x)
                x = self.gap(x)
                x = x.squeeze(dim=(2,3))
                return self.classifier(x)
        ```

    ```python
    import torch.nn as nn
    from torchmeter import Meter

    # prepare your pytorch model
    underlying_model = ExampleNet() # (1)
    underlying_model.example_attr = "ABC"

    # suppose that the backbone is freezed
    for p in model.backbone.parameters():
        p.requires_grad = False

    # create a proxy for your model
    model = Meter(underlying_model)
    print(model)

    # move to gpu
    model.to("cuda")

    # validate the proxy
    print(getattr(model, "example_attr"))
    print(hasattr(model, "_inner_net"))
    ```

    1.    :man_raising_hand: see above for implementation of `ExampleNet`

??? success ":material-numeric-2-circle-outline: 𝙶𝚎𝚝 𝚒𝚗𝚜𝚒𝚐𝚑𝚝𝚜 𝚒𝚗𝚝𝚘 𝚝𝚑𝚎 𝚖𝚘𝚍𝚎𝚕 𝚜𝚝𝚛𝚞𝚌𝚝𝚞𝚛𝚎"

    ```python
    from rich import print

    print(model.structure)
    ```

??? success ":material-numeric-3-circle-outline: 𝚀𝚞𝚊𝚗𝚝𝚒𝚏𝚢 𝚖𝚘𝚍𝚎𝚕 𝚙𝚎𝚛𝚏𝚘𝚛𝚖𝚊𝚗𝚌𝚎 𝚏𝚛𝚘𝚖 𝚟𝚊𝚛𝚒𝚘𝚞𝚜 𝚍𝚒𝚖𝚎𝚗𝚜𝚒𝚘𝚗𝚜"

    ```python
    # Parameter Analysis
    print(model.param)
    tb, data = model.profile('param', no_tree=True)

    # before measuring calculation you should first execute a feed-forward
    import torch
    input = torch.randn(1, 3, 32, 32)
    output = model(input) # (1)

    # Computational Profiling
    print(model.cal) # (2)
    tb, data = model.profile('cal', no_tree=True)

    # Memory Diagnostics
    print(model.mem) # (3)
    tb, data = model.profile('mem', no_tree=True)

    # Performance Benchmarking
    print(model.ittp) # (4)
    tb, data = model.profile('ittp', no_tree=True)
    ```

    1.    :man_raising_hand: you do **not** need to concern about the device mismatch, just feed the model
    2.    :man_raising_hand: `cal` for calculation
    3.    :man_raising_hand: `mem` for memory
    4.    :man_raising_hand: `ittp` for inference time & throughput

??? success ":material-numeric-4-circle-outline: 𝙴𝚡𝚙𝚘𝚛𝚝 𝚛𝚎𝚜𝚞𝚕𝚝𝚜 𝚏𝚘𝚛 𝚏𝚞𝚛𝚝𝚑𝚎𝚛 𝚊𝚗𝚊𝚕𝚢𝚜𝚒𝚜"

    ```python
    # export to csv
    model.profile('param', show=False, save_to="params.csv")

    # export to excel
    model.profile('cal', show=False, save_to="calculation.xlsx")
    ```

??? success ":material-numeric-5-circle-outline: 𝙰𝚍𝚟𝚊𝚗𝚌𝚎𝚍 𝚞𝚜𝚊𝚐𝚎"

    1. [Attributes/methods access of underlying model]()
    2. [Automatic device synchronization]()
    3. [Performance gallery]()
    4. [Detailed inspection]()
    5. Customized visulization 
        - [for operation trees]()
        - [for tabular reports]()
        - [combination of tree and report]()
    6. Best practice of programmable tabular report
        - [Real-time structure adjustment]()   
        - [Real-time data analysis]()
    7. [Tabular report export and post-export]()
    8. [Centralized configuration management]()

## 𝒟. 𝒞𝑜𝓃𝓉𝓇𝒾𝒷𝓊𝓉𝑒

Thank you for wanting to make `TorchMeter` even better!

There are several ways to make a contribution:

- 💬 [Start/join discussions]()
- 🚨 [Report issues]()
- 👨‍💻 [Create pull requests (PRs)]()

Before jumping in, let's ensure smooth collaboration by reviewing our 📋 [**contribution guidelines**]() first. 

Thanks again !

## ℰ. 𝒞𝑜𝒹𝑒 𝑜𝒻 𝒞𝑜𝓃𝒹𝓊𝒸𝓉

> Refer to official [code-of-conduct file](https://github.com/TorchMeter/torchmeter/blob/master/CODE_OF_CONDUCT.md) for more details.

- `TorchMeter` is an open-source project built by developers worldwide. We're committed to fostering a **friendly, safe, and inclusive** environment for all participants. 

- This code applies to all community spaces including but not limited to GitHub repositories, community forums, etc.

## ℱ. 𝐿𝒾𝒸𝑒𝓃𝓈𝑒

- `TorchMeter` is released under the **AGPL-3.0 License**, see the [LICENSE](https://github.com/TorchMeter/torchmeter/blob/master/LICENSE) file for the full text. 
- Please carefully review the terms in the [LICENSE](https://github.com/TorchMeter/torchmeter/blob/master/LICENSE) file before using or distributing `TorchMeter`. 
- Ensure compliance with the licensing conditions, especially when integrating this project into larger systems or proprietary software.