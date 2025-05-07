---
title: "Conventions"
---

# Conventions — Let's Make it Easy and Standardize

!!! info ""

    Hi, contributors:

    We highly appreciate your patience in following these guidelines to help us keep `torchmeter` organized and maintainable.

    **Thank you !** 🌟

## **:material-numeric-1-circle-outline: Branch Name**

### **Why this matters?**

Consistent naming rule helps us:  

- 🧐 Quickly evaluate contributions  
- 💪 Maintain codebase health  
- 🤝 Improve collaborative efficiency  

---

### **Structure**

```title="" linenums="0"
[category]/[optional-issue-number]-[short-description]
```

??? tip "Key Principles"

    1. **Descriptive & Concise**: Balance clarity with brevity for quick scanning
    2. **Semantic Structure**: Use meaningful prefixes and descriptive suffixes
    3. **Traceability**: Link branches to specific development contexts

??? abstract "Category Prefixes"

    | Prefix       | Purpose                | When to Use                  | Example                     |
    |:------------:|:----------------------:|:----------------------------:|:---------------------------:|
    | `feat`       | New functionality      | Adding new capabilities      | `feature/#86-optimize-cache`|
    | `bugfix`     | Bug corrections        | Fixing unexpected behavior   | `bugfix/div-zero-error`     |
    | `docs`       | Documentation updates  | Improving guides/comments    | `docs/add-install-notes`    |
    | `test`       | Testing improvements   | Enhancing test coverage      | `test/add-edge-cases`       |
    | `refactor`   | Code restructuring     | Improving code structure     | `refactor/metrics-handler`  |
    | `hotfix`     | Critical fixes         | Urgent production fixes      | `hotfix/memory-leak-patch`  |
    | `chore`      | Project maintenance    | Updating dependencies/builds | `chore/update-requirements` |

---

### **Best Practices**

??? success ":material-numeric-1-box-multiple-outline: Reference issues (when applicable)"

    ```title="" linenums="0"
    bugfix/#123-fix-tensor-shape
    ```

??? success ":material-numeric-2-box-multiple-outline: Keep it concise (3-5 key words)"
   
    ```bash title="" linenums="0"
    # 👍 Clear and scoped
    feat/nocall-modules-handling

    # 👎 Too vague
    feat/new-stuff
    ```

??? success ":material-numeric-3-box-multiple-outline: Use lowercase with hyphens"
   
    ```bash title="" linenums="0"
    # 👍 Consistent formatting
    docs/update-contrib-guide

    # 👎 Mixed formatting
    Docs/Update_contrib_guide
    ```

??? success ":material-numeric-4-box-multiple-outline: Avoid unclear abbreviations"

    ```bash title="" linenums="0"
    # 👍 Full description
    bugfix/fix-memory-leak

    # 👎 Use abbreviations without prior agreement
    bugfix/fx-mem
    ```

??? success ":material-numeric-5-box-multiple-outline: Avoid version numbers"

    ```bash title="" linenums="0"
    # 👍 Feature description
    feat/new-tree-renderer

    # 👎 Include version numbers
    feat/v2.1.0
    ```

---

## **:material-numeric-2-circle-outline: Commit Message**

### **Why this matters?**

Clear commit message helps us:

- 🔍 Track down specific changes
- 📖 Understand change context quickly
- 🤝 Improve collaborative efficiency

---

### **Structure**

```title="" linenums="0"
<type>[optional scope]: <subject>

[optional body]

[optional footer]
```

??? abstract "Type Prefixes"

    |   Prefix   |          Change Type           |                         Example                          |
    |:----------:|:------------------------------:|:--------------------------------------------------------:|
    |   `feat`   |          New feature           |  `feat(render): implement custom display of statistic`   |
    |   `fix`    |            Bug fix             | `fix(memory): resolve CUDA memory leak in measuring mem` |
    |   `docs`   |         Documentation          |               `docs: update API reference`               |
    |   `test`   |          Test-related          |         `test(metrics): add edge cases for xxx`          |
    |    `ci`    |        Workflow-related        |   `ci(badge-update): revise the content to be updated`   |
    | `refactor` |        Code refactoring        |         `refactor: simplify module registration`         |
    |   `perf`   |          Performance           |             `perf: optimize tree rendering`              |
    |  `chore`   |        Repo maintemance        |              `chore: update issue template`              |
    |  `build`   | Distribution packages building |    `build: update package introduction in setup.cfg`     |

