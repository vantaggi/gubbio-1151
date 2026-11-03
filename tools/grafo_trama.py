#!/usr/bin/env python3
"""Il grafo della trama: dice se la storia regge (buchi, vicoli ciechi, battute che non si sentono mai).

Legge il copione con lo stesso lettore del gioco (tools/genera_storia.py: scene, condizioni, varianti,
scelte, NPC per fase) e lo fa girare con le regole di include/storia_logica.h: una scena parte entrando
nella sua area se le bandiere richieste sono accese, nessuna vietata e quella che segue e' fatta; la fase
degli NPC viene dalle bandiere; salire agli Stradoni nel digiuno senza aver deciso del borgo vale
BORGO_FUORI. Visita TUTTI gli stati raggiungibili (ogni ordine delle scene, ogni voce di ogni scelta, ogni
NPC ascoltato o no) e da li' trova:

  ERRORE  scena mai raggiungibile; vicolo cieco (uno stato da cui i titoli di coda non si raggiungono
          piu'); bandiera letta ma che niente accende; battuta che nessun percorso recita; bandiera
          scritta male; condizione del copione che il lettore non capisce.
  AVVISO  battuta che si sente solo dopo i titoli di coda; bandiera accesa che nessuno legge; scelta
          che non pesa dopo la sua scena; bandiera promessa nel testo che il gioco non vede.
  NOTA    cose da sapere (quest descritte ma non ancora nel motore, bandiere che legge solo il codice).

Legge anche la scaletta dell'Atto II (storia/ATTO_II_SCALETTA.md, se c'e'): scene A2-, bandiere che
accendono e leggono, scelte, ordine dei giorni, rimandi fra scene, coerenza con la v1.

    python3 tools/grafo_trama.py                          # il copione del repo; esce 1 se ci sono ERRORI
    python3 tools/grafo_trama.py --copione DIR --atto2 F  # un altro copione (es. /mnt/project-files)
    python3 tools/grafo_trama.py --json G.json --md R.md  # il grafo e il rapporto
"""
import argparse
import json
import os
import re
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genera_storia as GS  # noqa: E402

RADICE = GS.RADICE
ERRORE, AVVISO, NOTA = "ERRORE", "AVVISO", "NOTA"
FINE = "CRONACA_V1_FINITA"
TUTTE_NOTE = set(GS.BANDIERE) | set(GS.BANDIERE_QUEST)
FILE_COPIONE = GS.FILE_SCENE + (GS.FILE_NPC, "04_quest.md", GS.FILE_AMICI)
# Le bandiere che accende il gioco da solo (storia_logica.h, all_ingresso).
ACCESE_DAL_GIOCO = {"BORGO_FUORI": "storia::all_ingresso(): salire agli Stradoni nel digiuno senza aver deciso del borgo"}


def problema(gravita, codice, dove, testo, proposta=""):
    return {"gravita": gravita, "codice": codice, "dove": dove, "testo": testo, "proposta": proposta}


# --- il modello del copione v1 ---------------------------------------------------------------------------

def nome(i):
    return GS.TUTTE[i]


def vale(g, accese, scelta):
    """storia::vale() con le bandiere per nome. La Crescia c'e' (il gioco ne da' 2 all'inizio)."""
    tipo = g[0]
    if tipo == "SEMPRE":
        return True
    if tipo in ("BANDIERA", "VARIANTE_BANDIERA"):
        return nome(g[1]) in accese
    if tipo in ("NON_BANDIERA", "VARIANTE_NON_BANDIERA"):
        return nome(g[1]) not in accese
    if tipo == "SCELTA":
        return scelta == g[1]
    if tipo == "ALMENO_DUE":
        return sum(nome(i) in accese for i in g[1:]) >= 2
    if tipo == "OGGETTO_E_NON_BANDIERA":
        return nome(g[2]) not in accese
    raise ValueError(tipo)


def bandiere_della_guardia(g):
    if g[0] in ("BANDIERA", "VARIANTE_BANDIERA", "NON_BANDIERA", "VARIANTE_NON_BANDIERA"):
        return [nome(g[1])]
    if g[0] == "ALMENO_DUE":
        return [nome(i) for i in g[1:]]
    if g[0] == "OGGETTO_E_NON_BANDIERA":
        return [nome(g[2])]
    return []


def fase(accese):
    if "RIENTRO_PORTA_METAURO" in accese:
        return "NOTTE"
    return "DIGIUNO" if "CITTA_IN_DIGIUNO" in accese else "ULTIMATUM"


def carica_v1(cartella):
    """Le scene e gli NPC dal lettore del gioco, piu' il testo grezzo dei file (per i controlli sul testo)."""
    vecchia = GS.COPIONE
    GS.COPIONE = cartella
    try:
        scene, npc = GS.leggi_copione()
    finally:
        GS.COPIONE = vecchia
    testi = {}
    for f in FILE_COPIONE:
        p = os.path.join(cartella, f)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as t:
                testi[f] = t.read()
    for i, s in enumerate(scene):
        s["i"] = i
        s["area"] = GS.AREE.get(s["codice"], "?") or "SCHERMO_INTERO"
        for k, b in enumerate(s["battute"]):
            b["id"] = f"{s['codice']}#{k}"
    for p in npc:
        for k, b in enumerate(p["frasi"]):
            b["id"] = f"{p['nome']}#{k}"
            b["dove"] = riga_di(testi, b["frase"]) or b["dove"]
    return {"scene": scene, "npc": npc, "testi": testi}


def riga_di(testi, frase):
    """file:riga della battuta (il lettore del gioco segna gli amici come 03_npc_ambiente.md)."""
    for f in (GS.FILE_AMICI, GS.FILE_NPC):
        for n, r in enumerate(testi.get(f, "").splitlines(), 1):
            if r.startswith("- ") and r.rstrip().endswith(frase):
                return f"{f}:{n}"
    return None


