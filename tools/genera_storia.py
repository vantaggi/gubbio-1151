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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_npc as FN  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIONE = os.path.join(RADICE, "copione")
USCITA_H = os.path.join(RADICE, "include", "storia.h")
USCITA_TESTI = os.path.join(RADICE, "testi", "copione.testi")
FILE_SCENE = ("00_prologo.md", "01_atto_I.md", "02_bottaccione_epilogo.md")
FILE_NPC = "03_npc_ambiente.md"
FILE_AMICI = "05_npc_amici.md"
AMICI = __import__("json").load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                  "dati", "amici.json"), encoding="utf-8"))["amici"]

# Le bandiere della storia (README del copione, intervallo 0-63), nell'ordine di comparsa.
BANDIERE = ["PROLOGO_VISTO", "ULTIMATUM_RICEVUTO", "GIORGIO_NEL_GRUPPO", "CHIACCHIERA_CONSOLI", "POSTIERLA_APERTA",
            "ANTONIO_NEL_GRUPPO", "CITTA_IN_DIGIUNO", "PORTA_DEL_MONTE", "IMBOSCATA_STRADONI", "SPIA_CATTURATA",
            "CERI_RISVEGLIATI", "SPETTRI_VINTI", "VISIONE_BOTTACCIONE", "BOTTACCIONE_ENTRATI", "MIASMI_VISTI",
            "PIANO_DI_CORRADO", "CORRADO_INCONTRATO", "CONDOTTO_SALVO", "RIENTRO_PORTA_METAURO", "ATTO_I_COMPLETATO",
            "CRONACA_V1_FINITA", "CORRADO_SCONFITTO", "BORGO_DENTRO", "BORGO_FUORI", "ESULE_PRIGIONIERO",
            "ESULE_LIBERATO", "GIUSTIZIA_OFFERTA", "ALBA_CONFERMATA"]
# Le bandiere delle quest, degli indizi e degli ascolti (intervallo 64-127): stanno in GameState::quest.
BANDIERE_QUEST = ["INDIZIO_CARTA", "INDIZIO_ACQUA", "INDIZIO_ROCCIA", "RICCIARDO_ASCOLTATO", "RUFINO_ASCOLTATO", "PANE_DATO",
         "DONO_MATTEO", "INDIZIO_LUCIA", "INDIZIO_VENDITORE", "INDIZIO_FONTANIERE"]
PRIMA_QUEST = 64
TUTTE = BANDIERE + [None] * (PRIMA_QUEST - len(BANDIERE)) + BANDIERE_QUEST

# Le bandiere che nessuna scena legge (nelle condizioni) ma che legge il gioco, e dove.
LETTE_DAL_GIOCO = {
    "GIORGIO_NEL_GRUPPO": "storia::gruppo(): Giorgio combatte da qui",
    "IMBOSCATA_STRADONI": "storia::scontro_attivo(): l'Imboscata sulla mappa non torna",
    "CORRADO_SCONFITTO": "storia::scontro_attivo(): Corrado sulla mappa non torna",
    "CRONACA_V1_FINITA": "Storia::recita(): il cartello dei titoli di coda",
}

# Quelle che il gioco non legge ancora: sono in docs/bandiere_da_fare.md, con cosa dovranno fare.
DA_FARE = ["MIASMI_VISTI", "PIANO_DI_CORRADO", "CORRADO_INCONTRATO", "CERI_RISVEGLIATI"]

# Dove avviene ogni scena (AreaId), dalla riga Luogo; None per le scene a schermo intero (il prologo, e la
# vetrata di E-02, che il gioco recita subito dopo E-01 senza risalire alla Basilica).
AREE = {"P-00": None, "P-01": None, "P-02": None, "A1-01": "PIAZZA_GRANDE", "A1-02": "VIA_DEI_CONSOLI", "A1-05b": "SANT_ANDREA",
        "A1-03": "SAN_MARTINO", "A1-04": "TEATRO_ROMANO", "A1-05": "PIAZZA_GRANDE", "A1-06": "DUOMO_DUCALE",
        "A1-07": "MONTE_INGINO", "A1-08": "BASILICA_INTERNO", "A1-09": "BASILICA_INTERNO", "B-01": "GOLA_STRISCIA",
        "B-02": "GOLA_MIASMI", "B-03": "GOLA_ARCO", "B-04": "CONDOTTO", "B-05": "SAN_MARTINO",
        "E-01": "PIAZZA_GRANDE", "E-02": None}
