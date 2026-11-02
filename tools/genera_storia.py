#!/usr/bin/env python3
"""Il motore della storia dalle pagine del copione v1 (copione/*.md): scrive testi/copione.testi
(le battute e i nomi di chi parla, per tools/genera_testi.py) e include/storia.h (le bandiere, le
scene con luogo, condizione, bandiere che accendono e battaglia, gli NPC d'ambiente per fase).

Le scene vengono da 00_prologo.md, 01_atto_I.md e 02_bottaccione_epilogo.md (tabelle Luogo,
Condizione, Imposta, Battaglia; battute "- PARLANTE (espressione): testo"). Gli NPC da
03_npc_ambiente.md ("- FASE: PARLANTE: testo"). Le quest di 04_quest.md sono descritte in QUEST
qui sotto (il loro testo e i contatori arrivano in F6 parte 2) e tests/test_storia.py le controlla
contro la tabella del copione.

    python tools/genera_storia.py            # controlla che i file generati siano aggiornati
    python tools/genera_storia.py --scrivi   # li riscrive
"""
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIONE = os.path.join(RADICE, "copione")
USCITA_H = os.path.join(RADICE, "include", "storia.h")
USCITA_TESTI = os.path.join(RADICE, "testi", "copione.testi")
FILE_SCENE = ("00_prologo.md", "01_atto_I.md", "02_bottaccione_epilogo.md")
FILE_NPC = "03_npc_ambiente.md"

# Le bandiere della storia (README del copione, intervallo 0-63), nell'ordine di comparsa.
BANDIERE = ["PROLOGO_VISTO", "ULTIMATUM_RICEVUTO", "GIORGIO_NEL_GRUPPO", "CHIACCHIERA_CONSOLI", "POSTIERLA_APERTA",
            "ANTONIO_NEL_GRUPPO", "CITTA_IN_DIGIUNO", "PORTA_DEL_MONTE", "IMBOSCATA_STRADONI", "SPIA_CATTURATA",
            "CERI_RISVEGLIATI", "SPETTRI_VINTI", "VISIONE_BOTTACCIONE", "BOTTACCIONE_ENTRATI", "MIASMI_VISTI",
            "PIANO_DI_CORRADO", "CORRADO_INCONTRATO", "CONDOTTO_SALVO", "RIENTRO_PORTA_METAURO", "ATTO_I_COMPLETATO",
            "CRONACA_V1_FINITA", "CORRADO_SCONFITTO"]

# Le bandiere che nessuna scena legge (nelle condizioni) ma che legge il gioco, e dove.
LETTE_DAL_GIOCO = {
    "GIORGIO_NEL_GRUPPO": "storia::gruppo(): Giorgio combatte da qui",
    "IMBOSCATA_STRADONI": "storia::scontro_attivo(): l'Imboscata sulla mappa non torna",
    "CORRADO_SCONFITTO": "storia::scontro_attivo(): Corrado sulla mappa non torna",
    "CRONACA_V1_FINITA": "Storia::recita(): il cartello dei titoli di coda",
}

# Quelle che il gioco non legge ancora: sono in docs/bandiere_da_fare.md, con cosa dovranno fare.
DA_FARE = ["MIASMI_VISTI", "PIANO_DI_CORRADO", "CORRADO_INCONTRATO", "CERI_RISVEGLIATI"]

# Dove avviene ogni scena (AreaId), dalla riga Luogo; None per le scene a schermo intero (prologo).
AREE = {"P-00": None, "P-01": None, "P-02": None, "A1-01": "PIAZZA_GRANDE", "A1-02": "VIA_DEI_CONSOLI",
        "A1-03": "SAN_MARTINO", "A1-04": "TEATRO_ROMANO", "A1-05": "PIAZZA_GRANDE", "A1-06": "DUOMO_DUCALE",
        "A1-07": "MONTE_INGINO", "A1-08": "BASILICA_INTERNO", "A1-09": "BASILICA_INTERNO", "B-01": "BOTTACCIONE",
        "B-02": "BOTTACCIONE", "B-03": "BOTTACCIONE", "B-04": "BOTTACCIONE", "B-05": "SAN_MARTINO",
        "E-01": "PIAZZA_GRANDE", "E-02": "BASILICA_INTERNO"}
