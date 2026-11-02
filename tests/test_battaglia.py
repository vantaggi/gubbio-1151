#!/usr/bin/env python3
"""La battaglia a eventi: include/battaglia*.h contro il mirror tools/battaglia_mirror.py.

Il confronto vero fra C++ e mirror avviene in due posti: a tempo di compilazione
(src/autotest_battaglia.cpp confronta ogni battaglia con include/battaglia_attese.h) e a runtime
sul GBA (ROM con GUBBIO_AVVIO=3, che scrive una riga di log per battaglia; le righe di una corsa
in mGBA stanno in tests/dati/battaglia_mgba.txt). Qui si controlla che le firme attese siano
quelle del mirror, che le tabelle coincidano, che ogni EventKind sia emesso, che il log del GBA
torni con il mirror, e le decisioni del piano F4. Ogni controllo ha la sua prova negativa.

    python -m unittest tests.test_battaglia
"""
import copy
import importlib.util
import os
import re
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("battaglia_mirror", os.path.join(RADICE, "tools", "battaglia_mirror.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

DATI = open(os.path.join(RADICE, "include", "battaglia_dati.h"), encoding="utf-8").read()
MOTORE = open(os.path.join(RADICE, "include", "battaglia.h"), encoding="utf-8").read()
LOG_GBA = os.path.join(RADICE, "tests", "dati", "battaglia_mgba.txt")
FIRME = B.tutte_le_firme()
# I tipi che il pilota puo' emettere: tutti tranne quelli dei consumabili (CURA, PURIFICA), che
# usa solo il giocatore e che si provano a tempo di compilazione (src/autotest_oggetti.cpp).
TUTTI_I_TIPI = (1 << B.TIPI_DEL_PILOTA) - 1


def righe_tabella(testo, nome):
    """Le righe { ... } di una tabella constexpr di battaglia_dati.h, come liste di token."""
    corpo = re.search(r"inline constexpr \w+ %s\[[^\]]*\] = \{(.*?)\n\};" % nome, testo, re.S).group(1)
    return [re.findall(r"-?[\w:]+", r) for r in re.findall(r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", corpo)]


def valore(token):
    nomi = {"FISICO": B.FISICO, "FEDE": B.FEDE, "FIAMMA": B.FIAMMA, "OMBRA": B.OMBRA, "NESSUNO": B.NESSUNO,
            "NEMICO": B.NEMICO_B, "ALLEATO": B.ALLEATO_B, "USTIONE": B.USTIONE, "MURO_DELLA_FEDE": B.MURO,
            "BASTIONE": B.BASTIONE, "DIFESA_SU": B.DIFESA_SU, "SE_STESSO": B.SE_STESSO_B, "true": True, "false": False}
    t = token.split("::")[-1]
    if t in nomi:
        return nomi[t]
    return int(t)


def errori_tabelle(testo):
    """Le differenze fra le tabelle di battaglia_dati.h e quelle del mirror."""
    err = []
    effetti = {"NESSUNO": B.NESSUN_EFFETTO, "USTIONE": B.USTIONE, "MURO_DELLA_FEDE": B.MURO, "BASTIONE": B.BASTIONE,
                "DIFESA_SU": B.DIFESA_SU}
    abilita = [[effetti[t.split("::")[1]] if t.startswith("Effetto::") else valore(t) for t in r]
               for r in righe_tabella(testo, "ABILITA")]
    for i, (c, m) in enumerate(zip(abilita, B.ABILITA)):
        if tuple(c) != m:
            err.append(f"ABILITA[{i}]: C++ {tuple(c)}, mirror {m}")
    eroi = [tuple(valore(t) for t in r) for r in righe_tabella(testo, "STATISTICHE_EROI")]
    if eroi != B.STATISTICHE_EROI:
        err.append(f"STATISTICHE_EROI: C++ {eroi}, mirror {B.STATISTICHE_EROI}")
    nemici = []
    script = {"SCRIPT_MOB": B.SCRIPT_MOB, "SCRIPT_SPIA": B.SCRIPT_SPIA, "SCRIPT_CORRADO": B.SCRIPT_CORRADO}
    for r in righe_tabella(testo, "NEMICI"):
        v = [script[t] if t in script else valore(t) for t in r]
        nemici.append((tuple(v[:10]), v[10], v[11], v[12]))
    if nemici != B.NEMICI:
        err.append(f"NEMICI: C++ {nemici}, mirror {B.NEMICI}")
    for nome in ("BOOST_COSTO", "BOOST_COLPI", "BOOST_DANNO", "BOOST_SCUDO_PER_COLPO", "BOOST_SOSTEGNO", "FERVORE_INIZIALE"):
        c = [int(v) for v in re.search(r"%s\[[^\]]*\] = \{([^}]*)\}" % nome, testo).group(1).split(",")]
        if c != getattr(B, nome):
            err.append(f"{nome}: C++ {c}, mirror {getattr(B, nome)}")
    return err


def righe_log(testo):
    """Le righe BATTAGLIA del log del GBA: {(incontro, seme, pilota debole): (hash, eventi, round, esito, ok)}."""
    out = {}
    for r in testo.splitlines():
        t = r.split()
        if len(t) == 9 and t[0] == "BATTAGLIA":
            out[(int(t[1]), int(t[2]), t[3] == "1")] = (int(t[4]), int(t[5]), int(t[6]), int(t[7]), t[8] == "OK")
    return out


def errori_log(righe, firme):
    """Le battaglie in cui il log del GBA non torna con il mirror (o manca)."""
    err = []
    for chiave, f in sorted(firme.items()):
        if chiave not in righe:
            err.append(f"{chiave}: manca nel log")
        elif righe[chiave][:4] != (f.hash, f.eventi, f.round, f.esito) or not righe[chiave][4]:
            err.append(f"{chiave}: log {righe[chiave]}, mirror {(f.hash, f.eventi, f.round, f.esito)}")
    return err


def hash_eventi(lista):
    h = 2166136261
    for kind, a, b, an, bn, q, p in lista:
        q, p = q & 0xFFFF, p & 0xFFFF
        for byte in (kind, a, b, int(an), int(bn), q & 0xFF, q >> 8, p & 0xFF, p >> 8):
            h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return h


def break_annulla_tutte(lista):
    """Dopo ogni SHIELD_BREAK su Corrado, il suo round successivo ha due BREAK_SKIP (le sue due azioni)."""
    salti = [i for i, e in enumerate(lista) if e[0] == B.BREAK_SKIP and e[3]]
    rotture = [i for i, e in enumerate(lista) if e[0] == B.SHIELD_BREAK and e[4]]
    if not rotture:
        return None
    return len([i for i in salti if i > rotture[0]]) >= 2


class FirmeEMirror(unittest.TestCase):

    def test_attese_scritte_dal_mirror(self):
        with open(B.USCITA, encoding="utf-8") as f:
            self.assertEqual(f.read(), B.header(FIRME), "eseguire python tools/battaglia_mirror.py")

    def test_quattrocento_battaglie_confrontate(self):
        """4 incontri (Pattuglia Perugina, Imboscata agli Stradoni, Duello con Corrado, il rito della
        Basilica con gli Spettri del Dubbio) x 50 semi x 2 piloti."""
        self.assertEqual(len(B.INCONTRO), 4)
        self.assertEqual(len(FIRME), 4 * 50 * 2)
        self.assertEqual(len({f.hash for f in FIRME.values()}), 400, "ogni seme da' una battaglia diversa")

    def test_con_il_pilota_debole_si_perde(self):
        perse = [k for k, f in FIRME.items() if k[2] and f.esito == B.SCONFITTA]
        self.assertGreater(len(perse), 0)

    def test_negativa_pilota_forte_non_e_il_debole(self):
        """Il pilota debole sceglie davvero diversamente: stesse battaglie, firme diverse."""
        self.assertNotEqual(FIRME[(0, 1, False)].hash, FIRME[(0, 1, True)].hash)

    def test_negativa_evento_alterato(self):
        """Un evento cambiato nella sequenza cambia la firma: il confronto lo vede."""
        f = FIRME[(2, 7, False)]
        self.assertEqual(hash_eventi(f.lista), f.hash)
        lista = list(f.lista)
        k, a, b, an, bn, q, p = lista[10]
        lista[10] = (k, a, b, an, bn, q + 1, p)
        self.assertNotEqual(hash_eventi(lista), f.hash)

    def test_tabelle_uguali(self):
        self.assertEqual(errori_tabelle(DATI), [])

    def test_negativa_tabella_diversa(self):
        alterato = DATI.replace("{ 228, 0, 45, 40,  8, 20, 26, 2,", "{ 229, 0, 45, 40,  8, 20, 26, 2,")
        self.assertNotEqual(alterato, DATI)
        self.assertTrue(any(e.startswith("NEMICI") for e in errori_tabelle(alterato)))

    def test_event_kind_uguali(self):
        corpo = re.search(r"enum class EventKind : uint8_t\n\{(.*?)\};", MOTORE, re.S).group(1)
        nomi = re.findall(r"^\s+(\w+),", corpo, re.M)
        self.assertEqual(nomi, B.EVENT_KINDS + ["COUNT"])


class Copertura(unittest.TestCase):

    def test_ogni_event_kind_emesso(self):
        tipi = 0
        for f in FIRME.values():
            tipi |= f.tipi
        self.assertEqual(tipi, TUTTI_I_TIPI,
                         [B.EVENT_KINDS[k] for k in range(len(B.EVENT_KINDS)) if not tipi >> k & 1])

    def test_negativa_senza_guard_redirect(self):
        """Togliendo l'emissione di GUARD_REDIRECT la copertura diventa rossa."""
        tipi = 0
        for i in range(len(B.INCONTRO)):
            for s in B.SEMI:
                tipi |= B.gioca(i, s, senza_redirect=True).tipi
                tipi |= B.gioca(i, s, senza_redirect=True, pilota_debole=True).tipi
        self.assertNotEqual(tipi, TUTTI_I_TIPI)
        self.assertFalse(tipi >> B.GUARD_REDIRECT & 1)


class LogDelGba(unittest.TestCase):

    def setUp(self):
        with open(LOG_GBA, encoding="utf-8") as f:
            self.righe = righe_log(f.read())

    def test_log_del_gba_uguale_al_mirror(self):
        self.assertEqual(len(self.righe), 400)
        self.assertEqual(errori_log(self.righe, FIRME), [])

    def test_negativa_riga_alterata_nel_log(self):
        righe = dict(self.righe)
        h, e, r, x, ok = righe[(0, 3, False)]
        righe[(0, 3, False)] = (h ^ 1, e, r, x, ok)
        self.assertEqual(len(errori_log(righe, FIRME)), 1)

    def test_negativa_battaglia_diversa_segnata_nel_log(self):
        righe = dict(self.righe)
        h, e, r, x, _ = righe[(2, 50, False)]
        righe[(2, 50, False)] = (h, e, r, x, False)
        self.assertEqual(len(errori_log(righe, FIRME)), 1)


class DecisioniDelPiano(unittest.TestCase):

    def test_boss_due_azioni_comuni_una(self):
        self.assertEqual([n[1] for n in B.NEMICI], [1, 1, 2, 1, 1])
        self.assertIn("{ 1520, 0, 95, 60, 20, 30, 22, 4, Elemento::FIAMMA, Elemento::FISICO }, 2, true", DATI)

    def test_shield_break_annulla_entrambe(self):
        esiti = [break_annulla_tutte(FIRME[(2, s, False)].lista) for s in B.SEMI]
        self.assertTrue(any(e is not None for e in esiti))
        self.assertTrue(all(e for e in esiti if e is not None))

    def test_negativa_un_solo_salto(self):
        lista = [(B.SHIELD_BREAK, 2, 0, False, True, 1, 900), (B.BREAK_SKIP, 0, 0, True, True, 2, 900)]
        self.assertFalse(break_annulla_tutte(lista))

    def test_corrado_immune_finche_non_e_ustionato(self):
        b = B.Battaglia(2, 1)
        attacco = B.ABILITA[B.ATTACCO]
        azione = (False, B.GIORGIO, (B.T_ABILITA, B.ATTACCO, 0, 0), 0)
        b.colpo(azione, attacco, 0, 0)
        self.assertEqual(b.firma.lista[-1][0], B.IMMUNE)
        self.assertEqual(b.nemici[0].pv, 1520)
        b.nemici[0].ustione_cariche = 1
        b.colpo(azione, attacco, 0, 0)
        self.assertEqual(b.firma.lista[-1][0], B.HIT)
        self.assertLess(b.nemici[0].pv, 1520)

    def test_negativa_senza_immunita_si_ferisce(self):
        b = B.Battaglia(2, 1)
        b.nemici[0].immune_al_taglio = False
        b.colpo((False, B.GIORGIO, (B.T_ABILITA, B.ATTACCO, 0, 0), 0), B.ABILITA[B.ATTACCO], 0, 0)
        self.assertEqual(b.firma.lista[-1][0], B.HIT)

    def test_muro_sull_alleato_piu_ferito(self):
        b = B.Battaglia(0, 1)
        b.eroi[B.ANTONIO].pv = 50
        b.esegui((False, B.UBALDO, (B.T_ABILITA, B.MURO_DELLA_FEDE, -1, 0), 0))
        muro = [e for e in b.firma.lista if e[0] == B.BARRIER_UP]
        self.assertEqual(len(muro), 1)
        self.assertEqual(muro[0][2], B.ANTONIO)

    def test_negativa_muro_su_un_altro_ferito(self):
        b = B.Battaglia(0, 1)
        b.eroi[B.GIORGIO].pv = 50
        b.esegui((False, B.UBALDO, (B.T_ABILITA, B.MURO_DELLA_FEDE, -1, 0), 0))
        self.assertEqual([e for e in b.firma.lista if e[0] == B.BARRIER_UP][0][2], B.GIORGIO)

    def test_suprema_richiede_la_carica(self):
        b = B.Battaglia(0, 1)
        suprema = (False, B.UBALDO, (B.T_SUPREMA, B.GIUDIZIO, 0, B.BOOST_SUPREMA), 0)
        b.esegui(suprema)
        self.assertEqual([e[0] for e in b.firma.lista], [B.CHARGE])
        b.esegui(suprema)
        self.assertEqual([e[0] for e in b.firma.lista[1:] if e[0] == B.HIT], [B.HIT] * 3)

    def test_negativa_suprema_senza_carica_non_colpisce(self):
        b = B.Battaglia(0, 1)
        b.esegui((False, B.UBALDO, (B.T_SUPREMA, B.GIUDIZIO, 0, B.BOOST_SUPREMA), 0))
        self.assertNotIn(B.HIT, [e[0] for e in b.firma.lista])

    def test_ia_di_corrado_a_regole(self):
        """Primo round: Scudo di Forgia su se stesso (una volta); round pari: Martello d'Assedio su Giorgio."""
        f = FIRME[(2, 1, False)]
        self.assertIn(B.DEF_UP, [e[0] for e in f.lista])
        self.assertEqual([e[0] for e in f.lista].count(B.DEF_UP), 1)
        b = B.Battaglia(2, 1)
        b.firma.round = 1
        b.pilota()
        b.prepara_coda()
        abilita = [a[2][1] for a in b.azioni if a[0]]
        self.assertEqual(abilita, [B.SCUDO_DI_FORGIA, B.COLPO_NEMICO])
        b.firma.round = 2
        b.pilota()
        b.prepara_coda()
        mosse = [(a[2][1], a[2][2]) for a in b.azioni if a[0]]
        self.assertIn((B.MARTELLO, B.GIORGIO), mosse)

    def test_negativa_regola_una_per_battaglia(self):
        """Lo Scudo di Forgia e' UNA_PER_BATTAGLIA: al secondo passaggio la regola non vale piu'."""
        b = B.Battaglia(2, 1)
        b.pilota()
        b.prepara_coda()
        self.assertIn(B.SCUDO_DI_FORGIA, [a[2][1] for a in b.azioni if a[0]])
        b.nemici[0].ia_round = 0
        b.prepara_coda()
        self.assertNotIn(B.SCUDO_DI_FORGIA, [a[2][1] for a in b.azioni if a[0]])

    def test_zero_heap_array_fissi(self):
        """Il motore non usa contenitori dinamici: solo array a misura fissa."""
        for vietato in ("new ", "malloc", "std::vector", "bn::vector", "float", "double"):
            self.assertNotIn(vietato, MOTORE)

    def test_negativa_zero_heap(self):
        self.assertIn("bn::vector", MOTORE.replace("Evento _eventi[", "bn::vector<Evento, 8> _eventi["))


if __name__ == "__main__":
    unittest.main(verbosity=2)