def recita(battute, accese):
    """Ogni modo di recitare queste battute: [(bandiere alla fine, ids dette, voci scelte)]."""
    esiti = []

    def giro(k, accese, scelta, dette, voci):
        while k < len(battute):
            b = battute[k]
            if vale(b["guardia"], accese, scelta):
                if b["voci"]:
                    for v in (0, 1):
                        a = b["accende"][v]
                        giro(k + 1, accese | ({nome(a)} if a != GS.NESSUNA else set()), v, dette + [b["id"]],
                             voci + [(b["id"], b["voci"][v])])
                    return
                dette = dette + [b["id"]]
            k += 1
        esiti.append((frozenset(accese), dette, voci))

    giro(0, frozenset(accese), -1, [], [])
    return esiti


def frasi_npc(p, accese):
    """Le battute di un NPC nella fase di oggi: la prima variante che vale, o le altre in ordine."""
    f = fase(accese)
    della_fase = [b for b in p["frasi"] if b["fase"] == f]
    for b in della_fase:
        if b["guardia"][0].startswith("VARIANTE") and vale(b["guardia"], accese, -1):
            return [b]
    return [b for b in della_fase if not b["guardia"][0].startswith("VARIANTE")]


def esplora(m):
    """Tutti gli stati raggiungibili. Uno stato e' (bandiere accese, scene fatte). Le azioni: entrare in
    un'area (parte la prima scena pronta, come storia::prossima_scena), salire agli Stradoni, parlare
    con un NPC. Dopo i titoli di coda il giro continua (il gioco torna alla mappa), ma si segna a parte."""
    scene, npc = m["scene"], m["npc"]
    aree = []
    for s in scene:
        if s["area"] not in aree:
            aree.append(s["area"])
    inizio = (frozenset(), frozenset())
    padre = {inizio: None}
    coda = deque([inizio])
    dette_prima, dette_dopo, dette_trama = set(), set(), set()
    passi = []          # (stato, azione, stato dopo, scena giocata o None)
    voci_viste = {}     # id della scelta -> {voce: stati dopo}

    def pronta(s, accese, fatte):
        return (s["codice"] not in fatte and set(s["richieste"]) <= accese and not set(s["vietate"]) & accese
                and (s["codice"] not in GS.SEGUE or GS.SEGUE[s["codice"]] in fatte))

    while coda:
        stato = coda.popleft()
        accese, fatte = stato
        finita = FINE in accese
        uscite = []
        for area in aree:
            a = set(accese)
            if area == "MONTE_INGINO" and "CITTA_IN_DIGIUNO" in a and not {"BORGO_DENTRO", "BORGO_FUORI"} & a:
                a.add("BORGO_FUORI")
            s = next((s for s in scene if s["area"] == area and pronta(s, a, fatte)), None)
            if s is None:
                if a != accese:
                    uscite.append(("sale agli Stradoni (il borgo resta fuori)", (frozenset(a), fatte), None, [], []))
                continue
            for fin, dette, voci in recita(s["battute"], a):
                fin = fin | set(s["imposta"])
                etichetta = f"scena {s['codice']}" + "".join(f" «{v}»" for _, v in voci)
                uscite.append((etichetta, (frozenset(fin), fatte | {s["codice"]}), s["codice"], dette, voci))
        for p in npc:
            f = fase(accese)
            for fin, dette, voci in recita(frasi_npc(p, accese), accese):
                if p["imposta"] is not None and p["imposta_fasi"] & (1 << GS.FASI.index(f)):
                    fin = fin | {nome(p["imposta"])}
                if dette and (fin != accese or voci or not finita):
                    etichetta = f"parla con {p['nome']}" + "".join(f" «{v}»" for _, v in voci)
                    uscite.append((etichetta, (frozenset(fin), fatte), None, dette, voci))
        for etichetta, dopo, codice, dette, voci in uscite:
            (dette_dopo if finita else dette_prima).update(dette)
            if not finita and "ATTO_I_COMPLETATO" not in accese:
                dette_trama.update(dette)
            for idb, v in voci:
                voci_viste.setdefault(idb, set()).add(v)
            if dopo != stato:
                passi.append((stato, etichetta, dopo, codice))
            if dopo not in padre:
                padre[dopo] = (stato, etichetta)
                coda.append(dopo)
    return {"stati": set(padre), "padre": padre, "passi": passi, "dette_prima": dette_prima,
            "dette_dopo": dette_dopo, "dette_trama": dette_trama, "voci": voci_viste}


def percorso(e, stato, massimo=40):
    azioni = []
    while e["padre"][stato] is not None:
        stato, a = e["padre"][stato]
        if not a.startswith("parla con") or "«" in a:
            azioni.append(a)
    azioni.reverse()
    return azioni[-massimo:]


def chi_legge(m):
    """bandiera -> [(dove, come)] per tutte le letture del motore."""
    letture = {}

    def leggi(b, dove, come):
        letture.setdefault(b, []).append((dove, come))

    for s in m["scene"]:
        for b in s["richieste"]:
            leggi(b, s["codice"], "condizione")
        for b in s["vietate"]:
            leggi(b, s["codice"], "condizione (vietata)")
        for x in s["battute"]:
            for b in bandiere_della_guardia(x["guardia"]):
                leggi(b, s["codice"], "variante di battuta")
    for p in m["npc"]:
        for x in p["frasi"]:
            for b in bandiere_della_guardia(x["guardia"]):
                leggi(b, p["nome"], f"battuta {x['fase']}")
    for b, dove in GS.LETTE_DAL_GIOCO.items():
        leggi(b, "codice del gioco", dove)
    for b in ("CITTA_IN_DIGIUNO", "RIENTRO_PORTA_METAURO"):
        leggi(b, "fase degli NPC", "storia::fase_npc()")
    for b in ("BORGO_DENTRO", "BORGO_FUORI"):
        leggi(b, "codice del gioco", "storia::all_ingresso() e gli NPC del borgo")
    return letture


