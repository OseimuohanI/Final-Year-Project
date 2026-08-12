# Monorepo Workspace

This repository serves as the central hub for our project ecosystem. It links separate component repositories (like the Frontend and Backend) together in one place using Git Submodules.

---

## Getting Started

Because this repository relies on Git Submodules to link external repositories, standard cloning will leave the component directories empty. Follow the setups below to clone the code correctly.

### 1. First-Time Setup (Cloning)
To pull this repository along with **all linked submodules** at the same time, include the `--recursive` flag:

```bash
git clone --recursive [https://github.com](https://github.com/OseimuohanI/Final-Year-Project.git)
cd Final-Year-Project
```

### 2. Already Cloned Without Submodules?
If you accidentally cloned this repository normally and notice your component folders are empty, initialize and update them by running:

```bash
git submodule update --init --recursive
```

---

## Keeping Code Updated

Submodules link to a specific commit snapshot of their respective repositories. They do not update automatically when changes are pushed to the independent repos.

### Pull Latest Changes From All Linked Repos
To update all your local submodules to their latest upstream commits in one go, run:

```bash
git submodule update --remote --merge
```

---

## Working with Linked Repositories

When making modifications inside a linked folder (e.g., `Frontend/`):

1. **Navigate into the folder:** `cd Frontend`
2. **Treat it like its own repository:** Make changes, commit them, and push them to its specific origin host.
3. **Update the parent pointer:** Step back out (`cd ..`) to the root of this main monorepo, then stage and commit the new folder pointer change:
   ```bash
   git add Frontend
   git commit -m "Update Frontend submodule tracking point"
   git push origin main
   ```
