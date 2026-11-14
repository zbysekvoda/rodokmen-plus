"""Názvy vzdálenějších pokrevních vztahů (tools/graf.py, zrcadlo web/src/lib/pribuzni.js)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/rodokmen-plus/tools"))
from graf import nazev_pokrevni as n  # noqa: E402


class NazevPokrevni(unittest.TestCase):
    def test_bratranci_z_kolena(self):
        self.assertEqual(n(2, 2, "M"), "bratranec")
        self.assertEqual(n(3, 3, "M"), "bratranec z 2. kolena")
        self.assertEqual(n(3, 3, "F"), "sestřenice z 2. kolena")
        self.assertEqual(n(4, 4, "F"), "sestřenice z 3. kolena")

    def test_o_generaci_nahoru(self):
        self.assertEqual(n(3, 2, "M"), "strýc z 2. kolena")
        self.assertEqual(n(3, 2, "F"), "teta z 2. kolena")
        self.assertEqual(n(4, 2, "F"), "prateta z 2. kolena")
        self.assertEqual(n(4, 3, "M"), "strýc z 3. kolena")

    def test_o_generaci_dolu(self):
        self.assertEqual(n(2, 3, "M"), "synovec z 2. kolena")
        self.assertEqual(n(2, 3, "F"), "neteř z 2. kolena")
        self.assertEqual(n(2, 4, "M"), "prasynovec z 2. kolena")

    def test_blizke_beze_zmeny(self):
        self.assertEqual(n(3, 1, "M"), "prastrýc")
        self.assertEqual(n(1, 3, "F"), "praneteř")

    def test_fallback(self):
        self.assertEqual(n(6, 6, "M"), "vzdálený příbuzný (společný předek 6. a 6. generace)")
        self.assertEqual(n(7, 2, "F"), "vzdálená příbuzná (společný předek 7. a 2. generace)")


if __name__ == "__main__":
    unittest.main()
