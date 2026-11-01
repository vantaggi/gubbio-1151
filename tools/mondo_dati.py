#!/usr/bin/env python3
"""Il mondo di Gubbio come dati, calcolati dal censimento F3.

Legge:
  mondo/grafo.json                 aree, quote e varchi (bussola reale)
  mondo/fonti/censimento_osm.csv   33 monumenti con misure e coordinate OSM

Scrive (con --scrivi):
  mondo/monumenti.json             per monumento: area, impronta in tile,
                                   lato della facciata sullo schermo,
                                   posizione rispetto all'ancora dell'area
  mondo/varchi.json                per area: i varchi, con il lato dello
                                   schermo su cui si aprono

Senza argomenti controlla che i file scritti siano aggiornati (esce con 1 se no).

La rotazione del gioco (decisa nel prototipo, confermata il 1 nov 2026):
  alto dello schermo = ovest, basso = est, destra = nord, sinistra = sud.
  In griglia x cresce verso nord, y cresce verso est.
  Una facciata che guarda a est si vede di fronte (FRONTALE).

Scala: 1 tile (8 px) = 1,5 m. Gli edifici sono in scala; le distanze fra
edifici si possono comprimere quando si disegna l'area (qui restano reali).
"""
import csv
import json
import math
import os
import sys

RADICE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GRAFO = os.path.join(RADICE, "mondo", "grafo.json")
CENSIMENTO = os.path.join(RADICE, "mondo", "fonti", "censimento_osm.csv")
OUT_MONUMENTI = os.path.join(RADICE, "mondo", "monumenti.json")
OUT_VARCHI = os.path.join(RADICE, "mondo", "varchi.json")

METRI_PER_TILE = 1.5
RAGGIO_TERRA_M = 6371000.0

# Oltre questa lunghezza un elemento OSM non e' un edificio ma un tracciato
# (una via, la gola, l'acquedotto): non ha impronta, si disegna come percorso.
SOGLIA_TRACCIATO_M = 120.0

# Bussola: gradi da nord in senso orario.
BUSSOLA = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SO": 225, "O": 270, "NO": 315}

# Misure in pianta: vale OSM, salvo queste eccezioni motivate (decisione F3
# del 1 nov 2026, da rivedere con Cioti). (lato lungo, lato corto, perche').
ECCEZIONI_MISURE = {
    "basilica": (50.0, 22.0,
                 "OSM da' 70x45 m ma e' la relation del complesso con il convento; "
                 "per la chiesa resta il 50x22 del GDD finche' una foto o la pianta non dice altro"),
}


# --- rotazione -------------------------------------------------------------

def vettore_schermo(bussola_gradi):
    """Direzione reale -> vettore sullo schermo (dx verso destra, dy verso il basso).

    Nord = destra (+x), est = basso (+y)."""
    r = math.radians(bussola_gradi)
    return (math.cos(r), math.sin(r))


def lato_schermo(bussola_gradi):
    """Il lato dello schermo verso cui punta una direzione reale."""
    dx, dy = vettore_schermo(bussola_gradi)
    if abs(dx) >= abs(dy):
        return "destra" if dx > 0 else "sinistra"
    return "basso" if dy > 0 else "alto"


LATO_OPPOSTO = {"alto": "basso", "basso": "alto", "destra": "sinistra", "sinistra": "destra"}


def vista_facciata(bussola_gradi):
    """Come si vede una facciata che guarda in quella direzione."""
    return {
        "basso": "frontale",
        "alto": "retro (solo tetto)",
        "destra": "fianco destro",
        "sinistra": "fianco sinistro",
    }[lato_schermo(bussola_gradi)]


# --- geografia -------------------------------------------------------------

def metri_nord_est(da, a):
    """Spostamento in metri (nord, est) fra due punti (lat, lon). Piano locale."""
    lat0 = math.radians((da[0] + a[0]) / 2)
    nord = math.radians(a[0] - da[0]) * RAGGIO_TERRA_M
    est = math.radians(a[1] - da[1]) * RAGGIO_TERRA_M * math.cos(lat0)
    return (nord, est)


def rilevamento(da, a):
    """Gradi da nord, in senso orario, per andare da `da` ad `a`."""
    nord, est = metri_nord_est(da, a)
    return math.degrees(math.atan2(est, nord)) % 360


