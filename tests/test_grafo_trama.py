"""Il grafo della trama (tools/grafo_trama.py): il copione del repo regge, e lo strumento se ne accorge
quando non regge.

Sul copione vero: nessun ERRORE (scene tutte raggiungibili, nessun vicolo cieco, nessuna bandiera letta
che niente accende, nessuna battuta che nessun percorso recita, nessuna condizione che il gioco non
capisce), e i titoli di coda si raggiungono con ogni combinazione delle quattro scelte.
Prove negative: un copione rotto apposta in una cartella temporanea deve dare l'errore giusto.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("grafo_trama", os.path.join(RADICE, "tools", "grafo_trama.py"))
GT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GT)

COPIONE = os.path.join(RADICE, "copione")
VERO = GT.analizza(COPIONE)


def codici(r, gravita=GT.ERRORE):
    return {p["codice"] for p in r["problemi"] if p["gravita"] == gravita}


class CopioneVero(unittest.TestCase):
    def test_nessun_errore(self):
        errori = [f"{p['codice']} {p['dove']}: {p['testo']}" for p in VERO["problemi"] if p["gravita"] == GT.ERRORE]
        self.assertEqual(errori, [], "\n".join(errori))

    def test_tutte_le_scelte_arrivano_alla_fine(self):
        # D1 (dentro/fuori), D2 (prigioniero/liberato), D3 (pane sì/no), D4 (giustizia sì/no)
        self.assertGreater(VERO["conti"]["finali"], 0)
        self.assertEqual(VERO["conti"]["combinazioni_di_scelte"], 2 * 2 * 2 * 2)

    def test_il_grafo_ha_scene_bandiere_e_scelte(self):
        g = VERO["grafo"]["v1"]
        tipi = {n["tipo"] for n in g["nodi"]}
        self.assertTrue({"scena", "bandiera", "scelta", "npc", "cutscene"} <= tipi)
        scene = {n["id"] for n in g["nodi"] if n["tipo"] == "scena"}
        self.assertTrue(all(n["raggiunta"] for n in g["nodi"] if n["tipo"] == "scena"))
        self.assertIn({"da": "INIZIO", "a": "P-00"}, g["flusso"])
        self.assertTrue(all(a["a"] in scene for a in g["flusso"]))

    def test_vede_le_battute_dell_epilogo(self):
        # Le battute NOTTE con GIUSTIZIA_OFFERTA (Ciaccio, Giuliana) si sentono solo camminando da E-01 a
        # E-02 (revisione, T1): lo strumento lo deve dire finche' il copione non cambia.
        epilogo = [p for p in VERO["problemi"] if p["codice"] == "BATTUTA_SOLO_NELL_EPILOGO"]
        if any("GIUSTIZIA_OFFERTA" in p["testo"] for p in epilogo):
            self.assertIn("EPILOGO_A_PIEDI", codici(VERO, GT.AVVISO))


class Mappa(unittest.TestCase):
    def test_camminando_si_sentono_le_stesse_battute(self):
        # Il modello veloce teletrasporta il giocatore; quello con la mappa (mondo/varchi.json) lo fa camminare,
        # e ogni area attraversata puo' far partire la sua scena. Le battute raggiungibili devono essere le stesse.
        m = GT.carica_v1(COPIONE)
        veloce, mappa = GT.esplora(m), GT.esplora_mappa(m, GT.vicini())
        # le battute della vetrata (E-02, l'ultima scena) contano a parte: il controllo le esclude comunque
        finale = {b["id"] for x in m["scene"] if GT.FINE in x["imposta"] for b in x["battute"]}
        self.assertEqual(veloce["dette_trama"] - finale, mappa["dette_trama"] - finale)
        self.assertTrue(any(GT.FINE in s[0] for s in mappa["stati"]))


class CopioneRotto(unittest.TestCase):
    """Ogni prova copia il copione, ne rompe un punto e controlla che l'errore giusto esca."""

    def rompi(self, file, vecchio, nuovo):
        cartella = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, cartella)
        dest = os.path.join(cartella, "copione")
        shutil.copytree(COPIONE, dest)
        p = os.path.join(dest, file)
        testo = open(p, encoding="utf-8").read()
        self.assertIn(vecchio, testo)
        open(p, "w", encoding="utf-8").write(testo.replace(vecchio, nuovo, 1))
        return GT.analizza(dest)

    def test_bandiera_che_nessuno_accende(self):
        r = self.rompi("01_atto_I.md", "| Imposta | `PORTA_DEL_MONTE` |", "| Imposta | nessuna |")
        self.assertIn("SCENA_IRRAGGIUNGIBILE", codici(r))
        self.assertIn("BANDIERA_MAI_ACCESA", codici(r))
        self.assertIn("NESSUN_FINALE", codici(r))

    def test_vicolo_cieco(self):
        # la terza alba vietata a chi ha lasciato fuori il borgo: da li' la fine non si raggiunge
        r = self.rompi("02_bottaccione_epilogo.md", "| Condizione | `RIENTRO_PORTA_METAURO` e `ALBA_CONFERMATA` (la voce «Sì, è ora», in B-05 o dal console Guido) |",
                       "| Condizione | `RIENTRO_PORTA_METAURO` e non `BORGO_FUORI` |")
        self.assertIn("VICOLO_CIECO", codici(r))

    def test_battuta_che_non_si_sente_mai(self):
        # nell'ULTIMATUM non si e' ancora rientrati da Porta Metauro
        r = self.rompi("03_npc_ambiente.md", "- NOTTE: CECCO: Da Porta Metauro?",
                       "- ULTIMATUM (se RIENTRO_PORTA_METAURO): CECCO: Impossibile.\n- NOTTE: CECCO: Da Porta Metauro?")
        self.assertIn("BATTUTA_IRRAGGIUNGIBILE", codici(r))

    def test_condizione_che_il_gioco_non_capisce(self):
        r = self.rompi("02_bottaccione_epilogo.md", "Se «Lascialo andare»", "Se il ragazzo ha visto `CONDOTTO_SALVO` e piove:\n\nSe «Lascialo andare»")
        self.assertIn("CONDIZIONE_NON_CAPITA", codici(r))

    def test_bandiera_scritta_male(self):
        r = self.rompi("02_bottaccione_epilogo.md", "| Imposta | `CRONACA_V1_FINITA`", "| Imposta | `CRONACA_V1_FINTA`")
        self.assertTrue({"BANDIERA_SCONOSCIUTA", "NESSUN_FINALE"} & codici(r))


    def test_obiettivo_con_meta_sconosciuta(self):
        # MOB: l'area meta scritta a mano dev'essere un'area del mondo
        r = self.rompi("01_atto_I.md", "(area: TEATRO_ROMANO)", "(area: TEATRO_GRECO)")
        self.assertIn("OBIETTIVO_SENZA_META", codici(r))

    def test_obiettivo_senza_scena_dopo(self):
        # MOB: una riga OBIETTIVO nell'ultima scena, senza «(area: ID)», non ha meta
        r = self.rompi("02_bottaccione_epilogo.md", "## E-02 · La vetrata",
                       "## E-02 · La vetrata\n\n- OBIETTIVO: Guarda la vetrata.\n")
        self.assertIn("OBIETTIVO_SENZA_META", codici(r))

    def test_obiettivo_irraggiungibile(self):
        # MOB: senza il varco fra Piazza Grande e via XX Settembre la meta di A1-04 (Piazza Grande) non si raggiunge
        archi = [a for a in GT.archi_del_mondo() if "PIAZZA_GRANDE" not in a]
        self.assertTrue(GT.meta_raggiungibile("SAN_MARTINO", "TEATRO_ROMANO", archi))
        self.assertFalse(GT.meta_raggiungibile("SAN_MARTINO", "PIAZZA_GRANDE", archi))
        m = GT.carica_v1(COPIONE)
        self.assertEqual(GT.controlla_obiettivi(m), [])
        self.assertIn("OBIETTIVO_IRRAGGIUNGIBILE", {p["codice"] for p in GT.controlla_obiettivi(m, archi)})

    def test_regola_dei_nomi(self):
        # «Sant'Ubaldo» detto come persona fuori dalla Basilica; «di Sant'Ubaldo» (cose e luoghi) va bene
        r = self.rompi("02_bottaccione_epilogo.md", "- SCELTA: Sì, è ora / Non ancora",
                       "- GUIDO: Sant'Ubaldo, la piazza aspetta. I biscotti di Sant'Ubaldo sono pronti.\n- SCELTA: Sì, è ora / Non ancora")
        nomi = [p for p in r["problemi"] if p["codice"] == "REGOLA_NOMI" and "B-05" in p["dove"]]
        self.assertEqual(len(nomi), 1, nomi)


