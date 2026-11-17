"""Check restoration safety using disposable directories, never the real archive."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("restore_archive", Path(__file__).parents[1] / "restore_archive.py")
archive_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive_tool)


class RestoreArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "_archive" / "test"
        self.archive.mkdir(parents=True)

    def entry(self, name, content="preserved"):
        source = self.archive / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content)
        return {"path": name, "fingerprint": archive_tool.fingerprint(source)}

    def test_preview_then_restore_preserves_contents(self):
        entry = self.entry("Backend/app/Http/old.php")
        archive_tool.restore(self.root, self.archive, [entry])
        self.assertFalse((self.root / entry["path"]).exists())
        archive_tool.restore(self.root, self.archive, [entry], apply=True)
        self.assertEqual((self.root / entry["path"]).read_text(), "preserved")
        self.assertEqual(archive_tool.inspect(self.root, self.archive, [entry])[0][1], "restored")

    def test_conflict_preflights_entire_selection(self):
        first = self.entry("Backend/first.php")
        second = self.entry("Backend/second.php")
        destination = self.root / second["path"]
        destination.parent.mkdir()
        destination.write_text("new work")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            archive_tool.restore(self.root, self.archive, [first, second], apply=True)
        self.assertTrue((self.archive / first["path"]).exists())
        self.assertEqual(destination.read_text(), "new work")

    def test_modified_payload_is_rejected(self):
        entry = self.entry("old.py")
        (self.archive / "old.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            archive_tool.restore(self.root, self.archive, [entry], apply=True)
        self.assertFalse((self.root / "old.py").exists())

    def test_unsafe_paths_are_rejected(self):
        for name in ["../outside", "/tmp/outside", ".git/config", ".", "a/../outside", "a//b"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive_tool.safe_path(self.root, name)

    def test_symlink_parent_is_rejected(self):
        entry = self.entry("Backend/old.php")
        (self.root / "elsewhere").mkdir()
        (self.root / "Backend").symlink_to(self.root / "elsewhere", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink parent"):
            archive_tool.restore(self.root, self.archive, [entry], apply=True)

    def test_directory_and_dangling_symlink_restore_without_following(self):
        folder = self.archive / "old-environment"
        folder.mkdir()
        (folder / "script").write_bytes(b"original\x00bytes")
        (folder / "python").symlink_to("/missing/python")
        entry = {"path": "old-environment", "fingerprint": archive_tool.fingerprint(folder)}
        archive_tool.restore(self.root, self.archive, [entry], apply=True)
        self.assertTrue((self.root / "old-environment/python").is_symlink())
        self.assertEqual(archive_tool.fingerprint(self.root / "old-environment"), entry["fingerprint"])

    def test_missing_payload_is_reported_and_cannot_restore(self):
        entry = self.entry("old.py")
        (self.archive / "old.py").unlink()
        self.assertEqual(archive_tool.inspect(self.root, self.archive, [entry])[0][1], "unavailable")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            archive_tool.restore(self.root, self.archive, [entry], apply=True)


if __name__ == "__main__":
    unittest.main()