# Le parole della riga Luogo che confermano l'area scelta (il test controlla che ci siano).
PAROLE_LUOGO = {"PIAZZA_GRANDE": "Piazza Grande", "VIA_DEI_CONSOLI": "via dei Consoli", "SAN_MARTINO": "San Martino",
                "TEATRO_ROMANO": "Teatro Romano", "DUOMO_DUCALE": "Duomo", "MONTE_INGINO": "Stradoni", "SANT_ANDREA": "Sant'Andrea",
                "BASILICA_INTERNO": "Basilica", "BOTTACCIONE": "Bottaccione", "GOLA_STRISCIA": "Bottaccione",
                "GOLA_MIASMI": "Bottaccione", "GOLA_ARCO": "Bottaccione", "CONDOTTO": "Condotto"}

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
# Le presentazioni a fermo immagine (C3) entrano prima che il personaggio parli la prima volta: Ubaldo
# dopo il cartello della piazza, Giorgio, Antonio, Corrado.
INSERTI = {"A1-01": {1: "C3U", 2: "C3G", 4: "C2", 8: "C2P"}, "A1-04": {1: "C3A"}, "B-04": {0: "C3C"}}

# Le battaglie delle scene (battaglia::INCONTRO). Quelle con un nemico sulla mappa partono toccandolo;
# gli Spettri del Dubbio di A1-08 compaiono durante il rito: la scena parte entrando nella Basilica.
BATTAGLIE = {"A1-04": 0, "A1-07": 1, "B-04": 2, "A1-08": 3}

PARLANTI = {"UBALDO": "Sant'Ubaldo", "GIORGIO": "Giorgio", "ANTONIO": "Antonio", "GUIDO": "Console Guido",
            "ARALDO": "Araldo di Perugia", "CORRADO": "Corrado di Spoleto", "CECCO": "Cecco il Balestriere",
            "GUERRIERO": "Guerriero di Spoleto", "SPIA": "Spia umbra", "SPETTRO": "Spettro del Dubbio",
            "NELLO": "Nello", "ANDREUCCIO": "Andreuccio", "FAZIO": "Fazio", "LAURETTA": "Lauretta",
            "FOLLA": "Folla", "RAGAZZO": "Ragazzo eugubino", "FANTE": "Fante di Perugia", "CANONICO": "Canonico"}
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
            "Monte Ingino": "MONTE_INGINO", "Basilica": "BASILICA", "Strada del Bottaccione": "BOTTACCIONE",
            "Via dei Consoli": "VIA_DEI_CONSOLI", "Sant'Agostino (fuori Porta Romana)": "SANT_AGOSTINO"}

RIGA_BATTUTA = re.compile(r"^- ([A-Z][A-Z' ]*?)(?: \(([a-z]+)\))?: (.+)$")
# Le righe di battaglia ("- IN BATTAGLIA (evento): PARLANTE: testo", B-04): si dicono dentro lo scontro, non
# nel dialogo della scena; il lettore le mette da parte (scena["in_battaglia"]) e non le recita.
RIGA_BATTAGLIA = re.compile(r"^- IN BATTAGLIA \((.+?)\): ([A-Z][A-Z' ]*?)(?: \(([a-z]+)\))?: (.+)$")
RIGA_NPC = re.compile(r"^- (ULTIMATUM|DIGIUNO|NOTTE)(?: \(se (non )?([A-Z_0-9]+)\))?: ([A-Z][A-Z' ]*?)(?: \(([a-z]+)\))?: (.+)$")


