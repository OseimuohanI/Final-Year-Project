"""Inspect, verify or restore a dated workspace archive without overwriting files."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = "_archive/cleanup-2026-11-17"


def fingerprint(path):
    """Hash names, contents, modes and link targets; never follow symlinks."""
    tree = hashlib.sha256()
    files = size = 0

    def visit(node, relative):
        nonlocal files, size
        info = node.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            kind, value = "symlink", os.readlink(node)
            files += 1
        elif stat.S_ISDIR(info.st_mode):
            kind, value = "directory", ""
        elif stat.S_ISREG(info.st_mode):
            kind = "file"
            content = hashlib.sha256()
            with node.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    content.update(block)
            value = content.hexdigest()
            files += 1
            size += info.st_size
        else:
            raise ValueError(f"Unsupported filesystem object: {node}")
        tree.update((json.dumps([relative, kind, mode, value], ensure_ascii=True) + "\n").encode())
        if kind == "directory":
            for child in sorted(node.iterdir(), key=lambda item: item.name):
                visit(child, f"{relative}/{child.name}" if relative else child.name)

    visit(path, "")
    return {"sha256": tree.hexdigest(), "file_count": files, "bytes": size}


def safe_path(base, relative):
    parts = PurePosixPath(relative)
    if (not parts.parts or parts.as_posix() != relative or parts.is_absolute()
            or any(part in {"..", ".git"} for part in parts.parts)):
        raise ValueError(f"Unsafe archive path: {relative}")
    target = base.joinpath(*parts.parts)
    # A symlink at the leaf is an archived object, but parents cannot redirect us.
    for parent in [base, *target.parents]:
        if parent == base.parent:
            break
        if parent.is_symlink():
            raise ValueError(f"Symlink parent is not allowed: {parent}")
    return target


def exists(path):
    return path.exists() or path.is_symlink()


def inspect(root, archive, entries):
    results = []
    for entry in entries:
        source = safe_path(archive, entry["path"])
        destination = safe_path(root, entry["path"])
        if exists(source):
            state = "archived"
            actual = fingerprint(source)
        elif exists(destination):
            state = "restored"
            actual = fingerprint(destination)
        else:
            state, actual = "unavailable", None
        if actual is not None and actual != entry["fingerprint"]:
            raise ValueError(f"Checksum or permissions mismatch: {entry['path']}")
        results.append((entry, state))
    return results


def restore(root, archive, entries, apply=False):
    results = inspect(root, archive, entries)
    # Preflight the entire selection before moving any entry.
    for entry, state in results:
        if state == "unavailable":
            raise ValueError(f"Archive payload is unavailable locally: {entry['path']}")
        destination = safe_path(root, entry["path"])
        if state == "archived" and exists(destination):
            raise ValueError(f"Refusing to overwrite existing path: {entry['path']}")
    if apply:
        for entry, state in results:
            if state != "archived":
                continue
            source = safe_path(archive, entry["path"])
            destination = safe_path(root, entry["path"])
            if exists(destination):
                raise ValueError(f"Refusing to overwrite existing path: {entry['path']}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Exact original paths from the manifest")
    parser.add_argument("--archive", default=DEFAULT_ARCHIVE, help="Archive directory relative to project root")
    parser.add_argument("--all", action="store_true", help="Select every entry, including local-only artifacts")
    parser.add_argument("--verify", action="store_true", help="Verify selected payloads or list unavailable local artifacts")
    parser.add_argument("--apply", action="store_true", help="Restore the selection; otherwise only preview")
    args = parser.parse_args()
    try:
        if args.apply and args.verify:
            raise ValueError("Choose either --verify or --apply.")
        archive = safe_path(ROOT, args.archive)
        manifest = json.loads((archive / "manifest.json").read_text())
        entries = manifest["entries"]
        names = [entry["path"] for entry in entries]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate archive entries.")
        for name in names:
            if name.startswith("_archive/") or name in {"Backend", "Frontend", "NLP_Service", "Scraper"}:
                raise ValueError(f"Unsafe restoration target: {name}")
            if any(name.startswith(other + "/") for other in names if other != name):
                raise ValueError(f"Overlapping archive entries: {name}")
        unknown = set(args.paths) - set(names)
        if unknown:
            raise ValueError(f"Unknown original paths: {', '.join(sorted(unknown))}")
        if args.apply and not (args.paths or args.all):
            raise ValueError("Select paths or --all before using --apply.")
        selected = [entry for entry in entries if args.all or not args.paths or entry["path"] in args.paths]
        if args.verify:
            results = inspect(ROOT, archive, selected)
        elif args.paths or args.all:
            results = restore(ROOT, archive, selected, apply=args.apply)
        else:
            for entry in selected:
                print(f"{entry['path']} [{entry['distribution']}] — {entry['reason']}")
            return 0
        for entry, state in results:
            action = "restored" if args.apply and state == "archived" else state
            print(f"{action}: {entry['path']}")
        if not args.apply and not args.verify:
            print("Preview only. Add --apply to restore this selection.")
        return 1 if any(state == "unavailable" for _, state in results) else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Archive operation stopped: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
