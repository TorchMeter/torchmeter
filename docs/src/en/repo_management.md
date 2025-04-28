
This document outlines the `torchmeter` project's governance framework to transparently communicate our workflow for managing branches, handling issues, and processing contributions. It ensures contributors clearly understand how their efforts are reviewed and integrated into the project's development lifecycle.

## Branching Strategy

![branching-strategy](../assets/branch_strategy.gif)

To streamline collaboration and enable rapid iteration, `torchmeter` employs a simplified branching strategy inspired by `Git Flow` and practices from mature OSS projects. Our workflow(visualized above) balances stability with agility through two core branch types, i.e. the main branch(`master`) and the version branches(`vA.B.x`).

### ① 🗼 **Branch Architecture**

> [!TIP]  
> | Branch Name |            Name             |                          Purpose                          | Maintainer | Contributor Permissions |
> |:-----------:|:---------------------------:|:--------------------------------------------------------:|:----------:|:-----------------------:|
> | `main`      | Primary Development Branch  | Receives latest stable code, accepts new features, optimizations, and general bug fixes | All (with review) | **Allowed to submit PRs** |
> | `vA.B.x`    | Version Maintenance Branch  | **Only accepts** bug fixes for this version, **no new features** | Core Team  | **Forbidden to submit PRs directly** |

1. **Main Branch**
    - **Name**: `master`
    - **Purpose**: Always represents the latest stable state, incorporating validated features and fixes.
    - **Lifecycle**: Permanent
    - **Branch Protection Rules**:
        1. 🔒 Branch deletion forbidden
        2. ☝️ Direct commits prohibited. All changes must be proposed via Pull Requests (PRs) and approved through code review.
        3. PR Requirements before Merging:
            1. All comments must be resolved.
            2. Pass PR title checks and code compatibility tests.
            3. At least one approval from reviewers required.
   
2. **Version Branches**
    - **Name**: `v` + [semantic version](https://semver.org/) (e.g., `v1.2.x`[^1]). 
    - **Purpose**: Exclusive bugfix channel for specific releases
    - **Lifecycle**:
        - Created when incrementing major/minor versions
        - Archived when superseded by newer version branch (e.g., `v1.3.x`).
    - **Branch Protection Rules**: Inherits main branch protections

[^1]: It should be noted that the `PATCH` number is represented by the letter "x", which refers to a series of revisions to be updated in the future.

---

### ② 👩‍💻 Development Pipeline

#### A. **For Contributors**  

When proposing new features or fixes, please follow our [Contribution Guide](../CONTRIBUTING.md#-pull-requests--lets-squash-bugs--build-features).

#### B. **For Maintainers**

- **Merging PRs to Master**
    1. **Promptly review contributions**  
    2. **Update coverage badge in `README.md` before merging**:
        - Right-click coverage badge in PR's comment → Copy link  
        - Manually trigger `badge_updater.yml` workflow
    3. **Sync local after merging**: `git checkout master && git pull`

- **Creating a Version Branch** (when incrementing major/minor version)
    1. **Fetch latest changes**
        
        ```bash
        git checkout master
        git pull
        ```
   2. **Create new version branch**

        ```bash
        git checkout -b <version-branch>
        git push origin <version-branch>
        ```

- **Fixing Issues in Current Version**
    1. **Fetch latest changes**
        
        ```bash
        git checkout master
        git pull

        git checkout <latest-version-branch>
        git pull
        ```

    2. **Copy the change**

        ```bash
        # working branch: <latest-version-branch>
        git checkout -b bugfix/<PR-number>-<short-description>
        git cherry-pick <hash-of-commit-on-master>
        ```

    3. **Test locally**

        ```bash
        bash misc/lint_format.sh
        pytest -q
        ```

    4. **Push to remote**: `git push origin bugfix/<PR-number>-<short-description>`

    5. **Merge to codebase**: Create a PR to the latest version branch, merge and then delete the `bugfix/<PR-number>-<short-description>` branch.

- **Releasing a Version**
    1. **Fetch latest changes**
        
        ```bash
        git checkout master
        git pull

        git checkout <latest-version-branch>
        git pull
        ```

    2. **Push version tag to version branch**

        ```bash
        git tag <version>
        git push origin <version>
        ```

    3. **Publish github release**: Last step will trigger the publication workflow, if it succeeds, go to Github page → Releases → review and publish the draft release created by `release-drafter`.

---

## Issue Management

### ① 🔖 **Issue Labels **

> Labels help categorize and prioritize issues.

1. **Default Labels**

    - Issues created from templates are automatically labeled:  
        - `Bug Report` → `bug`  
        - `Feature Request` → `feat`  

    - Blank issues (created without templates) have no default labels.

2. **Adding Labels** 

   - Click the `Label` section in the right sidebar of the issue page
   - `torchmeter` provides 12 common issue labels, here we offer a quick glimpse. See our [Label page](https://github.com/TorchMeter/torchmeter/labels) for the most up-to-date list.<details>
     <summary>12 issue labels</summary>

     |     **Label**               |     **Description**                          |
     | :-------------------------: | :------------------------------------------: |
     | `breaking`                  | Backwards-incompatible API changes           |
     | `deprecation`               | Mark features/APIs for future removal        |
     | `performance`               | Optimize speed/resource usage                |
     | `feat`                      | New features                                 |
     | `bug`                       | Unexpected behaviors or flaws                |
     | `docs`                      | Documentation improvements                   |
     | `tests`                     | Test enhancements                            |
     | `maintain`                  | Routine maintenance tasks                    |
     | `refactor`                  | Code structure improvements                  |
     | `revert`                    | Rollback problematic changes                 |
     | `misc`                      | Miscellaneous tasks                          |
     | `good-first-issue`          | Beginner-friendly tasks for new contributors |

     </details>

---

### ② ✍ **Issue Ownership & Assignment**

> Assigning an issue indicates ownership responsibility for tracking and resolving it.

1. **Voluntary Claim**: Assignees should self-claim issues voluntarily. Avoid assigning to others without their consent.  

2. **PR-Based Assignment**: When someone creating a PR to address an issue, the maintainer might assign the issue to himself/herself and the contributor driving the resolution

3. **Accountability**  
   - Assignees are responsible for issue lifecycle management.  
   - The steps to resolve an issue through a PR are detailed in the Pull Request section in our [Contribution Guide](../CONTRIBUTING.md#-pull-requests--lets-squash-bugs--build-features).