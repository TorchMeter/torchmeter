---
hide:
    - navigation
---

## **:material-numeric-1-circle-outline: Default Configuration**

!!! tip ""

    When retrieving a global config ^^**not from a file**^^, `torchmeter` will initialize it using the following default configuration.    
    You can view it in a hierarchical way via:

    ```python linenums="0"
    from torchmeter import get_config

    cfg = get_config()
    print(cfg)
    ```

```yaml linenums="0"
--8<-- "default_cfg.yaml"
```

---

## **:material-numeric-2-circle-outline: Tree Level Index**

### **:material-numeric-1-box: What is the tree level index?**

As the name implies, it is the hierarchical index of a operation tree. 

Figuratively, within the model operation tree, ^^each guide line represents a level^^. The level index value commences from **0** and increments from left to right.

Additionally, the level index at which a tree node is mounted is equal to `len(tree_node.node_id.split('.'))`. For instance, the node `(1.1.6.2) 1 BatchNorm2d` below is mounted at level 4.

```title="" linenums="0"
AnyNet
├── (1) layers Sequential
│   ├── (1.1) 0 BasicBlock
│   │   ├── (1.1.1) conv1 Conv2d
│   │   ├── (1.1.2) bn1 BatchNorm2d
│   │   ├── (1.1.3) relu ReLU
│   │   ├── (1.1.4) conv2 Conv2d
│   │   ├── (1.1.5) bn2 BatchNorm2d
│   │   └── (1.1.6) downsample Sequential
│   │       ├── (1.1.6.1) 0 Conv2d
│   │       └── (1.1.6.2) 1 BatchNorm2d
│   └── (1.2) 1 BasicBlock
│       ├── (1.2.1) conv1 Conv2d
│       ├── (1.2.2) bn1 BatchNorm2d
│       ├── (1.2.3) relu ReLU
│       ├── (1.2.4) conv2 Conv2d
│       └── (1.2.5) bn2 BatchNorm2d
├── (2) avgpool AdaptiveAvgPool2d
└── (3) fc Linear

↑   ↑   ↑   ↑

0   1   2   3  (level index, each pointing to a guide line)
```

### **:material-numeric-3-box: How to use the tree level index?**

A valid level index empowers you to customize the operation tree with meticulous precision.
`torchmeter` regards the following value as a valid tree level index:

1. **A non-negative integer (e.g. `0`, `1`, `2`, ...)**: The configurations under a specific index apply only to the corresponding level.
2. **`default`**: The configurations under this index will be applied to all undefined levels.
3. **`all`**: The configurations under this index will **override** those at any other level, and will be applied with the highest priority **across all levels**. 

