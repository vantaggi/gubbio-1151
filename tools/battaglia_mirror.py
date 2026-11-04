#!/usr/bin/env python3
"""Il mirror Python della battaglia a eventi: lo stesso modello di include/battaglia.h, riga per riga.

Ripreso dal mirror del prototipo (tag prototipo-v0: tests/test_battle_engine.py) e riscritto sulla
macchina a stati nuova. Tutta l'aritmetica e' intera con troncamento verso zero, come su ARM7TDMI;
il caso e' lo stesso xorshift32. Per ogni incontro e ogni seme la sequenza di eventi deve essere
identica a quella del C++: il confronto passa dalla firma (hash FNV-1a degli eventi, numero di
eventi, round, esito, tipi emessi) che questo script scrive in include/battaglia_attese.h e che
src/autotest_battaglia.cpp verifica a tempo di compilazione, e che la ROM con GUBBIO_AVVIO=3 rifa'
a runtime.

    python tools/battaglia_mirror.py              # scrive include/battaglia_attese.h
    python tools/battaglia_mirror.py --controlla  # esce con 1 se non e' aggiornato
"""
import os
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
USCITA = os.path.join(RADICE, "include", "battaglia_attese.h")
SEMI = range(1, 51)

FISICO, FEDE, FIAMMA, OMBRA, NESSUNO = range(5)
ELEMENTO_DEBOLE, ELEMENTO_NEUTRO, ELEMENTO_RESISTE = 150, 100, 50
BOOST_SUPREMA = 3
BOOST_COSTO = [0, 25, 50, 100]
BOOST_COLPI = [1, 1, 2, 1]
BOOST_DANNO = [100, 150, 100, 350]
BOOST_SCUDO_PER_COLPO = [1, 1, 1, 3]
BOOST_SOSTEGNO = [100, 200, 200, 350]
DURATA_BREAK = 2
USTIONE_CARICHE_MAX = 3
DURATA_USTIONE = 3
USTIONE_PERCENTO_MISTICO = 25
DURATA_GUARDIA = 1
FERVORE_GIORGIO_COLPITO = 15
FERVORE_UBALDO_SOSTEGNO = 20
FERVORE_ANTONIO_USTIONE = 10
VARIANZA_MINIMA, VARIANZA_PASSI = 90, 21
ROUND_MAX = 40