def chi_accende(m):
    accensioni = {}

    def accendi(b, dove, come):
        accensioni.setdefault(b, []).append((dove, come))

    for s in m["scene"]:
        for b in s["imposta"]:
            accendi(b, s["codice"], "fine della scena")
        for x in s["battute"]:
            if x["voci"]:
                for v in (0, 1):
                    if x["accende"][v] != GS.NESSUNA:
                        accendi(nome(x["accende"][v]), s["codice"], f"scelta «{x['voci'][v]}»")
    for p in m["npc"]:
        if p["imposta"] is not None:
            accendi(nome(p["imposta"]), p["nome"], "parlandoci")
        for x in p["frasi"]:
            if x["voci"]:
                for v in (0, 1):
                    if x["accende"][v] != GS.NESSUNA:
                        accendi(nome(x["accende"][v]), p["nome"], f"scelta «{x['voci'][v]}»")
    for b, dove in ACCESE_DAL_GIOCO.items():
        accendi(b, "codice del gioco", dove)
    return accensioni


RIGHE_CAPITE = [r"^(?:Se|Con) «(.+?)»(.*):$", r"^Se almeno due indizi:$", r"^Se `([A-Z_0-9]+)`(, al posto della battuta di \w+)?.*:$",
                r"^Altrimenti:$", r"^Poi, per tutti:$", r"almeno una Crescia di Pasqua e non c'è `([A-Z_0-9]+)`"]


