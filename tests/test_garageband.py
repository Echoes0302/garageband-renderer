import importlib.util
import os
import tempfile
import time
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "garageband.py"
SPEC = importlib.util.spec_from_file_location("garageband_renderer", MODULE_PATH)
garageband = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(garageband)


class OutputNameTests(unittest.TestCase):
    def test_accepts_unicode_filename(self):
        self.assertEqual(garageband.validate_output_name("给朋友的小曲"), "给朋友的小曲")

    def test_rejects_path_traversal(self):
        for value in ("../song", "folder/song", "..", ""):
            with self.subTest(value=value):
                with self.assertRaises(garageband.GarageBandError):
                    garageband.validate_output_name(value)


class ExportDiscoveryTests(unittest.TestCase):
    def test_freshness_guard_rejects_stale_same_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "render.mp3"
            path.write_bytes(b"old")
            started_at = time.time()
            os.utime(path, (started_at - 30, started_at - 30))
            self.assertFalse(garageband.is_fresh_file(path, started_at=started_at))

    def test_find_export_returns_stable_fresh_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unique.mp3"
            path.write_bytes(b"new audio")
            found = garageband.find_export(
                path.name,
                started_at=time.time() - 1,
                directories=[Path(tmp)],
                timeout=2,
            )
            self.assertEqual(found, path)


class InputTests(unittest.TestCase):
    def test_rejects_unknown_input_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "song.wav"
            source.write_bytes(b"not midi")
            with self.assertRaises(garageband.GarageBandError):
                garageband.prepare_midi(source, Path(tmp) / "song.mid")


if __name__ == "__main__":
    unittest.main()