SCALETTA = """# Atto II di prova

## 4. Scaletta

### A2-01 · Primo (Piazza Grande, giorno 1)

- Con `CORRADO_PRESO` cambia tutto. Ripagato in A2-02.
- **Imposta**: `ATTO_II_INIZIATO`.

### A2-02 · Secondo (San Martino, giorno 2)

- **Scelta**: `SCELTA: Sì / No`
| Bandiera | `SI_DETTO` | `NO_DETTO` |

### A2-03 · Terzo (Duomo, giorno 1)

- Ripaga A2-01. Con `GIUSTIZIA_OFFERTA` e `PANE_DATO`, `BORGO_DENTRO`, `ESULE_LIBERATO`.
- Rimanda ad A2-09.
- **Imposta**: `CORRADO_PRESO`.

Bandiere nuove: `ATTO_II_INIZIATO`, `CORRADO_PRESO`, `SI_DETTO`, `NO_DETTO`.
"""


class AttoII(unittest.TestCase):
    def test_scaletta_rotta(self):
        cartella = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, cartella)
        p = os.path.join(cartella, "ATTO_II.md")
        open(p, "w", encoding="utf-8").write(SCALETTA)
        r = GT.analizza(COPIONE, p)
        a2 = {x["codice"] for x in r["problemi"] if x["atto"] == "II"}
        self.assertIn("A2_LETTA_PRIMA", a2)            # CORRADO_PRESO letta in A2-01, accesa in A2-03
        self.assertIn("A2_PROMESSA_SBAGLIATA", a2)     # «ripagato in A2-02», ma ripaga A2-03
        self.assertIn("A2_RIMANDO_ROTTO", a2)          # A2-09 non esiste
        self.assertIn("A2_ORDINE_DEL_TEMPO", a2)       # giorno 2 poi giorno 1
        self.assertIn("A2_SENZA_SEGUITO", a2)          # SI_DETTO e NO_DETTO non pesano mai
        self.assertIn("A2_SCELTA_V1_DIMENTICATA", a2)  # BORGO_FUORI, ESULE_PRIGIONIERO
        self.assertEqual(len(r["grafo"]["atto2"]["nodi"]) > 0, True)


if __name__ == "__main__":
    unittest.main()