# Le parole della riga Luogo che confermano l'area scelta (il test controlla che ci siano).
PAROLE_LUOGO = {"PIAZZA_GRANDE": "Piazza Grande", "VIA_DEI_CONSOLI": "via dei Consoli", "SAN_MARTINO": "San Martino",
                "TEATRO_ROMANO": "Teatro Romano", "DUOMO_DUCALE": "Duomo", "MONTE_INGINO": "Stradoni",
                "BASILICA_INTERNO": "Basilica", "BOTTACCIONE": "Bottaccione"}

# Le condizioni che non sono bandiere: la scena segue quella indicata (o, per P-00, l'accensione).
SEGUE = {"P-01": "P-00", "P-02": "P-01", "B-02": "B-01", "B-03": "B-02", "B-04": "B-03"}

# Le scene che sono cutscene (proposta approvata da Cioti, scambio/cutscene/PROPOSTA.md): il runner
# recita la cutscene del copione di regia (regia/*.regia); P-02 sta dentro C1 insieme a P-01.
REGIA = {"P-01": "C1", "E-02": "C4"}
DENTRO_LA_PRECEDENTE = {"P-02"}
CUTSCENE = set(REGIA) | DENTRO_LA_PRECEDENTE
REGIA_DENTRO = -2           # la scena e' gia' recitata dalla cutscene della scena prima
# Le cutscene dentro una scena: prima della battuta k (nell'ordine della scena), la cutscene. In A1-01
# C2 (le undici bandiere) entra prima che parli l'araldo, C2P (il pastorale) prima che risponda Ubaldo.
INSERTI = {"A1-01": {4: "C2", 7: "C2P"}}

# Le battaglie delle scene (battaglia::INCONTRO). Quelle con un nemico sulla mappa partono toccandolo;
# gli Spettri del Dubbio di A1-08 compaiono durante il rito: la scena parte entrando nella Basilica.
BATTAGLIE = {"A1-04": 0, "A1-07": 1, "B-04": 2, "A1-08": 3}

PARLANTI = {"UBALDO": "Sant'Ubaldo", "GIORGIO": "Giorgio", "ANTONIO": "Antonio", "GUIDO": "Console Guido",
            "ARALDO": "Araldo di Perugia", "CORRADO": "Corrado di Spoleto", "CECCO": "Cecco il Balestriere",
            "GUERRIERO": "Guerriero di Spoleto", "SPIA": "Spia umbra", "SPETTRO": "Spettro del Dubbio",
            "NELLO": "Nello", "FANTE": "Fante di Perugia", "CANONICO": "Canonico"}
SENZA_NOME = {"NARRATORE", "AREA", "SISTEMA", "OBIETTIVO", "SCELTA"}
ESPRESSIONI = ["calmo", "preoccupato", "deciso"]
TIPI = ["PERSONAGGIO", "NARRATORE", "AREA", "SISTEMA", "OBIETTIVO", "SCELTA"]
FASI = ["ULTIMATUM", "DIGIUNO", "NOTTE"]

# Le tre quest (04_quest.md): chi le da', da quando, dove si compiono, dove si consegnano, entro quando.
QUEST = [
    {"id": "Q-SM01", "datore": "SAN_MARTINO", "da": "ULTIMATUM_RICEVUTO", "obiettivo": "TEATRO_ROMANO",
     "consegna": "SAN_MARTINO", "entro": "ATTO_I_COMPLETATO"},
    {"id": "Q-SA01", "datore": "SANT_ANDREA", "da": "CITTA_IN_DIGIUNO", "obiettivo": "BOTTACCIONE",
     "consegna": "SANT_ANDREA", "entro": "ATTO_I_COMPLETATO"},
    {"id": "Q-SP01", "datore": "SAN_PIETRO", "da": "CITTA_IN_DIGIUNO", "obiettivo": "SAN_PIETRO",
     "consegna": "SAN_PIETRO", "entro": "ATTO_I_COMPLETATO"},
]