class ErroreStoria(Exception):
    pass


# --- le varianti del copione v2 ------------------------------------------------------------------------
# Ogni battuta ha una guardia: la recita il gioco solo se vale. Le guardie vengono dalle righe del copione
# fra le battute: "Se «voce» (`BANDIERA`):" (il blocco della voce scelta nell'ultimo menu, che accende la
# bandiera), "Se `BANDIERA`:" e "Altrimenti:", "Se `BANDIERA`, al posto della battuta di X:" (la battuta
# prima vale senza la bandiera), "Se almeno due indizi:", "Poi, per tutti:"; negli NPC "Con «voce» ...".
# Un blocco sono le battute subito dopo la sua riga, fino alla prima riga vuota.
GUARDIE = ["SEMPRE", "BANDIERA", "NON_BANDIERA", "SCELTA", "ALMENO_DUE", "VARIANTE_BANDIERA",
           "VARIANTE_NON_BANDIERA", "OGGETTO_E_NON_BANDIERA"]
SEMPRE = ("SEMPRE", 0, 0, 0)
INDIZI_DEL_CONDOTTO = ("INDIZIO_CARTA", "INDIZIO_ACQUA", "INDIZIO_ROCCIA")
OGGETTO_CRESCIA = 0          # GameState::oggetti[0], la Crescia di Pasqua (battaglia_dati.h)
NESSUNA = 255


def indice(b):
    return TUTTE.index(b)


class Battuta:
    """Una battuta del copione: si spacchetta come (chi, espressione, frase, dove), come nella v1, e porta
    la guardia, le voci e gli effetti di una SCELTA."""

    def __init__(self, chi, espressione, frase, dove, guardia=SEMPRE):
        self.d = {"chi": chi, "espr": espressione or "calmo", "frase": frase.strip(), "dove": dove,
                  "guardia": guardia, "voci": None, "accende": (NESSUNA, NESSUNA), "consuma": -1, "fase": None}

    def __getitem__(self, k):
        return tuple(self)[k] if isinstance(k, int) else self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def __iter__(self):
        return iter((self.d["chi"], self.d["espr"], self.d["frase"], self.d["dove"]))

    def __len__(self):
        return 4


def battuta(chi, espressione, frase, dove, guardia=SEMPRE):
    return Battuta(chi, espressione, frase, dove, guardia)


def id_voce(base, k):
    return f"{base}_{'AB'[k]}"


