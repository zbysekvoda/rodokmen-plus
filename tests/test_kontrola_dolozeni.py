#!/usr/bin/env python3
"""Testy tools/dolozeni.py (volá kontrola.py): kauzální/účastnické spojení osoby s událostí bez odkazu na zápis.

Spuštění: python3 -m unittest discover tests
"""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
sys.path.insert(0, TOOLS)
import dolozeni  # noqa: E402

N = dolozeni.nedolozena_spojeni


class Varuje(unittest.TestCase):
    def test_kvuli(self):
        self.assertTrue(N("Jan zemřel roku 1866 kvůli choleře, která zuřila v kraji."))

    def test_zucastnil_se(self):
        self.assertTrue(N("Josef se zúčastnil bitvy u Hradce Králové."))
        self.assertTrue(N("Marie se zúčastnila povstání."))

    def test_padl(self):
        self.assertTrue(N("Syn Václav padl v roce 1916 na italské frontě."))

    def test_zemrel_na_epidemii(self):
        self.assertTrue(N("Anna zemřela na choleru v létě 1855."))

    def test_v_dusledku(self):
        self.assertTrue(N("V důsledku hladomoru rodina odešla do Vídně."))

    def test_odkaz_jinde_v_odstavci_nestaci(self):
        t = ("Podle [[zdroj:mat_1]] se narodil roku 1840. Pak hospodařil na statku. Dlouho nic. "
             "Ještě jedna věta. A padl u Solferina.")
        self.assertTrue(N(t))


class Nevaruje(unittest.TestCase):
    def test_kontext(self):
        self.assertEqual(N("V těch letech zuřila v kraji cholera."), [])
        self.assertEqual(N("Žil v době napoleonských válek."), [])

    def test_s_wiki_odkazem(self):
        self.assertEqual(N("Jan zemřel na choleru ([[zdroj:mat_zemreli_1866]])."), [])

    def test_matrika_v_sousedni_vete(self):
        self.assertEqual(N("Václav padl roku 1916 u Doberdò. Uvádí to úmrtní matrika farnosti."), [])

    def test_vojensky_zaznam(self):
        self.assertEqual(N("Podle kmenového listu se zúčastnil bitvy u Custozzy."), [])

    def test_bez_spouste(self):
        self.assertEqual(N("Jan se oženil roku 1850 a měl osm dětí."), [])

    def test_padl_jako_soucast_slova(self):
        self.assertEqual(N("Statek připadl nejmladšímu synovi."), [])


if __name__ == "__main__":
    unittest.main()