AREE_NPC = {"Piazza Grande": "PIAZZA_GRANDE", "via dei Consoli": "VIA_DEI_CONSOLI",
            "Largo del Bargello": "LARGO_BARGELLO", "San Martino": "SAN_MARTINO", "Teatro Romano": "TEATRO_ROMANO",
            "via XX Settembre": "VIA_XX_SETTEMBRE", "Duomo e Palazzo Ducale": "DUOMO_DUCALE",
            "Sant'Agostino": "SANT_AGOSTINO", "Sant'Andrea": "SANT_ANDREA",
            "Piazza Quaranta Martiri": "PIAZZA_QUARANTA_MARTIRI", "San Pietro": "SAN_PIETRO",
            "Monte Ingino": "MONTE_INGINO", "Basilica": "BASILICA", "Strada del Bottaccione": "BOTTACCIONE"}

RIGA_BATTUTA = re.compile(r"^- ([A-Z][A-Z' ]*?)(?: \(([a-z]+)\))?: (.+)$")
RIGA_NPC = re.compile(r"^- (ULTIMATUM|DIGIUNO|NOTTE): ([A-Z][A-Z' ]*?)(?: \(([a-z]+)\))?: (.+)$")


class ErroreStoria(Exception):
    pass


def bandiere_in(testo):
    return [b for b in re.findall(r"`([A-Z_0-9]+)`", testo) if b in BANDIERE]


def leggi_scene(testi_file):
    """[{codice, titolo, luogo, richieste, vietate, imposta, battute}] dalle pagine delle scene."""
    scene = []
    for nome, testo in testi_file:
        attuale = None
        for n, riga in enumerate(testo.splitlines(), 1):
            m = re.match(r"^## ([A-Z0-9]+-\d+) · (.+)$", riga)
            if m:
                attuale = {"codice": m.group(1), "titolo": m.group(2), "luogo": "", "richieste": [], "vietate": [],
                           "imposta": [], "battute": [], "dove": f"{nome}:{n}"}
                scene.append(attuale)
                continue
            if attuale is None:
                continue
            cella = re.match(r"^\| (Luogo|Condizione|Imposta|Battaglia|Battaglie) \| (.+) \|$", riga)
            if cella:
                chiave, valore = cella.groups()
                if chiave == "Luogo":
                    attuale["luogo"] = valore
                elif chiave == "Condizione":
                    prima, _, dopo = valore.partition(" e non ")
                    attuale["richieste"] = bandiere_in(prima)
                    attuale["vietate"] = bandiere_in(dopo)
                    altre = [b for b in re.findall(r"`([A-Z_0-9]+)`", valore) if b not in BANDIERE]
                    if altre:
                        raise ErroreStoria(f"{nome}:{n}: bandiere sconosciute nella condizione: {altre}")
                elif chiave == "Imposta":
                    attuale["imposta"] = bandiere_in(valore)
                continue
            b = RIGA_BATTUTA.match(riga)
            if b:
                chi, espressione, frase = b.groups()
                if espressione and espressione not in ESPRESSIONI:
                    raise ErroreStoria(f"{nome}:{n}: espressione '{espressione}' sconosciuta")
                if chi not in SENZA_NOME and chi not in PARLANTI:
                    raise ErroreStoria(f"{nome}:{n}: parlante '{chi}' senza nome a schermo in PARLANTI")
                attuale["battute"].append((chi, espressione or "calmo", frase.strip(), f"{nome}:{n}"))
    return scene


def leggi_npc(testo):
    """[{area, nome, frasi: [(fase, parlante, espressione, testo)]}] da 03_npc_ambiente.md."""
    npc, area, attuale = [], None, None
    for riga in testo.splitlines():
        m = re.match(r"^## (.+)$", riga)
        if m:
            area = AREE_NPC.get(m.group(1).strip())
            attuale = None
            continue
        m = re.match(r"^\*\*(.+?)\*\*", riga)
        if m and area:
            attuale = {"area": area, "nome": m.group(1), "frasi": []}
            npc.append(attuale)
            continue
        m = RIGA_NPC.match(riga)
        if m and attuale is not None:
            fase, chi, espressione, frase = m.groups()
            attuale["frasi"].append((fase, chi, espressione or "calmo", frase.strip()))
    return [p for p in npc if p["frasi"]]


def id_battuta(codice, k):
    return "C_" + codice.replace("-", "_") + f"_{k:02d}"


