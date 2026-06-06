import tempfile
import unittest
from pathlib import Path

from src.file_utils import next_output_path


class FileUtilsTest(unittest.TestCase):
    def test_next_output_path_adds_suffix_and_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.png"
            source.write_bytes(b"source")
            (Path(tmp) / "sample_fuwamoza.png").write_bytes(b"existing")

            self.assertEqual(next_output_path(source).name, "sample_fuwamoza_2.png")


if __name__ == "__main__":
    unittest.main()