class Varianti:
    """Lo stato del lettore delle varianti dentro una scena o un NPC."""

    def __init__(self, dove):
        self.dove = dove
        self.guardia = SEMPRE
        self.nel_blocco = 0
        self.ultima_bandiera = None
        self.scelta = None              # l'ultima battuta SCELTA
        self.prossima_scelta = SEMPRE   # la guardia della prossima SCELTA (il D3 della popolana)

    def voce(self, etichetta, n):
        voci = self.scelta["voci"] if self.scelta else None
        if not voci:
            raise ErroreStoria(f"{self.dove}:{n}: blocco «{etichetta}» senza un menu SCELTA prima")
        e = etichetta.lower()
        for k, v in enumerate(voci):
            if e in v.lower() or v.lower() in e:
                return k
        raise ErroreStoria(f"{self.dove}:{n}: «{etichetta}» non e' una voce di {voci}")

    def riga(self, riga, n, battute):
        """Legge una riga che non e' una battuta; ritorna True se era una riga di variante."""
        r = riga.strip()
        if not r:
            if self.nel_blocco:
                self.guardia, self.nel_blocco = SEMPRE, 0
            return False
        m = re.match(r"^(?:Se|Con) «(.+?)»(.*):$", r)
        if m:
            k = self.voce(m.group(1), n)
            flag = re.findall(r"`([A-Z_0-9]+)`", m.group(2))
            if flag:
                self.scelta["accende"] = tuple(indice(flag[0]) if j == k else self.scelta["accende"][j] for j in (0, 1))
            if "si toglie 1 Crescia" in m.group(2):
                self.scelta["consuma"] = OGGETTO_CRESCIA
            self.guardia, self.nel_blocco = ("SCELTA", k, 0, 0), 0
            return True
        if r == "Se almeno due indizi:":
            self.guardia, self.nel_blocco = ("ALMENO_DUE",) + tuple(indice(b) for b in INDIZI_DEL_CONDOTTO), 0
            return True
        m = re.match(r"^Se `([A-Z_0-9]+)`(, al posto della battuta di \w+)?.*:$", r)
        if m:
            b = indice(m.group(1))
            if m.group(2):
                prima = battute[-1]
                prima["guardia"] = ("NON_BANDIERA", b, 0, 0)
            self.guardia, self.nel_blocco, self.ultima_bandiera = ("BANDIERA", b, 0, 0), 0, b
            return True
        if r == "Altrimenti:":
            self.guardia, self.nel_blocco = ("NON_BANDIERA", self.ultima_bandiera, 0, 0), 0
            return True
        if r == "Poi, per tutti:":
            self.guardia, self.nel_blocco = SEMPRE, 0
            return True
        m = re.search(r"almeno una Crescia di Pasqua e non c'è `([A-Z_0-9]+)`", r)
        if m:
            self.prossima_scelta = ("OGGETTO_E_NON_BANDIERA", OGGETTO_CRESCIA, indice(m.group(1)), 0)
            return True
        return False

    def aggiungi(self, b, battute):
        if b["chi"] == "SCELTA":
            b["voci"] = tuple(v.strip() for v in b["frase"].split(" / "))
            if len(b["voci"]) != 2:
                raise ErroreStoria(f"{b['dove']}: una SCELTA ha due voci")
            b["guardia"], self.prossima_scelta = self.prossima_scelta, SEMPRE
            self.scelta = b
        else:
            b["guardia"] = self.guardia if b["guardia"] == SEMPRE else b["guardia"]
        if self.guardia != SEMPRE:
            self.nel_blocco += 1
        battute.append(b)


def togli_scelte_senza_blocchi(battute):
    """Una SCELTA che nessun blocco segue (il «Sì, è ora / Non ancora» di B-05) non conta: non si recita."""
    usate = set()
    scelta = None
    for b in battute:
        if b["chi"] == "SCELTA":
            scelta = id(b)
        elif b["guardia"][0] == "SCELTA":
            usate.add(scelta)
    return [b for b in battute if b["chi"] != "SCELTA" or id(b) in usate]


def bandiere_delle_scelte(battute):
    return {TUTTE[a] for b in battute if b["chi"] == "SCELTA" for a in b["accende"] if a != NESSUNA}


def bandiere_in(testo):
    return [b for b in re.findall(r"`([A-Z_0-9]+)`", testo) if b in BANDIERE]