def controlla_v1(m, e):
    pr = []
    scene, npc = m["scene"], m["npc"]
    giocate = {c for _, _, _, c in e["passi"] if c}
    letture, accensioni = chi_legge(m), chi_accende(m)
    finali = [s for s in e["stati"] if FINE in s[0]]

    # 1. scene mai raggiungibili
    for s in scene:
        if s["codice"] not in giocate:
            pr.append(problema(ERRORE, "SCENA_IRRAGGIUNGIBILE", s["codice"],
                               f"«{s['titolo']}» non parte in nessun percorso (richiede {s['richieste'] or 'niente'}, "
                               f"vieta {s['vietate'] or 'niente'}).", "Controllare la riga Condizione o chi accende quelle bandiere."))

    # 1b. scene che possono partire in un altro momento della storia (fase diversa, o dopo i titoli)
    fasi_di = {}
    for a, _, _, c in e["passi"]:
        if c:
            fasi_di.setdefault(c, set()).add("DOPO I TITOLI" if FINE in a[0] else fase(a[0]))
    for s in scene:
        f = fasi_di.get(s["codice"], set())
        if len(f) > 1:
            ordine = [x for x in GS.FASI + ["DOPO I TITOLI"] if x in f]
            pr.append(problema(AVVISO, "SCENA_FUORI_TEMPO", s["codice"],
                               f"«{s['titolo']}» può partire in fasi diverse: {', '.join(ordine)} (se il giocatore non passa da "
                               f"{s['area']} quando la storia se lo aspetta).",
                               "Aggiungere un divieto (es. «e non `CITTA_IN_DIGIUNO`») o verificare che la mappa obblighi il passaggio."))

    # 2. vicoli ciechi: stati da cui i titoli non si raggiungono piu'
    avanti = {}
    for a, _, b, _ in e["passi"]:
        avanti.setdefault(b, set()).add(a)
    salvi = set(finali)
    coda = deque(finali)
    while coda:
        x = coda.popleft()
        for y in avanti.get(x, ()):
            if y not in salvi:
                salvi.add(y)
                coda.append(y)
    ciechi = [s for s in e["stati"] if s not in salvi]
    if not finali:
        pr.append(problema(ERRORE, "NESSUN_FINALE", "storia", "Nessun percorso arriva ai titoli di coda.", ""))
    elif ciechi:
        # i piu' "corti": quelli senza uscite verso stati nuovi
        primi = sorted(ciechi, key=lambda s: (len(s[1]), len(s[0])))[:3]
        for s in primi:
            pr.append(problema(ERRORE, "VICOLO_CIECO", ", ".join(sorted(s[1])) or "inizio",
                               f"Da qui i titoli di coda non si raggiungono più ({len(ciechi)} stati così). Bandiere: "
                               f"{sorted(s[0])}. Percorso: {' → '.join(percorso(e, s))}.", "Aggiungere una scena o togliere un divieto."))

    # 3. bandiere lette che niente accende, e accese che nessuno legge
    for b in sorted(letture):
        if b not in accensioni and b in TUTTE_NOTE:
            dove = sorted({d for d, _ in letture[b]})
            pr.append(problema(ERRORE, "BANDIERA_MAI_ACCESA", ", ".join(dove),
                               f"`{b}` è letta ({', '.join(c for _, c in letture[b][:3])}) ma niente nel copione la accende.",
                               "Aggiungerla all'Imposta della scena giusta, o a un NPC."))
    for b in sorted(accensioni):
        if b in letture:
            continue
        dove = ", ".join(sorted({d for d, _ in accensioni[b]}))
        if b in GS.DA_FARE:
            pr.append(problema(NOTA, "BANDIERA_DA_FARE", dove, f"`{b}` è accesa ma il gioco non la legge ancora (docs/bandiere_da_fare.md).", ""))
        else:
            pr.append(problema(AVVISO, "BANDIERA_MAI_LETTA", dove, f"`{b}` è accesa ma nessuna scena, battuta o codice la legge.",
                               "Darle una conseguenza o toglierla."))

    # 4. l'ultima scena: parte da sola dopo quella che la sblocca, o bisogna camminare fin li'?
    finale = next((s for s in scene if FINE in s["imposta"]), {"codice": None, "area": None, "richieste": []})
    prima = [s for s in scene if set(finale["richieste"]) & set(s["imposta"])]
    for s in prima:
        if s["area"] != finale["area"]:
            pr.append(problema(AVVISO, "EPILOGO_A_PIEDI", f"{s['codice']} → {finale['codice']}",
                               f"{finale['codice']} («{finale['titolo']}») parte solo entrando in {finale['area']}, ma {s['codice']} "
                               f"finisce in {s['area']}: dopo {s['codice']} il giocatore deve camminare fin lì, con gli NPC "
                               "nella fase NOTTE.", f"Far partire {finale['codice']} subito dopo {s['codice']} (scena a schermo "
                               "intero, come il prologo) o scrivere il tragitto."))
    # 5. battute che non si sentono mai, o solo dopo i titoli
    def tutte_le_battute():
        for s in scene:
            for b in s["battute"]:
                yield s["codice"], b
        for p in npc:
            for b in p["frasi"]:
                yield p["nome"], b
    for dove, b in tutte_le_battute():
        if b["id"] in e["dette_trama"] or dove == finale["codice"]:
            continue
        cosa = f"{b['chi']}{' (' + b['fase'] + ')' if b['fase'] else ''}: «{b['frase'][:70]}»"
        guardia = ", ".join(bandiere_della_guardia(b["guardia"])) or b["guardia"][0]
        if b["id"] in e["dette_prima"]:
            pr.append(problema(AVVISO, "BATTUTA_SOLO_NELL_EPILOGO", f"{dove} ({b['dove']})",
                               f"{cosa} si sente solo fra la terza alba e la vetrata, camminando fino a {finale['area']} per "
                               f"{finale['codice']} (guardia: {guardia}).",
                               "Decidere se fra E-01 ed E-02 si gioca: se no, E-02 deve partire subito e la battuta va spostata."))
        elif b["id"] in e["dette_dopo"]:
            pr.append(problema(AVVISO, "BATTUTA_DOPO_I_TITOLI", f"{dove} ({b['dove']})",
                               f"{cosa} si sente solo dopo i titoli di coda (guardia: {guardia}).",
                               "Spostare la battuta in una fase che il giocatore vive prima della fine, o accettarla come post-gioco."))
        else:
            pr.append(problema(ERRORE, "BATTUTA_IRRAGGIUNGIBILE", f"{dove} ({b['dove']})",
                               f"{cosa} non si sente in nessun percorso (guardia: {guardia}).",
                               "Cambiare la guardia o la fase, o toglierla."))

    # 5. scelte che non pesano dopo la loro scena (prima dei titoli)
    lette_prima = {}
    for dove, b in tutte_le_battute():
        if b["id"] in e["dette_trama"]:
            for f in bandiere_della_guardia(b["guardia"]):
                lette_prima.setdefault(f, set()).add(dove)
    for s in scene:
        lette_prima_scene = {f for f in s["richieste"] + s["vietate"]}
        for f in lette_prima_scene:
            lette_prima.setdefault(f, set()).add(s["codice"])
    for dove, b in tutte_le_battute():
        if not b["voci"]:
            continue
        for v in (0, 1):
            if b["accende"][v] == GS.NESSUNA:
                continue
            f = nome(b["accende"][v])
            altrove = (lette_prima.get(f, set()) - {dove}) | ({"codice del gioco"} if f in GS.LETTE_DAL_GIOCO else set())
            if not altrove:
                pr.append(problema(AVVISO, "SCELTA_SENZA_SEGUITO", dove,
                                   f"La voce «{b['voci'][v]}» accende `{f}`, ma prima dei titoli nessuno la legge fuori da {dove}: "
                                   "la scelta pesa solo nelle battute subito dopo.",
                                   "Va bene se la conseguenza è nell'Atto II; altrimenti darle un'eco nella v1."))

    # 6. bandiere nel testo: scritte male, o promesse che il motore non vede
    viste_dal_motore = set(letture) | set(accensioni)
    for f, testo in m["testi"].items():
        for n, riga in enumerate(testo.splitlines(), 1):
            if riga.startswith("| Battaglia"):
                continue        # i nomi degli incontri (enemy_data.h), non bandiere
            for b in re.findall(r"`([A-Z][A-Z_0-9]{3,})`", riga):
                if b not in TUTTE_NOTE:
                    if b.isupper() and "_" in b:
                        pr.append(problema(ERRORE, "BANDIERA_SCONOSCIUTA", f"{f}:{n}", f"`{b}` non è una bandiera del gioco.",
                                           "Refuso, o va aggiunta alle bandiere (genera_storia.py)."))
                elif b not in viste_dal_motore:
                    g = NOTA if f == "04_quest.md" else AVVISO
                    pr.append(problema(g, "PROMESSA_NEL_TESTO", f"{f}:{n}",
                                       f"Il testo parla di `{b}`, ma il motore della storia non la accende né la legge"
                                       f"{' (le quest arrivano in F6 parte 2)' if g == NOTA else ''}: «{riga.strip()[:90]}».", ""))

    # 7b. condizioni di scena con un pezzo in prosa, che il motore ignora
    for f in GS.FILE_SCENE:
        codice = None
        for n, riga in enumerate(m["testi"].get(f, "").splitlines(), 1):
            h = re.match(r"^## ([A-Z0-9]+-\d+[a-z]?) · ", riga)
            if h:
                codice = h.group(1)
            c = re.match(r"^\| Condizione \| (.+) \|$", riga)
            if c and codice not in GS.SEGUE and codice != "P-00":
                resto = re.sub(r"`[A-Z_0-9]+`|\([^)]*\)", " ", c.group(1))
                resto = [w for w in re.findall(r"[\wàèéìòù']+", resto) if w.lower() not in ("e", "non", "né", "o")]
                if resto and not re.match(r"^(segue|dopo|accensione|avvio)", " ".join(resto).lower()):
                    pr.append(problema(AVVISO, "CONDIZIONE_IN_PROSA", f"{f}:{n}",
                                       f"La condizione «{c.group(1)}» ha una parte in prosa («{' '.join(resto)}») che il gioco ignora.",
                                       "Trasformarla in una bandiera, o toglierla dalla condizione."))

    # 7. righe di regia che sembrano condizioni ma che il lettore del gioco non capisce
    for f in GS.FILE_SCENE + (GS.FILE_NPC, GS.FILE_AMICI):
        for n, riga in enumerate(m["testi"].get(f, "").splitlines(), 1):
            r = riga.strip()
            if re.match(r"^(Se|Con|Senza|Altrimenti|Solo se)\b", r) and r.endswith(":") and "`" in r + "«":
                if not any(re.search(p, r) for p in RIGHE_CAPITE):
                    pr.append(problema(ERRORE, "CONDIZIONE_NON_CAPITA", f"{f}:{n}",
                                       f"«{r[:90]}»: il gioco non la capisce e recita le battute dopo sempre.",
                                       "Riscriverla in una forma del README (Se `BANDIERA`:, Se «voce» (`BANDIERA`):, Altrimenti:)."))
    return pr


