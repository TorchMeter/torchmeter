<!-- # v1.4.0 -->

![](https://img.shields.io/badge/Version-v1.4.0-green)

## 🎉 Support `pyproject.toml`  

see assets below.

## 🔄 Change

- `.github/CONTRIBUTING.md`: add suggestion for creating a new branch to submit PR.

---

<!-- # v1.3.1 -->

![](https://img.shields.io/badge/Version-v1.3.1-green)

## 🌟 Add 

1. `.github/workflows/publish_release.yml` : enable continuous deployment(CD) workflows for automatic package building, publishing, and creating GitHub releases.

---

<!-- # v1.3.0 -->

![](https://img.shields.io/badge/Version-v1.3.0-green)

## 🌟 Add 

1. `.github/CONTRIBUTING.md` : guide other to make contribution to your project. 

2. `.github/ISSUE_TEMPLATE` : standardize the format of `issue` reporting. Composed of `bug_report.yml`, `feature_request.yml` and `config.yml`.

3. `.github/PULL_REQUEST_TEMPLATE.md` : standardize the format of `Pull Request`. 

---

<!-- # v1.2.3 -->

![](https://img.shields.io/badge/Version-v1.2.3-green)

## 🌟 Add 

- `docs/README.md`: instructions for docs, provide some tool suggestions to help you quickly build your own document.
- `tests/README.md`: instructions for testing, provide the whole procedure of testing.
- `examples/demo.ipynb`: provide an example of how to demonstrate your project.

## 🗑️ Delete

- `docs/.gitkeep`
- `tests/.gitkeep`
- `examples/.gitkeep`

---

<!-- # v1.2.2 -->

![](https://img.shields.io/badge/Version-v1.2.2-green)

## 🔄 Change

- `packaging.sh`: add logit of deleting the old distribution packages.
- `README.md`: add `🧰 Tools Recommended` section.

---

<!-- # v1.2.1 -->

![](https://img.shields.io/badge/Version-v1.2.1-green)

## 🔄 Change

- `check_meta.sh`: rectify logit of getting `Metadata-Version`
- `README.md`: rectify usage of `keyring`.

---

<!-- # v1.2.0 -->

![](https://img.shields.io/badge/Version-v1.2.0-green)

## 🎉 Support manual package maintenance

Including construction, inspection, and publishing to PyPI.   
Please refer to steps `6` through `8` in [`README.md`](https://github.com/Ahzyuan/Python-package-template/blob/v1.2.0/README.md) file.

## 🔄 Change

- `setup.py`: keep a minimal setting to ensure editable installation supported
- `README.md`: finish full pipeline of package development.
- `requirements.txt`: add more example dependencies.
- `ruff.toml`: `target-version` set to `"py37"`, cause it is the minimum requirement.
  
## 🌟 Add 

- `setup.cfg`: define the configuration of the build process
- `packaging.sh`: auto build the distribution packages.
- `check_meta.sh`: auto check the meta information of the built distribution packages.

---

<!-- # v1.1.0 -->

![](https://img.shields.io/badge/Version-v1.1.0-green)

## 🔄 Change

- `README.md`: Added more information and beautified it.
- `setu.py`: add [`SETUP_REQUIRED`](https://github.com/Ahzyuan/Python-package-template/commit/dc9d10b85c22a14fb8cbda869f1f4a7936192f48#diff-60f61ab7a8d1910d86d9fda2261620314edcae5894d5aaa236b821c7256badd7R65)

## 🌟 Add 

- `CHANGELOG.md`: record version changes.
- `ruff.toml`: define rules for code style, code inspection, and import management

---

<!-- # v1.0.1 -->

![](https://img.shields.io/badge/Version-v1.0.1-green)

## 🔄 Change

- Fix bugs in `setup.py`: Optimized the logic of dynamically obtaining version information, removed the extended function class `UploadCommand`(Cause `setpu.py` no longer supports functional customization, [see more](https://packaging.python.org/en/latest/discussions/setup-py-deprecated/#what-about-custom-commands))
- Fix bugs in `MANIFEST.in`: Discard unnecessary commands
- `<package-name>/__init__.py`: Added copyright definition and version definition
- `requirements.txt`: Added example dependencies
- `README.md`: Added more information and beautified it.

## 🗑️ Delete

- `<package-name>/__version__.py`

---

<!-- # v1.0.0 -->

![](https://img.shields.io/badge/Version-v1.0.0-green)

## 🎉 Preliminarily establish the project framework.

## 🎯 Features

- A relatively complete software engineering project structure, including directories for [code](https://github.com/Ahzyuan/Python-package-template/tree/v1.0.0/package-name), [test](https://github.com/Ahzyuan/Python-package-template/tree/v1.0.0/tests), [document](https://github.com/Ahzyuan/Python-package-template/tree/v1.0.0/docs), and [project demonstration](https://github.com/Ahzyuan/Python-package-template/tree/v1.0.0/examples)

- `setup.py` is a collection of useful patterns and best practices. It extends the `python setup.py` command to achieve one-step code updates, package builds, and releases to [PyPi](https://pypi.org/) using `Twine`.