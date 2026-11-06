"""Il metodo di lavoro per la serie (docs/metodo/, richiesta di Cioti del 6 nov 2026) resta in ordine:
registro delle decisioni, lezioni imparate e percorso da zero si citano a vicenda e ogni rifacimento
(decisione superata) ha la sua lezione. Lo strumento e' tools/controlla_metodo.py.
"""
import os
import sys
import unittest

from _stile import RADICE

sys.path.insert(0, os.path.join(RADICE, "tools"))
import controlla_metodo as M  # noqa: E402

TESTA = "| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |\n| :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
LEZIONE = ("## L01 · Prova\n\n**Cosa è successo.** x\n\n**Quanto è costato.** x\n\n**Perché.** x\n\n"
           "**Cosa si doveva decidere prima.** x (D001)\n\n**Regola nuova.** x\n\n**Dove vive ora.** x\n")


def registro(*righe):
    return TESTA + "\n".join(righe) + "\n"


class IlMetodoDelRepo(unittest.TestCase):
    def test_zero_errori(self):
        self.assertEqual(M.controlla_il_repo(), [])

    def test_ci_sono_decisioni_generiche_e_specifiche(self):
        with open(os.path.join(M.METODO, "DECISIONI.md"), encoding="utf-8") as f:
            decisioni, _ = M.leggi_decisioni(f.read())
        tipi = {d["tipo"] for d in decisioni.values()}
        self.assertTrue({"G", "S"} <= tipi, tipi)

    def test_i_file_del_metodo_ci_sono(self):
        for nome in ("README.md", "DECISIONI.md", "LEZIONI.md", "PERCORSO_DA_ZERO.md", "GENERICO_E_SPECIFICO.md",
                     "modelli/SCHEDA_AVVIO.md", "modelli/DECISIONE.md", "modelli/LEZIONE.md",
                     "modelli/BRIEF_THREAD.md"):
            self.assertTrue(os.path.isfile(os.path.join(M.METODO, nome)), nome)


class ProveNegative(unittest.TestCase):
    """Ogni difetto rimesso apposta deve far fallire il controllo."""

    def buono(self):
        return registro("| D001 | 2026-11-01 | Prova | Una scelta | Cioti | G | valida |",
                        "| D002 | 2026-11-02 | Prova | Un'altra | Claude | S | superata da D001 |")

    def test_il_caso_buono_passa(self):
        self.assertEqual(M.controlla(self.buono(), LEZIONE.replace("(D001)", "(D001, D002)"), "fase: L01"), [])

    def test_superata_senza_lezione(self):
        errori = M.controlla(self.buono(), LEZIONE, "fase: L01")
        self.assertTrue(any("D002" in e and "nessuna lezione" in e for e in errori), errori)

    def test_superata_da_una_decisione_che_non_esiste(self):
        r = registro("| D001 | 2026-11-01 | Prova | Una scelta | Cioti | G | superata da D009 |")
        self.assertTrue(any("D009" in e for e in M.leggi_decisioni(r)[1]))

    def test_id_ripetuto_data_tipo_stato(self):
        r = registro("| D001 | 2026-11-01 | Prova | Una | Cioti | G | valida |",
                     "| D001 | 1 nov | Prova | Due | Cioti | X | forse |")
        errori = " ".join(M.leggi_decisioni(r)[1])
        for atteso in ("ripetuta", "AAAA-MM-GG", "tipo «X»", "stato «forse»"):
            self.assertIn(atteso, errori)

    def test_colonne_mancanti(self):
        r = registro("| D001 | 2026-11-01 | Prova | Una | G | valida |")
        self.assertTrue(any("colonne" in e for e in M.leggi_decisioni(r)[1]))

    def test_lezione_senza_un_campo(self):
        errori = M.controlla(self.buono(), LEZIONE.replace("**Regola nuova.**", ""), "L01")
        self.assertTrue(any("Regola nuova" in e for e in errori), errori)

    def test_lezione_che_non_cita_decisioni(self):
        errori = M.controlla(self.buono(), LEZIONE.replace("(D001)", ""), "L01")
        self.assertTrue(any("non cita nessuna decisione" in e for e in errori), errori)

    def test_lezione_fuori_dal_percorso(self):
        errori = M.controlla(self.buono(), LEZIONE, "nessuna")
        self.assertTrue(any("L01" in e and "PERCORSO" in e for e in errori), errori)

    def test_percorso_cita_cose_che_non_esistono(self):
        errori = M.controlla(self.buono(), LEZIONE, "L01 L07 D777")
        self.assertTrue(any("L07" in e for e in errori) and any("D777" in e for e in errori), errori)


if __name__ == "__main__":
    unittest.main()