def leggi_scene(testi_file):
    """[{codice, titolo, luogo, richieste, vietate, imposta, battute}] dalle pagine delle scene."""
    scene = []
    for nome, testo in testi_file:
        attuale = None
        for n, riga in enumerate(testo.splitlines(), 1):
            m = re.match(r"^## ([A-Z0-9]+-\d+[a-z]?) · (.+)$", riga)
            if m:
                attuale = {"codice": m.group(1), "titolo": m.group(2), "luogo": "", "richieste": [], "vietate": [],
                           "imposta": [], "battute": [], "in_battaglia": [], "dove": f"{nome}:{n}"}
                varianti = Varianti(nome)
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
                    if " né " in valore:
                        prima, _, dopo = valore.partition(" né ")
                    attuale["richieste"] = bandiere_in(prima)
                    attuale["vietate"] = bandiere_in(dopo)
                    altre = [b for b in re.findall(r"`([A-Z_0-9]+)`", valore) if b not in BANDIERE]
                    if altre:
                        raise ErroreStoria(f"{nome}:{n}: bandiere sconosciute nella condizione: {altre}")
                elif chiave == "Imposta":
                    attuale["imposta"] = bandiere_in(valore)
                continue
            g = RIGA_BATTAGLIA.match(riga)
            if g:
                evento, chi, espressione, frase = g.groups()
                if chi not in SENZA_NOME and chi not in PARLANTI:
                    raise ErroreStoria(f"{nome}:{n}: parlante '{chi}' senza nome a schermo in PARLANTI")
                attuale["in_battaglia"].append((evento, battuta(chi, espressione, frase, f"{nome}:{n}")))
                continue
            b = RIGA_BATTUTA.match(riga)
            if b:
                chi, espressione, frase = b.groups()
                if espressione and espressione not in ESPRESSIONI:
                    raise ErroreStoria(f"{nome}:{n}: espressione '{espressione}' sconosciuta")
                if chi not in SENZA_NOME and chi not in PARLANTI:
                    raise ErroreStoria(f"{nome}:{n}: parlante '{chi}' senza nome a schermo in PARLANTI")
                varianti.aggiungi(battuta(chi, espressione, frase, f"{nome}:{n}"), attuale["battute"])
                continue
            varianti.riga(riga, n, attuale["battute"])
    for s in scene:
        s["battute"] = togli_scelte_senza_blocchi(s["battute"])
        scelte = bandiere_delle_scelte(s["battute"])
        s["imposta"] = [b for b in s["imposta"] if b not in scelte]
    return scene


def leggi_npc(testo, file=FILE_NPC):
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
            attuale = {"area": area, "nome": m.group(1), "frasi": [], "imposta": None, "imposta_fasi": 0}
            varianti = Varianti(f"{file} ({m.group(1)})")
            fase_corrente = None
            nota = re.search(r"(una qualunque sua battuta|la battuta del (ULTIMATUM|DIGIUNO|NOTTE)) imposta `([A-Z_0-9]+)`",
                             riga)
            if nota:
                attuale["imposta"] = indice(nota.group(3))
                attuale["imposta_fasi"] = 7 if nota.group(2) is None else 1 << FASI.index(nota.group(2))
            npc.append(attuale)
            continue
        if attuale is None:
            continue
        m = RIGA_NPC.match(riga)
        if m:
            fase, non, flag, chi, espressione, frase = m.groups()
            b = battuta(chi, espressione, frase, f"{FILE_NPC} ({attuale['nome']})")
            if flag:
                b["guardia"] = ("VARIANTE_NON_BANDIERA" if non else "VARIANTE_BANDIERA", indice(flag), 0, 0)
            fase_corrente = fase
            b["fase"] = fase
            varianti.guardia, varianti.nel_blocco = SEMPRE, 0
            varianti.aggiungi(b, attuale["frasi"])
            continue
        b = RIGA_BATTUTA.match(riga)
        if b and fase_corrente:
            chi, espressione, frase = b.groups()
            nuova = battuta(chi, espressione, frase, f"{FILE_NPC} ({attuale['nome']})")
            nuova["fase"] = fase_corrente
            varianti.aggiungi(nuova, attuale["frasi"])
            continue
        varianti.riga(riga, 0, attuale["frasi"])
    return [p for p in npc if p["frasi"]]


def id_battuta(codice, k):
    return "C_" + codice.replace("-", "_").upper() + f"_{k:02d}"


for _chi, _amico in AMICI.items():
    PARLANTI.setdefault(_chi, _amico["nome"])


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
    return "R_" + codice.replace("-", "_").upper() + f"_{k:02d}"