# --- il grafo v1 -------------------------------------------------------------------------------------------

def grafo_v1(m, e):
    nodi, archi = [], []
    giocate = {c for _, _, _, c in e["passi"] if c}
    for s in m["scene"]:
        nodi.append({"id": s["codice"], "tipo": "scena", "titolo": s["titolo"], "area": s["area"],
                     "battaglia": s["codice"] in GS.BATTAGLIE, "raggiunta": s["codice"] in giocate,
                     "battute": len(s["battute"])})
        for b in s["richieste"]:
            archi.append({"da": b, "a": s["codice"], "tipo": "richiede"})
        for b in s["vietate"]:
            archi.append({"da": b, "a": s["codice"], "tipo": "vieta"})
        for b in s["imposta"]:
            archi.append({"da": s["codice"], "a": b, "tipo": "accende"})
        if s["codice"] in GS.SEGUE:
            archi.append({"da": GS.SEGUE[s["codice"]], "a": s["codice"], "tipo": "segue"})
        for x in s["battute"]:
            if x["voci"]:
                sid = f"{x['id']}"
                nodi.append({"id": sid, "tipo": "scelta", "titolo": " / ".join(x["voci"]), "dove": s["codice"]})
                archi.append({"da": s["codice"], "a": sid, "tipo": "propone"})
                for v in (0, 1):
                    if x["accende"][v] != GS.NESSUNA:
                        archi.append({"da": sid, "a": nome(x["accende"][v]), "tipo": "accende", "voce": x["voci"][v]})
            for b in bandiere_della_guardia(x["guardia"]):
                archi.append({"da": b, "a": s["codice"], "tipo": "varia"})
    for p in m["npc"]:
        tocca = p["imposta"] is not None or any(bandiere_della_guardia(x["guardia"]) or x["voci"] for x in p["frasi"])
        if not tocca:
            continue
        pid = "NPC:" + p["nome"]
        nodi.append({"id": pid, "tipo": "npc", "titolo": p["nome"], "area": p["area"]})
        if p["imposta"] is not None:
            fasi = [f for k, f in enumerate(GS.FASI) if p["imposta_fasi"] & (1 << k)]
            archi.append({"da": pid, "a": nome(p["imposta"]), "tipo": "accende", "fasi": fasi})
        for x in p["frasi"]:
            for b in bandiere_della_guardia(x["guardia"]):
                archi.append({"da": b, "a": pid, "tipo": "varia", "fase": x["fase"]})
            if x["voci"]:
                for v in (0, 1):
                    if x["accende"][v] != GS.NESSUNA:
                        archi.append({"da": pid, "a": nome(x["accende"][v]), "tipo": "accende", "voce": x["voci"][v]})
    for b, dove in ACCESE_DAL_GIOCO.items():
        archi.append({"da": "GIOCO", "a": b, "tipo": "accende", "nota": dove})
    bandiere = sorted({a["da"] for a in archi if a["da"] in TUTTE_NOTE} | {a["a"] for a in archi if a["a"] in TUTTE_NOTE})
    for b in bandiere:
        nodi.append({"id": b, "tipo": "bandiera", "quest": b in GS.BANDIERE_QUEST})
    if any(a["da"] == "GIOCO" for a in archi):
        nodi.append({"id": "GIOCO", "tipo": "codice", "titolo": "regole del gioco"})
    # l'ordine vero delle scene nei percorsi: A -> B se B parte subito dopo A in qualche partita
    ultima = {(frozenset(), frozenset()): {"INIZIO"}}
    sequenze = set()
    for _ in range(2):
        for a, _, b, c in e["passi"]:
            prima = ultima.get(a, {"INIZIO"})
            if c:
                sequenze |= {(u, c) for u in prima}
                ultima.setdefault(b, set()).add(c)
            else:
                ultima.setdefault(b, set()).update(prima)
    flusso = [{"da": a, "a": b} for a, b in sorted(sequenze) if a != b]
    return {"nodi": nodi, "archi": archi, "flusso": flusso}


# --- le cutscene: quelle nel repo (regia/*.regia, agganciate da genera_storia) e quelle proposte -----------

def carica_cutscene(schede=None):
    titoli = {}
    for p in sorted(os.listdir(os.path.join(RADICE, "regia"))):
        for riga in open(os.path.join(RADICE, "regia", p), encoding="utf-8"):
            if riga.startswith("cutscene "):
                codice, _, titolo = riga[9:].partition("|")
                titoli[codice.strip()] = titolo.strip()
    cut = []
    for scena, c in GS.REGIA.items():
        cut.append({"codice": c, "titolo": titoli.get(c, c), "scena": scena, "stato": "nel repo"})
    for scena, inserti in GS.INSERTI.items():
        for _, c in sorted(inserti.items()):
            cut.append({"codice": c, "titolo": titoli.get(c, c), "scena": scena, "stato": "nel repo"})
    if schede and os.path.exists(schede):
        with open(schede, encoding="utf-8") as t:
            righe = t.read().splitlines()
        sezione = None
        usa = {}
        for riga in righe:
            h = re.match(r"^## (C\w+) · ", riga)
            if h:
                sezione = h.group(1)
            u = re.search(r"già nel copione \(([A-Z0-9]+-\d+[a-z]?), NARRATORE\)", riga)
            if u and sezione:
                usa[sezione] = u.group(1)
        for riga in righe:
            m = re.match(r"^\| (C\w+) ([^|]+?) \| ([^|]+?) \|", riga)
            if m and re.search(r"[A-Z]\d?-\d", m.group(3)):
                for scena in re.findall(r"[A-Z]\d?-\d+[a-z]?", m.group(3)):
                    cut.append({"codice": m.group(1), "titolo": m.group(2), "scena": scena, "stato": "proposta",
                                "fonte": os.path.basename(schede), "narratore_di": usa.get(m.group(1))})
    return cut