??? abstract "Scope"

    > A scope is to identify the specific area of the codebase being modified

    |      Scope Name      |            Notes             |                       Example                        |
    |:--------------------:|:----------------------------:|:----------------------------------------------------:|
    |       `infra`        |   For DevOps/Infra changes   |           `chore(infra): update CI config`           |
    |   `[module-name]`    | Match directory/module names |   `fix(core): add input validation for profile()`    |
    |   `[feature-area]`   |          See below           |       `perf(render): speed up tree rendering`        |
    | `[document-section]` |     Specific doc section     |  `docs(install): add method to install from source`  |
    | `[workflow-funtion]` |          See below           | `ci(badge-update): revise the content to be updated` | 
    | `unit` / `integrate` |        Test category         |             `test(unit): add edge cases`             |

    ??? note "Feature-Area"

        | Feature-Area |                                      Notes                                       |
        |:------------:|:--------------------------------------------------------------------------------:|
        |   `render`   |                 Changes related to rendering and terminal output                 |
        |  `measure`   |                 Changes related to the measurement of statistics                 |
        |   `config`   |                     Changes related to global configuration                      |
        | `model-scan` |                  Changes related to model structure exploration                  |
        |    `api`     | Changes related to code logic, interface changes, performance improvements, etc. |

    ??? note "Workflow-Funtion"

        |   Workflow-Funtion   |                                           Notes                                            |
        |:--------------------:|:------------------------------------------------------------------------------------------:|
        |   `PR-title-lint`    |              corresponding step: `pr_autolabel.yml::labeler::Check PR Title`               |
        |   `PR-auto-label`    |                 corresponding step: `pr_autolabel.yml::labeler::Label PR`                  |
        |    `badge-update`    |                   corresponding job: `badge_updater.yml::Coverage-Badge`                   |
        |    `lint-format`     |                        corresponding job: `*_test.yml::Lint-Format`                        |
        | `compatibility-test` |              corresponding job: `compatibility_test.yml::Compatibility-Test`               |
        |     `mini-test`      |                    corresponding job: `minimal_test.yml::Minimal-Test`                     |
        |       `build`        |           corresponding job: `publish_release.yml::Build-Distribution-Packages`            |
        |      `publish`       |                corresponding job: `publish_release.yml::Publish-(Test)PyPI`                |
        |   `draft-release`    |                 corresponding job: `publish_release.yml::Publish-Release`                  |
        |    `email-notify`    | corresponding step: `publish_release.yml::Publish-Release/Cleanup-Tag::Email Notification` |

??? abstract "Subject Line"

    - Keep under **72** characters
    - Use imperative mood: "Add" not "Added" or "Adds"

    ```bash title="" linenums="0"
    # 👍 Good
    feat: implement metric registry

    # 👎 Avoid
    Implemented metric registry
    ```

??? abstract "Body (when needed)"

    - Wrap text at **80** characters
    - Reference issues using `closes #123` or `refs: #123`
    - Explain **what** and **why** rather than **how**
    - Use ordered or unordered lists in `markdown` syntax to organize content

??? abstract "Footer (when needed)"

    - Link pull requests: `refs: #45`
    - For breaking changes: `BREAKING CHANGE: <description>`

---

### **Best Practices**

??? success ":material-numeric-1-box-multiple-outline: Feature Implementation"

    ```bash title="" linenums="0"
    # 👍 Clear scope and imperative mood
    feat(metrics): add precision-recall curve support

    - Implement curve plotting for binary classification tasks
    - Integrate with existing visualization toolkit
    closes #88

    # ----------------------------------------------------------

    # 👎 Vague description
    Added some metrics stuff
    ```

