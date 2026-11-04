#!/usr/bin/env python3
"""Il bilanciamento della v1 (F8): gioca gli scontri del mirror (tools/battaglia_mirror.py) ai livelli
che i Santi hanno davvero in quel punto della storia, con tre piloti:

- forte: il pilota del mirror (quasi ottimo);
- medio: un giocatore plausibile, sceglie a caso fra le mosse sensate (stesso caso per ogni seme);
- debole: solo l'Attacco, sempre.

L'esperienza e la crescita si leggono da include/progressione.h, cosi' i numeri non si sdoppiano.
I risultati vanno in docs/bilanciamento.md; tests/test_bilanciamento.py controlla gli obiettivi.

    python tools/bilanciamento.py      # stampa la tabella
"""
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battaglia_mirror as M  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESSIONE = os.path.join(RADICE, "include", "progressione.h")
ORDINE_STORIA = [0, 1, 3, 4, 2]       # Pattuglia, Imboscata, Spettri, Guerrieri di B-03, Corrado (indici di INCONTRO)
QUEST = 3
# Le battaglie facoltative (F10): le tre guardie delle fornaci di Q-SM01 e l'infiltrato di Q-SP01. Con le quest
# si contano tutte, e all'inizio: il caso peggiore per il livello con cui si arriva agli scontri della storia.
FACOLTATIVI = [5, 5, 5, 6]
# Il livello piu' basso con cui si puo' affrontare una facoltativa: le fornaci si raggiungono dall'ultimatum
# (livello 1), l'infiltrato dal digiuno, dopo la Pattuglia (livello 3).
LIVELLO_FACOLTATIVI = {5: 1, 6: 3}


def leggi_tabella(nome, testo=None):
    testo = testo or open(PROGRESSIONE, encoding="utf-8").read()
    m = re.search(nome + r"\[[^\]]*\]\s*=\s*\{([^}]*)\}", testo)
    return [int(x) for x in m.group(1).split(",")]


def leggi_costante(nome, testo=None):
    testo = testo or open(PROGRESSIONE, encoding="utf-8").read()
    return int(re.search(r"inline constexpr int " + nome + r"\s*=\s*(\d+);", testo).group(1))


ESPERIENZA_QUEST = leggi_costante("ESPERIENZA_QUEST")     # ricompensa di ogni quest (docs/bilanciamento.md)


def livello(esperienza, soglie):
    return sum(1 for s in soglie if esperienza >= s)


def livelli_lungo_la_storia(esperienza_nemico=None, con_quest=False):
    """{incontro: livello con cui lo si affronta} seguendo l'ordine della storia."""
    xp_nemico = esperienza_nemico or leggi_tabella("ESPERIENZA_NEMICO")
    soglie = leggi_tabella("ESPERIENZA_PER_LIVELLO")
    xp, livelli = (ESPERIENZA_QUEST * QUEST if con_quest else 0), {}
    if con_quest:
        xp += sum(xp_nemico[n] for i in FACOLTATIVI for n in M.INCONTRO[i])
    for i in ORDINE_STORIA:
        livelli[i] = livello(xp, soglie)
        xp += sum(xp_nemico[n] for n in M.INCONTRO[i])
    return livelli


class Medio(M.Battaglia):
    """Un giocatore plausibile: usa le abilita' ma senza calcolo."""

    def pilota(self):
        rng = self.rng
        for e, eroe in enumerate(self.eroi):
            if not eroe.vivo():
                self.comandi[e] = (M.T_ABILITA, M.ATTACCO, -1, 0)
                continue
            t = rng.choice([n for n, u in enumerate(self.nemici) if u.vivo()])
            firma = M.ABILITA_FIRMA[e]
            costo = M.ABILITA[firma][3]
            if eroe.carica:
                self.comandi[e] = (M.T_SUPREMA, firma, t, M.BOOST_SUPREMA)
                continue
            if e == M.UBALDO:
                f = self.piu_ferito()
                if (f >= 0 and eroe.fervore >= M.ABILITA[M.MURO_DELLA_FEDE][3] and
                        M.idiv(self.eroi[f].pv * 100, self.eroi[f].pv_max) < 50 and rng.random() < 0.6):
                    self.comandi[e] = (M.T_ABILITA, M.MURO_DELLA_FEDE, -1, 0)
                    continue
            opz = [(M.T_ABILITA, M.ATTACCO, t, 0)]
            if eroe.fervore >= costo:
                opz += [(M.T_ABILITA, firma, t, 0)] * 2
            if e == M.GIORGIO and eroe.fervore >= M.ABILITA[M.BASTIONE_AZZURRO][3] and rng.random() < 0.25:
                opz.append((M.T_ABILITA, M.BASTIONE_AZZURRO, -1, 0))
            if eroe.fervore >= costo + M.BOOST_COSTO[M.BOOST_SUPREMA] and rng.random() < 0.3:
                opz.append((M.T_CARICA, firma, -1, 0))
            self.comandi[e] = rng.choice(opz)


def gioca(incontro, liv, pilota, seme, scudo_meno=0, ceri=False):
    crescita = leggi_tabella("CRESCITA_PERCENTO")
    base = M.STATISTICHE_EROI
    try:
        M.STATISTICHE_EROI = [tuple(v * crescita[liv - 1] // 100 if k < 6 else v for k, v in enumerate(s))
                              for s in base]
        # lo scudo in meno passa dalla stessa manopola del C++ (Battaglia::ricomincia, scudi_in_meno)
        if pilota == "medio":
            b = Medio(incontro, seme, scudi_in_meno=scudo_meno, ceri=ceri)
            b.rng = random.Random(seme * 7919)
        else:
            b = M.Battaglia(incontro, seme, pilota_debole=(pilota == "debole"), scudi_in_meno=scudo_meno, ceri=ceri)
        return b.gioca()
    finally:
        M.STATISTICHE_EROI = base


def misura(incontro, liv, pilota, semi=200, scudo_meno=0, ceri=False):
    """(percentuale di vittorie, round mediano delle vittorie)."""
    vinte = sorted(f.round for f in (gioca(incontro, liv, pilota, s, scudo_meno, ceri) for s in range(1, semi + 1))
                   if f.esito == M.VITTORIA)
    return len(vinte) * 100 // semi, (vinte[len(vinte) // 2] if vinte else None)


def main():
    for con_quest in (False, True):
        livelli = livelli_lungo_la_storia(con_quest=con_quest)
        print("con le quest" if con_quest else "senza quest")
        for i in ORDINE_STORIA:
            riga = [f"{M.NOMI_INCONTRI[i]:26} liv {livelli[i]}"]
            for p in ("forte", "medio", "debole"):
                v, r = misura(i, livelli[i], p)
                riga.append(f"{p} {v:3}% r{r}")
            if i == 2:
                v, r = misura(i, livelli[i], "medio", scudo_meno=1)
                riga.append(f"medio scudo-1 {v}% r{r}")
            print("  " + " | ".join(riga))
    print("facoltative, al livello piu' basso")
    for i, liv in LIVELLO_FACOLTATIVI.items():
        riga = [f"{M.NOMI_INCONTRI[i]:26} liv {liv}"]
        for p in ("forte", "medio", "debole"):
            v, r = misura(i, liv, p)
            riga.append(f"{p} {v:3}% r{r}")
        print("  " + " | ".join(riga))
    return 0


if __name__ == "__main__":
    sys.exit(main())