def differenza_angolare(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def tile(metri):
    return max(1, int(round(metri / METRI_PER_TILE)))


# --- caricamento ------------------------------------------------------------

def carica_grafo(percorso=GRAFO):
    with open(percorso, encoding="utf-8") as f:
        return json.load(f)


def carica_censimento(percorso=CENSIMENTO):
    with open(percorso, encoding="utf-8", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def _num(s):
    s = (s or "").strip()
    return float(s) if s else None


def punto(riga):
    lat, lon = _num(riga.get("lat")), _num(riga.get("lon"))
    return (lat, lon) if lat is not None and lon is not None else None


def ancora_area(area, censimento):
    """Il punto (lat, lon) che rappresenta l'area."""
    if area.get("ancora"):
        p = punto(censimento[area["ancora"]])
        if p is None:
            raise ValueError("ancora senza coordinate: %s" % area["ancora"])
        return p
    return tuple(area["ancora_stimata"])


def quota_media(area):
    return sum(area["quota_m"]) / 2.0


# --- calcolo ------------------------------------------------------------------

def impronta(riga):
    """(tipo, lato_lungo_m, lato_corto_m, fonte) di un monumento."""
    mid = riga["id"]
    if mid in ECCEZIONI_MISURE:
        lungo, corto, _ = ECCEZIONI_MISURE[mid]
        return ("edificio", lungo, corto, "eccezione")
    lungo, corto = _num(riga["osm_lato_lungo_m"]), _num(riga["osm_lato_corto_m"])
    if lungo is None or corto is None:
        return ("senza_misura", None, None, None)
    if lungo > SOGLIA_TRACCIATO_M:
        return ("tracciato", lungo, corto, "osm")
    return ("edificio", lungo, corto, "osm")


def calcola_monumenti(grafo, censimento):
    area_di = {}
    for a in grafo["aree"]:
        for m in a["monumenti"]:
            area_di[m] = a
    out = {}
    for mid in sorted(censimento):
        r = censimento[mid]
        area = area_di[mid]
        tipo, lungo, corto, fonte = impronta(r)
        voce = {
            "nome": r["nome"],
            "area": area["id"],
            "ruolo": r["ruolo"],
            "tipo": tipo,
        }
        if tipo == "edificio":
            voce["misure_m"] = [round(lungo, 1), round(corto, 1)]
            voce["misure_tile"] = [tile(lungo), tile(corto)]
            voce["fonte_misure"] = fonte
            asse = _num(r["osm_asse_lungo_bussola"])
            if asse is not None:
                voce["asse_lungo_bussola"] = int(asse)
                voce["asse_lungo_schermo"] = (
                    "orizzontale" if lato_schermo(asse) in ("destra", "sinistra") else "verticale")
        elif tipo == "tracciato":
            voce["lunghezza_m"] = round(lungo, 1)
        normale = _num(r["facciata_normale_bussola"])
        if normale is not None:
            voce["facciata_bussola"] = int(normale)
            voce["facciata_lato_schermo"] = lato_schermo(normale)
            voce["facciata_vista"] = vista_facciata(normale)
        p = punto(r)
        if p is not None:
            nord, est = metri_nord_est(ancora_area(area, censimento), p)
            # Sullo schermo: x = nord (destra), y = est (basso).
            voce["dall_ancora_m"] = [round(nord, 1), round(est, 1)]
            voce["dall_ancora_tile"] = [int(round(nord / METRI_PER_TILE)),
                                        int(round(est / METRI_PER_TILE))]
        out[mid] = voce
    return out


def lato_varco(verso, rilev_reale):
    """Il lato dello schermo su cui si apre un varco.

    Le direzioni cardinali vanno dritte. Per le diagonali (NO, SE...) decide la
    componente piu' forte del rilevamento reale fra le due ancore, ma solo fra
    i due lati che la diagonale ammette."""
    b = BUSSOLA[verso]
    if b % 90 == 0:
        return lato_schermo(b)
    ammessi = {lato_schermo(b - 45), lato_schermo(b + 45)}
    dx, dy = vettore_schermo(rilev_reale)
    candidati = sorted(
        ammessi,
        key=lambda lato: -{"destra": dx, "sinistra": -dx, "basso": dy, "alto": -dy}[lato])
    return candidati[0]


def calcola_varchi(grafo, censimento):
    aree = {a["id"]: a for a in grafo["aree"]}
    out = {aid: [] for aid in aree}
    for arco in grafo["archi"]:
        da, a = arco["da"], arco["a"]
        rilev = rilevamento(ancora_area(aree[da], censimento), ancora_area(aree[a], censimento))
        lato = lato_varco(arco["verso"], rilev)
        inverso = (BUSSOLA[arco["verso"]] + 180) % 360
        verso_inv = [k for k, v in BUSSOLA.items() if v == inverso][0]
        out[da].append({"verso": a, "bussola": arco["verso"], "lato": lato, "come": arco["come"]})
        out[a].append({"verso": da, "bussola": verso_inv, "lato": LATO_OPPOSTO[lato],
                       "come": arco["come"] + " (al contrario)"})
    for aid in out:
        out[aid].sort(key=lambda v: v["verso"])
    return out


# --- controlli ----------------------------------------------------------------
# Ognuno restituisce una lista di errori (vuota = tutto bene). I test li usano
# sul mondo vero e su copie guastate apposta (prove negative).

PAROLE_DISCESA = ("discesa", "scende", "basso")
PAROLE_SALITA = ("salita", "sale")


def errori_archi(grafo):
    ids = {a["id"] for a in grafo["aree"]}
    err = []
    visti = set()
    for e in grafo["archi"]:
        for k in ("da", "a"):
            if e[k] not in ids:
                err.append("arco verso area inesistente: %s" % e[k])
        if e["verso"] not in BUSSOLA:
            err.append("direzione sconosciuta %s in %s>%s" % (e["verso"], e["da"], e["a"]))
        if e["da"] == e["a"]:
            err.append("arco su se stessa: %s" % e["da"])
        coppia = frozenset((e["da"], e["a"]))
        if coppia in visti:
            err.append("arco doppio: %s-%s" % (e["da"], e["a"]))
        visti.add(coppia)
    return err


def errori_connessione(grafo):
    """Ogni area si raggiunge da ogni altra (gli archi si percorrono nei due sensi)."""
    vicini = {a["id"]: set() for a in grafo["aree"]}
    for e in grafo["archi"]:
        if e["da"] in vicini and e["a"] in vicini:
            vicini[e["da"]].add(e["a"])
            vicini[e["a"]].add(e["da"])
    partenza = grafo["aree"][0]["id"]
    visti, coda = {partenza}, [partenza]
    while coda:
        for v in vicini[coda.pop()]:
            if v not in visti:
                visti.add(v)
                coda.append(v)
    return ["area irraggiungibile: %s" % a for a in sorted(set(vicini) - visti)]


def errori_anello(grafo):
    """L'anello dichiarato si chiude e ogni suo passo e' un arco vero."""
    anello = grafo["anello"]
    err = []
    if anello[0] != anello[-1]:
        err.append("l'anello non si chiude: %s ... %s" % (anello[0], anello[-1]))
    coppie = {frozenset((e["da"], e["a"])) for e in grafo["archi"]}
    for x, y in zip(anello, anello[1:]):
        if frozenset((x, y)) not in coppie:
            err.append("passo dell'anello senza arco: %s>%s" % (x, y))
    return err


def errori_quote(grafo):
    """Chi scende arriva piu' in basso, chi sale piu' in alto."""
    aree = {a["id"]: a for a in grafo["aree"]}
    err = []
    for e in grafo["archi"]:
        come = e["come"].lower()
        qd, qa = quota_media(aree[e["da"]]), quota_media(aree[e["a"]])
        if any(p in come for p in PAROLE_DISCESA) and not qd > qa:
            err.append("%s>%s si dice in discesa ma va da %g a %g m" % (e["da"], e["a"], qd, qa))
        if any(p in come for p in PAROLE_SALITA) and not qd < qa:
            err.append("%s>%s si dice in salita ma va da %g a %g m" % (e["da"], e["a"], qd, qa))
    return err


def errori_direzioni(grafo, censimento, tolleranza=90.0):
    """La direzione dichiarata del varco somiglia a quella vera fra le ancore."""
    aree = {a["id"]: a for a in grafo["aree"]}
    eccezioni = grafo.get("direzioni_da_confermare", {})
    err = []
    for e in grafo["archi"]:
        if "%s>%s" % (e["da"], e["a"]) in eccezioni:
            continue
        vero = rilevamento(ancora_area(aree[e["da"]], censimento), ancora_area(aree[e["a"]], censimento))
        scarto = differenza_angolare(vero, BUSSOLA[e["verso"]])
        if scarto >= tolleranza:
            err.append("%s>%s dichiarato %s ma in realta' %d gradi (scarto %d)"
                       % (e["da"], e["a"], e["verso"], vero, scarto))
    return err


def errori_monumenti(grafo, censimento):
    """Ogni monumento del censimento sta in una e una sola area, e viceversa."""
    err = []
    conta = {}
    for a in grafo["aree"]:
        for m in a["monumenti"]:
            conta[m] = conta.get(m, 0) + 1
        if a.get("ancora") and a["ancora"] not in a["monumenti"]:
            err.append("l'ancora di %s non e' fra i suoi monumenti" % a["id"])
    for m, n in sorted(conta.items()):
        if n > 1:
            err.append("monumento in %d aree: %s" % (n, m))
        if m not in censimento:
            err.append("monumento assente dal censimento: %s" % m)
    for m in sorted(set(censimento) - set(conta)):
        err.append("monumento del censimento senza area: %s" % m)
    return err


def errori_lati_varchi(varchi):
    """Ogni area ha almeno un varco, e andata e ritorno stanno su lati opposti."""
    err = []
    for aid, lista in varchi.items():
        if not lista:
            err.append("area senza varchi: %s" % aid)
        for v in lista:
            ritorno = [w for w in varchi[v["verso"]] if w["verso"] == aid]
            if len(ritorno) != 1:
                err.append("%s>%s senza ritorno" % (aid, v["verso"]))
            elif ritorno[0]["lato"] != LATO_OPPOSTO[v["lato"]]:
                err.append("%s>%s esce a %s ma rientra a %s"
                           % (aid, v["verso"], v["lato"], ritorno[0]["lato"]))
    return err


def tutti_gli_errori(grafo, censimento):
    return (errori_archi(grafo) + errori_connessione(grafo) + errori_anello(grafo)
            + errori_quote(grafo) + errori_direzioni(grafo, censimento)
            + errori_monumenti(grafo, censimento)
            + errori_lati_varchi(calcola_varchi(grafo, censimento)))


def documenti(grafo=None, censimento=None):
    grafo = grafo or carica_grafo()
    censimento = censimento or carica_censimento()
    intest = ("Generato da tools/mondo_dati.py dal censimento F3 (OSM, (c) contributori "
              "OpenStreetMap, ODbL) e da mondo/grafo.json. Non modificare a mano.")
    mon = {"_leggimi": intest, "metri_per_tile": METRI_PER_TILE,
           "rotazione": "alto=ovest, basso=est, destra=nord, sinistra=sud",
           "monumenti": calcola_monumenti(grafo, censimento)}
    var = {"_leggimi": intest, "rotazione": mon["rotazione"],
           "varchi": calcola_varchi(grafo, censimento)}
    return {OUT_MONUMENTI: mon, OUT_VARCHI: var}


def serializza(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main(argv):
    err = tutti_gli_errori(carica_grafo(), carica_censimento())
    if err:
        print("mondo/ non valido:\n  " + "\n  ".join(err))
        return 1
    docs = documenti()
    if "--scrivi" in argv:
        for percorso, doc in docs.items():
            with open(percorso, "w", encoding="utf-8", newline="\n") as f:
                f.write(serializza(doc))
            print("scritto", os.path.relpath(percorso, RADICE))
        return 0
    vecchi = []
    for percorso, doc in docs.items():
        try:
            with open(percorso, encoding="utf-8") as f:
                attuale = f.read()
        except FileNotFoundError:
            attuale = None
        if attuale != serializza(doc):
            vecchi.append(os.path.relpath(percorso, RADICE))
    if vecchi:
        print("da rigenerare con --scrivi:", ", ".join(vecchi))
        return 1
    print("mondo/ aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