??? success ":material-numeric-2-box-multiple-outline: Documentation Update"

    ```bash title="" linenums="0"
    # 👍 Specific document section reference
    docs(tutorial): add distributed training example

    - Demonstrate multi-GPU usage with DDP
    - Add benchmark results table
    refs: #102

    # ----------------------------------------------------------

    # 👎 Vague description
    docs: update docs
    ```

??? success ":material-numeric-3-box-multiple-outline: Test Enhancement"

    ```bash title="" linenums="0"
    # 👍 Clear test category and edge case
    test(integrate): add fp16 precision validation

    - Verify tensor dtype conversion in mixed precision mode
    - Add tolerance thresholds for different hardware

    # ----------------------------------------------------------

    # 👎 Unclear test scope
    test: fix some tests
    ```

??? success ":material-numeric-4-box-multiple-outline: Code Refactoring"

    ```bash title="" linenums="0"
    # 👍 Modular improvement explanation
    refactor(core): decouple metric calculation from IO

    - Separate computation logic from result saving
    - Create new ResultHandler class
    - BREAKING CHANGE: Remove save_to_csv() method

    # ----------------------------------------------------------

    # 👎 No scope/benefit explanation
    refactor: change some code
    ```

??? success ":material-numeric-5-box-multiple-outline: Performance Optimization"

    ```bash title="" linenums="0"
    # 👍 Quantifiable improvement
    perf(render): reduce tree visualization latency by 40%

    - Implement lazy loading for large model structures
    - Add caching mechanism for common architectures

    # ----------------------------------------------------------

    # 👎 Generic claim
    perf: make it faster
    ```

??? success ":material-numeric-6-box-multiple-outline: Maintenance Task"

    ```bash title="" linenums="0"
    # 👍 Clear infra context
    chore(infra): migrate CI from Travis to GitHub Actions

    - Add workflow for automated PyTorch version matrix testing
    - Remove .travis.yml configuration

    # ----------------------------------------------------------

    # 👎 Ambiguous maintenance
    chore: update files
    ```

---

## **:material-numeric-3-circle-outline: Pull Request Title**

### **Why this matters?**

