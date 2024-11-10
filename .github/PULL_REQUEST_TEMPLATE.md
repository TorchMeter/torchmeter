## 📋 Summary

> [!IMPORTANT]
> - [ ] This PR fixes an issue. [Link]() <!--Link to related issues if applicable -->    
> - [ ] This PR adds something new.
> - [ ] This PR is **not** a code change (e.g. `README`, typos, ...)
> - [ ] This PR has been tested.

<!-- What is this pull request for? Does it fix any issues? -->

## 📝 Changes

<!-- Describe what you change and what the purpose in this pull request. -->

<details>
<summary>Details</summary>

- `file1`: modify xxx, in order to achieve a xxx result.
- `file2`: add xxx, in order to fix xxx.

</details>

## 🛠️ How to test

<!-- Describe your testing approach and results. Replace the example below-->

<details>
<summary>Example</summary>

For manual testing:
- Install the library in a fresh virtual environment.
- Import main library functions/classes and perform basic operations.
- Test configuration options by setting different values and verify library behavior changes.
- If library interacts with external services, mock them and ensure it handles errors gracefully.

For automated testing:
- We use `pytest` for testing. Test suite has unit tests for functions and methods in library. 
- Integration tests are in place to check interaction between library components.
- We run tests on `GitHub Actions`. Ensures every commit triggers test suite, reports failures immediately.
- Performance tests are conducted periodically to measure the efficiency of critical functions. 

</details>


## 📷 Screenshots/Examples (if needed):

<!-- Add screenshots or examples to illustrate the changes if needed. -->