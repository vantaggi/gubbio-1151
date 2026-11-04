#!/usr/bin/env python3
"""Revisione redazionale dei testi a schermo (Cioti, 4 nov 2026: «è importantissima la coerenza e
anche la revisione dei testi»).

Legge le stesse voci del generatore (testi/*.testi, compreso copione.testi che viene dal copione) e
controlla quello che il generatore non controlla: la tipografia, il lessico del 1151 e la coerenza
delle parole. Che il testo stia nei riquadri lo controlla gia' tools/genera_testi.py (a capo in
pixel col font vero); i nomi ritirati tests/test_nomi_coerenti.py; i «San» dei protagonisti
tests/test_nomi_santi.py.

    python -m unittest tests.test_redazione
"""
import importlib.util
import os
import re
import unittest

from _stile import RADICE

_spec = importlib.util.spec_from_file_location("genera_testi", os.path.join(RADICE, "tools", "genera_testi.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

# Le frasi di prova del font e le etichette dell'autotest non sono testi del gioco.
FUORI = {"prova.testi"}

LETTERA = r"A-Za-zÀ-ÖØ-öø-ÿ"

# --- tipografia ------------------------------------------------------------------------------
TIPOGRAFIA = [
    (re.compile(r"  "), "doppio spazio"),
    (re.compile(r"^\s|\s$"), "spazio in testa o in coda"),
    (re.compile(r" [,.;:!?…]"), "spazio prima della punteggiatura"),
    (re.compile(rf"[,;:!?](?=[{LETTERA}«])"), "manca lo spazio dopo la punteggiatura"),
    (re.compile(rf"(?<![.\d])\.(?=[{LETTERA}«])"), "manca lo spazio dopo il punto"),
    (re.compile(r"(?<!\.)\.\.(?!\.)|\.{4,}"), "puntini di sospensione: sempre tre"),
    (re.compile(r'"'), "virgolette dritte: si usano le caporali « »"),
    (re.compile(r"« | »"), "spazio dentro le caporali"),
    (re.compile(r"[!?]{2,}"), "punteggiatura doppia"),
    (re.compile(rf"\b([{LETTERA}]+) \1\b", re.IGNORECASE), "parola ripetuta"),
    (re.compile(r"\bE'|\be'(?= )"), "«è» scritto con l'apostrofo"),
    (re.compile(r"\bpo\b(?!')|\bpò\b"), "«po'» si scrive con l'apostrofo"),
    (re.compile(r"\bqual'è\b|\bqual'era\b", re.IGNORECASE), "«qual è» senza apostrofo"),
    (re.compile(r"\b[Ss]e stess"), "«sé stesso» con l'accento"),
    (re.compile(r"\b[Nn]e (?:io|tu|lui|lei|noi|voi|loro)\b"), "«né» negazione con l'accento"),
    (re.compile(r"\bperchè\b|\bpoichè\b|\bbenchè\b|\bnè\b|\bsè\b", re.IGNORECASE), "accento: «perché», «né», «sé»"),
]

# --- lessico del 1151 --------------------------------------------------------------------------
# Parole che nel 1151 non esistono o tradiscono il gioco moderno. La battuta delle patate di Masio
# il Romano e' una battuta voluta: lo dice lui stesso, che non ci stanno.
ANACRONISMI = [
    (re.compile(r"\b(?:chilometr|kilometr|centimetr|millimetr)\w*|\bmetri\b|\bkm\b", re.IGNORECASE), "misure metriche: miglia, passi, spanne"),
    (re.compile(r"\bminut[oi]\b|\bsecond[oi] (?:fa|dopo)\b", re.IGNORECASE), "minuti e secondi: ore, vespri, un fiato"),
    (re.compile(r"\b(?:ciao|okay|ok)\b", re.IGNORECASE), "saluto o parola moderna"),
    (re.compile(r"\b(?:pomodor|tabacc|sigar|caff[eè]|cioccolat|mais\b|fucil|pistol|cannon|polvere da sparo)\w*", re.IGNORECASE), "cosa che nel 1151 non c'e'"),
    (re.compile(r"\b[Pp]odest[àa]\b"), "il podesta' viene dopo: Guido e' console"),
    (re.compile(r"\bacquedott\w*", re.IGNORECASE), "nel gioco e' sempre «il condotto»"),
]
ECCEZIONI_LESSICO = {"NPC_18_02"}  # Masio: «Co' le patate no, che non ci stanno.»

# --- coerenza delle parole ---------------------------------------------------------------------
# «vescovo» e i titoli si scrivono minuscoli dentro la frase; il nome del parlante (PARLANTE_*)
# e' un'etichetta e resta com'e' («Console Guido»).
TITOLO_MAIUSCOLO = re.compile(r"(?<=[^.!?…«\s] )(?<!dei )\b(?:Vescovo|Console|Consoli|Cavaliere|Eremita|Monsignore)\b")
# Il nome di un oggetto o di un nemico si scrive all'italiana: maiuscola solo all'inizio e nei
# nomi propri («Crescia di Pasqua», «Biscotti all'anice», «Pattuglia perugina»).
AGGETTIVI_MAIUSCOLI = re.compile(r"\b(?:Pattuglia|Biscotti all'|Crescia sotto la) ?(?:Perugin\w+|Anice|Cenere)\b")

# «Ricevi 3 Crescia di Pasqua»: il nome dell'oggetto e' singolare, il numero no.
PLURALE_SBAGLIATO = re.compile(r"\b(?:[2-9]|\d{2,}) (?:Crescia|Biscotto|Baccal)")


def voci():
    for nome, dati in G.sorgenti_del_repo():
        if os.path.basename(nome) in FUORI:
            continue
        for id_, contesto, testo, riga in G.leggi_voci(nome, dati):
            yield os.path.basename(nome), id_, contesto, testo


def problemi(id_, testo):
    trovati = [m for r, m in TIPOGRAFIA if r.search(testo)]
    if id_ not in ECCEZIONI_LESSICO:
        trovati += [m for r, m in ANACRONISMI if r.search(testo)]
    if not id_.startswith("PARLANTE_") and TITOLO_MAIUSCOLO.search(testo):
        trovati.append("titolo maiuscolo dentro la frase")
    if AGGETTIVI_MAIUSCOLI.search(testo):
        trovati.append("maiuscola all'inglese nel nome")
    if PLURALE_SBAGLIATO.search(testo):
        trovati.append("numero e nome non concordano")
    if testo.count("«") != testo.count("»"):
        trovati.append("caporali spaiate")
    return trovati


class Redazione(unittest.TestCase):

    def test_ci_sono_testi(self):
        self.assertGreater(len(list(voci())), 500)

    def test_nessun_problema_redazionale(self):
        errori = [f"{f} {i}: {', '.join(p)}: {t}" for f, i, _, t in voci() if (p := problemi(i, t))]
        self.assertEqual(errori, [], "\n" + "\n".join(errori))

    def test_stesso_id_stesso_testo_fra_copione_e_regia(self):
        """C_* (la battuta nella scena) e R_* (la stessa battuta nella cutscene) dicono la stessa cosa."""
        tutte = {i: t for _, i, _, t in voci()}
        diverse = [i for i, t in tutte.items() if i.startswith("R_") and ("C_" + i[2:]) in tutte
                   and tutte["C_" + i[2:]] != t]
        self.assertEqual(diverse, [])

    def test_fine_della_cronaca_coerente(self):
        """La scritta di fine della ROM e la didascalia dell'epilogo usano le stesse parole."""
        tutte = {i: t for _, i, _, t in voci()}
        self.assertTrue(tutte["STORIA_FINE"].startswith("Fine del primo atto."), tutte["STORIA_FINE"])

    # --- prove negative ---------------------------------------------------------------------

    def test_negativa_tipografia(self):
        for brutto in ["Ciao  mondo.", "Fermo ,ragazzo.", "Fermo,ragazzo.", "Aspetta..", "Aspetta....",
                       'Disse "no".', "Chi va là??", "Il il vescovo.", "Un po di pane.", "Perchè?",
                       "« Ciao»", "Fine.Poi"]:
            self.assertTrue(problemi("X", brutto), brutto)

    def test_negativa_lessico(self):
        for brutto in ["Due chilometri di salita.", "Aspetta un minuto.", "Ok, andiamo.",
                       "Il Podestà ha parlato.", "Il disegno dell'acquedotto.", "Un fucile."]:
            self.assertTrue(problemi("X", brutto), brutto)

    def test_negativa_maiuscole(self):
        for brutto in ["Grazie, Vescovo Ubaldo.", "Ricevi 3 Biscotti all'Anice.", "Pattuglia Perugina",
                       "Ricevi 3 Crescia di Pasqua.", "Il Vescovo dorme."]:
            self.assertTrue(problemi("X", brutto), brutto)

    def test_positiva_testi_giusti(self):
        for buono in ["Vescovo! Aprite.", "Monsignore... undici stendardi.", "Il 1151. Poi?",
                      "«Alba», disse.", "Fra' Bernardo, un po' di pane.", "Quasi due miglia di sterrato.",
                      "Ricevi 3 fette di Crescia di Pasqua.", "Console Guido", "Va'. Di' al tuo signore.",
                      "Due passi per via dei Consoli", "Vescovo Ubaldo! Aprite."]:
            self.assertEqual(problemi("X", buono), [], buono)


if __name__ == "__main__":
    unittest.main()