- 🏷️ Facilitates PR categorization and management.
- ✅ Required for merging – Valid titles are enforced by automated checks in our [workflow :material-link-variant:](https://github.com/TorchMeter/torchmeter/blob/master/.github/workflows/pr_autolabel.yml).
- 🤖 Enables automated changelog generation for releases – `torchmeter` use [release-drafter :material-link-variant:](https://github.com/release-drafter/release-drafter) to generate release notes based on PR labels.

---

### **Structure**

```title="" linenums="0"
<type>[optional scope][optional !]: <subject>
```

??? abstract "Type Prefixes"

    > Most are the same as [Commit Message Type Prefixes :material-link-variant:](#Structure_1){ data-preview }, cause the PR will finally be merged as a commit.

    !!! danger "Limitations"
        
        Type prefix **must be one** in the following table, otherwise the PR will be rejected!

        |  PR Type   |         When to Use         |          Example           |
        |:----------:|:---------------------------:|:--------------------------:|
        |   `feat`   |        New features         |  `feat: add FP16 support`  |
        |   `fix`    |          Bug fixes          |  `fix(core): memory leak`  |
        |   `perf`   |  Performance improvements   | `perf: optimize rendering` |
        |   `depr`   |        Deprecations         |   `depr: remove old API`   |
        |   `docs`   |    Documentation updates    |  `docs: add API examples`  |
        |   `test`   |    Test-related changes     |   `test: add edge cases`   |
        |    `ci`    |     CI/CD improvements      |   `ci: add GPU testing`    |
        |  `build`   | Changes related to building | `build: update setup.cfg`  |
        | `refactor` |     Code restructuring      |  `refactor: clean utils`   |
        |  `revert`  |      Reverted changes       |   `revert: #123 change`    |
        |  `chore`   |      Maintenance tasks      |    `chore: update deps`    |

??? abstract "Scope (Optional)"

    Totally same as [Commit Message Scope :material-link-variant:](#Structure_1){ data-preview }.

    !!! danger ""

        - If you don't plan to add a scope, please **don't** leave parentheses in the PR title.
        - Scope must **not** be empty or start with a space.

    ```bash title="" linenums="0"
    # 👍 Good
    fix(core): Memory leak

    # 👎 Avoid
    fix(): Memory leak
    ```

    ```bash title="" linenums="0"
    # 👍 Good
    fix(core): Memory leak

    # 👎 Avoid
    fix( ): Memory leak
    fix( core): memory leak
    ```

??? warning "Exclamation Mark (`!`, Optional)"

    A `!` indicates a breaking change, which means that the PR will {++bring a major version bump++}. Therefore, please use it with caution. The PRs denoted by `!` will undergo a more rigorous review procedure.

??? abstract "Subject"

    > Mostly same as [Commit Message Subject :material-link-variant:](#Structure_1){ data-preview }

    - Keep under **72** characters
    - Use imperative mood: `Add` not `Added`
    - Capitalize the initial letter.
    - Avoid ending with punctuation
    - Not to reference issues/PR/discussion ^^at beginning^^

    ```title="" linenums="0"
    # 👍 Good
    fix: memory leak described in #456

    # 👎 Avoid
    fix: #456 memory leak
    ```

---

### **Best Practices**

!!! tip "Quick Validation"

    You can validate your PR title with: `bash misc/validate_pr_title.sh '<your-PR-title>'`

??? success ":material-numeric-1-box-multiple-outline: Valid type usage"

    ```bash title="" linenums="0"
    # 👍 Proper type
    feat: Add histogram visualization

    # 👎 Invalid type
    feats: Add histogram visualization
    ```

??? success ":material-numeric-2-box-multiple-outline: Valid Scope Usage"

    ```bash title="" linenums="0"
    # 👍 Proper scoping
    feat(metrics): Add histogram visualization

    # 👎 Empty parentheses
    feat(): Add new feature

    # 👎 Space in scrpe beginning
    feat( ): Add new feature
    feat( core): Add new feature
    ```

??? success ":material-numeric-3-box-multiple-outline: Space before Subject"

    ```bash title="" linenums="0"
    # 👍 Only one space before subject line
    refactor: Remove deprecated methods

    # 👎 no/more than one space
    refactor:Remove deprecated methods
    refactor:  Remove deprecated methods
    ```

??? success ":material-numeric-4-box-multiple-outline: Capitalize the Beginning of Subject"

    ```bash title="" linenums="0"
    # 👍 Capitalized.
    refactor: Remove deprecated methods

    # 👎 Not been capitalized
    refactor: remove deprecated methods
    ```

??? success ":material-numeric-5-box-multiple-outline: Imperative Mood"

    ```bash title="" linenums="0"
    # 👍 Correct imperative form
    fix(core): Resolve memory leak

    # 👎 Past tense usage
    fix(core): Memory leak resolved
    ```

??? success ":material-numeric-6-box-multiple-outline: Reference Placement"

    ``` title="" linenums="0"
    # 👍 Proper reference position
    docs: Update installation guide (closes #123)

    # 👎 Error position
    docs(#123): Update installation guide
    docs: #123 Update installation guide
    ```

??? success ":material-numeric-7-box-multiple-outline: Length Control"

    ```bash title="" linenums="0"
    # 👍 Concise title (68 chars)
    perf(render): Optimize tree rendering latency using lazy-load

    # 👎 Overly long title (89 chars)
    perf(render): Implement multiple optimization techniques including lazy-load and caching for tree rendering
    ```

??? success ":material-numeric-8-box-multiple-outline: Punctuation Rules"

    ```bash title="" linenums="0"
    # 👍 Clean ending
    chore(ci): Migrate to GitHub Actions

    # 👎 Trailing punctuation
    chore(ci): Update CI configuration.
    ```