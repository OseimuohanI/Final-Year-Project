# Project repositories

The parent repository is `git@github.com:OseimuohanI/Final-Year-Project.git`.

| Parent path | Component repository | Branch |
| --- | --- | --- |
| `Backend/` | `git@github.com:OseimuohanI/FYP_Backend.git` | `main` |
| `Frontend/` | `git@github.com:OseimuohanI/FYP_Frontend.git` | `main` |
| `NLP_Service/` | `git@github.com:OseimuohanI/FYP_NLP.git` | `main` |

These three paths are Git submodules: the parent records a particular component commit, rather than copying its files. The parent also owns `Scraper/`, `docs/`, `scripts/`, its README and ignore rules. Scraper has no separately configured repository.

## Clone and update

```sh
git clone --recurse-submodules git@github.com:OseimuohanI/Final-Year-Project.git
cd Final-Year-Project
```

Existing clones, after saving local changes:

```sh
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
```

The NLP path was renamed from `PythonNLP/` to `NLP_Service/` to match the code, launcher and documentation. If an older clone contains local work in `PythonNLP/`, preserve it before updating. Submodule update normally checks out the exact recorded commit, which can leave a detached HEAD; switch to the component's `main` branch before developing there.

## Publish component changes first

From the component being edited, review and commit only the intended source changes, then push its branch. For example:

```sh
cd Frontend
git switch main
git add README.md index.html src
git commit -m "Describe the frontend change"
git push origin main
cd ..
```

Include any other intended component files in that example's staging command. After every changed component commit is available on GitHub, update the parent pointers and any shared files:

```sh
git add Backend Frontend NLP_Service
git commit -m "Update component versions"
git push origin main
```

A component push does not automatically advance its parent pointer. Conversely, pushing a pointer before its component commit exists remotely can leave fresh clones unable to obtain the recorded revision. Normal updates preserve history; force pushes are not part of this workflow.

## Local artifacts

Do not commit `.env` credentials, databases, virtual environments, dependencies, model caches, Python bytecode, logs or browser/source captures. Collected review datasets and generated evaluation outputs remain local and are documented separately. The CBN research input snapshot and compact forecasting protocol/release evidence are versioned in the NLP repository; they are different from local customer-review collections and model weights.

The demo launcher currently requires the retained itel collection and frozen scoring artifact. A fresh clone must restore/reproduce those and install Python/Composer dependencies before running the complete research demo. See [Testing the app](TESTING_THE_APP.md).