def id_parlante(chi):
    return "PARLANTE_" + re.sub(r"[^A-Z]", "_", chi)


def codici_regia():
    """I codici delle cutscene nell'ordine di include/regia.h (i file regia/*.regia in ordine)."""
    import glob
    codici = []
    for p in sorted(glob.glob(os.path.join(RADICE, "regia", "*.regia"))):
        for riga in open(p, encoding="utf-8"):
            if riga.startswith("cutscene "):
                codici.append(riga.split()[1])
    return codici


def indice_regia(codice):
    if codice in DENTRO_LA_PRECEDENTE:
        return REGIA_DENTRO
    if codice in REGIA:
        return codici_regia().index(REGIA[codice])
    return -1


def id_narratore(codice, k):
    return "R_" + codice.replace("-", "_") + f"_{k:02d}"


def id_titolo(codice):
    return "SCENA_" + codice.replace("-", "_")


def id_npc(i, k):
    return f"NPC_{i:02d}_{k:02d}"


def tipo_di(chi):
    return TIPI.index(chi) if chi in SENZA_NOME else 0


def posti_degli_npc(npc):
    """Una cella libera per ogni NPC: vicino al centro della sua area, lontana dai varchi e dagli altri."""
    sys.path.insert(0, os.path.join(RADICE, "tools"))
    import genera_mondo as G  # noqa: E402
    mondo = G.mondo_del_repo()
    aree = {}
    for nome, testo in G.sorgenti_del_repo():
        a = G.leggi_area(nome, testo)
        G.prepara_area(a, mondo)
        aree[a["id"].upper()] = a
    occupati = {}
    posti = []
    for p in npc:
        a = aree[p["area"]]
        g = a["griglia"]
        varchi = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in G.VARCHI]
        fermi = varchi + list(a["spawn"].values()) + occupati.get(p["area"], [])
        cx, cy = a["spawn"][0]
        scelto = None
        for raggio in range(2, 40):
            for y in range(max(1, cy - raggio), min(a["altezza"] - 1, cy + raggio + 1)):
                for x in range(max(1, cx - raggio), min(a["larghezza"] - 1, cx + raggio + 1)):
                    if max(abs(x - cx), abs(y - cy)) != raggio:
                        continue
                    libero = all(not G.solida(g[y + j][x + i]) and g[y + j][x + i] not in G.VARCHI
                                 for i in (-1, 0, 1) for j in (-1, 0, 1))
                    if libero and all(max(abs(x - u), abs(y - v)) >= 4 for u, v in fermi):
                        scelto = (x, y)
                        break
                if scelto:
                    break
            if scelto:
                break
        if not scelto:
            raise ErroreStoria(f"nessun posto per {p['nome']} in {p['area']}")
        occupati.setdefault(p["area"], []).append(scelto)
        posti.append(scelto)
    return posti


def leggi_copione():
    testi = [(f, open(os.path.join(COPIONE, f), encoding="utf-8").read()) for f in FILE_SCENE]
    scene = leggi_scene(testi)
    npc = leggi_npc(open(os.path.join(COPIONE, FILE_NPC), encoding="utf-8").read())
    return scene, npc


def controlla(scene):
    codici = [s["codice"] for s in scene]
    if sorted(codici) != sorted(AREE):
        raise ErroreStoria(f"scene del copione {codici} diverse da quelle note {sorted(AREE)}")
    for s in scene:
        area = AREE[s["codice"]]
        parola = {"B-04": "Condotto"}.get(s["codice"], PAROLE_LUOGO.get(area))  # il Condotto e' in fondo al Bottaccione
        if area and parola not in s["luogo"]:
            raise ErroreStoria(f"{s['dove']}: {s['codice']} in {area}, ma il Luogo dice '{s['luogo']}'")
        if not s["battute"] and s["codice"] != "P-00":     # P-00 e' il titolo, senza battute
            raise ErroreStoria(f"{s['dove']}: {s['codice']} senza battute")


