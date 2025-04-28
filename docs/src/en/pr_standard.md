Hi, contributors,

We highly appreciate your patience in following these guidelines to help us keep `torchmeter` organized and maintainable.

Thank you! 🌟

## Branch Name

### **Why This Matters**

Consistent naming rule helps us:  
- 🧐 Quickly evaluate contributions  
- 💪 Maintain codebase health  
- 🤝 Improve collaborative efficiency  

---

### **Structure**

```
[category]/[optional-issue-number]-[short-description]
```

> [!TIP] 
> 𝑲𝒆𝒚 𝑷𝒓𝒊𝒏𝒄𝒊𝒑𝒍𝒆𝒔
> 1. **Descriptive & Concise**: Balance clarity with brevity for quick scanning
> 2. **Semantic Structure**: Use meaningful prefixes and descriptive suffixes
> 3. **Traceability**: Link branches to specific development contexts

#### ① **Category Prefixes**

| Purpose                | Prefix       | When to Use                  | Example                     |
|:----------------------:|:------------:|:----------------------------:|:---------------------------:|
| New functionality      | `feat`       | Adding new capabilities      | `feature/#86-optimize-cache`|
| Bug corrections        | `bugfix`     | Fixing unexpected behavior   | `bugfix/div-zero-error`     |
| Documentation updates  | `docs`       | Improving guides/comments    | `docs/add-install-notes`    |
| Testing improvements   | `test`       | Enhancing test coverage      | `test/add-edge-cases`       |
| Code restructuring     | `refactor`   | Improving code structure     | `refactor/metrics-handler`  |
| Critical fixes         | `hotfix`     | Urgent production fixes      | `hotfix/memory-leak-patch`  |
| Project maintenance    | `chore`      | Updating dependencies/builds | `chore/update-requirements` |

---

### **Best Practices**

#### ① **Reference issues (when applicable)**:
   
```
bugfix/#123-fix-tensor-shape
```

#### ② **Keep it concise (3-5 key words)**:
   
```bash
# 👍 Clear and scoped
feat/nocall-modules-handling

# 👎 Too vague
feat/new-stuff
```

#### ③ **Use lowercase with hyphens**
   
```bash
# 👍 Consistent formatting
docs/update-contrib-guide

# 👎 Mixed formatting
Docs/Update_contrib_guide
```

#### ④ **Avoid unclear abbreviations**

```bash
# 👍 Full description
bugfix/fix-memory-leak

# 👎 Use abbreviations without prior agreement
bugfix/fx-mem
```

#### ⑤ **Avoid version numbers**

```bash
# 👍 Feature description
feat/new-tree-renderer

# 👎 Include version numbers
feat/v2.1.0
```

---

## Commit Message

### **Why It Matters**

Clear commit message helps us:
- 🔍 Track down specific changes
- 📖 Understand change context quickly
- 🤝 Improve collaborative efficiency

---

### **Structure**

```
<type>[optional scope]: <subject>

[optional body]

[optional footer]
```

#### ① **Type Prefixes**

|   Prefix   |          Change Type           |                         Example                          |
|:----------:|:------------------------------:|:--------------------------------------------------------:|
|   `feat`   |          New feature           |  `feat(render): implement custom display of statistic`   |
|   `fix`    |            Bug fix             | `fix(memory): resolve CUDA memory leak in measuring mem` |
|   `doc`    |         Documentation          |               `doc: update API reference`                |
|   `test`   |          Test-related          |         `test(metrics): add edge cases for xxx`          |
|    `ci`    |        Workflow-related        |   `ci(badge-update): revise the content to be updated`   |
| `refactor` |        Code refactoring        |         `refactor: simplify module registration`         |
|   `perf`   |          Performance           |             `perf: optimize tree rendering`              |
|  `chore`   |        Repo maintemance        |              `chore: update issue template`              |
|  `build`   | Distribution packages building |    `build: update package introduction in setup.cfg`     |

#### ② **Scope**

> A scope is to identify the specific area of the codebase being modified

|      Scope Name      |            Notes             |                       Example                        |
|:--------------------:|:----------------------------:|:----------------------------------------------------:|
|       `infra`        |   For DevOps/Infra changes   |           `chore(infra): update CI config`           |
|   `[module-name]`    | Match directory/module names |   `fix(core): add input validation for profile()`    |
|   `[feature-area]`   |          See below           |       `perf(render): speed up tree rendering`        |
| `[document-section]` |     Specific doc section     |  `doc(install): add method to install from source`  |
| `[workflow-funtion]` |          See below           | `ci(badge-update): revise the content to be updated` | 
| `unit` / `integrate` |        Test category         |             `test(unit): add edge cases`             |

<details>
<summary>Feature-area</summary>

| Feature-area |                                      Notes                                       |
|:------------:|:--------------------------------------------------------------------------------:|
|   `render`   |                 Changes related to rendering and terminal output                 |
|  `measure`   |                 Changes related to the measurement of statistics                 |
|   `config`   |                     Changes related to global configuration                      |
| `model-scan` |                  Changes related to model structure exploration                  |
|    `api`     | Changes related to code logic, interface changes, performance improvements, etc. |

</details>

<details>
<summary>workflow-funtion</summary>

|   workflow-funtion   |                                           Notes                                            |
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

</details>

#### ③ **Subject Line**

- Keep under **72** characters
- Use imperative mood: "Add" not "Added" or "Adds"

```bash
# 👍 Good
feat: implement metric registry

# 👎 Avoid
Implemented metric registry
```

#### ④ **Body (when needed)**

- Wrap text at **80** characters
- Reference issues using `Closes #123` or `Refs: #123`
- Explain **what** and **why** rather than **how**
- Use ordered or unordered lists in `markdown` syntax to organize content

