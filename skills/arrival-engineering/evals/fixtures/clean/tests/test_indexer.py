"""The exercise receipt behind control-properly-bound's L1 arrival."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from indexer import materialize_index  # noqa: E402


class IndexerTests(unittest.TestCase):
    def test_materialize_index_sorts(self) -> None:
        self.assertEqual(materialize_index(["b", "a"]), {"indexed": ["a", "b"]})


if __name__ == "__main__":
    unittest.main()