def testi_del_copione(scene, npc):
    righe = ["# GENERATO da tools/genera_storia.py dal copione v1 (copione/*.md): non modificare a mano.",
             "# Le battute delle scene, i nomi di chi parla e le battute degli NPC d'ambiente.", ""]
    for chi in sorted(PARLANTI):
        righe.append(f"{id_parlante(chi):26s}| HUD     | {PARLANTI[chi]}")
    for s in scene:
        righe.append(f"{id_titolo(s['codice']):26s}| DIALOGO | {s['titolo']}")
    for s in scene:
        for k, (chi, _, frase, _) in enumerate(s["battute"]):
            righe.append(f"{id_battuta(s['codice'], k):26s}| DIALOGO | {frase}")
            # il narratore parla anche nelle bande delle cutscene: la stessa frase, al massimo 2 righe
            if chi == "NARRATORE":
                righe.append(f"{id_narratore(s['codice'], k):26s}| NARRATORE | {frase}")
    for i, p in enumerate(npc):
        for k, (_, _, _, frase) in enumerate(p["frasi"]):
            righe.append(f"{id_npc(i, k):26s}| DIALOGO | {frase}")
    return "\n".join(r for r in righe if r is not None) + "\n"


def maschera(bandiere):
    v = 0
    for b in bandiere:
        v |= 1 << BANDIERE.index(b)
    return v