def controlla_cutscene(cut, m, e):
    pr = []
    codici = {s["codice"]: s for s in m["scene"]}
    giocate = {c for _, _, _, c in e["passi"] if c}
    for c in cut:
        s = codici.get(c["scena"])
        if s is None:
            pr.append(problema(ERRORE, "CUTSCENE_SENZA_SCENA", c["codice"], f"{c['codice']} «{c['titolo']}» va in {c['scena']}, che non c'è.", ""))
        elif s["codice"] not in giocate:
            pr.append(problema(ERRORE, "CUTSCENE_IRRAGGIUNGIBILE", c["codice"], f"{c['codice']} sta in {c['scena']}, che nessun percorso gioca.", ""))
        elif c.get("narratore_di") and not any(b["chi"] == "NARRATORE" for b in codici[c["narratore_di"]]["battute"]):
            pr.append(problema(AVVISO, "CUTSCENE_SENZA_NARRATORE", c["codice"],
                               f"{c['codice']} usa una battuta del NARRATORE di {c['narratore_di']}, ma la scena non ne ha.", ""))
    return pr


# --- la scaletta dell'Atto II ---------------------------------------------------------------------------

def tempo(testo):
    """Un numero per l'ordine dei momenti: giorno N = 2N, notte N = 2N+1, «notte 2-3» = 5, sera = +0,5."""
    t = testo.lower()
    m = re.search(r"notte (\d)(?:-(\d))?", t)
    if m:
        return 2 * int(m.group(1)) + 1
    m = re.search(r"giorno (\d)( sera)?", t)
    if m:
        return 2 * int(m.group(1)) + (0.5 if m.group(2) else 0)
    return None


def carica_atto2(percorso_file):
    with open(percorso_file, encoding="utf-8") as t:
        testo = t.read()
    righe = testo.splitlines()
    scene, attuale = [], None
    sezione = None
    for n, riga in enumerate(righe, 1):
        if riga.startswith("## "):
            sezione = riga[3:]
            attuale = None
        m = re.match(r"^### (A2-\d+|Missione facoltativa: .+?)(?:\s+·\s+(.+))?$", riga)
        if m:
            codice = m.group(1).strip()
            titolo = (m.group(2) or codice).strip()
            luogo = re.search(r"\(([^)]*)\)", titolo)
            attuale = {"codice": codice if codice.startswith("A2-") else "MISSIONE", "titolo": titolo, "riga": n,
                       "tempo": tempo(luogo.group(1)) if luogo else None, "momento": luogo.group(1) if luogo else "",
                       "testo": [], "imposta": [], "legge": [], "scelte": [], "rimandi": set(), "ripaga": [],
                       "boss": "BOSS" in riga, "facoltativa": not codice.startswith("A2-")}
            if attuale["codice"] == "MISSIONE":
                attuale["titolo"] = codice.split(":", 1)[1].strip()
            scene.append(attuale)
            continue
        if attuale is None:
            continue
        attuale["testo"].append(riga)
        flag = re.findall(r"`([A-Z][A-Z_0-9]{3,})`", riga)
        if re.match(r"^- \*\*Imposta\*\*", riga):
            attuale["imposta"] += re.findall(r"`([A-Z][A-Z_0-9]{3,})`", re.sub(r"\([^)]*\)", "", riga))
            attuale["legge"] += [f for f in flag if f not in attuale["imposta"] and f not in attuale["legge"]]
        elif re.match(r"^\| Bandiera \|", riga):
            attuale["scelte"].append(flag)
        else:
            attuale["legge"] += [f for f in flag if f not in attuale["legge"]]
        for s in re.findall(r"`SCELTA: ([^`]+)`", riga):
            attuale["voci"] = [v.strip() for v in s.split(" / ")]
        for r in re.findall(r"A2-\d+", riga):
            attuale["rimandi"].add(r)
        for r in re.findall(r"[Rr]ipagat\w* in (A2-\d+)", riga):
            attuale["ripaga"].append(("promesso", r))
        for r in re.findall(r"[Rr]ipaga (A2-\d+)", riga):
            attuale["ripaga"].append(("ripaga", r))
    # le tabelle globali: sez. 5 (bandiere v1 e dove pesano), «Bandiere nuove», sez. 7 (Atto III)
    pesano = {}
    nuove = []
    atto3 = set()
    sez = None
    for riga in righe:
        if riga.startswith("## "):
            sez = riga
        if sez and sez.startswith("## 5.") and riga.startswith("| `"):
            celle = [c.strip() for c in riga.strip("|").split("|")]
            for b in re.findall(r"`([A-Z_0-9]+)`", celle[0]):
                pesano[b] = re.findall(r"A2-\d+|«[^»]+»", celle[1])
        if riga.startswith("Bandiere nuove:"):
            nuove = re.findall(r"`([A-Z_0-9]+)`", riga)
        if sez and sez.startswith("## 7."):
            atto3 |= set(re.findall(r"`([A-Z_0-9]+)`", riga))
            if "D6" in riga:
                atto3 |= {"ILARIO_AI_CONSOLI", "ILARIO_AL_VESCOVO"}
    for s in scene:
        s["legge"] = [f for f in s["legge"] if f not in s["imposta"]]
        for coppia in s["scelte"]:
            s["legge"] = [f for f in s["legge"] if f not in coppia]
    return {"scene": scene, "pesano": pesano, "nuove": nuove, "atto3": atto3, "file": percorso_file}


