---
title: Issues
---

# :octicons-issue-opened-16: Issues — Let's Report & Enhance! 

???+ note

    <figure markdown> 
        ![TorchMeter Issues](../assets/contribute/issue_tab.png)
        <figcaption>[Access to `Issues` :material-link-variant:](https://github.com/TorchMeter/torchmeter/issues)</figcaption>
    </figure>

    - Issues section is for reporting **urgent bugs** or **feature requests** 
    - Further reading: [Github Docs of Issues :material-link-variant:](https://docs.github.com/en/issues)

## **:material-numeric-1-circle-outline: Scenarios of Filing Issues**

- [x] **Bugs reports**
- [x] **Feature proposals**
- [x] **Documentation errors reports**
- [ ] ~~Non-Urgent Questions~~ → Use [Discussions :material-link-variant:](discussions.md){ data-preview }
- [ ] ~~Help with Usage~~ → Use [Discussions :material-link-variant:](discussions.md){ data-preview }

## **:material-numeric-2-circle-outline: Submission Guide**

1. **Search First** 🔍: 
    - Check existing issues (open/closed)
    - If there are relevant issues, comment if you have more details. If the issue is addressed, give a 👍 reaction to show support, it motivates everyone involved!
    - Otherwise, create a new issue following the steps below.

2. **File an Issue** 🗳 
    - Navigate to the [`Issues` tab :material-link-variant:](https://github.com/TorchMeter/torchmeter/issues) and click `New issue`.  
    - Select the template matching your scenario (bug report, feature request, etc.).  
    - Fill out all fields (asterisks `*` denote required information).  
    - Click `Create` to submit.  

??? info "Tips"

    ??? example "Illustration of filing an issue"

        ![Illustration of filing an issue](../assets/contribute/create_issue_from_template.png)

    - Further reading: [How maintainers manage issues :material-link-variant:](../others/management.md#Issue-Management){ data-preview }

## **:material-numeric-3-circle-outline: Suggestions**

1. **Ensure a Clear Title** ✍️  
    - ✅ Good example: `"Export data error: target file not found"`
    - ❌ Avoid vague titles: `"Something's wrong!"`

2. **Link Related Content** 🔗  
    - If this issue relates to other issues, discussions, or PRs, use `#corresponding-number` to reference them.

3. **Tell the Full Story**   
    - If create an issue from a template: Fill out all requested fields for complete information.  
    - If participate in existing issues: Use the simplified template below to share your additional details.

```markdown title="Issue comment template for supplementing details"
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