def header(scene, npc, posti):
    codici = [s["codice"] for s in scene]
    out = ["// GENERATO da tools/genera_storia.py dal copione v1 (copione/*.md): non modificare a mano.",
           "#ifndef GUBBIO_STORIA_H", "#define GUBBIO_STORIA_H", "", "#include <cstdint>", "",
           "#include \"mondo.h\"", "#include \"testi.h\"", "", "namespace gubbio::storia", "{", "",
           "enum class Bandiera : uint8_t", "{"]
    out += [f"    {b}," for b in BANDIERE] + ["    CONTEGGIO,", "};", ""]
    out += [f"inline constexpr int SCENE = {len(scene)};", "inline constexpr int NESSUNA_AREA = -1;", "",
            "enum class TipoBattuta : uint8_t", "{"] + [f"    {t}," for t in TIPI] + ["};", "",
            "enum class Espressione : uint8_t", "{"] + [f"    {e.upper()}," for e in ESPRESSIONI] + ["};", "",
            "struct Battuta", "{", "    testi::TestoId testo;", "    testi::TestoId parlante;     // per un PERSONAGGIO",
            "    TipoBattuta tipo;", "    Espressione espressione;", "};", "",
            "struct Scena", "{", "    const char* codice;", "    testi::TestoId titolo;",
            "    bool cutscene;", "    int8_t regia;                // la cutscene (regia::CUTSCENE_DATI), -2 dentro la precedente", "    int8_t area;                 // mondo::AreaId, o NESSUNA_AREA (a schermo intero)",
            "    uint64_t richieste;          // tutte accese", "    uint64_t vietate;            // nessuna accesa",
            "    uint64_t imposta;            // accese alla fine", "    int8_t segue;                // la scena che deve essere gia' fatta, o -1",
            "    int8_t battaglia;            // battaglia::INCONTRO, o -1", "    uint16_t prima_battuta;",
            "    uint16_t battute;", "};", ""]
    battute = []
    righe_scene = []
    for s in scene:
        prima = len(battute)
        for k, (chi, espr, _, _) in enumerate(s["battute"]):
            parlante = f"testi::TestoId::{id_parlante(chi)}" if chi in PARLANTI else f"testi::TestoId::{id_battuta(s['codice'], k)}"
            battute.append(f"    {{ testi::TestoId::{id_battuta(s['codice'], k)}, {parlante}, TipoBattuta::{TIPI[tipo_di(chi)]}, "
                           f"Espressione::{espr.upper()} }},")
        area = f"int8_t(mondo::AreaId::{AREE[s['codice']]})" if AREE[s["codice"]] else "NESSUNA_AREA"
        segue = codici.index(SEGUE[s["codice"]]) if s["codice"] in SEGUE else -1
        righe_scene.append(f"    {{ \"{s['codice']}\", testi::TestoId::{id_titolo(s['codice'])}, "
                           f"{'true' if s['codice'] in CUTSCENE else 'false'}, {indice_regia(s['codice'])}, {area}, 0x{maschera(s['richieste']):X}u, 0x{maschera(s['vietate']):X}u, "
                           f"0x{maschera(s['imposta']):X}u, {segue}, {BATTAGLIE.get(s['codice'], -1)}, {prima}, {len(s['battute'])} }},")
    out += [f"inline constexpr int BATTUTE = {len(battute)};", "inline constexpr Battuta BATTUTA[BATTUTE] = {"] + battute + ["};", ""]
    out += ["inline constexpr Scena SCENA[SCENE] = {"] + righe_scene + ["};", ""]
    inserti = []
    regie = codici_regia()
    for s in scene:
        for k, codice in sorted(INSERTI.get(s["codice"], {}).items()):
            if not 0 <= k < len(s["battute"]) or codice not in regie:
                raise ValueError(f"inserto {s['codice']}:{k} {codice}: battuta o cutscene che non c'e'")
            prima = sum(len(t["battute"]) for t in scene[:scene.index(s)])
            inserti.append(f"    {{ {prima + k}, {regie.index(codice)} }},  // {s['codice']} prima della battuta {k}: {codice}")
    out += ["// Le cutscene dentro le scene: prima della battuta (indice in BATTUTA), la cutscene.",
            "struct Inserto", "{", "    uint16_t battuta;", "    int8_t regia;", "};", "",
            f"inline constexpr int INSERTI = {len(inserti)};",
            "inline constexpr Inserto INSERTO[INSERTI > 0 ? INSERTI : 1] = {"] + (inserti or ["    { 0xFFFF, -1 },"]) + ["};", ""]
    # NPC
    out += ["enum class Fase : uint8_t", "{"] + [f"    {f}," for f in FASI] + ["};", "",
            "struct Npc", "{", "    int8_t area;", "    uint8_t tx;", "    uint8_t ty;",
            "    uint16_t prima_frase[3];     // per fase (ULTIMATUM, DIGIUNO, NOTTE); 0xFFFF: non c'e'",
            "    uint8_t frasi[3];", "};", ""]
    frasi = []
    righe_npc = []
    for i, p in enumerate(npc):
        per_fase = {f: [] for f in FASI}
        for k, (fase, chi, espr, _) in enumerate(p["frasi"]):
            per_fase[fase].append((k, chi, espr))
        prime, conte = [], []
        for f in FASI:
            prime.append(str(len(frasi)) if per_fase[f] else "0xFFFF")
            conte.append(str(len(per_fase[f])))
            for k, chi, espr in per_fase[f]:
                parlante = f"testi::TestoId::{id_parlante(chi)}" if chi in PARLANTI else f"testi::TestoId::{id_npc(i, k)}"
                tipo = "PERSONAGGIO" if chi in PARLANTI else "SISTEMA"
                frasi.append(f"    {{ testi::TestoId::{id_npc(i, k)}, {parlante}, TipoBattuta::{tipo}, Espressione::{espr.upper()} }},")
        tx, ty = posti[i]
        righe_npc.append(f"    {{ int8_t(mondo::AreaId::{p['area']}), {tx}, {ty}, {{ {', '.join(prime)} }}, {{ {', '.join(conte)} }} }},  // {p['nome']}")
    out += [f"inline constexpr int FRASI_NPC = {len(frasi)};", "inline constexpr Battuta FRASE_NPC[FRASI_NPC] = {"] + frasi + ["};", ""]
    out += [f"inline constexpr int NPC = {len(npc)};", "inline constexpr Npc NPC_AMBIENTE[NPC] = {"] + righe_npc + ["};", ""]
    out += ["}", "", "#endif", ""]
    return "\n".join(out)


def genera():
    scene, npc = leggi_copione()
    controlla(scene)
    return header(scene, npc, posti_degli_npc(npc)), testi_del_copione(scene, npc)


def main(argv):
    try:
        h, t = genera()
    except ErroreStoria as e:
        print(f"[storia] ERRORE: {e}")
        return 1
    if "--scrivi" in argv:
        for p, testo in ((USCITA_H, h), (USCITA_TESTI, t)):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(testo)
        print("[storia] scritti include/storia.h e testi/copione.testi")
        return 0
    vecchi = [open(p, encoding="utf-8").read() if os.path.exists(p) else "" for p in (USCITA_H, USCITA_TESTI)]
    if vecchi != [h, t]:
        print("[storia] da rigenerare con --scrivi")
        return 1
    print("[storia] aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
