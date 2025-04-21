# ✨ Welcome to TorchMeter Contributors' Hub!

Thank you for wanting to make `torchmeter` even better!

Whether you're:

- 💬 **Asking questions**
- 🚨 **Reporting bugs**
- 👨‍💻 **Contributing code**

Your input is pretty valuable to our community! 

Before jumping in, let's ensure smooth collaboration by reviewing these guidelines first.     
They'll help us keep things organized and make your contribution process as efficient as possible! 

---

## 💬 Discussions — Let's Collaborate & Innovate!

> [!NOTE]
> - `Discussions` section is for **non-urgent questions**, **ideas**, or **general chat**        
> - Access to `Discussions`: 
>
>   | Github UI |  Link  |
>   | :-------: | :-----:|
>   | <img src="assets/discussion_button.png" style="width: 400px; height: auto;"> | [🔗 Jump to Discussions](https://github.com/TorchMeter/torchmeter/discussions) |
>
> - Further reading: [Github Docs of Discussions](https://docs.github.com/en/discussions)

### **① Scenarios of Using Discussions**  

👉 When you want to:  
- **Share use cases**  
- **Ask "how-to" questions**  
- **Brainstorm new features**
- **Discuss performance optimization strategies** 
- **Propose major refactorings or breaking changes**   
- ... 

> [!TIP]
> For bugs/feature requests → Use [Issues](#🆘-issues--lets-report--enhance)

### **② How to participate in a Discussion**  

- [Starting a discussion](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/collaborating-with-maintainers-using-discussions#starting-a-discussion)

- [Starting a poll](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/collaborating-with-maintainers-using-discussions#starting-a-poll)

### **③ Suggestions**

1. **Search First** 🔍
    - Search for similar topics first
    - Join existing discussions when possible
    - Create new thread only for distinct topics

2. **Hook 'em with a great title** ✍️
   - ✅ Clear example: `"How to show raw data in the tabular report?"`  
   - ❌ Avoid vague titles: `"Help pls"`  

3. **Structure Your Post** 📋
   - Organize content with special markdown syntax, such as header, code blocks, quotes, details blocks, etc. Check [markdown syntax on Github](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) for more details.
   - Link the discussion to relevant issues or PRs if applicable. Use `#issue-number`/`#pr-number` syntax to link to issues or PRs. 

4. **Engage Effectively** 🙋‍♂️
   - Be respectful & constructive  
   - Stay on-topic: Keep replies focused on the topic. 
   - Acknowledge Contributors: Always general to [mark someone’s comment as answer](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/participating-in-a-discussion#marking-a-comment-as-an-answer) if it helps resolve your problem, their contributions deserve recognition!

---

## 🚨 Issues — Let's Report & Enhance! 

> [!NOTE]
> - `Issues` section is for reporting **urgent bugs** or **feature requests**       
> - Access to `Issues`: 
>
>    | Github UI |  Link  |
>    | :-------: | :-----:|
>    | <img src="assets/issue_button.png" style="width: 400px; height: auto;"> | [🔗 Jump to Issues](https://github.com/TorchMeter/torchmeter/issues) |
>
> - Further reading: [Github Docs of Issues](https://docs.github.com/en/issues)

### **① Scenarios of Filing Issues**

👉 Perfect for:
- **Bugs reports**
- **Feature proposals**
- **Documentation errors reports**

> [!TIP]
> For non-urgent questions or help with usage → Use [Discussions](#💬-discussions--lets-collaborate--innovate)

### **② Submission Guide**

1. **Search First** 🔍: 
    - Check existing issues (open/closed)
    - If there are relevant issues, comment if you have more details. If the issue is addressed, give a 👍 reaction to show support, it motivates everyone involved!
    - Otherwise, create a new issue following the steps below.

2. **File an Issue** 🗳 
    - Go to the [`Issues` tab](https://github.com/TorchMeter/torchmeter/issues) and click `New issue`.  
    - Select the template matching your scenario (bug report, feature request, etc.).  
    - Fill out all fields (asterisks `*` denote required information).  
    - Click `Create` to submit.  

> [!TIP]
> 
> <details>
> <summary>1. Illustration of the steps mentioned above</summary>
> 
> <img src="assets/create_issue_from_template.png" style="width: 800px; height: auto;">
> 
> </details>
>
> 2. [How maintainers manage issues](docs/repo_management.md#issue-management)

### **③ Suggestions**

1. **Ensure a Clear Title** ✍️  
    - ✅ Good example: `"Export data error: target file not found"`
    - ❌ Avoid vague titles: `"Something's wrong!"`

2. **Link Related Content** 🔗  
    - If this issue relates to other issues, discussions, or PRs, use `#corresponding-number` to reference them.

3. **Tell the Full Story**   
    - If create an issue from a template: Fill out all requested fields for complete information.  
    - If participate in existing issues: Use the simplified template below to share your additional details:

        ```markdown
        ## If my situation differs from the issue author's
        
        - [ ] No
        - [ ] Yes

        <!-- If choose yes, describe your case -->
        In my case, I found that...
        
        ## Steps to Reproduce

        <details>
        <summary>Steps</summary>

        1. 
        2. 
        3. 

        </details>

        ## Environment
        
        - `OS`: Ubuntu 22.04
        - `Python`: 3.10
        - `torchmeter`: 0.4.2
        
        ## Additional context

        <!-- 
        Any addition information helping to resolve this issue is welcome. \
        You can include code snippets, error traces, screenshots/GIFs, or other relevant materials here. 
        -->

        <details>
        <summary>Details</summary>

        1. 
        2. 
        3. 

        </details>
        ```

## 📤 Pull Requests — Let's Squash Bugs & Build Features!

> [!NOTE]  
> - `Pull Requests (PR)` are for **code contributions**  
> - Access to PRs:  
> 
>   | GitHub UI | Quick Link |  
>   | :-------: | :--------- |  
>   | <img src="assets/pr_button.png" style="width:400px"> | [🔗 Jump to PRs](https://github.com/TorchMeter/torchmeter/pulls) |  
>
> - Further reading: [Github Docs of Pull Requests](https://docs.github.com/en/pull-requests)

### **① Scenarios of Submitting a PR**  

👉 Perfect for:  
- **Bug fixes**  
- **New features**  
- **Documentation updates**  
- **Performance optimizations**  
- **Test coverage enhancements**  
- **CI/CD pipeline improvements**
- **Code improvements / refactoring** 

### **② Step-by-Step Guide**

> [!IMPORTANT]
> 
> 1. `torchmeter` is hosted on [GitHub](https://github.com), so you’ll need a [GitHub account](https://github.com/signup/free) to begin contributing.
> 2. `torchmeter` uses [Git](https://git-scm.com/) for version control. If you're unfamiliar with Git basics or GitHub PR workflows, we recommend these resources: 
>    - [Git Tutorial](https://git-scm.com/book/en/v2) 
>    - [GitHub's Guide to Contributing via PR](https://docs.github.com/en/get-started/quickstart/contributing-to-projects)
> 3. Our branching strategy and contribution process draw inspiration from projects like `numpy`, `pandas`, `polars`, and `rich`. For reference:
>     - [torchmeter's branching strategy](docs/repo_management.md#branching-strategy) 
>     - [numpy's contributing guide](https://numpy.org/doc/stable/dev/index.html)
>     - [pandas' contributing guide](https://pandas.pydata.org/docs/dev/development/contributing.html)
>     - [polars' contributing guide](https://docs.pola.rs/development/contributing/)
>     - [rich's contributing guide](https://github.com/Textualize/rich/blob/master/CONTRIBUTING.md)

---

#### A. Claim Your Mission

> [!NOTE] 
> This section will guide you through:
> 
> - Discovering beginner-friendly start points
> - Properly claiming unassigned issues
> - Collaborating on existing development efforts
> 
> By following these protocols, you'll establish clear ownership while respecting community norms. We're excited to help you find meaningful work that aligns with project needs and your interests!

1. **Finding Beginner-Friendly Issues**: New to `torchmeter` or open-source? We recommend:
    - Start by searching for `good-first-issue` labeled issues on the [Issues page](https://docs.github.com/en/issues). These are specially marked for beginners and often have clear scopes.
    - Look for issues without existing assignees to avoid duplication of effort.

2. **Claiming an Issue**
    - To take ownership of an **unassigned** issue: Leave a polite comment like: `"I’d try to work on this!"` or just a single `"take"`. This signals your intent and allows maintainers to assign it to you.
    - Responsibility note: Claiming an issue means you’ll be responsible for following up and resolving it. If circumstances prevent you from continuing, please update the thread promptly so others can help.

3. **Joining Existing Efforts**
    - Politely ask current assignee via comment: For example, `"Hi @username, may I collaborate on this?"`
    - Wait patiently: If the current contributor hasn’t updated the issue for 7+ days, you may gently ask if they need help or if you can take over.

---

#### B. Environment Setup

> [!NOTE]  
> This section will help you configure a development environment for `torchmeter`. We'll walk through essential steps including:
> 
> - `Git` configuration for version control
> - `Python` environment setup with required dependencies
> - Local repository initialization and remote tracking
> 
> By completing these steps, you'll have a fully functional setup to start contributing code effectively. Let's begin now!

##### B.a Download & Install Git

1. Download: Visit the official Git download page → https://git-scm.com/downloads

2. Verify Installation: Open your terminal and run the following command. A successful installation will display the Git version (e.g., `git version 2.49.0`).

    ```bash
    git --version
    ```
---

##### B.b Create a Fork Repository

> [!TIP]
> - A fork repo is a copy of the original repository, allowing you to make changes without affecting the original project. 
> - Learn more: [GitHub Forking Guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)

1. Go to the official `torchmeter` repository page → https://github.com/TorchMeter/torchmeter

2. Click the `Fork` button in the top-right corner

3. Configure your fork:
   - Select your GitHub account as the owner
   - Keep the default repository name unless you want to customize it
   - Uncheck `Copy the master branch only` to include all branches

4. Click `Create fork`. You'll now have a personal sandbox repository at `https://github.com/<your-username>/torchmeter` if you not change the default repository name.

<details>
<summary>Illustration of forking torchmeter</summary>

<img src="assets/fork_torchmeter.png">

</details>

---

##### B.c Clone Your Fork to Local Machine

1. Go to your GitHub account's [Repositories page](https://github.com/) and navigate to your newly created fork of `torchmeter`.

2. Copy the repository URL:
   - Click the green `Code` button on your fork's page
   - Select the `Local-HTTPS` tab and copy the URL (e.g., `https://github.com/<your-username>/torchmeter.git` if you kept the default repository name)

3. Clone to your local system

    ```bash
    cd path/to/your/working/directory

    # Replace `torchmeter-yourname` with your desired directory name
    git clone <paste-the-url-copied-in-last-step-here> torchmeter-yourname
    ```

4. Verify: A new directory `torchmeter-yourname` will be created containing:
    - Working directory: Your local copy of the project files
    - Local repository: The `.git` folder managing version control (contains commit history, branches, etc.)

> [!TIP]  
> [What is the difference between the working directory (aka workspace) and the repository?](https://medium.com/tech-journey-with-anna/git-question-what-is-the-difference-between-the-working-directory-aka-workspace-and-the-eeee15b7e4b3)

---

##### B.d Link to Official Repository of torchmeter (Upstream)

1. Set up upstream tracking to sync with the latest changes:
 
    ```bash
    # pwd: path/to/your/working/directory

    cd torchmeter-yourname

    # Add the official repository as upstream
    git remote add upstream https://github.com/TorchMeter/torchmeter.git

    # Fetch the latest updates
    git fetch upstream
    ```

2. Verify the connection: Run `git branch -a` to confirm both your fork (`origin`) and the official repo (`upstream`) are connected:
   
    ```bash
    git branch -a

    # Expected output:
    #
    # * master
    # remotes/origin/HEAD -> origin/master
    # remotes/origin/master
    # remotes/origin/v0.1.x (or more of `remotes/origin/va.b.c`)
    # remotes/upstream/HEAD -> upstream/master
    # remotes/upstream/master
    # remotes/upstream/v0.1.x (or more of `remotes/upstream/va.b.c`)
    ```
> [!TIP] 
> Understanding remotes:
> - `origin` always points to your fork on GitHub, i.e., `https://github.com/<your-username>/torchmeter` if you kept the default repository name in forking.
> - `upstream` points to the official `torchmeter` repository, i.e., `https://github.com/TorchMeter/torchmeter.git`
> To update your fork: git pull upstream master
> Regularly sync your fork with the main project using our synchronization workflow

---

##### B.e Configure Python Environment

> [!TIP] 
> Virtual environment for `torchmeter`
> - We recommend creating a dedicated Python virtual environment for `torchmeter` development. 
> - You can use virtual environment management tools like `venv`, `uv`, `poetry`, or `conda`. 
> - Here we'll use `conda` as an example; other tools can be configured via their official documentation.

1. Install `Miniconda`:
    - Official guide: [Miniconda Installation](https://www.anaconda.com/docs/getting-started/miniconda/install)
    - Verify installation:
     
    ```bash
    conda --version  

    # Expected output: conda version (e.g., "conda 24.1.2")
    ```

2. Create virtual environment with `Python 3.8` (minimum required version):
   
    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

     # "torchmeter-dev" is customizable, is the virtual environment name
    conda create -n torchmeter-dev python=3.8 
    ```

3. Install `torchmeter` as well as its dependencies in editable mode:

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    # Replace `torchmeter-dev` with your virtual environment name
    conda activate torchmeter-dev
    pip install -e ".[test]"
    ```

> [!WARNING]
> 
> 1. The `-e` flag is required to enable coverage tracking in tests. Omitting it may cause coverage reporting issues.
>
> <details>
> <summary>2. For Windows Users with NVIDIA GPUs</summary>
> 
> 1. Verify `Pytorch`'s CUDA compatibility:
> 
>     ```powershell
>     # Replace `torchmeter-dev` with your virtual environment name
>     conda activate torchmeter-dev  
>     
>     python -c "import torch; print(torch.cuda.is_available())"  
>     # Should return True
>     ```
> 
> 2. If `False`, manually install GPU-enabled `Pytorch`:
> 
>      - Determine CUDA version:
> 
>        ```powershell
>        nvidia-smi | findstr "CUDA Version"  
>        # Check the version number, e.g. "CUDA Version: 12.4"
>        ```
> 
>      - Download appropriate `Pytorch` wheel:
>          - `Pytorch` binaries: [https://download.pytorch.org/whl/torch](https://download.pytorch.org/whl/torch)
>          - Match `Python` version (e.g., cp38 for Python 3.8), `CUDA` version (e.g., cu124), and `OS`. Example: `torch-2.4.1+cu124-cp38-cp38-win_amd64.whl`
>          - `torchmeter` supports `Pytorch` versions ≥ `1.7.0`.
> 
>      - Install `torch` by `whl` file:
> 
>        ```powershell
>        # Replace `torchmeter-dev` with your virtual environment name
>        conda activate torchmeter-dev
> 
>        pip install path/to/downloaded/torch.whl
>        ```
> 3. Validate GPU support: re-execute the command in step 1 to confirm GPU support.
> 
> </details>

---

#### C. Making Code Changes

> [!NOTE]  
> This section will guide you through:
> 
> - Understanding code architecture and implementing changes
> - Maintaining code quality through type-checking, linting and testing
> - Following proper version control practices for local/remote submissions
> 
> By completing these steps, your code will not only adhere to project standards and remain robust and maintainable, but also be properly prepared for official review.

##### C.a Understanding Code & Getting started

> [!TIP] 
> Recommended Tools
> 
> 1. Debugger: `pdb`
>     - Purpose: For code debugging
>     - Quickstart Guide: [PDB Tutorial](https://github.com/spiside/pdb-tutorial)
>     - Documentation: [Python PDB Docs](https://docs.python.org/3/library/pdb.html)
> 
> 2. Interactive Development: `IPython`
>     - Purpose: For rapid logic validation (powerful REPL)
>     - Documentation: [IPython Official Site](https://ipython.readthedocs.io/en/stable/)

1. Fetch Latest Code of `torchmeter` 

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    git checkout master
    git pull upstream master --ff-only
    ```

2. Create Your Development Branch

    > Please follow our [branch naming conventions](docs/pr_standard.md#branch-name) when naming a branch.

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname
    
    # Replace `<your-branch-name>` with your branch name
    git checkout -b <your-branch-name> upstream/master
    ```

3. Dive into the code
    1. You can start by reviewing the [annotated project tree](docs/project_structure.md) for a quick understanding of the project layout.
    2. Based on your insights, locate the specific files/classes/functions to modify. You can make it via the IDE's file tree, text searching or IDE navigation (`Ctrl/Cmd+Click` to jump to definitions).
    3. If you successfully find the parts you need to modify, you can start reading the source code in combination with the annotation document to figure out its logic and working principle.
    4. If you’re stuck, there are 3 ways to move on:
        - Use `pdb` breakpoints: insert `import pdb; pdb.set_trace()` at the problematic part of the code, then run the code and it will stop at the breakpoint and allow you to inspect the variables.
        - For persistent confusion, kindly start a [Discussion](#💬-discussions--lets-collaborate--innovate)

4. Start implementing your modifications after fully grasping the existing logic. Note that it's highly recommended to focus your changes on one issue or feature. This will make the review process easier.

5. You can verify your modifications through debugging or custom scripts, but we recommend using `IPython` for rapid testing:
     1. Install `Ipython`:

        ```bash
        # Replace `torchmeter-dev` with your virtual environment name
        conda activate torchmeter-dev

        pip install ipython
        ```

     2. Open the terminal and type `ipython` to start the interactive environment. You can then import and test your modified code directly. For example, if you added a new function `new_func()` in `torchmeter.core`: 

        ```python
        from torchmeter.core import new_func

        # Test your implementation
        new_func(args1, args2)
        ```

6. Finally, update contributors list: 
    1. Open `CONTRIBUTORS.md` in the project root directory
    2. Add your information at the end following this format to ensure proper formatting consistency:
     
        ```markdown
        - [Your-Name/Github-ID](GitHub-profile/your-home-page)
        ```

---

##### C.b Lint, Format and Test your Code

> [!TIP]  
> For VS Code users, we recommend installing:
> - [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) 
> - [Mypy extension](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker)

To ensure your code meets `torchmeter`'s standards, please complete these 3 critical steps **in order**.

1. Type Checking
    - `torchmeter` uses `mypy` for static type checking (already installed in step [B.e.3](#be-configure-python-environment)).
    - You'll need to add **type annotations** to your changes. Please refer to `mypy` [documentation](https://mypy-lang.org) for best practices.
    - After completing the type annotations, make sure to pass the following type checking commands:

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname
        
        # Replace `torchmeter-dev` with your virtual environment name
        conda activate torchmeter-dev
        
        mypy ./torchmeter
        # You should promise output is something like `Success: no issues found in <number-of-files> source files`
        ```

2. Linting and Formatting
    - `torchmeter` uses `ruff` for linting/formatting (already installed in step [B.e.3](#be-configure-python-environment)).
    - Our style rules are defined in `ruff.toml`, please respect these configurations. If you find any rules unreasonable, please start a [Discussions](#💬-discussions--lets-collaborate--innovate)
    - Ensure your changes comply with the project's code style by running the following linting commands:

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname
            
        # Replace `torchmeter-dev` with your virtual environment name
        conda activate torchmeter-dev

        ruff check \
        --preview \
        --target-version=py38 \
        --output-format=grouped

        # You should promise output is `All checks passed!`
        ```

    - If the code analysis passes, then ensure that the code format meets the project requirements.

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname
            
        # Replace `torchmeter-dev` with your virtual environment name
        conda activate torchmeter-dev

        ruff format \
        --diff \
        --preview \
        --target-version=py38

        # You should promise output is only one line showing`<number-of-file> files already formatted`
        ```

    - If any step fails, please modify the code according to the terminal output and re-execute the above steps until both steps are successful. If you are a VSCode user, we recommend using the `ruff` plugin to automatically perform code linting and formatting. This plugin uses underlines to highlight code snippets that do not conform to the predefined rules and allows you to automatically fix some common errors.

> [!TIP]   
> If you have a way to run the `shell` script (on Unix-like systems or `cygwin` on `windows`)), then: 
> ```bash  
> # pwd: path/to/your/working/directory/torchmeter-yourname  
> 
> bash misc/lint_format.sh  
> ```  
> This runs all linting and formatting in one command.

3. Testing
    - `torchmeter` uses `pytest` for testing code. Yes, `pytest` and the related plugins have also been installed in step [B.e.3](#be-configure-python-environment).
    
    - `torchmeter` has written the `pytest` running configuration in the `pytest.ini` file at the root directory of the project. This file defines how the tests are run, including the test directory, test filters, test configuration, etc. Specifically, `pytest` will only discover tests in the `tests` directory at the root of the project, and requires a test coverage rate of **> 90%**. 
    
    - Therefore, if you add new functions or classes, please ensure that corresponding test cases are added. Regarding the writing of test cases, you can refer to the [official documentation](https://docs.pytest.org/en/stable/index.html) of `pytest` or quickly get started through the project [`python_testing_tutorial`](https://github.com/krother/python_testing_tutorial). During the process of writing test cases, we recommend using `fixture` and `parametrize` for parameterized testing, so as to reduce duplicate code.
    
    - After you've completed the above steps (i.e. type annotation, linting and formatting), please make sure to run the following commands to ensure the logical correctness and stability of the code. 

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname
                    
        # Replace `torchmeter-dev` with your virtual environment name
        conda activate torchmeter-dev

        pytest -q
        # You should promise there is no error reported in the output.
        # If all tests passed, you will see the coverage report in the terminal.
        ```

---

##### C.c Add Documentation for Your Code

> [!NOTE]  
> **Why this matters?**  
> 1. **Your expertise**: Your first-hand knowledge makes your documentation the most authoritative and comprehensive source.  
> 2. **Enhance readability**: Clear documentation helps maintainers quickly grasp your code's logic and intent during PR reviews.  
> 3. **Faster iteration**: Consistent documentation practices reduce redundant efforts for maintainers, allowing `torchmeter` to evolve more efficiently.  
>   
> **How torchmeter builds docs**  
> - The documentation of `torchmeter` is built based on [`mkdocs`](https://www.mkdocs.org). For the `API Reference` section, `mkdocstrings[python]` is used to automatically extract multi-level annotations of modules, classes, functions, etc. and generate the relevant content.
> - To identify the structure in the extracted annotation text, `mkdocstrings[python]` requires a clear annotation format. In `torchmeter`, you are required to write annotation documents following the [`google` format specification](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings). 
>   
> **Recommended tool**: The VSCode extension `autodocstring`  
> - [Official Page](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring).  
> - Configure format: Open VSCode settings (`Ctrl/Cmd+,`) → search for `autodocstring.docstringFormat` → select `google`.  

1. For new/modified functions or class methods
    - Add **function-level documentation** following [Google’s function-level guidelines](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods).
    - Example:  

        ```python
        def example_function(arg1: int, arg2: str) -> bool:
            """Short description of the function's purpose.

            Args:
                arg1 (int): Description of argument 1.
                arg2 (str): Description of argument 2.
            
            Raises:
                ValueError: If `arg1` is not an integer, or `arg2` is not a string.

            Returns:
                bool: Description of return value.
            """
            
            if not isinstance(arg1, int):
                raise ValueError("arg1 must be an integer")

            if not isinstance(arg2, str):
                raise ValueError("arg2 must be a string")

            # Your implementation here

            return True if arg1 > 0 and args.startswith('a') else False
        ```  

2. For new/modified classes:  
   - Add **class-level documentation** following the [Google class guidelines](https://google.github.io/styleguide/pyguide.html#384-classes).
   - If you add a brand new class, you need to add both class-level documentation for the class and function-level documentation for each method.
   - Example:
  
        ```python
        class ExampleClass:
            """Class description and purpose.

            Attributes:
                attr1 (int): Description of class attribute.
            
            Methods:
                method1: Method description and purpose.
            """

            attr1 : int = 0

            def method1(self, arg1: int) -> bool:
                """Method description and purpose.

                Args:
                    arg1 (int): Description of argument 1.
                
                Raises:
                    ValueError: If `arg1` is not an integer.
                
                Returns:
                    bool: Description of return value.
                """
                if not isinstance(arg1, int):
                    raise ValueError("arg1 must be an integer")

                # Your implementation here

                return True if arg1 > 0 else False

            # other methods here
        ```

> [!TIP] 
> 𝑨𝒄𝒌𝒏𝒐𝒘𝒍𝒆𝒅𝒈𝒎𝒆𝒏𝒕       
> Document writing can be rather dull and requires clear expression skills.     
> We sincerely appreciate every contributor who is willing to add to the documentation!     
> Thank you 🙏

---

##### C.d Commit Changes to Local Repository

> [!TIP]   
> - Forgot what a local repository is? Please check step [B.c](#bc-clone-your-fork-to-local-machine).
> - Recommended Tools: [`Git Graph`](https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph)(VSCode extension) for visualizing commit history.

Once you feel that your changes have made phased progress, you can incorporate them into version management by committing the changes to the local repository.    
Please follow these steps:

1. Make sure you are on the branch for development
    1. Check your current branch

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname

        git branch --show-current
        ```
    2. You should ensure that the branch output by the above command is consistent with the branch set in step [C.a.2](#ca-understanding-code--getting-started). Otherwise, use the following command to switch branches:

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname

        # replace `<branch_name>` with your branch name set in step C.a.2
        git checkout <branch_name>
        ```

2. Review Your Changes
    1. List modified files

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname

        git status

        # You may see something like this
        # ---------------------------------------------------------------------------
        # On branch <your-branch-name>
        # Changed but not updated:
        #   (use "git add <file>..." to update what will be committed)
        #   (use "git checkout -- <file>..." to discard changes in working directory)
        #
        #  modified:   a.py
        #
        # Untracked files:
        #   (use "git add <file>..." to include in what will be committed)
        #
        #  b.py
        no changes added to commit (use "git add" and/or "git commit -a")
        ```
    
    2. Please ensure that all your changes appear in the output of the above command. If there are unexpected changes, you can execute the following command to view it:

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname

        git diff path/to/unexpected_changed_files
        ```

    3. If there are any changes you don't want, you can use the following command to undo them. Otherwise, you can skip this step.

        ```bash
        # pwd: path/to/your/working/directory/torchmeter-yourname

        # ⚠️ be careful, this command will discard all changes in the target file and it is irreversible
        git restore path/to/modified_files
        ```

3. When all changes have been confirmed, you can optionally commit them to the staging area[^1].

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname
    
    # You can execute "git add" multiple times to ensure that all the changes you wish to commit have been added to the staging area
    git add path/to/modified_files/you/want/to/commit
    ```

4. When all the changes you desire have been staged, you can use the following command to commit the staged changes to the local repository:

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname
    
    # Double-check staged files
    git status

    git commit
    ```

5. The above command will open a text editor in the terminal (it will be opened with `vim` or `nano`), and you need to fill in the commit message in it.
    - We recommend describing **what** and **why** of the changes in the simplest possible way. If this commit is related to an `issue` or `PR`, please ensure that you have associated this commit with the corresponding `issue` or `PR` by using `closes #<issue-number>`, `fixes #<issue-number>` or `Refs: <PR-number>`etc. 
    - Refer to our [Commit Message Guidelines](docs/pr_standard.md#commit-message) for specific requirements.

6. After editing, save and close the editor. Then the changes in the staging area will be committed to the local repository. You can use the following command to view your commit history. If you are a VSCode user, you can use the `Git Graph` extension to view the commit history more conveniently and intuitively.

    ```bash
    git log --pretty=format:'%h %ad | %an | %s%d' --graph --date=short
    ```

> [!IMPORTANT]
> While multiple commits are acceptable before pushing to the remote repository (i.e. your fork repository), it is highly recommended to **keep your commit history concise** (e.g., 3–6 commits). That is because large batches of changes may complicate review processes. For extensive refactors, consider splitting work into separate PRs addressing individual features/fixes.

[^1]: The staging area is a temporary storage area that holds the changes you'll add to your next commit. It's like the shopping cart you use before paying at the supermarket, where the items in the cart are your changes here. It should be noted that when you need to stage an empty folder, please ensure that the folder is not empty. Otherwise, you need to create an empty file named `.gitkeep` in it.

---

##### C.e Push Changes to Your Fork Repository

> [!TIP] 
> 
> 𝑬𝒏𝒂𝒃𝒍𝒆 𝑮𝒊𝒕𝑯𝒖𝒃 𝑨𝒄𝒕𝒊𝒐𝒏𝒔 𝒊𝒏 𝒀𝒐𝒖𝒓 𝑭𝒐𝒓𝒌 𝑹𝒆𝒑𝒐𝒔𝒊𝒕𝒐𝒓𝒚
>
> 1. **What is GitHub Actions in forks?**    
>     - `GitHub Actions` is GitHub's CI/CD service that automates workflows through `YAML` configurations. Learn more: [GitHub Actions Docs](https://docs.github.com/en/actions).   
>     - `torchmeter` uses predefined workflows for compatibility testing, automated releases, PR management, and README updates, etc. See all our [workflow files](.github/workflows/)   
> 
> 2. **Why enable it?**   
>     - Your fork inherits the original repo's workflows but defaults to disabled for security[^2].    
>     - Enabling it allows you to simulate the CI process triggered when a PR is submitted to the official repo, which helps you find problems as early as possible.   
>     - In `torchmeter`, compatibility testing is mandatory for PR merging. Therefore, it is necessary to enable it for simulating the CI process.
>
> 3. **How to enable**: Go to your fork's **Actions** tab → click the `I understand my workflows, go ahead and enable them` button.

1. When you believe you've completed all your changes or need to save your progress temporarily, you can push the current commit history of your local repository to the remote repository (i.e., your `fork` repository). Execute the following commands.

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    # You need to replace <your-branch-name> with the branch name created in step C.a.2.
    # You also need to replace <remote-branch-name> with one that will receive the changes in remote repository. Generally, we keep it the same as <your-branch-name>.
    git push -u origin <your-branch-name>:<remote-branch-name>
    ```

2. If you have enabled the `Github Actions` for your `fork` repository, you can submit a PR to the `master` branch of the remote repository (i.e., your `fork` repository) to automatically trigger the compatibility test we've prepared for you:
    1. Open the page of your fork repository. Shortly after pushing your changes, you'll find a prominent `Compare & pull request` button. ([Illustration](https://docs.github.com/assets/cb-34097/mw-1440/images/help/pull_requests/pull-request-compare-pull-request.webp))
    2. Click this button. In the pop-up page, select the `base` branch as the `master` branch of **your fork repository**, and select the `head` branch as the `<remote-branch-name>` branch you just pushed.Please double-check that the `base` branch is the `master` branch of **your `fork` repository**, not the `master` branch of the official `torchmeter` repository.
    3. Fill in the PR title. See [PR Title Convention](docs/pr_standard.md#pull-request-title)
    4. Fill in the PR description. Since you are just testing, the description can be brief, no need to fill it in according to the predefined template. 
    5. Click the `Create Pull Request` button below, and you have created a PR targeting the `master` branch in your fork repository.
    6. Click on the `Actions` tab. You will see a task named `✅ Compatibility Test ❌` is running. It is the compatibility test workflow of the `torchmeter` project.
    7. Wait for the task to finish running. If the task fails, check the error, modify the code locally, and then re-commit to the remote repository. This will update the commit history of the PR and trigger the minimal test `✅ Minimal Test ❌`.
    8. If the minimum test is passed, click on the `Actions` tab, select `✅ Compatibility Test ❌`, click `Run workflow`, choose your branch and run. This will re-trigger the compatibility test, do it until it is passed.

> [!TIP] 
> In the command of step 1, the `-u` parameter indicates that the `<your-branch-name>` branch in local repository will track the `<remote-branch-name>` branch in remote repository. Thus, when you make new commits on `<your-branch-name>` in local repository, you can easily push them to the `<remote-branch-name>` branch in remote repository with a simple `git push` command, no need to re-type the remote repository's target branch name. 

[^2]: You can enable `Github Actions` for your fork repo without worry as we've added repository validation for sensitive operations (like package publishing), so you can rest assured to enable it.

---

#### D. Contribute to Official Repository

> [!NOTE]  
> Now, your code has been pushed to GitHub but is not yet part of the official `torchmeter` repository. In this section, we'll guide you through the final steps to complete your contribution journey:
> 
> - Submit your PR to the official torchmeter repository  
> - Collaborate positively with reviewers  
> - Celebrate your successful contribution
>   
> By following these steps, your code will officially merge into `torchmeter`'s `master` branch and become part of the next release to benefit all users. We're thrilled to guide you through this final phase!

##### D.a Avoiding Protential Merge Conflicts

> [!CAUTION]   
> 
> 1. **What is a merge conflict?**  
> When two branches make conflicting changes to the **same part of a file**, `Git` cannot automatically decide which should be kept. This creates a blocking state where your PR cannot be merged until resolved. 
> 
> 2. **Why they happen?**
> As all contributors work on the `master` base branch, new commits may be added while you develop. Then when you try to merge your PR, your changes may clash with these updates.
> 
> 3. **Learn more**  
>     - [Understanding merge conflicts](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/about-merge-conflicts)  
>     - [Step-by-step conflict resolution guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line)

1. Check for upstream changes: 

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    git fetch upstream

    # You need to replace <your-branch-name> with the branch name created in step C.a.2.
    git rev-list --count <your-branch-name>..upstream/master 
    ```

2. If output is 0, it indicates that there are no leading commits in `upstream/master`. In this case, proceed to [D.b](#db-create-a-pull-request-to-torchmeter)

3. If output > 0, it indicates that there are ahead commits in `upstream/master`. In this case, you need to resolve the merge conflicts through [`rebase`](https://git-scm.com/book/en/v2/Git-Branching-Rebasing):

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    # back up the new branch, you need to replace <your-branch-name> with the branch name created in step C.a.2.
    git checkout <your-branch-name>
    git branch <your-branch-name>-bak <your-branch-name>

    # rebase the new branch onto the latest commit of the target branch.
    git rebase upstream/master
    ```

4. The above command will attempt to rebase your branch `<your-branch-name>` onto the latest commit of the `master` branch of official `torchmeter` repo(i.e. the `upstream/master` in your local repo). Two scenarios may occur:
    - Your changes do not conflict with the latest commit of the target branch. The rebase was successful, and you will see the following output. In this case, you're ready to proceed to [D.b](#db-create-a-pull-request-to-torchmeter)

        ```
        Successfully rebased and updated refs/heads/<your-branch-name>.
        ```

    - There is a conflict between your changes and the latest commit of the target branch, and the rebase has failed. You will see output similar to the following, which indicates the commit where the conflict occurred and the file(s) involved.

        ```
        Auto-merging test.py
        CONFLICT (content): Merge conflict in test.py
        error: could not apply 5d3f9e2... Add new feature logic

        hint: Resolve all conflicts manually, mark them as resolved with
        hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
        hint: You can instead skip this commit with "git rebase --skip".
        hint: To abort and get back to the state before "git rebase", run "git rebase --abort".

        Could not apply 5d3f9e2... Add new feature logic
        ```

5. If the rebase fails, when you open the conflicted files, you will find conflict markers such as `<<<<<<< HEAD`, `=======`, `>>>>>>>` in them. The conflict content of the two branches is divided by `=======`, as shown below.

    ```python
    <<<<<<< HEAD
    print("Original content from master branch")
    =======
    print("New feature implementation")
    >>>>>>> 5d3f9e2... Add new feature logic
    ``` 

6. If there are conflicts, you need to resolve them manually. Discard the old changes and remove all conflict markers[^3]. It should be noted that during the conflict resolution process, you are actually in an interrupted state of the previous `rebase` command. Therefore, you can use the following commands to revert the changes or completely cancel the whole `rebase` operation:
    - Discard the existing changes：`git reset --hard <your-branch-name>`
    - Cancel rebase: `git rebase --abort`

7. Once you have resolved all the conflicts, you need to execute the following commands to continue the `rebase` operation:

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    git status
    git add path/to/conflict/file
    git rebase --continue
    ```

8. Repeat step 5 ~ 7 until the rebase is successful. After that, commit the changes to the local repository, and then you can delete the backup branch.

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    git commit 

    # delete the backup branch, you need to replace <your-branch-name> with the branch name created in step C.a.2.
    git branch -D <your-branch-name>-bak
    ```

9. Execute the following commands to synchronize the changes to your fork repository[^4].

    ```bash
    # pwd: path/to/your/working/directory/torchmeter-yourname

    # you need to replace <your-branch-name> with the branch name created in step C.a.2.
    git checkout <your-branch-name>
    git push 
    ```

[^3]: Currently, IDEs have mature support for resolving merge conflicts. For example, you can refer to [Resolve conflicts in VsCode](https://dev.to/adiatiayu/how-to-resolve-merge-conflicts-using-the-merge-editor-feature-on-vs-code-pic) and [Resolve conflicts in PyCharm](https://www.jetbrains.com/help/pycharm/2023.3/resolve-conflicts.html).

[^4]: If you have created a PR to the `master` branch of your fork repo in step [C.e](#ce-push-changes-to-your-fork-repository), you will see that the commit history of PR will be updated synchronously and the minimum test workflow will be automatically triggered to verify the correctness and robustness of your changes.

---

##### D.b Create a Pull Request to torchmeter

> [!IMPORTANT]   
> Before creating a PR, kindly ensure the following prerequisites are met:  
> 1. **Test coverage**: If your changes introduce new functionality or logic, please add corresponding tests (see step [C.b.3](#cb-lint-format-and-test-your-code)).  
> 2. **Documentation**: We highly appreciate contributors who add/update docstrings for your changes (see step [C.c](#cc-add-documentation-for-your-code)).  
> 3. **Branch hygiene**:  
>     - Your local changes are **not** on the master branch (`upstream/master` or `origin/master`). 
>     - The name of the branch to host your change follows our [branch naming conventions](docs/pr_standard.md#branch-name). If not, rename it via: 
>    
>     ```bash
>     # pwd: path/to/your/working/directory/torchmeter-yourname
>     git checkout <your-branch-name> 
>     git branch -m <new-branch-name>
>     ```
> 4. **Sync status**:  
>    - Your branch has been rebased onto the latest `upstream/master` (see step [D.a](#da-avoiding-protential-merge-conflicts))  
>    - All changes pushed to your fork repository. If workflows are enabled, ensure the `✅ Compatibility Test ❌` completes successfully (see step [C.e.2](#ce-push-changes-to-your-fork-repository)).


Once the requirements above are met, proceed to create your PR as follows:

1. Open your fork repository → Click `Pull requests` tab → `New pull request`

2. Configure the PR source/destination:  
   - **base repository**: `TorchMeter/torchmeter`  
   - **base**: `master`  
   - **head repository**: `your-github-id/your-fork-repo`  
   - **compare**: `<your-branch-name>` 

3. Pay attention to the status prompt. If it shows `Can't automatically merge` ([example](assets/merge_conflict_warning.jpg)), there are merge conflicts. In this case, please exit the PR creation page, resolve them following the steps in [D.a](#da-avoiding-protential-merge-conflicts) and retry.

4. Review your changes down the page, so as to ensure complete/correct file modifications.

5. Click the green `Create pull request` button, and complete PR details:
    - **Title**: Follow `torchmeter`'s [PR title conventions](docs/pr_standard.md#pull-request-title).
    - **Description**: You can see that your "Add a description" field is not empty. That's because we've prepared a content template for you to guide your filling. You just need to use [`markdown` syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) to fill it out as completely as possible according to the requirements in the comments. That's all what you need to do. Finally, you can click `Preview` above the input box to preview the rendered content you've filled in.

6. If everything looks good, please check the option `Allow edits and access to secrets by maintainers`. This permission is required to auto-update the `README.md` coverage badge before the PR is merged[^5].

7. Submit your PR
    - For complete implementations (e.g., bug fixes/new features), click **Create pull request** for immediate review.  
    - For in-progress work or consultation requests, choose **Create draft pull request** from the dropdown. [Draft PRs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests) won't trigger formal review processes until you mark it **Ready for review**.  

> [!TIP]  
> All PR types trigger the **Compatibility Test workflow** immediately upon creation to ensure code quality and cross-environment compatibility.

[^5]: The workflow named `🌟 Update README Badge 🔰` is responsible for updating  the coverage badge in `README.md` and committing the changes to PR history. If you're worried about the security issues brought by enabling this option, you can review the [content] of this workflow. `torchmeter` ensures that only modifications related to the coverage badge in `README.md` will be made. No other code or sensitive information will be involved. Moreover, all changes will be publicly recorded, and you can review them at any time. Thanks for your trust!

---

##### D.c Update your PR

Once your PR is created (whether draft or final), `torchmeter` uses automated workflows to ensure quality and facilitate efficient review/merge processes. If these checks fail, please actively collaborate to update the PR accordingly.

1. **PR Title Linting and Formatting**: Once a PR is created, a [workflow](.github/workflows/pr_autolabel.yml) named `🤖 PR Auto-Labeler ⛳` will be automatically triggered. It will determine whether the PR title complies with our [PR title conventions](docs/pr_standard.md#pull-request-title).
    - **If non-compliant**:  
        1. A red `PR-title-needs-formatting` label will be added  
        2. You'll need to modify the PR title using the `Edit` button next to it  
    - **For compliant titles**:  
        1. Category labels are automatically assigned based on title prefixes  
        2. These labels help organize PRs and inform our changelog generation  

2. **Code Linting, Formatting and Compatibility Testing**:
    - Once a PR is created, a [workflow](.github/workflows/compatibility_test.yml) named `✅ Compatibility Test ❌` will be automatically triggered. It will check whether the code in the PR meets the style and format requirements defined in `ruff.toml`. If both pass, compatibility tests will be conducted across platforms (`windows`, `macOs`, `linux`) and across versions (`python 3.8` to `python 3.13`).
    - If any step fails, `torchmeter` will provide an error report on the workflow run page. Please download it, review it, and try to fix the problem. You can try to solve the problem by creating a new commit for the fix in your local repository and pushing it to the remote repository. The commit history of the PR will be automatically synchronized with the history of the `head` branch. It should be noted that every time PR is updated like this, an automated test [workflow] () named `✅ Minimal Test ❌` will be triggered, which will execute the test in a randomly selected system and `python 3.8`. Without consuming a lot of time and resources like compatibility testing, this is beneficial for you to find new problems that may be introduced by new submission as soon as possible.

---

##### D.d Waiting for Review & Active Collaboration

> [!CAUTION]    
> Kindly note that your pull request (PR) may be manually closed under these circumstances:  
> 1. **Incorrect target branch**: Ensure the `base` branch is set to `master`  
> 2. **Duplicate contributions**: Existing PRs already address the same changes  
> 3. **CI failures with prolonged inactivity**: PRs failing CI checks without updates for 30+ days  
> 4. **Outdated scope**: When the code area involved in the PR has been refactored or cancelled

1. After passing compatibility tests, your PR enters formal [review](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/reviewing-proposed-changes-in-a-pull-request#about-reviewing-pull-requests). Typical first review occurs within **5-7 business days** (may vary with maintainer availability).

2. During the review process, reviewers may leave comments. If any questions arise, please respond patiently and courteously to clarify your implementation rationale:
    - Kindly respond to review comments as soon as possible  
    - Use [`Resolve conversation` button](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/commenting-on-a-pull-request#resolving-conversations) when fixes are applied  
    - For unclear requests, ask clarifying questions like: `"Could you please elaborate on [...]?"` 

3. Provided everything checks out, maintainers will: 
    - Manually trigger compatibility tests to verify code standards, correctness, robustness, and cross-environment compatibility
    - Manually execute the `🤖 Update README Badge 🔰` workflow (as mentioned in [D.b.6](#db-create-a-pull-request-to-torchmeter)) to update the coverage badge in `README.md`

4. If everything goes well，your PR will be merged into the `master` branch in `Squash` or `Merge` way. Your contribution will be officially released and acknowledged in the **next version** announcement.

---

##### D.e Celebrate Your Successful Contribution 🎉

1. Once your PR is merged, you'll receive a notification email from GitHub with a message similar to: `Merged #<PR-number> into master.`

2. Congratulations! Your contribution is now part of `torchmeter`. We'll announce your changes in our **next official release** and express our gratitude again on the [release page](https://github.com/TorchMeter/torchmeter/releases).

3. This marks the completion of your contribution journey! Take a well-deserved break, share the achievement with your peers, or celebrate in any way that brings you joy. We sincerely appreciate your time and effort!  

> [!NOTE]  
> The merged changes will be visible on the `master` branch. To update locally:  
> 
> ```bash
> # pwd: path/to/your/working/directory/torchmeter-yourname
> 
> git checkout master
> git pull
> ```
> 
> This ensures your local environment reflects the latest project state including your contribution.

## 🤝 Acknowledgement 

We extend our heartfelt gratitude to every contributor who has helped shape `torchmeter` into a better tool!

Your efforts, whether through code contributions, bug reports, or thoughtful discussions, are the lifeblood of this open-source project.

Thank you very much for your time and effort!