def id_titolo(codice):
    return "SCENA_" + codice.replace("-", "_").upper()


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
    richieste = []
    for p in npc:
        ancora = AMICI[p["amico"]]["ancora"] if p.get("amico") else None
        richieste.append((p, p["area"], ancora))
    for p in npc:
        if p.get("amico") and AMICI[p["amico"]].get("borgo"):
            # con il borgo dentro: accampati in Sant'Andrea, dietro Porta Romana (il varco verso Sant'Agostino)
            richieste.append((p, "SANT_ANDREA", "varco B"))
    for p, area_id, ancora in richieste:
        a = aree[area_id]
        g = a["griglia"]
        varchi = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in G.VARCHI]
        fermi = varchi + list(a["spawn"].values()) + occupati.get(area_id, [])
        cx, cy = punto_dell_ancora(a, ancora, G)
        scelto = None
        for raggio in range(0, 90):
            for y in range(max(1, cy - raggio), min(a["altezza"] - 1, cy + raggio + 1)):
                for x in range(max(1, cx - raggio), min(a["larghezza"] - 1, cx + raggio + 1)):
                    if max(abs(x - cx), abs(y - cy)) != raggio:
                        continue
                    libero = all(not G.solida(g[y + j][x + i]) and g[y + j][x + i] not in G.VARCHI
                                 for i in (-1, 0, 1) for j in (-1, 0, 1))
                    if libero and all(max(abs(x - u), abs(y - v)) >= 3 for u, v in fermi):
                        scelto = (x, y)
                        break
                if scelto:
                    break
            if scelto:
                break
        if not scelto:
            raise ErroreStoria(f"nessun posto per {p['nome']} in {area_id}")
        occupati.setdefault(area_id, []).append(scelto)
        posti.append(scelto)
    # i primi len(npc) sono i posti di sempre; poi quelli del borgo, nell'ordine degli NPC del borgo
    principali = posti[:len(npc)]
    borgo = iter(posti[len(npc):])
    return [(xy, next(borgo) if p.get("amico") and AMICI[p["amico"]].get("borgo") else None)
            for p, xy in zip(npc, principali)]


def punto_dell_ancora(a, ancora, G):
    """Il punto da cui cercare il posto di un NPC: lo spawn 0, o davanti al monumento, al varco o
    all'edificio nuovo dell'ancora (se l'edificio non c'e' ancora, lo spawn 0)."""
    if ancora:
        tipo, _, nome = ancora.partition(" ")
        if tipo == "varco":
            celle = [(x, y) for y, r in enumerate(a["griglia"]) for x, c in enumerate(r) if c == nome]
            return sum(x for x, _ in celle) // len(celle), sum(y for _, y in celle) // len(celle)
        chiave = nome if tipo == "edificio" else ancora
        if chiave in a.get("edifici", {}):
            x0, y0, w, h = a["edifici"][chiave]
            return x0 + w // 2, min(a["altezza"] - 2, y0 + h + 1)
    return a["spawn"][0]


def leggi_copione():
    testi = [(f, open(os.path.join(COPIONE, f), encoding="utf-8").read()) for f in FILE_SCENE]
    scene = leggi_scene(testi)
    npc = leggi_npc(open(os.path.join(COPIONE, FILE_NPC), encoding="utf-8").read())
    amici = leggi_npc(open(os.path.join(COPIONE, FILE_AMICI), encoding="utf-8").read(), FILE_AMICI)
    for p in amici:
        p["amico"] = parlante_dell_amico(p)
    return scene, npc + amici


def parlante_dell_amico(p):
    """L'amico di una scheda: il parlante delle sue battute, che deve stare in dati/amici.json."""
    chi = {b[0] for b in p["frasi"] if b[0] not in SENZA_NOME and b[0] not in ("UBALDO", "GIORGIO", "ANTONIO")}
    if len(chi) != 1 or next(iter(chi)) not in AMICI:
        raise ErroreStoria(f"{FILE_AMICI} ({p['nome']}): parlante {sorted(chi)} senza voce in dati/amici.json")
    return next(iter(chi))


def figura_dell_npc(p):
    """La figura nel gioco: per un NPC d'ambiente quella del mestiere, per un amico la sua (dati/amici.json)."""
    if p.get("amico"):
        a = AMICI[p["amico"]]
        return FN.figura_composta(a["base"], a["accessorio"])
    return FN.figura_composta(FN.figura_di(p["nome"]), None)


