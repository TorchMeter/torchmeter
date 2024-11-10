## 📦 A Project Template for Self-developed Python Package

[![Package Version](https://img.shields.io/badge/Version-v1.4.0-green)](https://github.com/Ahzyuan/Python-package-template/releases/tag/v1.4.0)
[![License](https://img.shields.io/badge/License-MIT-khaki)](https://opensource.org/license/MIT)
![Pypi Template](https://img.shields.io/badge/PyPI-Package_pattern-yellow?logo=pypi&labelColor=%23FAFAFA)

[![setuptools](https://img.shields.io/badge/Build-setuptools-red)](https://github.com/pypa/setuptools)
[![Ruff](https://img.shields.io/badge/Formatter-Ruff-sienna?logo=ruff)](https://github.com/astral-sh/ruff)
[![Isort](https://img.shields.io/badge/%20Imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

> • Planning to develop your first Python third-party package?   
> • Troubled by `setuptools`'s numerous, complex configurations?   
> • Unsure about what the structure of a project should be?    
> 𝐓𝐡𝐞𝐧 𝐲𝐨𝐮'𝐯𝐞 𝐜𝐨𝐦𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐫𝐢𝐠𝐡𝐭 𝐩𝐥𝐚𝐜𝐞!

This repo provides an 𝐨𝐮𝐭-𝐨𝐟-𝐭𝐡𝐞-𝐛𝐨𝐱 𝐩𝐫𝐨𝐣𝐞𝐜𝐭 𝐬𝐭𝐫𝐮𝐜𝐭𝐮𝐫𝐞 𝐭𝐞𝐦𝐩𝐥𝐚𝐭𝐞 that accelerates your third-party Python package development.

## 🎯 Features

<details>
<summary>𝐏𝐫𝐚𝐜𝐭𝐢𝐜𝐚𝐥, 𝐚𝐧𝐝 𝐫𝐞𝐚𝐝𝐲 𝐭𝐨 𝐠𝐨 𝐬𝐭𝐫𝐚𝐢𝐠𝐡𝐭 𝐨𝐮𝐭 𝐨𝐟 𝐭𝐡𝐞 𝐛𝐨𝐱</summary>

> 💡 Tips      
> • We use [`setup.cfg`](setup.cfg) to manage all metadata, and just keep a minimal [`setup.py`](setup.py) to ensure editable installation supported. 

We provide:

1. **A fully configured package-setup file**, i.e., [`setup.cfg`](setup.cfg) or [`pyproject.toml`](https://github.com/Ahzyuan/Python-package-template/releases/download/v1.4.0/pyproject.toml).
   - It covers most common config items, allows dynamic access to `version`, `README`, and project dependencies at build time.
   - It is well commented, so you don't need to look up [documents](https://setuptools.pypa.io/en/latest/references/keywords.html) to understand each item's meaning.

2. **A complete and concise usage guidance**, i.e. [`🔨 Usage`](#-usage) below.      

</details>

<details>
<summary>𝐄𝐟𝐟𝐢𝐜𝐢𝐞𝐧𝐭 𝐚𝐧𝐝 𝐩𝐫𝐨𝐟𝐞𝐬𝐬𝐢𝐨𝐧𝐚𝐥</summary>

We provide a **useful, complete project structure**, which    
• not only complies with software engineering specifications,    
• but also includes **all file templates** required for a project and **continuous deployment(CD) workflows**(see [`CI/CD via Github Action 🤖` below](#-project-management)).

Here is the detailed structure of the project:

```plaix-txt
Python-package-template/
├── .github/                      # Storage Github Action workflow files and templates of Issue, PR 
│   ├── CONTRIBUTING.md           # Instructions for contributing to project
│   ├── ISSUE_TEMPLATE            # Storage Issue template files
│   │   ├── bug_report.yml        # Bug report template
│   │   ├── feature_request.yml   # Feature request template
│   │   └── config.yml            # Template choosing configuration
│   ├── PULL_REQUEST_TEMPLATE.md  # Template for PR description
│   └── workflows                 # Storage Github Action workflow files    
│       └── publish_release.yml   # Workflow for publishing and releaseing Python package
|
├── tests/           # Storage unit test code
│   └── README.md    # Instructions for testing your code
|
├── docs/            # Store document related files
│   └── README.md    # Instructions for building document for your project
|
├── examples/        # Store project demo code
│   └── demo.ipynb   # Demonstration of your project
|
├── package-name/    # Store project code
│   ├── core.py      # Core code
│   └── __init__.py  # Package initialization file, defining copyright, version,and other information
|
├── .gitignore       # File ignored by Git
├── LICENSE          # Project license
├── MANIFEST.in      # Describe the files included or not included in buildpackage
├── CHANGELOG.md     # Project changelog
├── README.md        # Project description
├── requirements.txt # Project dependency
├── ruff.toml        # Define rules for code style, code inspection, and importmanagement
├── packaging.sh     # Package building script
├── check_meta.sh    # Distribution metadata checking script
├── setup.cfg        # Project packaging configuration
└── setup.py         # Project packaging script
```

</details>

<details>
<summary>𝐒𝐭𝐚𝐧𝐝𝐚𝐫𝐝 𝐲𝐞𝐭 𝐡𝐢𝐠𝐡𝐥𝐲 𝐜𝐮𝐬𝐭𝐨𝐦𝐢𝐳𝐚𝐛𝐥𝐞</summary>

- **We standardize code sytle and quality** with the wonderful Python linter and formatter [`Ruff`](https://github.com/astral-sh/ruff).
- **We standardize contributing pipeline** with [`CONTRIBUTING.md`](.github/CONTRIBUTING.md) to cuts communication costs and boosts development efficiency.
- **We offer ready-to-use templates** for `issue`, `pull requests(PR)`, and package publishing workflows, complete with modifications and usage instructions to help you customize them effectively.

</details>

## 🔨 Usage

> [!IMPORTANT]   
> - In demo below, we assume that your github ID is `me` and project name is `my-project`.         
>   **❗️❗️❗️ Remember to replace them with your own ID and project name when using ❗️❗️❗️**
>
> - This template uses `setup.cfg` to manage all metadata by default. While `pyproject.toml` is an officially recommended alternative, I find it more complicated, so I prefer `setup.cfg`. But if you really want to use `pyproject.toml`, please **replace the `setup.cfg` with following file**. 
> 
>    - [Download `pyproject.toml`](https://github.com/Ahzyuan/Python-package-template/releases/download/v1.4.0/pyproject.toml)
>    - <details>
>      <summary>𝚙𝚢𝚙𝚛𝚘𝚓𝚎𝚌𝚝.𝚝𝚘𝚖𝚕</summary>
>
>       ```toml
>       # refer to https://packaging.python.org/en/latest/guides/writing-pyproject-toml
>       # See https://docs.astral.sh/ruff/settings for configuring ruff
>       
>       [build-system]  # define build backend and dependencies needed to build your project
>       requires = ["setuptools>=66.0", "cython", "wheel", "isort", "ruff"]           # dependencies needed to build your project
>       build-backend = "setuptools.build_meta"                             # build backend
>       
>       [project] # define metadata of your project
>       
>       # ---------------- Dynamic info ----------------
>       dynamic = ["version","dependencies"]                                # dynamic info will be filled in by the build backend
>       
>       # ---------------- Basic info ----------------
>       name = "your-package"                                               # package name
>       authors = [
>         { name="your-name", email="your-email@mail.com" }, 
>       ]
>       maintainers = [
>         { name="your-name", email="your-email@mail.com" }, 
>       ]
>       description = "Package test"                             # one-line description of your project
>       readme = {file = "README.md", content-type = "text/markdown"}       # specify README file
>       
>       # ---------------- Dependency info ----------------
>       requires-python = ">=3.7"                                           # Python version requirement
>       
>       # ---------------- Other ----------------
>       keywords = ["A","B","c"]      # keywords of your project, will help to suggest your project when people search for these keywords.
>       classifiers = [               # Trove classifiers, Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
>         "Development Status :: 4 - Beta",
>         "Intended Audience :: Developers",
>         "Topic :: Software Development :: Build Tools",
>         "License :: OSI Approved :: MIT License",
>         "Programming Language :: Python :: 3",
>         "Programming Language :: Python :: 3.7",
>         "Programming Language :: Python :: 3.8",
>         "Programming Language :: Python :: 3.9",
>         "Programming Language :: Python :: 3.10",
>         "Programming Language :: Python :: 3.11",
>         "Programming Language :: Python :: 3.12",
>       ]
>       
>       # ---------------- Optional dependency ----------------
>       [project.optional-dependencies] 
>       docs = ["sphinx>=7.0.0"]
>       
>       test = [
>         "pytest", 
>         "pytest-sugar"]
>       
>       cli = [
>         "rich",
>         "click",
>       ]
>       
>       # Install a command as part of your package
>       [project.gui-scripts]                           # use [project.gui-scripts] to compatiable with differernt system   
>       your-package = "your-package.cli:app"           # command = package:func
>       
>       
>       # URLs associated with your project
>       [project.urls]
>       Homepage = "https://github.com/your-name/your-package"                    
>       Repository = "https://github.com/your-name/your-package.git" 
>       Issues = "https://github.com/your-name/your-package/issues" 
>       Changelog = "https://github.com/your-name/your-package/blob/master/CHANGELOG.md"
>       
>       [tool.setuptools.dynamic]
>       version = {attr = "your-package.__version__"}  # automatically obtain the value by `my_package.__version__`.
>       dependencies = {file = ["requirements.txt", "requirement.txt", > "requirement"]}
>       
>       # -------------------------------- Tools Setting --------------------------------
>       [tool.setuptools]
>       license-files = ['LICEN[CS]E*', 'COPYING*', 'NOTICE*', 'AUTHORS*']  # specify License files
>       
>       [tool.setuptools.packages]
>       find = {}  # Scan the project directory with the default parameters
>       
>       [tool.ruff]
>       # Allow lines to be as long as 120.
>       line-length = 120
>       
>       [tool.ruff.format]
>       # Enable reformatting of code snippets in docstrings.
>       docstring-code-format = true
>       
>       [tool.ruff.lint]
>       # Skip unused variable rules
>       ignore = [
>           "ANN101",  # Missing type annotation for `self` in method
>           "ANN102",  # Missing type annotation for `cls` in classmethod
>           "ANN401",  # Dynamically typed expressions (typing.Any) are disallowed
>           "C901",    # function is too complex (12 > 10)
>           "COM812",  # Trailing comma missing
>           "D",       # Docstring rules
>           "EM101",   # Exception must not use a string literal, assign to variable first
>           "EM102",   # Exception must not use an f-string literal, assign to variable first
>           "ERA001",  # Found commented-out code
>           "FBT001",  # Boolean positional arg in function definition
>           "FBT002",  # Boolean default value in function definition
>           "FBT003",  # Boolean positional value in function call
>           "FIX002",  # Line contains TODO
>           "ISC001",  # Isort
>           "PLR0911", # Too many return statements (11 > 6)
>           "PLR2004", # Magic value used in comparison, consider replacing 2 with a constant variable
>           "PLR0912", # Too many branches
>           "PLR0913", # Too many arguments to function call
>           "PLR0915", # Too many statements
>           "S101",    # Use of `assert` detected
>           "S311",    # Standard pseudo-random generators are not suitable for cryptographic purposes
>           "T201",    # print() found
>           "T203",    # pprint() found
>           "TD002",   # Missing author in TODO; try: `# TODO(<author_name>): ...`
>           "TD003",   # Missing issue link on the line following this TODO
>           "TD005",   # Missing issue description after `TODO`
>           "TRY003",  # Avoid specifying long messages outside the exception class
>           "PLW2901", # `for` loop variable `name` overwritten by assignment target
>           "SLF001",  # Private member accessed: `_modules`
>       ]
>       
>       [tool.ruff.lint.isort]
>       length-sort = true                              # sort imports by their string length
>       combine-as-imports = true                       # combines as imports on the same line
>       known-first-party = ["your-package"]
>       lines-after-imports = 1                         # Use a single line after each import block.
>       single-line-exclusions = ["os", "json", "re"]   # modules to exclude from the single line rule
>       ```
> </details>

1. <details>
    <summary>🚀 𝐂𝐫𝐞𝐚𝐭𝐞 𝐲𝐨𝐮𝐫 𝐫𝐞𝐩𝐨</summary>
    
    Press the `Use this template` button next to `star` button,   
    so as to use this repo as a template to create your repo.
  
2. <details>
   <summary>📥 𝐂𝐥𝐨𝐧𝐞 𝐲𝐨𝐮𝐫 𝐫𝐞𝐩𝐨 𝐭𝐨 𝐥𝐨𝐜𝐚𝐥 𝐦𝐚𝐜𝐡𝐢𝐧𝐞</summary>
    
    Find new repo on your GitHub `repositories` page.    
    Pull it to your machine with `git clone`.

    ```bash
    # replace 'me' with your github ID, 
    # 'my-project' with your project name, 
    # and `MYPROJECT` with your local project folder name
    git clone https://github.com/me/my-project MYPROJECT
    ```
    </details>

3.  <details>
    <summary>✏️ 𝐑𝐞𝐧𝐚𝐦𝐞 𝐩𝐫𝐨𝐣𝐞𝐜𝐭 𝐟𝐨𝐥𝐝𝐞𝐫</summary>

    ```bash
    cd MYPROJECT

    # replace 'my-project' with your project name
    git mv package-name my-project
    ```

    > <details>
    > <summary>𝘯𝘰𝘸 𝘺𝘰𝘶𝘳 𝘱𝘳𝘰𝘫𝘦𝘤𝘵 𝘴𝘵𝘳𝘶𝘤𝘵𝘶𝘳𝘦 𝘴𝘩𝘰𝘶𝘭𝘥 𝘣𝘦 𝘭𝘪𝘬𝘦 𝘵𝘩𝘪𝘴</summary>
    >
    > ```
    > # Note: 
    > # the directory structure below neglects the `.github` dir
    > 
    > MYPROJECT/
    > ├── tests/ 
    > │   └── README.md     
    > |      
    > ├── docs/   
    > │   └── README.md    
    > |            
    > ├── examples/  
    > │   └── demo.ipynb    
    > |         
    > ├── my-project/    
    > │   ├── core.py      
    > │   └── __init__.py   
    > |
    > ├── .gitignore   
    > ├── LICENSE          
    > ├── MANIFEST.in     
    > ├── CHANGELOG.md     
    > ├── README.md        
    > ├── requirements.txt 
    > ├── ruff.toml       
    > ├── packaging.sh     
    > ├── check_meta.sh    
    > ├── setup.cfg        
    > └── setup.py         
    > ```
    > 
    > </details>
    
    </details>

4.  <details>
    <summary>📄 𝐌𝐨𝐝𝐢𝐟𝐲 𝐭𝐡𝐞 𝐟𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 𝐟𝐢𝐥𝐞𝐬</summary>

    <details>
    <summary>① 𝚜𝚎𝚝𝚞𝚙.𝚌𝚏𝚐 / 𝚙𝚢𝚙𝚛𝚘𝚓𝚎𝚌𝚝.𝚝𝚘𝚖𝚕 (𝚖𝚘𝚜𝚝 𝚒𝚖𝚙𝚘𝚛𝚝𝚊𝚗𝚝)</summary>

    > 💡 Tips  
    > 
    > • If your `README` is in `rst` format, you need to replace `"text/markdown"` with  `"text/x-rst"` in `long_description_content_type`(`setup.cfg`) or `readme`(`pyproject.toml`).  
    > 
    > • If you want to create a CLI command for your package, enable `[options.entry_points]` option in `setup.cfg` or `[project.gui-scripts]` in `pyproject.toml`. See more [here](https://packaging.python.org/en/latest/guides/creating-command-line-tools/).
    > 
    > • If you want more configuration, refer to [keywords of `setup.cfg`](https://setuptools.pypa.io/en/latest/references/keywords.html) or [keywords of `pyproject.toml`](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)

    **Look for the following variables in `setup.cfg` and modify as per comments.**

    |       Basic        |    Requirement related     | Package structure related |
    |:------------------:|:--------------------------:|:-------------------------:|
    |       `name`       |     `python_requires`      |        `packages`         |
    |     `version`      |     `install_requires`     |  `include_package_data`   |
    |      `author`      |         `exclude`          |                           |
    |   `author_email`   | `[options.extras_require]` |                           |
    |   `description`    |                            |                           |
    | `long_description` |                            |                           |
    |       `url`        |                            |                           |
    |     `keywords`     |                            |                           |
    |     `license`      |                            |                           |
    |   `classifiers`    |                            |                           |

    **If you are using `pyproject.toml`, you may need to replace `your-package` with `my-package` in file first, then check out and modify following variables.**

    |      Basic       |        Requirement related        | Package structure related |
    |:----------------:|:---------------------------------:|:-------------------------:|
    |      `name`      |            `requires`             |          `find`           |
    |    `version`     |         `requires-python`         |                           | 
    |    `authors`     | `[project.optional-dependencies]` |                           |
    |  `maintainers`   |                                   |                           |
    |  `description`   |                                   |                           |
    |     `readme`     |                                   |                           |
    | `[project.urls]` |                                   |                           |
    |    `keywords`    |                                   |                           |
    |  `classifiers`   |                                   |                           |
    
    </details>

    <details>
    <summary> ② 𝚖𝚢-𝚙𝚛𝚘𝚓𝚎𝚌𝚝/__𝚒𝚗𝚒𝚝__.𝚙𝚢 </summary>

    - `line 2`: `<your-name>` → `me`, replace with your github ID
    - `line 8`: `0.1.0` → `0.0.1`, replace with your project initial version

    </details>

    <details>
    <summary> ③ 𝚛𝚞𝚏𝚏.𝚝𝚘𝚖𝚕 </summary>

    > • Here show the common change of `ruff.toml`  
    > • With comments in the file, you can modify everything as needed.   
    > • If you want more configuration, refer to [Ruff document](https://docs.astral.sh/ruff/)

    - `line 3`: `target-version = "py37"` → `"py310"`, replace with your target python 
    - `line 46`: `known-first-party = ["<your_package_name>"]` → `["my-project"]`, replace with your project name

    </details>

    <details>
    <summary> ④ 𝚛𝚎𝚚𝚞𝚒𝚛𝚎𝚖𝚎𝚗𝚝𝚜.𝚝𝚡𝚝 </summary>

    > Change with your project dependencies, here is an example

    ```plain-txt
    setuptools
    isort
    ruff
    opencv-python
    tqdm
    ```

    </details>

    <details>
    <summary> ⑤ 𝚁𝙴𝙰𝙳𝙼𝙴.𝚖𝚍 </summary>

    > Change with your project description. Here is an example

    ```markdown
    # 🧐 my-project

    ![Static Badge](https://img.shields.io/badge/Version-v0.0.1-green)

    ## 👋 Introduction

    This is my first Python package called `my-project`.

    ## 📦 Getting Started

    Install the package with pip: `pip install my-project`

    ## 📄 License

    This project is licensed under the MIT License, 
    see the [LICENSE.md](LICENSE.md) for details

    ## 💖 Acknowledge

    Thanks for John for his help.
    ```

    </details>


    <details>
    <summary> ⑥ 𝙻𝚒𝚌𝚎𝚗𝚜𝚎 </summary>

    > Default license is `MIT`, you can change it to other.  
    > See https://choosealicense.com/licenses/

    ```
    line 3: Copyright (c) <YEAR> <COPYRIGHT HOLDER>
    ↓
    line 3: Copyright (c) 2024 me
    ```

    </details>

    <details>
    <summary> ⑦ .𝚐𝚒𝚝𝚑𝚞𝚋/𝚠𝚘𝚛𝚔𝚏𝚕𝚘𝚠𝚜/𝚙𝚞𝚋𝚕𝚒𝚜𝚑_𝚛𝚎𝚕𝚎𝚊𝚜𝚎.𝚢𝚖𝚕 </summary>

    > • Change this file to use `Github Actions` for package publication.    
    > • If you want to change the preset workflow, see see [`CI/CD via Github Action 🤖` below](#-project-management) below and refer to [Github Actions document](https://docs.github.com/en/actions)

    - `<package-name>` → `my-project`
  
    </details>

    </details>

5.  <details>
    <summary>👨‍💻 𝐃𝐞𝐯𝐞𝐥𝐨𝐩 𝐲𝐨𝐮𝐫 𝐩𝐫𝐨𝐣𝐞𝐜𝐭</summary>

    > 💡 Tips    
    > • Cross-module imports can be made via `.module-name` or `my-project.module-name` in each module file.  
    > 
    > • You can test your code using `python -m my-project.<module-name>` with working directory in `MYPROJECT`.   
    > 
    > • To develop a command-line tool, add `__main__.py` in `my-project` folder. It defines logit when typing `my-project` in terminal. See more [here](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)

    **Fill your logit into `my-project` folder**.

    </details>

6.  <details>
    <summary>🗳 𝐁𝐮𝐢𝐥𝐝 𝐝𝐢𝐬𝐭𝐫𝐢𝐛𝐮𝐭𝐢𝐨𝐧 𝐩𝐚𝐜𝐤𝐚𝐠𝐞𝐬</summary>

    > This step will generate `.tar.gz` source distribution file and `.whl` built distribution in new created folder `dist` .

    ```bash
    # pwd: .../MYPROJECT
    chmod +x packaging.sh

    # Assume you are using anaconda to manage your python environment
    ./packaging.sh

    # Otherwise, activate your environment and execute following command
    python -m build -v -n .
    ```

    </details>

7.  <details>
    <summary>🔍 𝐕𝐚𝐥𝐢𝐝𝐚𝐭𝐞 𝐩𝐚𝐜𝐤𝐚𝐠𝐞</summary>

    ①. 𝖵𝖺𝗅𝗂𝖽𝖺𝗍𝖾 𝖽𝗂𝗌𝗍𝗋𝗂𝖻𝗎𝗍𝗂𝗈𝗇 𝗆𝖾𝗍𝖺𝖽𝖺𝗍𝖺

    ```bash
    # pwd: .../MYPROJECT
    pip install twine

    chmod +x check_meta.sh
    ./check_meta.sh
    ```

    ②. 𝖵𝖺𝗅𝗂𝖽𝖺𝗍𝖾 `𝖬𝖠𝖭𝖨𝖥𝖤𝖲𝖳.𝗂𝗇` 𝗂𝖿 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝗍𝗁𝗂𝗌 𝖿𝗂𝗅𝖾.

    ```bash
    # pwd: .../MYPROJECT
    pip install check-manifest

    # command below will automatically add missing file patterns to MANIFEST.in.
    check-manifest -u -v
    ```

    ③. `𝖮𝗉𝗍𝗂𝗈𝗇` 𝖵𝖺𝗅𝗂𝖽𝖺𝗍𝖾 𝗉𝖺𝖼𝗄𝖺𝗀𝖾 𝖿𝗎𝗇𝖼𝗍𝗂𝗈𝗇𝗌
    
    ```bash
    # pwd: .../MYPROJECT
    pip install dist/*.whl
    
    # then test your package to see whether it works well.
    # this is necessary if you have create a CLI tool for your package.
    ```
    
    </details>

8.  <details>
    <summary>📢 𝐏𝐮𝐛𝐥𝐢𝐬𝐡 𝐩𝐚𝐜𝐤𝐚𝐠𝐞</summary>

    > • This step will upload your package to [`PyPI`](https://pypi.org/) or [`TestPyPI`](https://test.pypi.org/).  
    > • So firstly, you need to register an account with [`PyPI`](https://pypi.org/) or [`TestPyPI`](https://test.pypi.org/).  
    > • Also, don't forget to generate a token for uploading your package. See more [here](https://pypi.org/help/#apitoken).
    
    > 📋 **𝖲𝗎𝗀𝗀𝖾𝗌𝗍𝗂𝗈𝗇**   
    > You likely have many commits to `PyPI` or `TestPyPI` to familiarize yourself with the process. In this case, you can maintain a **forged `PyPI` server locally**, see [`🧰 Tools Recommended -> pypi-server` below](#-tools-recommended).

    ```bash
    # pwd: .../MYPROJECT

    # (Option but strongly recommended) upload to testpypi firstly to see if anywhere wrong
    twine upload --repository testpypi dist/* 

    # upload to pypi
    # then everyone can install your package via `pip install my-project`
    twine upload --repository pypi dist/* 
    ```
    After executing command above, you will be asked to **enter your account token**.  

    - Sure, you can paste your token in terminal to go through the process.   
    
    - But if you are tired of doing this, you can use `.pypirc` and `keyring` to automatically access your token whenever needed. Follow the step in [`configure .pypirc and keyring 🔐` below](#-tools-recommended).:

    </details>

---

> 🥳 𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀!   
> • You have successfully published your package to `PyPI`.    
> • Now everyone can install it via `pip install my-project`   
> • To update your package to a new version, you have two choices:    
> ① Manually update: repeat steps 5 to 8 above.    
> ② CI/CD workflow(**recommended**): see [`CI/CD via Github Action 🤖` below](#-project-management)

## 🧰 Tools Recommended

<details>
<summary>Ⅰ 𝚙𝚢𝚙𝚒-𝚜𝚎𝚛𝚟𝚎𝚛 🖥️</summary>

> • **What is it**: A simple `PyPI` server for local use.   
> • **Highly recommended** if you are **testing your CI/CD workflow**.

You likely have many commits to `PyPI` or `TestPyPI` to familiarize yourself with publishing process. Then there exists two problems:
  
> • [`TestPyPI` / `PyPI` project size limit](https://pypi.org/help/#project-size-limit): many commits can exceed project size limit.    
> 
> • Using `TestPyPI` as the index of `pip install` is not always reliable:  especially when your package depends on some packages that are only available on `PyPI` but not on `TestPyPI`.   
> >For example, if your package `mp-project` depends on `ruff`, then `pip install mp-project -i https://test.pypi.org/simple` will fail with `ResolutionImpossible` or `Package not found` in the process of finding and downloading `ruff`, cause `ruff` is only available on `PyPI`.

To solve these problems and fully imitate the bahvior of normal `pip install` using `PyPI` index. You can deploy a local `PyPI` server with `pypi-server`.

Here is a quick guide to get started, please check [pypiserver's repo](https://github.com/pypiserver/pypiserver ) for more details.


```bash
pip install pypiserver 

mkdir Path/to/store/packages  # path to store distribution packages

pypi-server run \
-i 0.0.0.0 \
-p <port> \                  # specify a port to listen
<path-to-store>/.pypiserver_pkgs\
-a . -P . &                  # disable authentication for intranet use

cat >~/.pypirc<<EOF          # add local server to .pypirc
[distutils]
index-servers =
    pypi
    testpypi
    local

[pypi]
repository: https://upload.pypi.org/legacy/

[testpypi]
repository: https://test.pypi.org/legacy/

[local]
    repository: http://0.0.0.0:7418
    username: none          # random string, not important
    password: none          # random string, not important
EOF
```

OK, then we can use commands below to upload and install packages:

```bash
# pwd: .../package project dir

# upload package to local server
twine upload --repository local dist/*

# install package from local server
pip install <package> \
--trusted-host \
--extra-index-url http://0.0.0.0:<port>/simple/ 
```

❗️❗️❗️ If you want to close the server, using `kill -9 "$(pgrep pypi-server)"`.

</details>

<details>
<summary>Ⅱ 𝖼𝗈𝗇𝖿𝗂𝗀𝗎𝗋𝖾 .𝚙𝚢𝚙𝚒𝚛𝚌 𝖺𝗇𝖽 𝚔𝚎𝚢𝚛𝚒𝚗𝚐 🔐</summary>

1. Configure `keyring` first

    ```bash
    pip install keyring keyrings.alt

    # if you are on Linux, execute commands below additionally.
    cat >"$(keyring diagnose | grep "config path:" | cut -d' ' -f3)"<<EOF
    [backend]
    default-keyring=keyrings.alt.file.PlaintextKeyring
    EOF

    # encrypt your pypi token 
    ## pypi
    keyring set https://upload.pypi.org/legacy/ __token__

    ## enter your pypi token when prompted

    # verify that the encrypted token has been stored
    keyring get https://upload.pypi.org/legacy/ __token__ 

    # ------------------------ same for testpypi ------------------------

    ## testpypi
    keyring set https://test.pypi.org/legacy/ __token__

    ## enter your pypi token when prompted

    # verify that the encrypted token has been stored
    keyring get https://test.pypi.org/legacy/ __token__
    ```

2. Configure `.pypirc`

    ```bash
    # refer to https://packaging.python.org/en/latest/specifications/pypirc/
    cat >~/.pypirc<<EOF
    [distutils]
    index-servers =
        pypi
        testpypi

    [pypi]
    repository = https://upload.pypi.org/legacy/

    [testpypi]
    repository = https://test.pypi.org/legacy/
    EOF

    chmod 600 ~/.pypirc
    ```

3. At this point, there is **no need** to verify your token manually when you upload packages via `twine upload`

</details>

## 🗃 Project Management 

> This section emphasizes the effective management of your project on `GitHub`.

<details>
<summary>Ⅰ 𝐒𝐭𝐚𝐧𝐝𝐚𝐫𝐝𝐢𝐳𝐞𝐝 𝐜𝐨𝐧𝐭𝐫𝐢𝐛𝐮𝐭𝐢𝐨𝐧 𝐩𝐫𝐨𝐜𝐞𝐬𝐬 💼</summary>

Standardizing project participation cuts communication costs and boosts development efficiency. This mainly focus on the files below: 

1. [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) : guide other to make contribution to your project. To change it, refer to [link](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors).

2. [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE) : standardize the format of `issue` reporting. Composed of
    > Tips: Open the [`Issue page`](https://github.com/Ahzyuan/Python-package-template/issues/new/choose) to see what the template looks like.

    - [`bug_report.yml`](.github/ISSUE_TEMPLATE/bug_report.yml): template for reporting bugs.
    - [`feature_request.yml`](.github/ISSUE_TEMPLATE/feature_request.yml): template for requesting new features.
    - [`config.yml`](.github/ISSUE_TEMPLATE/config.yml): A selector for templates that restricts issue initiation without templates.
    
    If you are to change it, refer to [link1](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository), [link2](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) and [link3](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema).
   
3. [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) : standardize the format of `Pull Request`. To change it, refer to [link](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).

</details>

<details>
<summary>Ⅱ 𝐂𝐈/𝐂𝐃 𝐯𝐢𝐚 𝐆𝐢𝐭𝐡𝐮𝐛 𝐀𝐜𝐭𝐢𝐨𝐧 🤖</summary>

> ⚠️⚠️⚠️     
> • Due to the need of publishing to PyPI and TestPypi, **trusted publishers of  two platform needs to be configured first before use**. Following [tutorial 1](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/#configuring-trusted-publishing) and [tutorial 2](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/#github-actions) to make it.       
> 
> • **NOTE**: The `Environment name` item in configuration should be the same as what you specify in the workflow file.
> > For example, in the provided [publish_release.yml](.github/workflows/publish_release.yml), the `Environment name` is `pypi` in PyPI platform, cause we specify it in job `Publish-PyPI.environment.name`.

- By creating a `.yml` file under the `.github/workflows/` directory, CI/CD support for the project can be achieved.

- In this template repo, the automation of **steps 6 to 8** in `🔨 Usage` section is implemented. Once a **push with a tag** is made and the **tag matches a template** of the form `v*.*.*`, events below will happen:
  1. Build distribution packages, i.e., `.tar.gz` and `.whl` files
  2. Verify meta information of the distribution packages
  3. Release distribution packages to `PyPI` and `TestPyPI`, respectively
  4. Generate release according to tag name and `CHANGELOG.md`
  5. Upload the distribution package to the generated release.

- If you are to change the task flows, please see [Github Actions document](https://docs.github.com/en/actions) for more details.
  
> ❗️❗️❗️      
> If you want to disable the CI/CD feature, there are two options:           
> • delete the `.github/workflows/` directory        
> • do `Settings -> Actions -> General -> Disable actions` in project setting.

</details>

## 📑 To Do

- [x] Add full pipeline of package development, from project preparation to maintaining.
- [x] Add CI/CD support, such as GitHub Actions
- [x] Add `pyproject.toml` support
- [x] Add linter

## 👀 See More

- [Ruff document](https://docs.astral.sh/ruff/)
- [Isort document](https://pycqa.github.io/isort/index.html)
- [Setuptools User Guide](https://setuptools.pypa.io/en/latest/userguide/index.html)
- [Official Python Packaging User Guide](https://packaging.python.org)
- [Publishing package using GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

# 🧾 License

This is free and unencumbered software released into the public domain. Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.