from __future__ import annotations

import asyncio
import unittest
import warnings

from reproduce import collect, verify


class BoundaryCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        warnings.simplefilter("ignore", UserWarning)

    def test_published_path_and_repair_controls(self) -> None:
        published, repaired, benign = asyncio.run(collect())
        verify(published, repaired, benign)

    def test_repair_is_discriminating(self) -> None:
        _, repaired, benign = asyncio.run(collect())
        self.assertTrue(repaired.blocked)
        self.assertEqual(repaired.ledger, [])
        self.assertFalse(benign.blocked)
        self.assertEqual(benign.ledger, [50])


if __name__ == "__main__":
    unittest.main()