def controlla_atto2(a2, m):
    pr = []
    scene = a2["scene"]
    codici = [s["codice"] for s in scene]
    accese_v1 = set(chi_accende(m)) | {"CORRADO_SCONFITTO"}
    accesa_in = {}
    for i, s in enumerate(scene):
        for f in s["imposta"] + [f for c in s["scelte"] for f in c]:
            accesa_in.setdefault(f, i)
    letta_in = {}
    for i, s in enumerate(scene):
        for f in s["legge"]:
            letta_in.setdefault(f, []).append(i)

    for i, s in enumerate(scene):
        for f in s["legge"]:
            if f in accesa_in and f not in TUTTE_NOTE:
                if accesa_in[f] > i and not s["facoltativa"]:
                    pr.append(problema(ERRORE, "A2_LETTA_PRIMA", s["codice"],
                                       f"`{f}` è letta qui ma si accende dopo, in {scene[accesa_in[f]]['codice']}.", "Riordinare le scene."))
            elif f in accesa_in:
                pass
            elif f not in TUTTE_NOTE:
                pr.append(problema(ERRORE, "A2_BANDIERA_MAI_ACCESA", s["codice"],
                                   f"`{f}` è letta ma non è né della v1 né accesa da una scena dell'Atto II.", ""))
            elif f not in accese_v1:
                pr.append(problema(AVVISO, "A2_DIPENDE_DA_V1_NON_ACCESA", s["codice"],
                                   f"`{f}` viene dalla v1, ma nel copione v1 niente la accende ancora (es. quest non nel motore).", ""))
        for r in sorted(s["rimandi"]):
            if r not in codici:
                pr.append(problema(ERRORE, "A2_RIMANDO_ROTTO", s["codice"], f"Rimanda a {r}, che non esiste.", ""))
    # ordine dei momenti
    prec = None
    for s in scene:
        if s["facoltativa"] or s["tempo"] is None:
            continue
        if prec and s["tempo"] < prec["tempo"]:
            pr.append(problema(AVVISO, "A2_ORDINE_DEL_TEMPO", f"{prec['codice']} → {s['codice']}",
                               f"{prec['codice']} è «{prec['momento']}» ma viene prima di {s['codice']}, «{s['momento']}»: "
                               "la numerazione va indietro nel tempo.", "Scambiare l'ordine o correggere il momento."))
        prec = s
    # promesse «ripagato in» contro «ripaga»
    promesse = [(s["codice"], r) for s in scene for t, r in s["ripaga"] if t == "promesso"]
    pagate = {(r, s["codice"]) for s in scene for t, r in s["ripaga"] if t == "ripaga"}
    for da, a in promesse:
        if (da, a) not in pagate:
            vera = [y for x, y in pagate if x == da]
            pr.append(problema(ERRORE, "A2_PROMESSA_SBAGLIATA", da,
                               f"{da} dice che sarà ripagata in {a}, ma {a} non la ripaga"
                               f"{'; la ripaga ' + ', '.join(vera) if vera else ''}.",
                               f"Correggere il rimando in {da}" + (f": «Ripagato in {vera[0]}»." if vera else ".")))
    # le bandiere nuove: dichiarate contro accese, e chi le legge
    accese = set(accesa_in)
    for f in a2["nuove"]:
        if f not in accese:
            pr.append(problema(AVVISO, "A2_NUOVA_MAI_ACCESA", "Bandiere nuove", f"`{f}` è nell'elenco ma nessuna scena la accende.", ""))
    for f in sorted(accese - set(a2["nuove"])):
        if f not in TUTTE_NOTE:
            pr.append(problema(AVVISO, "A2_NUOVA_NON_ELENCATA", scene[accesa_in[f]]["codice"],
                               f"`{f}` si accende ma manca dall'elenco «Bandiere nuove».", ""))
    for f in sorted(accese):
        if f in TUTTE_NOTE:
            continue
        dopo = [i for i in letta_in.get(f, []) if i > accesa_in[f]]
        di_scelta = any(f in c for x in scene for c in x["scelte"])
        if not dopo and f not in a2["atto3"]:
            pr.append(problema(AVVISO if di_scelta else NOTA, "A2_SENZA_SEGUITO", scene[accesa_in[f]]["codice"],
                               f"`{f}` si accende e poi nessuna scena dell'Atto II né la tabella dell'Atto III la legge.",
                               "Dire dove pesa (Atto III) o non farne una bandiera."))
    # sez. 5: dove dichiara che pesa una bandiera v1, contro dove la scena la legge davvero
    for f, dove in a2["pesano"].items():
        for d in dove:
            if d.startswith("A2-"):
                s = next((x for x in scene if x["codice"] == d), None)
                if s and f not in s["legge"]:
                    pr.append(problema(AVVISO, "A2_TABELLA_DISALLINEATA", d,
                                       f"La tabella del par. 5 dice che `{f}` pesa in {d}, ma la scena non la nomina.", ""))
        reali = [scene[i]["codice"] for i in letta_in.get(f, [])]
        for r in reali:
            if r.startswith("A2-") and r not in dove:
                pr.append(problema(NOTA, "A2_TABELLA_INCOMPLETA", r, f"`{f}` pesa anche in {r}, che la tabella del par. 5 non elenca.", ""))
    # scelte v1 che l'Atto II non raccoglie
    for f in ("BORGO_DENTRO", "BORGO_FUORI", "ESULE_PRIGIONIERO", "ESULE_LIBERATO", "PANE_DATO", "GIUSTIZIA_OFFERTA"):
        if f not in letta_in:
            pr.append(problema(AVVISO, "A2_SCELTA_V1_DIMENTICATA", "Atto II", f"La scelta della v1 `{f}` non pesa in nessuna scena dell'Atto II.", ""))
    return pr


def grafo_atto2(a2):
    nodi, archi = [], []
    prec = None
    for s in a2["scene"]:
        nodi.append({"id": s["codice"], "tipo": "scena", "titolo": s["titolo"], "momento": s["momento"],
                     "boss": s["boss"], "facoltativa": s["facoltativa"]})
        if not s["facoltativa"]:
            if prec:
                archi.append({"da": prec, "a": s["codice"], "tipo": "segue"})
            prec = s["codice"]
        for f in s["imposta"]:
            archi.append({"da": s["codice"], "a": f, "tipo": "accende"})
        for f in s["legge"]:
            archi.append({"da": f, "a": s["codice"], "tipo": "varia"})
        for k, c in enumerate(s["scelte"]):
            sid = f"{s['codice']}#scelta{k}"
            nodi.append({"id": sid, "tipo": "scelta", "titolo": " / ".join(s.get("voci", c)), "dove": s["codice"]})
            archi.append({"da": s["codice"], "a": sid, "tipo": "propone"})
            for f in c:
                archi.append({"da": sid, "a": f, "tipo": "accende"})
    flag = sorted({a["a"] for a in archi if a["tipo"] == "accende"} | {a["da"] for a in archi if a["tipo"] == "varia"})
    for f in flag:
        nodi.append({"id": f, "tipo": "bandiera", "v1": f in TUTTE_NOTE, "atto3": f in a2["atto3"]})
    if a2["atto3"]:
        nodi.append({"id": "ATTO_III", "tipo": "scena", "titolo": "Atto III (Rinaldo alla porta)"})
        for f in sorted(a2["atto3"]):
            archi.append({"da": f, "a": "ATTO_III", "tipo": "varia"})
    return {"nodi": nodi, "archi": archi}