#### ⑤ **Footer**

- Link pull requests: `Refs: #45`
- For breaking changes: `BREAKING CHANGE: <description>`

---

### **Best Practices**

#### ① **Feature Implementation**

```bash
# 👍 Clear scope and imperative mood
feat(metrics): add precision-recall curve support

- Implement curve plotting for binary classification tasks
- Integrate with existing visualization toolkit
Closes #88

# ----------------------------------------------------------

# 👎 Vague description
Added some metrics stuff
```

#### ② **Documentation Update**

```bash
# 👍 Specific document section reference
doc(tutorial): add distributed training example

- Demonstrate multi-GPU usage with DDP
- Add benchmark results table
Refs: #102

# ----------------------------------------------------------

# 👎 Vague description
doc: update docs
```

#### ③ **Test Enhancement**

```bash
# 👍 Clear test category and edge case
test(integrate): add fp16 precision validation

- Verify tensor dtype conversion in mixed precision mode
- Add tolerance thresholds for different hardware

# ----------------------------------------------------------

# 👎 Unclear test scope
test: fix some tests
```

#### ④ **Code Refactoring**

```bash
# 👍 Modular improvement explanation
refactor(core): decouple metric calculation from IO

- Separate computation logic from result saving
- Create new ResultHandler class
- BREAKING CHANGE: Remove save_to_csv() method

# ----------------------------------------------------------

# 👎 No scope/benefit explanation
refactor: change some code
```

#### ⑤ **Performance Optimization**
```bash
# 👍 Quantifiable improvement
perf(render): reduce tree visualization latency by 40%

- Implement lazy loading for large model structures
- Add caching mechanism for common architectures

# ----------------------------------------------------------

# 👎 Generic claim
perf: make it faster
```

#### ⑥ **Maintenance Task**
```bash
# 👍 Clear infra context
chore(infra): migrate CI from Travis to GitHub Actions

- Add workflow for automated PyTorch version matrix testing
- Remove .travis.yml configuration

# ----------------------------------------------------------

# 👎 Ambiguous maintenance
chore: update files
```

---

## Pull Request Title

### **Why It Matters**

- 🏷️ Facilitates PR categorization and management.
- ✅ Required for merging – Valid titles are enforced by automated checks in our workflow.
- 🤖 Enables automated changelog generation for releases – `torchmeter` use [release-drafter](https://github.com/release-drafter/release-drafter) to generate release notes  based on PR labels.

---

### **Structure**

```
<type>[optional scope][optional !]: <subject>
```

#### ① **Type Prefixes**

> Most are the same as [Commit Message Type Prefixes](#type-prefixes), cause the PR will finally be merged as a commit.

> [!CAUTION]  
> Type prefix must be one in the following table, otherwise the PR will be rejected!

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

#### ② **Scope** (Optional)

Totally same as [Commit Message Scope](#scope).

Note that if you don't plan to add a scope, please don't leave parentheses in the PR title.

```bash
# 👍 Good
fix(core): Memory leak

# 👎 Avoid
fix(): Memory leak
```

Additionally, the scope must **not** be empty or start with a space.

```bash
# 👍 Good
fix(core): Memory leak

# 👎 Avoid
fix( ): Memory leak
fix( core): memory leak
```

#### ③ **Exclamation Mark** (`!`, Optional)

A `!` indicates a breaking change, which means that the PR will bring a major version bump.

#### ④ **Subject** 

> Mostly same as [Commit Message Subject](#subject-line)

- Keep under 72 characters
- Use imperative mood: `Add` not `Added`
- Capitalize the initial letter.
- Avoid ending with punctuation
- Not to reference issues/PR/discussion at beginning

    ```
    # 👍 Good
    fix: memory leak described in #456

    # 👎 Avoid
    fix: #456 memory leak
    ```

---

### **Best Practices**

> [!TIP]  
> You can validate your PR title with: `bash misc/validate_pr_title.sh <your-PR-title>`

#### ① **Valid type usage**

```bash
# 👍 Proper type
feat: Add histogram visualization

# 👎 Invalid type
feats: Add histogram visualization
```

#### ② **Valid Scope Usage**

```bash
# 👍 Proper scoping
feat(metrics): Add histogram visualization

# 👎 Empty parentheses
feat(): Add new feature

# 👎 Space in scrpe beginning
feat( ): Add new feature
feat( core): Add new feature
```

#### ③ **Space before Subject**

```bash
# 👍 Only one space before subject line
refactor: Remove deprecated methods

# 👎 no/more than one space
refactor:Remove deprecated methods
refactor:  Remove deprecated methods
```

#### ④ **Capitalize the Beginning of Subject**

```bash
# 👍 Capitalized.
refactor: Remove deprecated methods

# 👎 Not been capitalized
refactor: remove deprecated methods
```

#### ⑤ **Imperative Mood**

```bash
# 👍 Correct imperative form
fix(core): Resolve memory leak

# 👎 Past tense usage
fix(core): Memory leak resolved
```

#### ⑥ **Reference Placement**

```
# 👍 Proper reference position
doc: Update installation guide (closes #123)

# 👎 Error position
doc(#123): Update installation guide
doc: #123 Update installation guide
```

#### ⑦ **Length Control**

```bash
# 👍 Concise title (68 chars)
perf(render): Optimize tree rendering latency using lazy-load

# 👎 Overly long title (89 chars)
perf(render): Implement multiple optimization techniques including lazy-load and caching for tree rendering
```

#### ⑧ **Punctuation Rules**

```bash
# 👍 Clean ending
chore(ci): Migrate to GitHub Actions

# 👎 Trailing punctuation
chore(ci): Update CI configuration.
```