NEMICO_B, ALLEATO_B, SE_STESSO_B = 0, 1, 2
NESSUN_EFFETTO, USTIONE, MURO, BASTIONE, DIFESA_SU = range(5)
DIFESA_SU_PERCENTO = 50
ATTACCO, MURO_DELLA_FEDE, GIUDIZIO, FENDENTE, BASTIONE_AZZURRO, FUOCO, COLPO_NEMICO, SCUDO_DI_FORGIA, MARTELLO = range(9)
# (elemento, bersaglio, effetto, costo, potenza, danno_mistico, perforazione, priorita)
ABILITA = [
    (FISICO, NEMICO_B, NESSUN_EFFETTO, 0, 100, 0, 0, 0),
    (FEDE, ALLEATO_B, MURO, 25, 0, 0, 0, 4),
    (FEDE, NEMICO_B, NESSUN_EFFETTO, 20, 0, 35, 0, 0),
    (FISICO, NEMICO_B, NESSUN_EFFETTO, 20, 160, 0, 50, 0),
    (NESSUNO, ALLEATO_B, BASTIONE, 15, 0, 0, 0, 8),
    (FIAMMA, NEMICO_B, USTIONE, 15, 0, 40, 0, 0),
    (FISICO, NEMICO_B, NESSUN_EFFETTO, 0, 100, 0, 0, 0),
    (NESSUNO, SE_STESSO_B, DIFESA_SU, 0, 0, 0, 0, 6),
    (FISICO, NEMICO_B, NESSUN_EFFETTO, 0, 220, 0, 25, -4),
]
EROI, UBALDO, GIORGIO, ANTONIO = 3, 0, 1, 2
# (pv, fervore, attacco, difesa, mistico, resistenza, velocita, scudo, debolezza, resiste)
STATISTICHE_EROI = [
    (240, 180, 25, 45, 95, 72, 30, 0, NESSUNO, NESSUNO),
    (380, 120, 90, 80, 25, 40, 42, 0, NESSUNO, NESSUNO),
    (210, 210, 18, 28, 95, 56, 38, 0, NESSUNO, NESSUNO),
]
FERVORE_INIZIALE = [80, 45, 20]
# Con i Ceri risvegliati (CERI_RISVEGLIATI, A1-08) ogni Santo parte con questi punti percentuali in piu' del
# suo Fervore massimo, mai oltre il massimo (FERVORE_CERI di battaglia_dati.h).
FERVORE_CERI = 15
ABILITA_FIRMA = [GIUDIZIO, FENDENTE, FUOCO]
# IA a regole: (condizione, param, limite, abilita, mira, param_mira)
SEMPRE, ROUND_UGUALE, ROUND_PARI, ROUND_DISPARI = range(4)
RIPETIBILE, UNA_PER_ROUND, UNA_PER_BATTAGLIA = range(3)
MENO_DIFESA, MENO_PV, EROE, SE_STESSO = range(4)
REGOLE = [
    (SEMPRE, 0, RIPETIBILE, COLPO_NEMICO, MENO_DIFESA, 0),
    (SEMPRE, 0, RIPETIBILE, COLPO_NEMICO, MENO_PV, 0),
    (ROUND_UGUALE, 1, UNA_PER_BATTAGLIA, SCUDO_DI_FORGIA, SE_STESSO, 0),
    (ROUND_PARI, 0, UNA_PER_ROUND, MARTELLO, EROE, GIORGIO),
    (SEMPRE, 0, RIPETIBILE, COLPO_NEMICO, MENO_DIFESA, 0),
]
SCRIPT_MOB, SCRIPT_SPIA, SCRIPT_CORRADO = range(3)
SCRIPT = [(0, 1), (1, 1), (2, 3)]
# (statistiche, azioni per turno, immune al taglio, script)
NEMICI = [
    ((228, 0, 45, 40, 8, 20, 26, 2, FIAMMA, NESSUNO), 1, False, SCRIPT_MOB),
    ((456, 0, 62, 55, 12, 26, 34, 3, FEDE, FISICO), 1, False, SCRIPT_MOB),
    ((1520, 0, 95, 60, 20, 30, 22, 4, FIAMMA, FISICO), 2, True, SCRIPT_CORRADO),
    ((180, 0, 50, 30, 10, 22, 44, 2, FEDE, NESSUNO), 1, False, SCRIPT_SPIA),
    ((300, 0, 40, 30, 30, 40, 30, 2, FEDE, FISICO), 1, False, SCRIPT_SPIA),
    ((520, 0, 60, 62, 10, 22, 24, 3, FIAMMA, FISICO), 1, False, SCRIPT_MOB),
    ((300, 0, 56, 36, 16, 28, 46, 3, FEDE, NESSUNO), 1, False, SCRIPT_SPIA),
]
NEMICI_MAX = 6
INCONTRO = [[0, 0, 1], [3, 3, 3], [2], [4, 4], [5, 5], [5], [6, 3, 3]]
NOMI_INCONTRI = ["Pattuglia perugina", "Imboscata agli Stradoni", "Duello con Corrado", "Il rito della Basilica",
                 "Guerrieri della Roccia", "Guardia della fornace", "L'infiltrato delle Logge"]

(HIT, SHIELD_BREAK, BARRIER_ABSORB, GUARD_REDIRECT, FERVOR_GAIN, BURN_TICK, DEFEAT, BARRIER_UP, GUARD_UP,
 CHARGE, BREAK_SKIP, IMMUNE, FERVOR_SPEND, DEF_UP) = range(14)
