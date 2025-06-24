
!!! tip ""

    This page outlines the `torchmeter` project's governance framework to transparently communicate our workflow for ^^managing branches^^, ^^handling issues^^, and ^^processing contributions^^. It ensures contributors clearly understand how their efforts are reviewed and integrated into the project's development lifecycle.

## **:material-numeric-1-circle-outline: Branching Strategy**

<figure markdown="span">
    ![branching-strategy](../assets/others/branch_strategy.svg){ .off-glb }
</figure>

To streamline collaboration and enable rapid iteration, `torchmeter` employs a simplified branching strategy inspired by `Git Flow` and practices from mature OSS projects. Our workflow(visualized above) balances stability with agility through two core branch types, i.e. the `master` branch and the version branches(`vA.B.x`).

### **:material-numeric-1-box-multiple-outline: Branch Architecture**

??? abstract "Overview"

    | Branch Name |    Name  |  Purpose  |  Maintainer  |  Contributor Permissions   |
    |:-----------:|:-------------:|:------------:|:-----------------:|:--    -------:|
    |   `master`  | Primary Development Branch | Receives latest stable code, accepts new features, optimizations, and general bug fixes | All (with review) |      **Allowed** to submit PRs       |
    |  `vA.B.x`   | Version Maintenance Branch |             **Only accepts** bug fixes for a minor version, **no new features**               |     Core Team     | **Forbidden** to submit PRs directly |

#### **:material-numeric-1-box: Master Branch**

- **Name**: `master`
- **Purpose**: Always represents the latest stable state, incorporating validated features and fixes.
- **Lifecycle**: Permanent
- **Branch Protection Rules**:
    1. :material-lock: Branch deletion forbidden
    2. :fontawesome-solid-ban: Direct commits prohibited. All changes must be proposed via Pull Requests (PRs) and approved through code review.
    3. :octicons-git-merge-16: PR Requirements before Merging:
        - All comments must be resolved.
        - Pass PR title checks and code compatibility tests.
        - At least one approval from reviewers required.
   
#### **:material-numeric-2-box: Version Branches**

- **Name**: `v` + [semantic version :material-link-variant:](https://semver.org/) (e.g., `v1.2.x`[^1]). 
- **Purpose**: Exclusive bugfix channel for specific releases
- **Lifecycle**:
    1. Created when incrementing major/minor versions
    2. Archived when superseded by newer version branch (e.g., a new branch named `v1.3.x` will supersede `v1.2.x`).
- **Branch Protection Rules**: Inherits `master` branch's rules

[^1]: It should be noted that the `PATCH` number is represented by the letter `x`, which refers to a series of revisions to be updated in the future.

---

### **:material-numeric-2-box-multiple-outline: Development Pipeline**

#### **:material-numeric-1-box: For Contributors**  

When proposing new features or fixes, please follow our [Contribution Guide :material-link-variant:](../contribute/welcome_contributors.md){ data-preview }.

#### **:material-numeric-2-box: For Maintainers**

??? tip "Merging PRs to Master"

    1. **Promptly review contributions**

        Promise the PR has a valid title and pass the compatiability tests.

    2. **Manually trigger ✅ Compatibility Test ❌** {==[Optional, do only when essential files changed]==}
    
        If the changes brought by the PR are related to the following aspects, manually trigger `compatibility_test.yml` workflow, and {++make sure the compatibility test passes++}:

        - source code (`torchmeter/`)
        - test code (`tests/`)
        - configuration files(`requirements.txt`, `default_cfg.yml`, `pyproject.toml`, `setup.cfg`, `setup.py`)

    3. **Update coverage badge in `README.md` before merging**:
        - Right-click coverage badge in PR's comment → Copy link  
        - Manually trigger `badge_updater.yml` workflow

    4. **Sync local after merging**: `git checkout master && git pull`

??? tip "Fixing Issues in Current Version"

    1. **Fetch latest changes**
        
        ```bash linenums="0"
        git checkout master
        git pull

        git checkout <latest-version-branch>
        git pull
        ```

    2. **Copy the change**

        ```bash linenums="0"
        # working branch: <latest-version-branch>
        git checkout -b bugfix/<PR-number>-<short-description>
        git cherry-pick <hash-of-commit-on-master> # (1)
        ```

        1. 🙋‍♂️ Usually should resolve merge conflicts according to [steps :material-link-variant:](../contribute/prs.md#Da-Avoiding-Protential-Merge-Conflicts){ data-preview }.

    3. **Test locally**

        ```bash linenums="0"
        bash misc/lint_format.sh
        pytest -q
        ```

    4. **Push to remote**
   
        ```bash linenums="0"
        git push origin bugfix/<PR-number>-<short-description> # (1)
        ```

        1. 🙋‍♂️ If it the work can't be finished at the moment, consider to enable the `-u` flag to track the upstream branch.

    5. **Merge to codebase**
        
        Create a PR to the latest version branch, merge and then delete the `bugfix/<PR-number>-<short-description>` branch.

    6. **Release a Patch Version**

        See below.

??? tip "Releasing a Major/Minor Version"

    1. **Fetch latest changes**
        
        ```bash linenums="0"
        git checkout master
        git pull
        ```

    2. **Create new version branch**

        ```bash linenums="0"
        git checkout -b <version-branch>
        git push origin <version-branch>
        ```
    
    3. **Push version tag to version branch**

        ```bash linenums="0"
        git tag <version>
        git push origin <version>
        ```

    4. **Publish github release**
   
        Last step will trigger the publication workflow, if it succeeds, go to Github Repo → Releases → review and publish the draft release created by `release-drafter`.

??? tip "Releasing a Patch Version"

    1. **Fetch latest changes**
        
        ```bash linenums="0"
        git checkout master
        git pull

        git checkout <latest-version-branch>
        git pull
        ```

    2. **Push version tag to version branch**

        ```bash linenums="0"
        git tag <version>
        git push origin <version>
        ```

    3. **Publish github release**
   
        Last step will trigger the publication workflow, if it succeeds, go to Github Repo → Releases → review and publish the draft release created by `release-drafter`.

---

## **:material-numeric-2-circle-outline: Issue Management**

### **:material-numeric-1-box-multiple-outline: Issue Labels**

> Labels help categorize and prioritize issues.

1. **Default Labels**

    - Issues created from templates are automatically labeled:  
        1. `Bug Report` → `bug`  
        2. `Feature Request` → `feat`  

    - Blank issues (created without templates) have no default labels.

2. **Add Labels** 

    - Click the `Label` section in the right sidebar of the issue page.
    - View all labels `torchmeter` provided at our [Label page :material-link-variant:](https://github.com/TorchMeter/torchmeter/labels).

---

### **:material-numeric-2-box-multiple-outline: Issue Ownership & Assignment**

> Assigning an issue indicates ownership responsibility for **tracking** and **resolving** it.

**Voluntary Claim**

:   Assignees should **self-claim** issues voluntarily. Avoid assigning to others without their consent.  

**PR-Based Assignment**

:   When someone creating a PR to address an issue, the maintainer might assign the issue to himself/herself and the contributor driving the resolution.

**Accountability**

:   - Assignees are responsible for issue lifecycle management.  
    - The steps to resolve an issue through a PR are detailed in the [Pull Request Guide :material-link-variant:](../contribute/prs.md){ data-preview }.