Please refer to [Customize the Hierarchical Display](https://docs.torchmeter.top/latest/demo/#fb1-customize-the-hierarchical-display){ .md-button } for specific usage scenarios.

---

## **:material-numeric-3-circle-outline: Tree Node Attributes**

### **:material-numeric-1-box: What is a tree node attribute?**

- Upon the instantiation of a `torchmeter.Meter` in combination with a `Pytorch` model, an automated scan of the model's architecture will be executed. Subsequently, a tree structure will be produced to depict the model. 

- This tree structure is realized via `torchmeter.engine.OperationTree`. In this tree, each node is an instance of `torchmeter.engine.OperationNode`, which represents a layer or operation (such as `nn.Conv2d`, `nn.ReLU`, etc.) within the model. 

- Therefore, ^^the attributes of a tree node are the attributes / properties of an instance of `OperationNode`^^.

### **:material-numeric-2-box: What can a tree node attribute help me?**

All the attributes that are available, as defined below, are intended to:

- facilitate your acquisition of supplementary information of a tree node;
- customize the display of the tree structure during the rendering procedure. 

### **:material-numeric-3-box: What are the available attributes of a tree node?**

??? example "Illustrative Example"

    ```python
    from collections import OrderedDict
    import torch.nn as nn

    class SimpleModel(nn.Module):
        def __init__(self):
            super(SimpleModel, self).__init__()

            self.single_1 = nn.Linear(1, 10)

            self.repeat_1x2 = nn.Sequential(OrderedDict({
                "A": nn.Linear(10, 10),
                "B": nn.Linear(10, 10),
            }))

            self.single_2 = nn.ReLU()

            self.repeat_2x3 = nn.Sequential(OrderedDict({
                "C": nn.Linear(10, 5),
                "D": nn.ReLU(),
                "E": nn.Linear(5, 10),

                "F": nn.Linear(10, 5),
                "G": nn.ReLU(),
                "H": nn.Linear(5, 10),

                "I": nn.Linear(10, 5),
                "J": nn.ReLU(),
                "K": nn.Linear(5, 10),
            }))

            self.single_3 = nn.Linear(10, 1)
    ```

    Taking the above model as an example, the values of each attribute in each layer are as follows:

    ??? info "name  ,  type  ,  node_id  ,  is_leaf  ,  operation  ,  module_repr"

        | node_id |     name      |     type      | is_leaf |                       operation                       |                     module_repr                      |
        |:-------:|:-------------:|:-------------:|:-------:|:-----------------------------------------------------:|:----------------------------------------------------:|
        |   `0`   | `SimpleModel` | `SimpleModel` | `False` |         instance created via `SimpleModel()`          |                    `SimpleModel`                     |
        |   `1`   |  `single_1`   |   `Linear`    | `True`  |  instance created via `nn.Linear(1, 10)` in line `8`  | `Linear(in_features=1, out_features=10, bias=True)`  |
        |   `2`   | `repeat_1x2`  | `Sequential`  | `False` |   instance created via `nn.Sequential` in line `10`   |                     `Sequential`                     |
        |  `2.1`  |      `A`      |   `Linear`    | `True`  | instance created via `nn.Linear(10, 10)` in line `11` | `Linear(in_features=10, out_features=10, bias=True)` |
        |  `2.2`  |      `B`      |   `Linear`    | `True`  | instance created via `nn.Linear(10, 10)` in line `12` | `Linear(in_features=10, out_features=10, bias=True)` |
        |   `3`   |  `single_2`   |    `ReLU`     | `True`  |     instance created via `nn.ReLU()` in line `15`     |                       `ReLU()`                       |
        |   `4`   | `repeat_2x3`  | `Sequential`  | `False` |   instance created via `nn.Sequential` in line `17`   |                     `Sequential`                     |
        |  `4.1`  |      `C`      |   `Linear`    | `True`  | instance created via `nn.Linear(10, 5)` in line `18`  | `Linear(in_features=10, out_features=5, bias=True)`  |
        |  `4.2`  |      `D`      |    `ReLU`     | `True`  |     instance created via `nn.ReLU()` in line `19`     |                       `ReLU()`                       |
        |  `4.3`  |      `E`      |   `Linear`    | `True`  | instance created via `nn.Linear(5, 10)` in line `20`  | `Linear(in_features=5, out_features=10, bias=True)`  |
        |  `4.4`  |      `F`      |   `Linear`    | `True`  | instance created via `nn.Linear(10, 5)` in line `22`  | `Linear(in_features=10, out_features=5, bias=True)`  |
        |  `4.5`  |      `G`      |    `ReLU`     | `True`  |     instance created via `nn.ReLU()` in line `23`     |                       `ReLU()`                       |
        |  `4.6`  |      `H`      |   `Linear`    | `True`  | instance created via `nn.Linear(5, 10)` in line `24`  | `Linear(in_features=5, out_features=10, bias=True)`  |
        |  `4.7`  |      `I`      |   `Linear`    | `True`  | instance created via `nn.Linear(10, 5)` in line `26`  | `Linear(in_features=10, out_features=5, bias=True)`  |
        |  `4.8`  |      `J`      |    `ReLU`     | `True`  |     instance created via `nn.ReLU()` in line `27`     |                       `ReLU()`                       |
        |  `4.9`  |      `K`      |   `Linear`    | `True`  | instance created via `nn.Linear(5, 10)` in line `28`  | `Linear(in_features=5, out_features=10, bias=True)`  |
        |   `5`   |  `single_3`   |   `Linear`    | `True`  | instance created via `nn.Linear(10, 1)` in line `31`  | `Linear(in_features=10, out_features=1, bias=True)`  |

    ??? info "parent & childs"

        > Here we use the **^^node id^^** of the parent and childs of each node to simplify the display.    
        > In actual uage, a node's `parent` is `None` or an instance of `torchmeter.engine.OperationNode`;     
        > while the `childs` is an orderdict with node id as key and the node instance as value.

        | node_id |     name      |     type      | parent |   childs    |
        |:-------:|:-------------:|:-------------:|:------:|:-----------:|
        |   `0`   | `SimpleModel` | `SimpleModel` | `None` |   `1 ~ 5`   |
        |   `1`   |  `single_1`   |   `Linear`    |  `0`   |             |
        |   `2`   | `repeat_1x2`  | `Sequential`  |  `0`   | `2.1, 2.2`  |
        |  `2.1`  |      `A`      |   `Linear`    |  `2`   |             |
        |  `2.2`  |      `B`      |   `Linear`    |  `2`   |             |
        |   `3`   |  `single_2`   |    `ReLU`     |  `0`   |             |
        |   `4`   | `repeat_2x3`  | `Sequential`  |  `0`   | `4.1 ~ 4.9` |
        |  `4.1`  |      `C`      |   `Linear`    |  `4`   |             |
        |  `4.2`  |      `D`      |    `ReLU`     |  `4`   |             |
        |  `4.3`  |      `E`      |   `Linear`    |  `4`   |             |
        |  `4.4`  |      `F`      |   `Linear`    |  `4`   |             |
        |  `4.5`  |      `G`      |    `ReLU`     |  `4`   |             |
        |  `4.6`  |      `H`      |   `Linear`    |  `4`   |             |
        |  `4.7`  |      `I`      |   `Linear`    |  `4`   |             |
        |  `4.8`  |      `J`      |    `ReLU`     |  `4`   |             |
        |  `4.9`  |      `K`      |   `Linear`    |  `4`   |             |
        |   `5`   |  `single_3`   |   `Linear`    |  `0`   |             |

    ??? info "repeat_winsz & repeat_time"

        | node_id |     name      |     type      | repeat_winsz  |  repeat_time  | explanation                                                                                                                                         |
        |:-------:|:-------------:|:-------------:|:-------------:|:-------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------: |
        |   `0`   | `SimpleModel` | `SimpleModel` |      `1`      |      `1`      | no repeatition                                                                                                                                      |
        |   `1`   |  `single_1`   |   `Linear`    |      `1`      |      `1`      | no repeatition                                                                                                                                      |
        |   `2`   | `repeat_1x2`  | `Sequential`  |      `1`      |      `1`      | no repeatition                                                                                                                                      |
        |  `2.1`  |      `A`      |   `Linear`    | {== **1** ==} | {== **2** ==} | Repeating windows cover `2.1` and `2.2`. <br>The two layers have the same definition, <br>so it can be considered that one module is repeated twice |
        |  `2.2`  |      `B`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |   `3`   |  `single_2`   |    `ReLU`     |      `1`      |      `1`      | no repeatition                                                                                                                                      |
        |   `4`   | `repeat_2x3`  | `Sequential`  |      `1`      |      `1`      | no repeatition                                                                                                                                      |
        |  `4.1`  |      `C`      |   `Linear`    | {== **3** ==} | {== **3** ==} | Repeating windows taking `4.1 ~ 4.3` as a whole and cover `4.1 ~ 4.9`.                                                                              |
        |  `4.2`  |      `D`      |    `ReLU`     |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.3`  |      `E`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.4`  |      `F`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.5`  |      `G`      |    `ReLU`     |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.6`  |      `H`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.7`  |      `I`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.8`  |      `J`      |    `ReLU`     |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |  `4.9`  |      `K`      |   `Linear`    |      `1`      |      `1`      | Have been included in a repeating window. <br>So skip repetitiveness analysis and use default values.                                               |
        |   `5`   |  `single_3`   |   `Linear`    |      `1`      |      `1`      | no repeatition                                                                                                                                      |

|   Attribute    |     Type     |     Explanation     |
|:--------------:|:------------:|:-------------------:|
|  `operation`   |  `torch.nn.Module`  |  The underlying pytorch module  |
|     `type`     |  `str`  |   The operation type. If the operation is a pytorch module, use the name of its class   |
|     `name`     |  `str`  |   The module name defined in the underlying pytorch model  |
|   `node_id`    |  `str`  |   A globally unique module identifier, <br>formatted as `<parent-node-id>.<node-number-in-current-level>`. <br>The index commences from `1`, cause the root is denoted as `0` |
|   `is_leaf`    |  `bool` |   Whether the node is a leaf node (no child nodes)   |
| `module_repr`  |  `str` | The text representation of the current operation. <br>For non-leaf nodes, it's the ndoe type. <br>Conversely, it is the return of `__repr__()` method |
|    `parent`    |  `torchmeter.engine.OperationNode` |  The parent node of this node. Each node has only one parent |
|    `childs`    |  `OrderDict[str,  OperationNode]`  |  An orderdict storing children of this node in feed-forward order. <br>Key is `node_id` of child, value is the child node itself.  |
| `repeat_winsz` |  `int`   |   The size of the repeating window for the current node. <br>Default is 1, meaning no repetition (window has only the node itself)  |
| `repeat_time`  |  `int`   |   The number of repetitions of the window where the current module is located. <br>Default is 1, meaning no repetition  |

### **:material-numeric-4-box: How to use the attributes of a tree node?**

An attribute of a tree node can be employed as a {++placeholder++} within the value of certain configurations. This allows for the ^^**dynamic retrieval of the attribute value**^^ during the tree-rendering procedure.

The configurations/scenario supporting the tree node attribute as a placeholder are listed below.

|           configuration/scenario           |                                                    Default Value                                                    |
|:------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------:|
| `tree_levels_args.[level-index].label`[^1] |                         `'[b gray35](<node_id>) [green]<name>[/green] [cyan]<type>[/]'`[^2]                         |
|       `tree_repeat_block_args.title`       |                                    `'[i]Repeat [[b]<repeat_time>[/b]] Times[/]'`                                    |
|       `tree_renderer.repeat_footer`        | Support text and function, see [Customize the footer :material-link-variant:](demo.ipynb#fb23-customize-the-footer) | 

[^1]: As for the value of `[level-index]`, please refer to [Tree Level Index :material-link-variant:](#Tree-Level-Index).
[^2]: The [style markup :material-link-variant:](https://rich.readthedocs.io/en/latest/markup.html) and its [abbreviation :material-link-variant:](https://rich.readthedocs.io/en/latest/style.html#defining-styles) in `rich` is supported in writing value content.

??? info "Usage Example"

    For example, if you want to unify the titles of all repeated blocks into bold `My Repeat Title`, then you can do this

    ```python linenums="0"
    from rich import print
    from torchmeter import Meter
    from torchvision import models

    resnet18 = models.resnet18()
    model = Meter(resnet18)

    model.tree_repeat_block_args.title = '[b]My Repeat Title[/b]' #(1)

    print(model.structure) 
    ```

    1. 🙋‍♂️ That's all, then you can see the titles in all repeat blocks have been changed

---

## **:material-numeric-4-circle-outline: Unit Explanation**

There are four types of units in `torchmeter`, listed as follows:

!!! note ""

    The `raw-data` tag in the subsequent content indicates that the unit marked with this tag is used in the [`raw data` mode :material-link-variant:](https://docs.torchmeter.top/latest/demo/#i1-raw-data-mode)

=== ":material-counter: Counting Units"

    > Used by `param`, `cal`

    |  unit  |    explanation     |    tag     | example                                  |
    |:------:|:------------------:|:----------:|:---------------------------------------- |
    | `null` | Number of subjects | `raw-data` | `5`: There are `5` semantic subjects     | 
    |  `K`   |       $10^3$       |            | `5 K`: There are `5,000` ...             |
    |  `M`   |       $10^6$       |            | `5 M`: There are `5,000,000` ...         |
    |  `G`   |       $10^9$       |            | `5 G`: There are `5,000,000,000` ...     |
    |  `T`   |     $10^{12}$      |            | `5 T`: There are `5,000,000,000,000` ... |

=== ":fontawesome-solid-square-binary: Binary Storage Units"

    > Used by `mem`

    | unit  |     explanation     |    tag     | example                                           |
    |:-----:|:-------------------:|:----------:|:------------------------------------------------- |
    |  `B`  |    $2^0=1$ bytes    | `raw-data` | `5 B`: $5 \times 1 = 5$  bytes                    |
    | `KiB` | $2^{10}=1024$ bytes |            | `5 KiB`: $5 \times 2^{10} = 5120$  bytes          |
    | `MiB` |   $2^{20}$ bytes    |            | `5 MiB`: $5 \times 2^{20} = 5242880$  bytes       |
    | `GiB` |   $2^{30}$ bytes    |            | `5 GiB`: $5 \times 2^{30} = 5368709120$  bytes    |
    | `TiB` |   $2^{40}$ bytes    |            | `5 TiB`: $5 \times 2^{40} = 5497558138880$  bytes |

=== ":material-av-timer: Time Units"

    > Used by `ittp` - inference time

    | unit  | explanation |    tag     | example                             |
    |:-----:|:-----------:|:----------:|:----------------------------------- |
    | `ns`  | nanosecond  |            | `5 ns`: $5 \times 10^{-9}$  seconds |
    | `us`  | microsecond |            | `5 us`: $5 \times 10^{-6}$  seconds |
    | `ms`  | millisecond |            | `5 ms`: $5 \times 10^{-3}$  seconds |
    |  `s`  |   second    | `raw-data` | `5 s`: $5 \times 10^{0}$  seconds   |
    | `min` |   minute    |            | `5 min`: $5 \times 60^{1}$  seconds |
    |  `h`  |    hour     |            | `5 h`: $5 \times 60^{2}$  seconds   | 

=== ":material-speedometer: Inference Speed Units"

    > Used by `ittp` - throughput

    |  unit  |   explanation    |    tag     | example                                                 |
    |:------:|:----------------:|:----------:|:------------------------------------------------------- |
    | `IPS`  | Input Per Second | `raw-data` | `5 IPS`: process `5` inputs per second                  |
    | `KIPS` |    $10^3$ `IPS`    |            | `5 KIPS`: process `5,000` inputs per second             |
    | `MIPS` |    $10^6$ `IPS`    |            | `5 MIPS`: process `5,000,000` inputs per second         |
    | `GIPS` |    $10^9$ `IPS`    |            | `5 GIPS`: process `5,000,000,000` inputs per second     |
    | `TIPS` |  $10^{12}$ `IPS`   |            | `5 TIPS`: process `5,000,000,000,000` inputs per second | 