def controlla(scene):
    codici = [s["codice"] for s in scene]
    if sorted(codici) != sorted(AREE):
        raise ErroreStoria(f"scene del copione {codici} diverse da quelle note {sorted(AREE)}")
    for s in scene:
        area = AREE[s["codice"]]
        parola = PAROLE_LUOGO.get(area)
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
        for k, b in enumerate(s["battute"]):
            chi, _, frase, _ = b
            if b["voci"]:
                righe += [f"{id_voce(id_battuta(s['codice'], k), j):26s}| SCELTA  | {v}" for j, v in enumerate(b["voci"])]
                continue
            righe.append(f"{id_battuta(s['codice'], k):26s}| DIALOGO | {frase}")
            # il narratore parla anche nelle bande delle cutscene: la stessa frase, al massimo 2 righe
            if chi == "NARRATORE":
                righe.append(f"{id_narratore(s['codice'], k):26s}| NARRATORE | {frase}")
    for i, p in enumerate(npc):
        for k, b in enumerate(p["frasi"]):
            if b["voci"]:
                righe += [f"{id_voce(id_npc(i, k), j):26s}| SCELTA  | {v}" for j, v in enumerate(b["voci"])]
                continue
            righe.append(f"{id_npc(i, k):26s}| DIALOGO | {b['frase']}")
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
            "enum class TipoGuardia : uint8_t", "{"] + [f"    {g}," for g in GUARDIE] + ["};", "",
            "// La guardia di una battuta: la si recita solo se vale (le varianti del copione v2). a, b, c sono",
            "// bandiere (0-127), la voce scelta nell'ultimo menu (SCELTA) o l'oggetto (OGGETTO_E_NON_BANDIERA).",
            "struct Guardia", "{", "    TipoGuardia tipo;", "    uint8_t a;", "    uint8_t b;", "    uint8_t c;", "};", "",
            "inline constexpr uint8_t NESSUNA_BANDIERA = 255;", "",
            "struct Battuta", "{", "    testi::TestoId testo;         // per una SCELTA: la prima voce",
            "    testi::TestoId parlante;     // per un PERSONAGGIO; per una SCELTA: la seconda voce",
            "    TipoBattuta tipo;", "    Espressione espressione;", "    uint8_t guardia;              // GUARDIA",
            "    uint8_t accende[2];          // SCELTA: la bandiera che accende ogni voce, o NESSUNA_BANDIERA",
            "    int8_t consuma;              // SCELTA: l'oggetto che la prima voce consuma, o -1", "};", "",
            "struct Scena", "{", "    const char* codice;", "    testi::TestoId titolo;",
            "    bool cutscene;", "    int8_t regia;                // la cutscene (regia::CUTSCENE_DATI), -2 dentro la precedente", "    int8_t area;                 // mondo::AreaId, o NESSUNA_AREA (a schermo intero)",
            "    uint64_t richieste;          // tutte accese", "    uint64_t vietate;            // nessuna accesa",
            "    uint64_t imposta;            // accese alla fine", "    int8_t segue;                // la scena che deve essere gia' fatta, o -1",
            "    int8_t battaglia;            // battaglia::INCONTRO, o -1", "    uint16_t prima_battuta;",
            "    uint16_t battute;", "};", ""]
    guardie = [SEMPRE]

    def riga_battuta(b, base, npc=False):
        chi, espr, _, _ = b
        if b["guardia"] not in guardie:
            guardie.append(b["guardia"])
        if b["voci"]:
            testo, parlante = (f"testi::TestoId::{id_voce(base, j)}" for j in (0, 1))
        else:
            testo = f"testi::TestoId::{base}"
            parlante = f"testi::TestoId::{id_parlante(chi)}" if chi in PARLANTI else testo
        tipo = TIPI[tipo_di(chi)]
        if npc and not b["voci"]:
            tipo = "PERSONAGGIO" if chi in PARLANTI else "SISTEMA"
        return (f"    {{ {testo}, {parlante}, TipoBattuta::{tipo}, Espressione::{espr.upper()}, "
                f"{guardie.index(b['guardia'])}, {{ {b['accende'][0]}, {b['accende'][1]} }}, {b['consuma']} }},")

    battute = []
    righe_scene = []
    for s in scene:
        prima = len(battute)
        for k, b in enumerate(s["battute"]):
            battute.append(riga_battuta(b, id_battuta(s["codice"], k)))
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
            "    uint8_t frasi[3];", "    uint8_t figura;               // FIGURA_NPC (tools/figure_npc.py)",
            "    uint8_t imposta;              // la bandiera che accende parlando, o NESSUNA_BANDIERA",
            "    uint8_t imposta_fasi;         // in quali fasi (bit 0 ULTIMATUM, 1 DIGIUNO, 2 NOTTE)",
            "    uint8_t tx_borgo;             // del borgo: con BORGO_DENTRO, in DIGIUNO e NOTTE, sta qui in Sant'Andrea",
            "    uint8_t ty_borgo;",
            "    bool del_borgo;", "};", ""]
    figure = []
    frasi = []
    righe_npc = []
    for i, p in enumerate(npc):
        per_fase = {f: [] for f in FASI}
        for k, b in enumerate(p["frasi"]):
            per_fase[b["fase"]].append((k, b))
        prime, conte = [], []
        for f in FASI:
            # prima le varianti "(se BANDIERA)" (vince la prima che vale), poi il resto, in ordine
            ordinate = sorted(per_fase[f], key=lambda kb: 0 if kb[1]["guardia"][0].startswith("VARIANTE") else 1)
            prime.append(str(len(frasi)) if ordinate else "0xFFFF")
            conte.append(str(len(ordinate)))
            for k, b in ordinate:
                frasi.append(riga_battuta(b, id_npc(i, k), npc=True))
        (tx, ty), borgo = posti[i]
        imposta = p["imposta"] if p["imposta"] is not None else NESSUNA
        figura = figura_dell_npc(p)
        if figura not in figure:
            figure.append(figura)
        bx, by = borgo or (0, 0)
        righe_npc.append(f"    {{ int8_t(mondo::AreaId::{p['area']}), {tx}, {ty}, {{ {', '.join(prime)} }}, {{ {', '.join(conte)} }}, "
                         f"{figure.index(figura)}, {imposta}, {p['imposta_fasi']}, {bx}, {by}, {'true' if borgo else 'false'} }},"
                         f"  // {p['nome']}")
    out += [f"inline constexpr int FRASI_NPC = {len(frasi)};", "inline constexpr Battuta FRASE_NPC[FRASI_NPC] = {"] + frasi + ["};", ""]
    out += [f"inline constexpr int NPC = {len(npc)};", "inline constexpr Npc NPC_AMBIENTE[NPC] = {"] + righe_npc + ["};", ""]
    out += [f"inline constexpr int GUARDIE = {len(guardie)};", "inline constexpr Guardia GUARDIA[GUARDIE] = {"]
    out += [f"    {{ TipoGuardia::{g[0]}, {g[1]}, {g[2]}, {g[3]} }}," for g in guardie] + ["};", ""]
    out += ["// Le bandiere delle quest e degli indizi (64-127, GameState::quest), per nome."]
    out += [f"inline constexpr uint8_t {b} = {PRIMA_QUEST + i};" for i, b in enumerate(BANDIERE_QUEST)] + [""]
    out += ["// Le figure degli NPC, 16x32 (8 tile in mappatura 1D) con la palette dei popolani: quelle dei",
            "// mestieri (tools/figure_npc.py) e quelle degli amici (base e accessorio, dati/amici.json).",
            f"inline constexpr int FIGURE_NPC = {len(figure)};",
            "inline constexpr uint32_t FIGURA_NPC[FIGURE_NPC][8 * 8] = {"]
    for f in figure:
        parole = FN.parole(f)
        out.append("    {")
        out += ["        " + ", ".join(f"0x{v:08X}" for v in parole[k:k + 8]) + "," for k in range(0, 64, 8)]
        out.append("    },")
    out += ["};", ""]
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