# --- tutto insieme ------------------------------------------------------------------------------------------

def analizza(cartella, atto2=None, schede=None):
    pr = []
    try:
        m = carica_v1(cartella)
    except (GS.ErroreStoria, ValueError) as x:
        return {"problemi": [problema(ERRORE, "COPIONE_ILLEGGIBILE", cartella, str(x), "")], "grafo": {}, "conti": {}}
    try:
        GS.controlla(m["scene"])
    except GS.ErroreStoria as x:
        pr.append(problema(ERRORE, "SCENE_DIVERSE_DAL_MOTORE", "genera_storia.py", str(x), ""))
    e = esplora(m)
    pr += controlla_v1(m, e)
    grafo = {"v1": grafo_v1(m, e)}
    cut = carica_cutscene(schede)
    pr += controlla_cutscene(cut, m, e)
    for c in cut:
        nid = "CUT:" + c["codice"]
        if not any(n["id"] == nid for n in grafo["v1"]["nodi"]):
            grafo["v1"]["nodi"].append({"id": nid, "tipo": "cutscene", "titolo": f"{c['codice']} {c['titolo']}", "stato": c["stato"]})
        grafo["v1"]["archi"].append({"da": nid, "a": c["scena"], "tipo": "dentro", "stato": c["stato"]})
    finali = {s for s in e["stati"] if FINE in s[0]}
    esiti = sorted({tuple(sorted(f for f in s[0] if f in ("BORGO_DENTRO", "BORGO_FUORI", "ESULE_PRIGIONIERO",
                                                              "ESULE_LIBERATO", "PANE_DATO", "GIUSTIZIA_OFFERTA")))
                    for s in finali})
    battute = sum(len(s["battute"]) for s in m["scene"]) + sum(len(p["frasi"]) for p in m["npc"])
    conti = {"scene": len(m["scene"]), "npc": len(m["npc"]), "battute": battute, "stati": len(e["stati"]),
             "finali": len(finali), "combinazioni_di_scelte": len(esiti),
             "dette": len(e["dette_prima"]), "solo_dopo_titoli": len(e["dette_dopo"] - e["dette_prima"])}
    if atto2 and os.path.exists(atto2):
        a2 = carica_atto2(atto2)
        pr += [dict(p, atto="II") for p in controlla_atto2(a2, m)]
        grafo["atto2"] = grafo_atto2(a2)
        conti["scene_atto2"] = len(a2["scene"])
    for p in pr:
        p.setdefault("atto", "I")
    ordine = {ERRORE: 0, AVVISO: 1, NOTA: 2}
    pr.sort(key=lambda p: (ordine[p["gravita"]], p["atto"], p["codice"], p["dove"]))
    return {"problemi": pr, "grafo": grafo, "conti": conti}


def rapporto_md(r, cartella, atto2):
    c = r["conti"]
    per = {g: [p for p in r["problemi"] if p["gravita"] == g] for g in (ERRORE, AVVISO, NOTA)}
    out = ["# Grafo della trama: rapporto", "",
           f"Generato da `tools/grafo_trama.py` su `{cartella}`" + (f" e `{atto2}`" if atto2 else "") + ".", "",
           f"- Copione v1: {c.get('scene')} scene, {c.get('npc')} NPC, {c.get('battute')} battute; "
           f"{c.get('stati')} stati di gioco visitati, {c.get('finali')} arrivano ai titoli di coda, "
           f"{c.get('combinazioni_di_scelte')} combinazioni diverse di scelte alla fine.",
           f"- Battute che si sentono prima dei titoli: {c.get('dette')}; solo dopo i titoli: {c.get('solo_dopo_titoli')}.",
           f"- Scaletta Atto II: {c.get('scene_atto2', 0)} scene.", "",
           f"**{len(per[ERRORE])} errori, {len(per[AVVISO])} avvisi, {len(per[NOTA])} note.**", ""]
    for g in (ERRORE, AVVISO, NOTA):
        if not per[g]:
            continue
        out += [f"## {g}", "", "| Atto | Tipo | Dove | Cosa | Proposta |", "| :-- | :-- | :-- | :-- | :-- |"]
        for p in per[g]:
            cella = [p["atto"], p["codice"], p["dove"], p["testo"], p["proposta"]]
            out.append("| " + " | ".join(x.replace("|", "/").replace("\n", " ") for x in cella) + " |")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--copione", default=os.path.join(RADICE, "copione"))
    ap.add_argument("--atto2", default=None, help="la scaletta dell'Atto II (markdown)")
    ap.add_argument("--schede", default=None, help="le schede delle cutscene proposte (cutscene/v2/SCHEDE.md)")
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args(argv)
    r = analizza(a.copione, a.atto2, a.schede)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"conti": r["conti"], "problemi": r["problemi"], "grafo": r["grafo"]}, f, ensure_ascii=False, indent=1)
    if a.md:
        with open(a.md, "w", encoding="utf-8", newline="\n") as f:
            f.write(rapporto_md(r, a.copione, a.atto2))
    errori = [p for p in r["problemi"] if p["gravita"] == ERRORE]
    for p in r["problemi"]:
        if p["gravita"] != NOTA:
            print(f"[trama] {p['gravita']} {p['atto']} {p['codice']} {p['dove']}: {p['testo']}")
    c = r["conti"]
    print(f"[trama] {c.get('stati')} stati, {c.get('finali')} finali, {len(errori)} errori, "
          f"{sum(p['gravita'] == AVVISO for p in r['problemi'])} avvisi")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