EVENT_KINDS = ["HIT", "SHIELD_BREAK", "BARRIER_ABSORB", "GUARD_REDIRECT", "FERVOR_GAIN", "BURN_TICK", "DEFEAT",
               "BARRIER_UP", "GUARD_UP", "CHARGE", "BREAK_SKIP", "IMMUNE", "FERVOR_SPEND", "DEF_UP",
               # i consumabili: li usa solo il giocatore, il pilota mai (il mirror non li gioca)
               "CURA", "PURIFICA"]
TIPI_DEL_PILOTA = EVENT_KINDS.index("CURA")
IN_CORSO, VITTORIA, SCONFITTA, PARITA = range(4)
T_ABILITA, T_CARICA, T_SUPREMA = range(3)
M32 = 0xFFFFFFFF


def idiv(a, b):
    """Divisione intera C++: troncamento verso zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class Caso:
    def __init__(self, seme):
        self.stato = (seme * 2654435761 + 0x9E3779B9) & M32 or 1

    def prossimo(self):
        x = self.stato
        x ^= (x << 13) & M32
        x ^= x >> 17
        x ^= (x << 5) & M32
        self.stato = x
        return x

    def intero(self, n):
        return self.prossimo() % n


class Unita:
    def __init__(self, s, nemico):
        (self.pv, self.fervore_max, self.attacco, self.difesa, self.mistico, self.resistenza, self.velocita,
         self.scudo, self.debolezza, self.resiste) = s
        self.pv_max = self.pv
        self.scudo_max = self.scudo
        self.fervore = 0
        self.barriera = 0
        self.rotto = 0
        self.ustione_cariche = self.ustione_danno = self.ustione_turni = 0
        self.guardia = 0
        self.carica = False
        self.nemico = nemico
        self.azioni = 1
        self.immune_al_taglio = False
        self.difesa_bonus = 0
        self.script = 0
        self.ia_round = 0
        self.ia_battaglia = 0
        self.ia_round_bit = 0

    def vivo(self):
        return self.pv > 0

    def difesa_effettiva(self):
        d = idiv(self.difesa * (100 + self.difesa_bonus), 100)
        return idiv(d, 2) if self.rotto > 0 else d

    def resistenza_effettiva(self):
        return idiv(self.resistenza, 2) if self.rotto > 0 else self.resistenza


def moltiplicatore(b, elemento):
    if elemento == NESSUNO:
        return ELEMENTO_NEUTRO
    if b.debolezza == elemento:
        return ELEMENTO_DEBOLE
    return ELEMENTO_RESISTE if b.resiste == elemento else ELEMENTO_NEUTRO


def calcola_danno(a, b, ab, boost):
    elemento, _, _, _, potenza, mistico, perforazione, _ = ab
    if elemento == FISICO:
        difesa = idiv(b.difesa_effettiva() * (100 - perforazione), 100)
        danno = idiv(a.attacco * 2 - difesa, 2)
        danno = idiv(danno * potenza, 100)
    else:
        danno = mistico + idiv(a.mistico - b.resistenza_effettiva(), 2)
    danno = idiv(danno * moltiplicatore(b, elemento), 100)
    danno = idiv(danno * BOOST_DANNO[boost], 100)
    return max(1, danno)


def calcola_muro(l, boost):
    return idiv((idiv(l.mistico * 18, 10) + 12) * BOOST_SOSTEGNO[boost], 100)


class Firma:
    def __init__(self):
        self.hash = 2166136261
        self.eventi = 0
        self.round = 0
        self.esito = IN_CORSO
        self.tipi = 0
        self.lista = []      # gli eventi, per i test


class Battaglia:
    """Opzioni per le prove negative: senza_redirect toglie l'emissione di GUARD_REDIRECT.
    scudi_in_meno: quanti scudi in meno hanno i nemici (mai sotto 0), come Battaglia::ricomincia() del C++:
    Corrado ne ha uno in meno con Q-SM01 consegnata o RUFINO_ASCOLTATO (storia::scudi_in_meno()).
    ceri: i Ceri risvegliati (storia::ceri_accesi()): il Fervore iniziale sale di FERVORE_CERI punti percentuali."""

    def __init__(self, incontro, seme, senza_redirect=False, pilota_debole=False, scudi_in_meno=0, ceri=False):
        self.caso = Caso(seme)
        self.senza_redirect = senza_redirect
        self.pilota_debole = pilota_debole
        self.eroi = []
        for e in range(EROI):
            u = Unita(STATISTICHE_EROI[e], False)
            u.fervore = idiv(u.fervore_max * min(100, FERVORE_INIZIALE[e] + (FERVORE_CERI if ceri else 0)), 100)
            self.eroi.append(u)
        self.nemici = []
        for n in INCONTRO[incontro]:
            s, azioni, immune, script = NEMICI[n]
            u = Unita(s, True)
            u.azioni = azioni
            u.immune_al_taglio = immune
            u.script = script
            u.scudo = u.scudo_max = max(0, u.scudo - scudi_in_meno)
            self.nemici.append(u)
        self.firma = Firma()
        self.comandi = [None] * EROI
        self.azioni = []

    def unita(self, nemico, slot):
        return self.nemici[slot] if nemico else self.eroi[slot]

    def lato(self, nemici):
        return self.nemici if nemici else self.eroi

    def tutti_morti(self, nemici):
        return not any(u.vivo() for u in self.lato(nemici))

    def primo_vivo(self, nemici):
        for i, u in enumerate(self.lato(nemici)):
            if u.vivo():
                return i
        return -1

    def piu_ferito(self):
        scelto = -1
        for e, u in enumerate(self.eroi):
            if u.vivo() and (scelto < 0 or idiv(u.pv * 100, u.pv_max) <
                             idiv(self.eroi[scelto].pv * 100, self.eroi[scelto].pv_max)):
                scelto = e
        return scelto

    def emetti(self, kind, an, a, bn, b, quantita, pv_dopo):
        q, p = quantita & 0xFFFF, pv_dopo & 0xFFFF
        for byte in (kind, a, b, int(an), int(bn), q & 0xFF, q >> 8, p & 0xFF, p >> 8):
            self.firma.hash = ((self.firma.hash ^ byte) * 16777619) & M32
        self.firma.eventi += 1
        self.firma.tipi |= 1 << kind
        self.firma.lista.append((kind, a, b, an, bn, quantita, pv_dopo))

    def pilota(self):
        for e, eroe in enumerate(self.eroi):
            if not eroe.vivo():
                self.comandi[e] = (T_ABILITA, ATTACCO, -1, 0)
                continue
            if self.pilota_debole:
                self.comandi[e] = (T_ABILITA, ATTACCO, self.primo_vivo(True), 0)
                continue
            firma = ABILITA_FIRMA[e]
            costo_suprema = ABILITA[firma][3] + BOOST_COSTO[BOOST_SUPREMA]
            ferito = self.piu_ferito()
            serve_il_muro = (e == UBALDO and ferito >= 0 and self.eroi[ferito].barriera == 0 and
                             (idiv(self.eroi[ferito].pv * 100, self.eroi[ferito].pv_max) < 40 or self.firma.round == 2) and
                             eroe.fervore >= ABILITA[MURO_DELLA_FEDE][3])
            if eroe.carica:
                c = (T_SUPREMA, firma, self.primo_vivo(True), BOOST_SUPREMA)
            elif serve_il_muro:
                c = (T_ABILITA, MURO_DELLA_FEDE, -1, 0)
            elif self.firma.round >= 2 and eroe.fervore >= costo_suprema:
                c = (T_CARICA, firma, -1, 0)
            elif e == UBALDO:
                debole = next((n for n, u in enumerate(self.nemici) if u.vivo() and u.debolezza == FEDE), -1)
                if debole >= 0 and eroe.fervore >= 20:
                    c = (T_ABILITA, GIUDIZIO, debole, 0)
                else:
                    c = (T_ABILITA, ATTACCO, self.primo_vivo(True), 0)
            elif e == GIORGIO:
                if self.firma.round % 2 == 1 and eroe.fervore >= 15:
                    c = (T_ABILITA, BASTIONE_AZZURRO, -1, 0)
                elif eroe.fervore >= 20:
                    scelto = -1
                    for n, u in enumerate(self.nemici):
                        if u.vivo() and (scelto < 0 or u.pv < self.nemici[scelto].pv):
                            scelto = n
                    c = (T_ABILITA, FENDENTE, scelto, 0)
                else:
                    c = (T_ABILITA, ATTACCO, self.primo_vivo(True), 0)
            else:
                bersaglio = next((n for n, u in enumerate(self.nemici) if u.vivo() and u.debolezza == FIAMMA), -1)
                bersaglio = self.primo_vivo(True) if bersaglio < 0 else bersaglio
                if self.firma.round == 1:
                    c = (T_ABILITA, ATTACCO, self.primo_vivo(True), 0)
                elif eroe.fervore >= 15 + BOOST_COSTO[2]:
                    c = (T_ABILITA, FUOCO, bersaglio, 2)
                elif eroe.fervore >= 15:
                    c = (T_ABILITA, FUOCO, bersaglio, 0)
                else:
                    c = (T_ABILITA, ATTACCO, self.primo_vivo(True), 0)
            self.comandi[e] = c

    def mira(self, m, param):
        if m == EROE and 0 <= param < EROI and self.eroi[param].vivo():
            return param
        scelto = -1
        for e, eroe in enumerate(self.eroi):
            if not eroe.vivo():
                continue
            if scelto < 0 or (eroe.pv < self.eroi[scelto].pv if m == MENO_PV
                              else eroe.difesa_effettiva() < self.eroi[scelto].difesa_effettiva()):
                scelto = e
        return scelto

    def prepara_coda(self):
        self.azioni = []
        for e, eroe in enumerate(self.eroi):
            if eroe.vivo():
                c = self.comandi[e]
                priorita = 0 if c[0] == T_CARICA else ABILITA[c[1]][7]
                self.azioni.append((False, e, c, eroe.velocita + priorita))
        fine = False
        for n, nemico in enumerate(self.nemici):
            if not nemico.vivo() or fine:
                continue
            if nemico.rotto > 0:
                for _ in range(nemico.azioni):
                    self.azioni.append((True, n, (T_ABILITA, COLPO_NEMICO, -1, 0), nemico.velocita))
                continue
            nemico.ia_round += 1
            for _ in range(nemico.azioni):
                if fine:
                    break
                prima, quante = SCRIPT[nemico.script]
                for r in range(quante):
                    cond, param, limite, ab, m, param_mira = REGOLE[prima + r]
                    regge = (cond == SEMPRE or (cond == ROUND_UGUALE and nemico.ia_round == param) or
                             (cond == ROUND_PARI and nemico.ia_round % 2 == 0) or
                             (cond == ROUND_DISPARI and nemico.ia_round % 2 == 1))
                    if not regge:
                        continue
                    bit = 1 << r
                    if limite != RIPETIBILE:
                        if limite == UNA_PER_BATTAGLIA:
                            if nemico.ia_battaglia & bit:
                                continue
                            nemico.ia_battaglia |= bit
                        else:
                            if nemico.ia_round_bit & bit:
                                continue
                            nemico.ia_round_bit |= bit
                    bersaglio = n if m == SE_STESSO else self.mira(m, param_mira)
                    if bersaglio < 0:
                        fine = True
                        break
                    self.azioni.append((True, n, (T_ABILITA, ab, bersaglio, 0), nemico.velocita + ABILITA[ab][7]))
                    break
        # insertion sort stabile, decrescente
        for i in range(1, len(self.azioni)):
            chiave = self.azioni[i]
            j = i - 1
            while j >= 0 and self.azioni[j][3] < chiave[3]:
                self.azioni[j + 1] = self.azioni[j]
                j -= 1
            self.azioni[j + 1] = chiave

    def esegui(self, azione):
        an, slot, c, _ = azione
        attore = self.unita(an, slot)
        if not attore.vivo():
            return
        if attore.rotto > 0:
            self.emetti(BREAK_SKIP, an, slot, an, slot, attore.rotto, attore.pv)
            return
        tipo, ab_id, b, boost = c
        if tipo == T_CARICA or (tipo == T_SUPREMA and not attore.carica):
            attore.carica = True
            self.emetti(CHARGE, an, slot, an, slot, 0, attore.pv)
            return
        ab = ABILITA[ab_id]
        costo = ab[3] + BOOST_COSTO[boost]
        if attore.fervore < costo:
            return
        attore.fervore -= costo
        if costo > 0:
            self.emetti(FERVOR_SPEND, an, slot, an, slot, costo, attore.fervore)
        if tipo == T_SUPREMA:
            attore.carica = False
        if ab[2] == MURO:
            bersaglio = b if b >= 0 and self.eroi[b].vivo() else self.piu_ferito()
            if bersaglio < 0:
                return
            punti = calcola_muro(attore, boost)
            self.eroi[bersaglio].barriera += punti
            attore.fervore = min(attore.fervore_max, attore.fervore + FERVORE_UBALDO_SOSTEGNO)
            self.emetti(BARRIER_UP, False, slot, False, bersaglio, punti, self.eroi[bersaglio].pv)
            self.emetti(FERVOR_GAIN, False, slot, False, slot, FERVORE_UBALDO_SOSTEGNO, attore.fervore)
            return
        if ab[2] == DIFESA_SU:
            attore.difesa_bonus = DIFESA_SU_PERCENTO
            self.emetti(DEF_UP, an, slot, an, slot, DIFESA_SU_PERCENTO, attore.pv)
            return
        if ab[2] == BASTIONE:
            attore.guardia = DURATA_GUARDIA + boost
            self.emetti(GUARD_UP, False, slot, False, slot, attore.guardia, attore.pv)
            return
        lato_nemico = not an
        if boost == BOOST_SUPREMA:
            for i in range(len(self.lato(lato_nemico))):
                if self.unita(lato_nemico, i).vivo():
                    self.colpo(azione, ab, boost, i)
            return
        if b < 0 or not self.unita(lato_nemico, b).vivo():
            b = self.primo_vivo(lato_nemico)
            if b < 0:
                return
        for _ in range(BOOST_COLPI[boost]):
            if not self.unita(lato_nemico, b).vivo():
                break
            self.colpo(azione, ab, boost, b)

    def colpo(self, azione, ab, boost, slot):
        an, a_slot, _, _ = azione
        attore = self.unita(an, a_slot)
        lato_nemico = not an
        giorgio = self.eroi[GIORGIO]
        if not lato_nemico and slot != GIORGIO and giorgio.vivo() and giorgio.guardia > 0:
            if not self.senza_redirect:
                self.emetti(GUARD_REDIRECT, an, a_slot, False, slot, GIORGIO, giorgio.pv)
            slot = GIORGIO
        b = self.unita(lato_nemico, slot)
        if not b.vivo():
            return
        elemento, _, effetto = ab[0], ab[1], ab[2]
        if b.immune_al_taglio and elemento == FISICO and b.ustione_cariche == 0:
            self.emetti(IMMUNE, an, a_slot, lato_nemico, slot, 0, b.pv)
            return
        if elemento == b.debolezza and b.scudo > 0:
            b.scudo -= BOOST_SCUDO_PER_COLPO[boost]
            if b.scudo <= 0:
                b.scudo = 0
                b.rotto = DURATA_BREAK
                self.emetti(SHIELD_BREAK, an, a_slot, lato_nemico, slot, BOOST_SCUDO_PER_COLPO[boost], b.pv)
        danno = calcola_danno(attore, b, ab, boost)
        danno = idiv(danno * (VARIANZA_MINIMA + self.caso.intero(VARIANZA_PASSI)), 100)
        danno = max(1, danno)
        if b.barriera > 0:
            assorbito = min(danno, b.barriera)
            b.barriera -= assorbito
            danno -= assorbito
            self.emetti(BARRIER_ABSORB, an, a_slot, lato_nemico, slot, assorbito, b.pv)
        era_vivo = b.vivo()
        b.pv = b.pv - danno if b.pv > danno else 0
        self.emetti(HIT, an, a_slot, lato_nemico, slot, danno, b.pv)
        if era_vivo and not b.vivo():
            self.emetti(DEFEAT, an, a_slot, lato_nemico, slot, 0, 0)
        if not lato_nemico and slot == GIORGIO and elemento == FISICO and b.vivo():
            b.fervore = min(b.fervore_max, b.fervore + FERVORE_GIORGIO_COLPITO)
            self.emetti(FERVOR_GAIN, an, a_slot, False, slot, FERVORE_GIORGIO_COLPITO, b.fervore)
        if effetto == USTIONE and b.vivo():
            b.ustione_cariche = min(USTIONE_CARICHE_MAX, b.ustione_cariche + 1)
            b.ustione_danno = max(1, idiv(attore.mistico * USTIONE_PERCENTO_MISTICO, 100))
            b.ustione_turni = DURATA_USTIONE

    def fine_round(self, u, nemico, slot):
        if u.ustione_cariche > 0 and u.vivo():
            danno = u.ustione_danno * u.ustione_cariche
            u.pv = u.pv - danno if u.pv > danno else 0
            self.emetti(BURN_TICK, nemico, slot, nemico, slot, danno, u.pv)
            if not u.vivo():
                self.emetti(DEFEAT, nemico, slot, nemico, slot, 0, 0)
            if nemico and self.eroi[ANTONIO].vivo():
                antonio = self.eroi[ANTONIO]
                antonio.fervore = min(antonio.fervore_max, antonio.fervore + FERVORE_ANTONIO_USTIONE)
                self.emetti(FERVOR_GAIN, nemico, slot, False, ANTONIO, FERVORE_ANTONIO_USTIONE, antonio.fervore)
            u.ustione_turni -= 1
            if u.ustione_turni <= 0:
                u.ustione_cariche = 0
                u.ustione_turni = 0
        if u.guardia > 0:
            u.guardia -= 1
        u.ia_round_bit = 0
        if u.rotto > 0:
            u.rotto -= 1
            if u.rotto == 0:
                u.scudo = u.scudo_max

    def gioca(self):
        while True:
            self.firma.round += 1
            self.pilota()
            self.prepara_coda()
            for azione in self.azioni:
                if self.tutti_morti(True) or self.tutti_morti(False):
                    break
                self.esegui(azione)
            for n, u in enumerate(self.nemici):
                self.fine_round(u, True, n)
            for e, u in enumerate(self.eroi):
                self.fine_round(u, False, e)
            if self.tutti_morti(True):
                self.firma.esito = VITTORIA
            elif self.tutti_morti(False):
                self.firma.esito = SCONFITTA
            elif self.firma.round >= ROUND_MAX:
                self.firma.esito = PARITA
            if self.firma.esito != IN_CORSO:
                return self.firma


def gioca(incontro, seme, **opzioni):
    return Battaglia(incontro, seme, **opzioni).gioca()


PILOTI = (False, True)      # forte, debole


def tutte_le_firme():
    return {(i, s, d): gioca(i, s, pilota_debole=d) for d in PILOTI for i in range(len(INCONTRO)) for s in SEMI}


# Il duello con Corrado con uno scudo in meno (Q-SM01 o RUFINO_ASCOLTATO): 50 semi x 2 piloti, a parte
# dalle 400 battaglie di sempre, che restano quelle.
INCONTRO_CORRADO = 2


def firme_scudo_in_meno():
    return {(INCONTRO_CORRADO, s, d): gioca(INCONTRO_CORRADO, s, pilota_debole=d, scudi_in_meno=1)
            for d in PILOTI for s in SEMI}


# I Ceri risvegliati (CERI_RISVEGLIATI, A1-08): gli scontri obbligatori che vengono dopo la scena, Corrado e i
# Guerrieri della Roccia di B-03, con il Fervore iniziale piu' alto. 50 semi x 2 piloti ciascuno, a parte.
INCONTRI_CON_I_CERI = (INCONTRO_CORRADO, 4)


def firme_ceri():
    return {(i, s, d): gioca(i, s, pilota_debole=d, ceri=True)
            for d in PILOTI for i in INCONTRI_CON_I_CERI for s in SEMI}


def righe_attese(firme):
    esiti = ["IN_CORSO", "VITTORIA", "SCONFITTA", "PARITA"]
    return [f"    {{ {i}, {s}, {'true' if d else 'false'}, 0x{f.hash:08X}u, {f.eventi}, {f.round}, "
            f"Esito::{esiti[f.esito]}, 0x{f.tipi:04X}u }}," for (i, s, d), f in sorted(firme.items())]


def header(firme, scudo_in_meno=None, ceri=None):
    scudo_in_meno = firme_scudo_in_meno() if scudo_in_meno is None else scudo_in_meno
    ceri = firme_ceri() if ceri is None else ceri
    out = ["// GENERATO da tools/battaglia_mirror.py: le firme che il mirror Python trova per ogni",
           "// incontro e ogni seme. src/autotest_battaglia.cpp le confronta con il C++ (include/battaglia.h).",
           "// Non modificare a mano.",
           "#ifndef GUBBIO_BATTAGLIA_ATTESE_H",
           "#define GUBBIO_BATTAGLIA_ATTESE_H",
           "",
           "#include \"battaglia.h\"",
           "",
           "namespace gubbio::battaglia",
           "{",
           "",
           "struct Attesa",
           "{",
           "    int incontro;",
           "    uint32_t seme;",
           "    bool pilota_debole;",
           "    uint32_t hash;",
           "    int eventi;",
           "    int round;",
           "    Esito esito;",
           "    uint32_t tipi;",
           "};",
           "",
           f"inline constexpr int ATTESE_CONTEGGIO = {len(firme)};",
           "inline constexpr Attesa ATTESE[ATTESE_CONTEGGIO] = {"]
    out += righe_attese(firme)
    out += ["};", "",
            "// Il duello con Corrado con uno scudo in meno (Battaglia::ricomincia(..., scudi_in_meno = 1)).",
            f"inline constexpr int ATTESE_SCUDO_IN_MENO_CONTEGGIO = {len(scudo_in_meno)};",
            "inline constexpr Attesa ATTESE_SCUDO_IN_MENO[ATTESE_SCUDO_IN_MENO_CONTEGGIO] = {"]
    out += righe_attese(scudo_in_meno)
    out += ["};", "",
            "// Corrado e i Guerrieri di B-03 con i Ceri risvegliati (Battaglia::ricomincia(..., ceri = true)).",
            f"inline constexpr int ATTESE_CERI_CONTEGGIO = {len(ceri)};",
            "inline constexpr Attesa ATTESE_CERI[ATTESE_CERI_CONTEGGIO] = {"]
    out += righe_attese(ceri)
    out += ["};", "", "}", "", "#endif", ""]
    return "\n".join(out)


def main(argv):
    testo = header(tutte_le_firme())
    if "--controlla" in argv:
        attuale = open(USCITA, encoding="utf-8").read() if os.path.exists(USCITA) else ""
        if attuale != testo:
            print("[battaglia] include/battaglia_attese.h non e' aggiornato: python tools/battaglia_mirror.py")
            return 1
        print("[battaglia] OK: include/battaglia_attese.h aggiornato")
        return 0
    with open(USCITA, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)
    print(f"[battaglia] scritto {os.path.relpath(USCITA, RADICE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
