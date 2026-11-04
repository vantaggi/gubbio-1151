#!/usr/bin/env python3
"""Il motore della storia dalle pagine del copione v1 (copione/*.md): scrive testi/copione.testi
(le battute e i nomi di chi parla, per tools/genera_testi.py) e include/storia.h (le bandiere, le
scene con luogo, condizione, bandiere che accendono e battaglia, gli NPC d'ambiente per fase).

Le scene vengono da 00_prologo.md, 01_atto_I.md e 02_bottaccione_epilogo.md (tabelle Luogo,
Condizione, Imposta, Battaglia; battute "- PARLANTE (espressione): testo"). Gli NPC da
03_npc_ambiente.md ("- FASE: PARLANTE: testo"). Le quest di 04_quest.md sono descritte in QUEST
qui sotto (tests/test_storia.py le controlla contro la tabella del copione); le loro battute (proposta,
attesa, consegna, raccolta, dopo, indizi, infiltrato) le legge leggi_quest(), e gli oggetti da raccogliere
sulla mappa sono in RACCOLTE, con il posto scelto sulla griglia di tools/genera_mondo.py (SV2c).

    python tools/genera_storia.py            # controlla che i file generati siano aggiornati
    python tools/genera_storia.py --scrivi   # li riscrive
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_npc as FN  # noqa: E402
import figure_popolo as FP  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIONE = os.path.join(RADICE, "copione")
USCITA_H = os.path.join(RADICE, "include", "storia.h")
USCITA_TESTI = os.path.join(RADICE, "testi", "copione.testi")
FILE_SCENE = ("00_prologo.md", "01_atto_I.md", "02_bottaccione_epilogo.md")
FILE_NPC = "03_npc_ambiente.md"
FILE_AMICI = "05_npc_amici.md"
FILE_MESTIERI = "06_npc_mestieri.md"
# I mestieri (pezzo VIVA): figura di tools/figure_popolo.py e ancora di ognuno, dal nome in grassetto.
MESTIERI = __import__("json").load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                    "dati", "mestieri.json"), encoding="utf-8"))["mestieri"]
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
         "DONO_MATTEO", "INDIZIO_LUCIA", "INDIZIO_VENDITORE", "INDIZIO_FONTANIERE",
         # le quest consegnate (04_quest.md): le accende storia::consegna_quest(), una volta sola
         "Q_SM01_CONSEGNATA", "Q_SA01_CONSEGNATA", "Q_SP01_CONSEGNATA",
         # SV2c, le quest giocabili: la quest presa dal datore (la proposta), poi un bit per ogni oggetto
         # dell'obiettivo (il contatore e' quanti sono accesi): i 3 blocchi di ferro, le 4 radici, la Rosa
         "Q_SM01_PRESA", "Q_SA01_PRESA", "Q_SP01_PRESA", "FERRO_1", "FERRO_2", "FERRO_3",
         "ELLEBORO_1", "ELLEBORO_2", "ELLEBORO_3", "ELLEBORO_4", "ROSA_RIPRESA",
         # T2, la gola: i due forzieri negli slarghi, presi una volta (88-89)
         "FORZIERE_CRESCIA", "FORZIERE_BISCOTTI",
         # F10, i nemici che mancavano: la battaglia breve di B-03 vinta (90), le tre guardie delle fornaci di
         # Q-SM01 battute (91-93). Ogni scontro si gioca una volta sola; il salvataggio resta v3
         "GUERRIERI_VINTI", "GUARDIA_FORNACE_1", "GUARDIA_FORNACE_2", "GUARDIA_FORNACE_3",
         # INTC, gli interni: i due doni (Padellino, Valenza), dati una volta sola (94-95)
         "DONO_PADELLINO", "DONO_VALENZA"]
PRIMA_QUEST = 64
TUTTE = BANDIERE + [None] * (PRIMA_QUEST - len(BANDIERE)) + BANDIERE_QUEST

# Le bandiere che nessuna scena legge (nelle condizioni) ma che legge il gioco, e dove.
LETTE_DAL_GIOCO = {
    "GIORGIO_NEL_GRUPPO": "storia::gruppo(): Giorgio combatte da qui",
    "IMBOSCATA_STRADONI": "storia::scontro_attivo(): l'Imboscata sulla mappa non torna",
    "CORRADO_SCONFITTO": "storia::scontro_attivo(): Corrado sulla mappa non torna",
    "CRONACA_V1_FINITA": "Storia::recita(): il cartello dei titoli di coda",
    "RUFINO_ASCOLTATO": "storia::scudi_in_meno(): Corrado entra nel duello con uno scudo in meno",
    "Q_SM01_CONSEGNATA": "storia::scudi_in_meno() e storia::consegna_quest(): lo scudo di Corrado, una consegna sola",
    "Q_SA01_CONSEGNATA": "storia::consegna_quest(): una consegna sola",
    "Q_SP01_CONSEGNATA": "storia::consegna_quest(): una consegna sola",
    # SV2c: le quest giocabili (storia_logica.h, QUEST_GIOCO e RACCOLTA di storia.h)
    "Q_SM01_PRESA": "storia::momento_del_datore(): Raniero passa dalla proposta all'attesa e alla consegna",
    "Q_SA01_PRESA": "storia::momento_del_datore() e la prima radice: Agnese, e Ubaldo se la quest non e' presa",
    "Q_SP01_PRESA": "storia::momento_del_datore() e storia::indizio_dell_npc(): Fra' Bernardo e gli indizi",
    "FERRO_1": "storia::pezzi_raccolti(): il contatore dei blocchi; il blocco non torna sulla mappa",
    "FERRO_2": "storia::pezzi_raccolti(): il contatore dei blocchi; il blocco non torna sulla mappa",
    "FERRO_3": "storia::pezzi_raccolti(): il contatore dei blocchi; il blocco non torna sulla mappa",
    "ELLEBORO_1": "storia::pezzi_raccolti(): il contatore delle radici; la radice non torna sulla mappa",
    "ELLEBORO_2": "storia::pezzi_raccolti(): il contatore delle radici; la radice non torna sulla mappa",
    "ELLEBORO_3": "storia::pezzi_raccolti(): il contatore delle radici; la radice non torna sulla mappa",
    "ELLEBORO_4": "storia::pezzi_raccolti(): il contatore delle radici; la radice non torna sulla mappa",
    "ROSA_RIPRESA": "storia::pezzi_raccolti() e storia::infiltrato_presente(): la Rosa ripresa, l'infiltrato sparito",
    "INDIZIO_LUCIA": "storia::infiltrato_presente(): con i tre indizi l'infiltrato compare sotto le Logge",
    "INDIZIO_VENDITORE": "storia::infiltrato_presente(): con i tre indizi l'infiltrato compare sotto le Logge",
    "INDIZIO_FONTANIERE": "storia::infiltrato_presente(): con i tre indizi l'infiltrato compare sotto le Logge",
    # T2, la gola del Bottaccione (storia_logica.h, FORZIERE di storia.h)
    "MIASMI_VISTI": "storia::respira_i_miasmi(): i miasmi feriscono solo dopo l'avviso di Ubaldo (B-02)",
    "PIANO_DI_CORRADO": "storia::sentinelle_presenti(): i due soldati di B-03 stanno oltre l'arco fino al piano",
    "CORRADO_INCONTRATO": "storia::varco_chiuso() e storia::gia_incontrata(): l'uscita del Condotto chiusa nel duello, "
                          "le battute di B-04 dette una volta",
    "FORZIERE_CRESCIA": "storia::forziere_chiuso(): il forziere dello slargo della striscia nera, preso una volta",
    "FORZIERE_BISCOTTI": "storia::forziere_chiuso(): il forziere dello slargo dell'arco, preso una volta",
    "DONO_PADELLINO": "storia::dono_dell_npc(): la Crescia di Padellino, data una volta",
    "DONO_VALENZA": "storia::dono_dell_npc(): i Biscotti di Valenza, dati una volta",
    # F10, i nemici che mancavano (storia_logica.h, GUARDIA_FORNACE di storia.h)
    "GUERRIERI_VINTI": "storia::guerrieri_da_battere(): la battaglia breve di B-03 si gioca una volta sola",
    "GUARDIA_FORNACE_1": "storia::guardia_presente() e storia::raccolta_libera(): la guardia non torna, il blocco si prende",
    "GUARDIA_FORNACE_2": "storia::guardia_presente() e storia::raccolta_libera(): la guardia non torna, il blocco si prende",
    "GUARDIA_FORNACE_3": "storia::guardia_presente() e storia::raccolta_libera(): la guardia non torna, il blocco si prende",
    # F10, i Ceri risvegliati di A1-08: in battaglia il Fervore parte piu' alto; nella Basilica i ceri accesi
    "CERI_RISVEGLIATI": "storia::ceri_accesi(): il Fervore iniziale dei Santi piu' alto, i tre ceri accesi sull'altare",
}

# Quelle che il gioco non legge ancora: sono in docs/bandiere_da_fare.md, con cosa dovranno fare.
DA_FARE = []

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
# F10: C5 (il risveglio dei Ceri) prima del narratore di A1-08, che la cutscene dice nelle bande; C6 (la visione
# nel vetro) in A1-09 dopo lo scambio dei due indizi e prima che Ubaldo nomini il Bottaccione; le presentazioni
# dei luoghi all'inizio della scena: C7S in A1-07 (prima di «Ingresso»), C7B in B-01 (prima di Antonio).
INSERTI = {"A1-01": {1: "C3U", 2: "C3G", 4: "C2", 8: "C2P"}, "A1-04": {1: "C3A"}, "B-04": {0: "C3C"},
           "A1-07": {0: "C7S"}, "A1-08": {9: "C5"}, "A1-09": {3: "C6"}, "B-01": {0: "C7B"}}
# Le cartoline dei luoghi che partono entrando nell'area della scena, non quando la scena comincia: A1-07 parte
# toccando l'Imboscata a meta' salita (49,44), ma C7S presenta gli Stradoni al primo tornante (copione, «Ingresso»).
# Partono la prima volta che si entra nell'area con la scena pronta (pronta(): non fatta, condizione accesa) e la
# cutscene non vista. Ognuna resta anche inserto alla battuta 0 della sua scena: li' non riparte (gia' vista), ma
# la recita chi non cammina (GUBBIO_AVVIO=8). Non deve coprire battute del narratore della scena: vista all'ingresso,
# la scena le leggerebbe di nuovo nella vista di gioco.
ALL_INGRESSO = {"A1-07": "C7S"}

# Le battaglie delle scene (battaglia::INCONTRO). Quelle con un nemico sulla mappa partono toccandolo;
# gli Spettri del Dubbio di A1-08 compaiono durante il rito: la scena parte entrando nella Basilica.
BATTAGLIE = {"A1-04": 0, "A1-07": 1, "B-04": 2, "A1-08": 3, "B-03": 4}
# Le battaglie a meta' scena: prima della battuta k (nell'ordine della scena) si combatte, poi la scena va avanti.
# In B-03 i Guerrieri della Roccia si battono dopo l'ascolto, prima del ragazzo eugubino (la regia del dilemma D2:
# «il gruppo esce dall'arco. Battaglia breve con i due Guerrieri»). Le altre scene combattono alla fine.
BATTAGLIA_A_META = {"B-03": 8}
# La bandiera (64-127) che una battaglia a meta' scena accende quando e' vinta: non si rigioca.
VINTA_A_META = {"B-03": "GUERRIERI_VINTI"}

PARLANTI = {"UBALDO": "Ubaldo", "GIORGIO": "Giorgio", "ANTONIO": "Antonio", "GUIDO": "Console Guido",
            "ARALDO": "Araldo di Perugia", "CORRADO": "Corrado di Spoleto", "CECCO": "Cecco il Balestriere",
            "GUERRIERO": "Guerriero di Spoleto", "SPIA": "Spia umbra", "SPETTRO": "Spettro del Dubbio",
            "NELLO": "Nello", "ANDREUCCIO": "Andreuccio", "FAZIO": "Fazio", "LAURETTA": "Lauretta",
            "FOLLA": "Folla", "RAGAZZO": "Ragazzo eugubino", "FANTE": "Fante di Perugia", "CANONICO": "Canonico",
            # i datori delle quest e chi parla nelle loro battute (04_quest.md)
            "RANIERO": "Mastro Raniero", "AGNESE": "Monna Agnese", "FRA' BERNARDO": "Fra' Bernardo",
            "FERITO": "Ferito", "INFILTRATO": "Infiltrato"}
SENZA_NOME = {"NARRATORE", "AREA", "SISTEMA", "OBIETTIVO", "SCELTA"}
ESPRESSIONI = ["calmo", "preoccupato", "deciso"]
TIPI = ["PERSONAGGIO", "NARRATORE", "AREA", "SISTEMA", "OBIETTIVO", "SCELTA"]
FASI = ["ULTIMATUM", "DIGIUNO", "NOTTE"]

# Le tre quest (04_quest.md): chi le da', da quando, dove si compiono, dove si consegnano, entro quando
# (la conferma dell'alba che avvia E-01: dopo E-01, ATTO_I_COMPLETATO, nessuna consegna), la bandiera della
# consegna e il premio (l'oggetto, indice di GameState::oggetti come battaglia::OggettoId, e quanti).
OGGETTI = ["CRESCIA", "CENERE", "BACCALA", "BISCOTTI", "VINO"]     # battaglia::OggettoId, nell'ordine
# SV2c: la bandiera della quest presa, i pezzi dell'obiettivo (bandiere consecutive: il contatore e' quante sono
# accese) e dove sta il datore (l'ancora: un monumento dell'area, None per lo spawn 0, come per gli NPC).
QUEST = [
    {"id": "Q-SM01", "datore": "SAN_MARTINO", "da": "ULTIMATUM_RICEVUTO", "obiettivo": "TEATRO_ROMANO",
     "consegna": "SAN_MARTINO", "entro": "ATTO_I_COMPLETATO", "consegnata": "Q_SM01_CONSEGNATA",
     "premio": ("CRESCIA", 3), "nome_premio": "Crescia di Pasqua",
     "presa": "Q_SM01_PRESA", "pezzi": ["FERRO_1", "FERRO_2", "FERRO_3"], "ancora": None},
    {"id": "Q-SA01", "datore": "SANT_ANDREA", "da": "CITTA_IN_DIGIUNO", "obiettivo": "BOTTACCIONE",
     "consegna": "SANT_ANDREA", "entro": "ATTO_I_COMPLETATO", "consegnata": "Q_SA01_CONSEGNATA",
     "premio": ("BISCOTTI", 3), "nome_premio": "Biscotti all'anice",
     "presa": "Q_SA01_PRESA", "pezzi": ["ELLEBORO_1", "ELLEBORO_2", "ELLEBORO_3", "ELLEBORO_4"], "ancora": "san_marziale"},
    {"id": "Q-SP01", "datore": "SAN_PIETRO", "da": "CITTA_IN_DIGIUNO", "obiettivo": "SAN_PIETRO",
     "consegna": "SAN_PIETRO", "entro": "ATTO_I_COMPLETATO", "consegnata": "Q_SP01_CONSEGNATA",
     "premio": ("CENERE", 1), "nome_premio": "Crescia sotto la cenere",
     "presa": "Q_SP01_PRESA", "pezzi": ["ROSA_RIPRESA"], "ancora": "san_pietro"},
]
FILE_QUEST = "04_quest.md"

# Gli oggetti da raccogliere sulla mappa (SV2c): la bandiera, l'area che dice il copione, le celle accanto a cui
# sta (i simboli della griglia di tools/genera_mondo.py) e il punto dell'area verso cui cercarlo (frazioni di
# larghezza e altezza). Il posto lo sceglie posti_delle_raccolte(): una cella calpestabile col gioco, raggiungibile
# dallo spawn 0, lontana da varchi, spawn, NPC, nemici sulla mappa e dagli altri oggetti.
# Q-SM01: le fornaci basse sotto le arcate del Teatro Romano. Q-SA01: le rocce bagnate della Strada del Bottaccione
# e della gola, una dentro i miasmi e una sotto gli archi di B-03 (04_quest.md); si raccolgono anche dopo B-05.
RACCOLTE = [
    {"bandiera": "FERRO_1", "area": "TEATRO_ROMANO", "vicino": "U", "verso": (0.22, 0.38), "figura": "ferro"},
    {"bandiera": "FERRO_2", "area": "TEATRO_ROMANO", "vicino": "U", "verso": (0.55, 0.28), "figura": "ferro"},
    {"bandiera": "FERRO_3", "area": "TEATRO_ROMANO", "vicino": "U", "verso": (0.86, 0.44), "figura": "ferro"},
    {"bandiera": "ELLEBORO_1", "area": "BOTTACCIONE", "vicino": "#", "verso": (0.75, 0.25), "figura": "elleboro"},
    {"bandiera": "ELLEBORO_2", "area": "GOLA_STRISCIA", "vicino": "k", "verso": (0.70, 0.30), "figura": "elleboro"},
    {"bandiera": "ELLEBORO_3", "area": "GOLA_MIASMI", "vicino": "g", "verso": (0.42, 0.45), "figura": "elleboro"},
    {"bandiera": "ELLEBORO_4", "area": "GOLA_ARCO", "vicino": "J", "verso": (0.50, 0.60), "figura": "elleboro"},
]
# Le aree dove il copione mette gli oggetti di ogni quest (il test controlla RACCOLTE contro queste).
AREE_DELLE_RACCOLTE = {"Q-SM01": {"TEATRO_ROMANO"},
                       "Q-SA01": {"BOTTACCIONE", "GOLA_STRISCIA", "GOLA_MIASMI", "GOLA_ARCO"}}
# L'infiltrato di Q-SP01: sotto le Logge dei Tiratori, con il mantello e il bastone del pellegrino; la battaglia
# e' la sua (F10, battaglia::INCONTRO 6): l'infiltrato e due spie umbre, come dice il copione.
INFILTRATO = {"area": "PIAZZA_QUARANTA_MARTIRI", "ancora": "loggia_tiratori", "figura": ("mercante", "lanterna_bastone"),
              "incontro": 6}
# F10: le guardie delle fornaci di Q-SM01, una per blocco di ferro («ognuna guardata da un Guerriero della Roccia
# visibile sulla mappa. Battuto il guerriero, il blocco si raccoglie toccando la fornace»). Ogni guardia sta a due
# celle dal suo blocco, dalla parte dello spawn 0 (chi arriva la incontra prima del ferro); la battaglia e' la
# guardia della fornace (battaglia::INCONTRO 5); vinta, la bandiera della guardia si accende e il blocco si prende.
GUARDIE_FORNACE = [{"raccolta": "FERRO_1", "bandiera": "GUARDIA_FORNACE_1"},
                   {"raccolta": "FERRO_2", "bandiera": "GUARDIA_FORNACE_2"},
                   {"raccolta": "FERRO_3", "bandiera": "GUARDIA_FORNACE_3"}]
INCONTRO_FORNACE = 5

# --- T2, la gola del Bottaccione ------------------------------------------------------------------------------
# Le scene che partono su una cella dell'area invece che entrando: B-02 sulla prima nebbia dei miasmi («primo
# ingresso in una zona di miasmi»), B-03 sotto l'arco del contrafforte («il gruppo e' nascosto sotto l'arco»).
# tools/disegna_gola.py (SBARRANO) controlla che quelle celle sbarrino la via da un varco all'altro: la scena non
# si salta, e la storia non si ferma.
INNESCHI = {"B-02": "g", "B-03": "J"}
# I due soldati di B-03 («stanno di guardia vicino a un fuoco»), con la figura del soldato: oltre l'arco, verso
# monte, a 'passi' colonne dall'ultima colonna dell'arco, uno in alto e uno in basso sulla via. Ci sono finche'
# PIANO_DI_CORRADO e' spenta (poi uno e' fuggito al Condotto e l'altro e' il ragazzo del dilemma).
SENTINELLE = {"area": "GOLA_ARCO", "oltre": "J", "passi": 5, "figura": "soldato", "quanti": 2}
# I forzieri negli slarghi della gola (tools/disegna_gola.py, SLARGHI): toccarli da' l'oggetto (fino al massimo che
# se ne porta) e accende la bandiera; non tornano. Le bandiere stanno nell'intervallo quest: il salvataggio resta v3.
FORZIERI = [
    {"bandiera": "FORZIERE_CRESCIA", "area": "GOLA_STRISCIA", "slargo": "gola_striscia", "oggetto": "CRESCIA",
     "quanti": 2, "testo": "FORZIERE_CRESCIA"},
    {"bandiera": "FORZIERE_BISCOTTI", "area": "GOLA_ARCO", "slargo": "gola_arco", "oggetto": "BISCOTTI",
     "quanti": 3, "testo": "FORZIERE_BISCOTTI"},
]

# I doni degli interni (INTC, interni/COPIONE_INTERNI.md sez. 4): dopo le sue battute, una volta sola, l'amico da'
# l'oggetto (fino al massimo che se ne porta) e dice il testo; la bandiera resta accesa.
DONI = [
    {"npc": "Padellino", "bandiera": "DONO_PADELLINO", "oggetto": "CRESCIA", "quanti": 1, "testo": "DONO_PADELLINO"},
    {"npc": "Valenza", "bandiera": "DONO_VALENZA", "oggetto": "BISCOTTI", "quanti": 2, "testo": "DONO_VALENZA"},
]

AREE_NPC = {"Piazza Grande": "PIAZZA_GRANDE", "via dei Consoli": "VIA_DEI_CONSOLI",
            "Largo del Bargello": "LARGO_BARGELLO", "San Martino": "SAN_MARTINO", "Teatro Romano": "TEATRO_ROMANO",
            "via XX Settembre": "VIA_XX_SETTEMBRE", "Duomo e Palazzo Ducale": "DUOMO_DUCALE",
            "Sant'Agostino": "SANT_AGOSTINO", "Sant'Andrea": "SANT_ANDREA",
            "Piazza Quaranta Martiri": "PIAZZA_QUARANTA_MARTIRI", "San Pietro": "SAN_PIETRO",
            "Monte Ingino": "MONTE_INGINO", "Basilica": "BASILICA", "Strada del Bottaccione": "BOTTACCIONE",
            "Via dei Consoli": "VIA_DEI_CONSOLI", "Sant'Agostino (fuori Porta Romana)": "SANT_AGOSTINO",
            # gli interni esplorabili (pezzo INTC): chi ci lavora sta dentro
            "Taverna del corso": "TAVERNA_INTERNO", "Spezieria e ospizio": "SPEZIERIA_INTERNO",
            "Bottega dei conti e dei congegni": "BOTTEGA_CONTI_INTERNO", "Bottega del carradore": "CARRADORE_INTERNO",
            "Casa del medico": "CASA_MEDICO_INTERNO", "Sala dei Consoli": "SALA_CONSOLI"}

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
# CONTEGGIO e CONTEGGIO_E_NON_BANDIERA (SV2c) sono delle battute di raccolta delle quest: a e' la quest, b quanti
# pezzi dell'obiettivo sono raccolti (dopo la raccolta), c una bandiera che deve essere accesa (o NESSUNA) o spenta.
GUARDIE = ["SEMPRE", "BANDIERA", "NON_BANDIERA", "SCELTA", "ALMENO_DUE", "VARIANTE_BANDIERA",
           "VARIANTE_NON_BANDIERA", "OGGETTO_E_NON_BANDIERA", "CONTEGGIO", "CONTEGGIO_E_NON_BANDIERA"]
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
        frase, meta = meta_dell_obiettivo(chi, frase, dove)
        self.d = {"chi": chi, "espr": espressione or "calmo", "frase": frase.strip(), "dove": dove,
                  "guardia": guardia, "voci": None, "accende": (NESSUNA, NESSUNA), "consuma": -1, "fase": None,
                  "meta": meta}

    def __getitem__(self, k):
        return tuple(self)[k] if isinstance(k, int) else self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def __iter__(self):
        return iter((self.d["chi"], self.d["espr"], self.d["frase"], self.d["dove"]))

    def __len__(self):
        return 4


# MOB: l'area meta di una riga OBIETTIVO scritta a mano in fondo alla riga, «(area: ID)» con un mondo::AreaId.
# Non e' testo a schermo: si toglie dalla frase (anche verifica_copione.py la toglie prima di misurare).
META_OBIETTIVO = re.compile(r"\s*\(area: ([A-Z_]+)\)\s*$")


def meta_dell_obiettivo(chi, frase, dove):
    """(frase senza «(area: ID)», ID o None). L'annotazione vale solo per le righe OBIETTIVO."""
    m = META_OBIETTIVO.search(frase)
    if not m:
        return frase, None
    if chi != "OBIETTIVO":
        raise ErroreStoria(f"{dove}: «(area: ...)» solo nelle righe OBIETTIVO")
    return frase[:m.start()], m.group(1)


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


# --- le quest giocabili (SV2c) --------------------------------------------------------------------------
# 04_quest.md: per ogni quest "## Q-XXNN · titolo", il datore (il primo nome in grassetto), le sezioni "###":
# Proposta, Attesa, Consegna, Dopo (righe "- FASE: PARLANTE: testo"), la sezione di raccolta (titolo con i due
# punti, "Teatro Romano: le fornaci"), Gli indizi e L'infiltrato (Q-SP01). La postierla di Q-SM01 si ignora:
# nella v1 nessun varco si chiude. Nella raccolta le righe SISTEMA in cima valgono una per pezzo, nell'ordine,
# se sono piu' d'una (se e' una, a ogni pezzo); "Al primo blocco, una volta sola[, ... (`BANDIERA`)]:" vale al
# primo pezzo (con la bandiera accesa); "Se la quest non è attiva, alla prima radice:" al primo pezzo senza la
# quest presa.
SEZIONI_QUEST = {"Proposta": "proposta", "Attesa": "attesa", "Consegna": "consegna", "Dopo": "dopo",
                 "Gli indizi": "indizi", "L'infiltrato": "infiltrato", "La postierla": None}
RIGA_UNA_VOLTA = re.compile(r"^(?:Al primo|Alla prima) \w+, una volta sola(?:.*`([A-Z_0-9]+)`)?.*:$")
RIGA_NON_ATTIVA = re.compile(r"^Se la quest non è attiva, (?:al primo|alla prima) \w+:$")


def tipo_sezione(titolo, dove):
    for inizio, tipo in SEZIONI_QUEST.items():
        if titolo.startswith(inizio):
            return tipo
    if ":" in titolo:
        return "raccolta"
    raise ErroreStoria(f"{dove}: sezione «{titolo}» che il lettore delle quest non conosce")


def leggi_quest(testo):
    """{id: {datore, proposta, attesa, consegna, raccolta, dopo: {fase: [...]}, indizi, completi, infiltrato_prima,
    infiltrato_dopo}} da 04_quest.md, con le guardie come nelle scene."""
    ids = [q["id"] for q in QUEST]
    quest, attuale, sezione = {}, None, None
    for n, riga in enumerate(testo.splitlines(), 1):
        dove = f"{FILE_QUEST}:{n}"
        m = re.match(r"^## (Q-[A-Z]+\d+) · (.+)$", riga)
        if m:
            if m.group(1) not in ids:
                raise ErroreStoria(f"{dove}: {m.group(1)} non e' in QUEST")
            qi = ids.index(m.group(1))
            attuale = {"id": m.group(1), "datore": None, "proposta": [], "attesa": [], "consegna": [], "raccolta": [],
                       "dopo": {f: [] for f in FASI}, "indizi": [], "completi": [], "infiltrato_prima": [],
                       "infiltrato_dopo": []}
            quest[m.group(1)] = attuale
            sezione = None
            continue
        if attuale is None:
            continue
        if riga.startswith("---"):
            attuale, sezione = None, None
            continue
        m = re.match(r"^### (.+)$", riga)
        if m:
            sezione = tipo_sezione(m.group(1), dove)
            varianti = Varianti(FILE_QUEST)
            guardia, nel_blocco, in_testa, iniziali, bersaglio = SEMPRE, 0, True, [], None
            if sezione == "raccolta":
                attuale["iniziali"] = iniziali
            continue
        if sezione is None:
            g = re.match(r"^\*\*(.+?)\*\*", riga)
            if g and attuale["datore"] is None and not attuale["proposta"]:
                attuale["datore"] = g.group(1)
            continue
        if sezione == "dopo":
            d = RIGA_NPC.match(riga)
            if d:
                fase, non, flag, chi, espressione, frase = d.groups()
                if flag:
                    raise ErroreStoria(f"{dove}: nel Dopo le varianti con bandiera non servono")
                attuale["dopo"][fase].append(battuta(chi, espressione, frase, dove))
            elif riga.startswith("- "):
                raise ErroreStoria(f"{dove}: riga del Dopo senza fase")
            continue
        b = RIGA_BATTUTA.match(riga)
        if b:
            chi, espressione, frase = b.groups()
            if espressione and espressione not in ESPRESSIONI:
                raise ErroreStoria(f"{dove}: espressione '{espressione}' sconosciuta")
            # gli indizi li dicono NPC d'ambiente, che parlano senza cartiglio come nelle loro battute
            if chi not in SENZA_NOME and chi not in PARLANTI and sezione != "indizi":
                raise ErroreStoria(f"{dove}: parlante '{chi}' senza nome a schermo in PARLANTI")
            nuova = battuta(chi, espressione, frase, dove)
        else:
            nuova = None
        if sezione in ("proposta", "attesa", "consegna"):
            if nuova:
                if chi == "SCELTA":
                    raise ErroreStoria(f"{dove}: nelle quest non ci sono menu")
                varianti.aggiungi(nuova, attuale[sezione])
            else:
                varianti.riga(riga, n, attuale[sezione])
        elif sezione == "raccolta":
            r = riga.strip()
            if nuova:
                if in_testa and chi == "SISTEMA" and guardia == SEMPRE:
                    iniziali.append(nuova)
                else:
                    in_testa = False
                    nuova["guardia"] = guardia
                    nel_blocco += 1
                    attuale["raccolta"].append(nuova)
            elif not r:
                if nel_blocco:
                    guardia, nel_blocco = SEMPRE, 0
            elif RIGA_UNA_VOLTA.match(r):
                flag = RIGA_UNA_VOLTA.match(r).group(1)
                guardia, nel_blocco, in_testa = ("CONTEGGIO", qi, 1, indice(flag) if flag else NESSUNA), 0, False
            elif RIGA_NON_ATTIVA.match(r):
                guardia, nel_blocco, in_testa = ("CONTEGGIO_E_NON_BANDIERA", qi, 1, indice(QUEST[qi]["presa"])), 0, False
        elif sezione == "indizi":
            g = re.match(r"^\*\*(.+?)\*\*.*Imposta `([A-Z_0-9]+)`", riga)
            if g:
                bersaglio = {"nome": g.group(1), "bandiera": g.group(2), "frasi": []}
                attuale["indizi"].append(bersaglio)
            elif riga.startswith("Con i tre indizi"):
                bersaglio = {"frasi": attuale["completi"]}
            elif nuova:
                if bersaglio is None:
                    raise ErroreStoria(f"{dove}: battuta di un indizio prima del suo NPC")
                bersaglio["frasi"].append(nuova)
        elif sezione == "infiltrato":
            if riga.startswith("Dopo la vittoria"):
                in_testa = False
            elif nuova:
                attuale["infiltrato_prima" if in_testa else "infiltrato_dopo"].append(nuova)
    for q in quest.values():
        iniziali = q.pop("iniziali", [])
        qi = ids.index(q["id"])
        if len(iniziali) > 1:
            for k, b in enumerate(iniziali):
                b["guardia"] = ("CONTEGGIO", qi, k + 1, NESSUNA)
        q["raccolta"] = iniziali + q["raccolta"]
    mancanti = [i for i in ids if i not in quest]
    if mancanti:
        raise ErroreStoria(f"{FILE_QUEST}: quest senza sezione: {mancanti}")
    for q in quest.values():
        for k in ("datore", "proposta", "attesa", "consegna"):
            if not q[k]:
                raise ErroreStoria(f"{FILE_QUEST}: {q['id']} senza {k}")
    return quest


def frasi_della_quest(q):
    """Tutte le battute di una quest in fila, nell'ordine di FRASE_QUEST, con le loro sezioni."""
    sezioni = [("proposta", q["proposta"]), ("attesa", q["attesa"]), ("consegna", q["consegna"]),
               ("raccolta", q["raccolta"])]
    sezioni += [(f"dopo_{f}", q["dopo"][f]) for f in FASI]
    sezioni += [(f"indizio_{k}", i["frasi"]) for k, i in enumerate(q["indizi"])]
    sezioni += [("completi", q["completi"]), ("infiltrato_prima", q["infiltrato_prima"]),
                ("infiltrato_dopo", q["infiltrato_dopo"])]
    return sezioni


def id_frase_quest(codice, k):
    return "QST_" + codice.replace("Q-", "") + f"_{k:02d}"


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


def narratore_della_regia(codice):
    """Le battute del narratore che la cutscene 'codice' dice nelle bande (regia/*.regia), nell'ordine."""
    import glob
    for p in sorted(glob.glob(os.path.join(RADICE, "regia", "*.regia"))):
        with open(p, encoding="utf-8") as f:
            righe = [r.split("#", 1)[0].strip() for r in f]
        if any(r.startswith("cutscene ") and r.split()[1] == codice for r in righe):
            return [r.split()[1] for r in righe if r.startswith("narratore ")]
    return []


def coperte(scena, k, codice):
    """Quante battute della scena, dalla k in poi, la cutscene inserita prima della k ha gia' detto nelle bande
    (le battute del NARRATORE del copione, R_<scena>_<k>): nella vista di gioco non si ripetono. Una battuta
    della scena detta dalla cutscene ma non subito dopo l'inserto e' un errore: si sentirebbe due volte, o
    prima del suo momento."""
    prefisso = id_narratore(scena["codice"], 0)[:-2]          # R_A1_08_
    proprie = [b for b in narratore_della_regia(codice) if b.startswith(prefisso)]
    n = 0
    while k + n < len(scena["battute"]) and id_narratore(scena["codice"], k + n) in proprie:
        n += 1
    if n != len(proprie):
        raise ValueError(f"inserto {scena['codice']}:{k} {codice}: la cutscene dice {', '.join(proprie)}, "
                         f"che non vengono subito dopo l'inserto")
    return n


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


_AREE = {}


def aree_del_mondo():
    """Le aree come le prepara tools/genera_mondo.py (griglia finale, spawn, edifici), per AreaId."""
    if not _AREE:
        sys.path.insert(0, os.path.join(RADICE, "tools"))
        import genera_mondo as G  # noqa: E402
        mondo = G.mondo_del_repo()
        for nome, testo in G.sorgenti_del_repo():
            a = G.leggi_area(nome, testo)
            G.prepara_area(a, mondo)
            _AREE[a["id"].upper()] = a
    return _AREE


def posti_degli_npc(npc, altri=(), occupati=None):
    """Una cella libera per ogni NPC: vicino al centro della sua area, lontana dai varchi e dagli altri.
    'altri' sono (nome, area, ancora) cercati dopo tutti gli NPC (i datori delle quest, l'infiltrato): i posti
    degli NPC non cambiano. Con 'altri' ritorna anche i loro posti; 'occupati' raccoglie tutte le celle prese."""
    import genera_mondo as G  # noqa: E402
    aree = aree_del_mondo()
    occupati = {} if occupati is None else occupati
    posti = []
    richieste = []
    for p in npc:
        ancora = AMICI[p["amico"]]["ancora"] if p.get("amico") else (
            MESTIERI[p["mestiere"]]["ancora"] if p.get("mestiere") else None)
        richieste.append((p, p["area"], ancora))
    for p in npc:
        if p.get("amico") and AMICI[p["amico"]].get("borgo"):
            # con il borgo dentro: accampati in Sant'Andrea, dietro Porta Romana (il varco verso Sant'Agostino)
            richieste.append((p, "SANT_ANDREA", "varco B"))
    quanti_npc = len(richieste)
    for nome, area_id, ancora in altri:
        richieste.append(({"nome": nome}, area_id, ancora))
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
    borgo = iter(posti[len(npc):quanti_npc])
    degli_npc = [(xy, next(borgo) if p.get("amico") and AMICI[p["amico"]].get("borgo") else None)
                 for p, xy in zip(npc, principali)]
    if altri:
        return degli_npc, posti[quanti_npc:]
    return degli_npc


def solida_nel_gioco(c, G):
    """Una cella solida come la vede il gioco (mondo::solida: indice di Cella da PRIMA_CELLA_SOLIDA in su). Da T2
    coincide con la .area (genera_mondo.controlla_ordine_celle: il MIASMA e il PONTE stanno prima di FONTANA), ma
    resta calcolata dall'indice: un oggetto si raccoglie solo dove si cammina davvero."""
    if c in G.VARCHI:
        return False
    solide = [s for _, s in G.CELLE.values()]
    return list(G.CELLE).index(c) >= solide.index(True)


def raggiungibili_da(a, sx, sy, G):
    """Le celle raggiungibili dallo spawn (passi di una cella, nessun varco attraversato), col gioco."""
    g = a["griglia"]
    viste, coda = {(sx, sy)}, [(sx, sy)]
    while coda:
        x, y = coda.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < a["larghezza"] and 0 <= ny < a["altezza"] and (nx, ny) not in viste:
                c = g[ny][nx]
                if not solida_nel_gioco(c, G) and c not in G.VARCHI:
                    viste.add((nx, ny))
                    coda.append((nx, ny))
    return viste


def scontri_sulla_mappa():
    """Le celle dei nemici sulla mappa (SCONTRI_SULLA_MAPPA di include/progressione.h), per area."""
    testo = open(os.path.join(RADICE, "include", "progressione.h"), encoding="utf-8").read()
    celle = {}
    for area, x, y in re.findall(r"\{ mondo::AreaId::([A-Z_]+), (\d+), (\d+), \d+, Bandiera::", testo):
        celle.setdefault(area, []).append((int(x), int(y)))
    return celle


def posti_delle_raccolte(raccolte, occupati):
    """La cella di ogni oggetto da raccogliere (RACCOLTE): la piu' vicina al suo punto 'verso' fra quelle
    calpestabili col gioco, raggiungibili dallo spawn 0, accanto (anche in diagonale) a una cella del simbolo
    'vicino', a 3 celle almeno da varchi, spawn, NPC e nemici sulla mappa e a 4 dagli altri oggetti."""
    import genera_mondo as G  # noqa: E402
    aree = aree_del_mondo()
    nemici = scontri_sulla_mappa()
    presi = {}
    posti = []
    for r in raccolte:
        a = aree[r["area"]]
        g = a["griglia"]
        varchi = [(x, y) for y, riga in enumerate(g) for x, c in enumerate(riga) if c in G.VARCHI]
        lontani = varchi + list(a["spawn"].values()) + occupati.get(r["area"], []) + nemici.get(r["area"], [])
        raggiunte = raggiungibili_da(a, *a["spawn"][0], G)
        vx, vy = r["verso"][0] * a["larghezza"], r["verso"][1] * a["altezza"]
        scelto = None
        for x, y in sorted(raggiunte, key=lambda xy: ((xy[0] - vx) ** 2 + (xy[1] - vy) ** 2, xy[1], xy[0])):
            accanto = any(0 <= y + j < a["altezza"] and 0 <= x + i < a["larghezza"] and g[y + j][x + i] in r["vicino"]
                          for i in (-1, 0, 1) for j in (-1, 0, 1))
            if (accanto and all(max(abs(x - u), abs(y - v)) >= 3 for u, v in lontani) and
                    all(max(abs(x - u), abs(y - v)) >= 4 for u, v in presi.get(r["area"], []))):
                scelto = (x, y)
                break
        if not scelto:
            raise ErroreStoria(f"nessun posto per {r['bandiera']} in {r['area']} accanto a «{r['vicino']}»")
        presi.setdefault(r["area"], []).append(scelto)
        posti.append(scelto)
    return posti


def posti_delle_sentinelle(posti_raccolte):
    """Le celle dei soldati di B-03: 'passi' colonne oltre l'arco, sulla prima e sull'ultima cella calpestabile
    della via in quella colonna meno una; raggiungibili dallo spawn 0 e a 3 celle almeno dagli oggetti."""
    import genera_mondo as G  # noqa: E402
    a = aree_del_mondo()[SENTINELLE["area"]]
    g = a["griglia"]
    x = max(x for riga in g for x, c in enumerate(riga) if c == SENTINELLE["oltre"]) + SENTINELLE["passi"]
    raggiunte = raggiungibili_da(a, *a["spawn"][0], G)
    righe = [y for y in range(a["altezza"]) if (x, y) in raggiunte]
    posti = [(x, min(righe) + 1), (x, max(righe) - 1)]
    oggetti = [(tx, ty) for r, (tx, ty) in zip(RACCOLTE, posti_raccolte) if r["area"] == SENTINELLE["area"]]
    for tx, ty in posti:
        if (tx, ty) not in raggiunte or any(max(abs(tx - u), abs(ty - v)) < 3 for u, v in oggetti):
            raise ErroreStoria(f"un soldato di B-03 in ({tx}, {ty}) non sta sulla via o sta addosso a una radice")
    return posti[:SENTINELLE["quanti"]]


def posti_dei_forzieri(posti_raccolte):
    """La cella di ogni forziere: il centro del suo slargo (tools/disegna_gola.py), calpestabile col gioco,
    raggiungibile dallo spawn 0, a 3 celle almeno da varchi, spawn e oggetti da raccogliere."""
    import genera_mondo as G  # noqa: E402
    import disegna_gola as D  # noqa: E402
    aree = aree_del_mondo()
    posti = []
    for f in FORZIERI:
        a = aree[f["area"]]
        x, y = D.SLARGHI[f["slargo"]]
        varchi = [(u, v) for v, riga in enumerate(a["griglia"]) for u, c in enumerate(riga) if c in G.VARCHI]
        lontani = varchi + list(a["spawn"].values()) + [p for r, p in zip(RACCOLTE, posti_raccolte) if r["area"] == f["area"]]
        if ((x, y) not in raggiungibili_da(a, *a["spawn"][0], G) or
                any(max(abs(x - u), abs(y - v)) < 3 for u, v in lontani)):
            raise ErroreStoria(f"il forziere {f['bandiera']} in ({x}, {y}) non si raggiunge o sta addosso a qualcosa")
        posti.append((x, y))
    return posti


def punto_dell_ancora(a, ancora, G):
    """Il punto da cui cercare il posto di un NPC: lo spawn 0, o davanti al monumento, al varco o
    all'edificio nuovo dell'ancora (se l'edificio non c'e' ancora, lo spawn 0); "posto X Y" e' una cella
    dell'area (negli interni: dove il mockup mette la figura, tools/pittore_interni.py)."""
    if ancora:
        tipo, _, nome = ancora.partition(" ")
        if tipo == "posto":
            x, y = map(int, nome.split())
            return x, y
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
    mestieri = leggi_npc(open(os.path.join(COPIONE, FILE_MESTIERI), encoding="utf-8").read(), FILE_MESTIERI)
    for p in mestieri:
        if p["nome"] not in MESTIERI:
            raise ErroreStoria(f"{FILE_MESTIERI} ({p['nome']}): manca in dati/mestieri.json")
        p["mestiere"] = p["nome"]
    return scene, npc + amici + mestieri


def parlante_dell_amico(p):
    """L'amico di una scheda: il parlante delle sue battute, che deve stare in dati/amici.json."""
    chi = {b[0] for b in p["frasi"] if b[0] not in SENZA_NOME and b[0] not in ("UBALDO", "GIORGIO", "ANTONIO")}
    if len(chi) != 1 or next(iter(chi)) not in AMICI:
        raise ErroreStoria(f"{FILE_AMICI} ({p['nome']}): parlante {sorted(chi)} senza voce in dati/amici.json")
    return next(iter(chi))


def figura_popolo(base, accessorio=None, nome=None):
    """Una figura della gente (tools/figure_popolo.py, pezzo VIVA): la chiave con cui si cerca in FIGURA_NPC."""
    return (base, accessorio, nome)


def figura_dell_npc(p):
    """La figura nel gioco: per un NPC d'ambiente quella del mestiere, per un amico la sua (dati/amici.json), per un
    mestiere nuovo quella di dati/mestieri.json."""
    if p.get("amico"):
        a = AMICI[p["amico"]]
        if a.get("figura"):
            return figura_popolo(a["figura"], None, a["nome"])
        return figura_popolo(a["base"], a["accessorio"], a["nome"])
    if p.get("mestiere"):
        return figura_popolo(MESTIERI[p["mestiere"]]["figura"], None, p["nome"])
    return figura_popolo(FN.figura_di(p["nome"]), None, p["nome"])


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


def aree_del_grafo():
    """Gli id delle aree del gioco (mondo::AreaId), da mondo/grafo.json."""
    with open(os.path.join(RADICE, "mondo", "grafo.json"), encoding="utf-8") as f:
        return [a["id"] for a in __import__("json").load(f)["aree"]]


def obiettivi(scene, quest):
    """Le righe OBIETTIVO (MOB, menu/PROPOSTA.md sez. 5): [{testo, area, quest, scena, dove, frase}].
    Nelle scene l'area meta e' quella della prima scena che segue nel copione con un'area (il suo Luogo, AREE),
    oppure quella scritta a mano con «(area: ID)»; nelle quest e' l'area dell'obiettivo della quest (QUEST), se
    la riga non ne scrive una. quest = -1 per le righe della cronaca, scena = -1 per quelle delle quest."""
    validi = set(aree_del_grafo())
    righe = []
    for i, s in enumerate(scene):
        for k, b in enumerate(s["battute"]):
            if b["chi"] != "OBIETTIVO":
                continue
            meta = b["meta"] or next((AREE[t["codice"]] for t in scene[i + 1:] if AREE.get(t["codice"])), None)
            righe.append({"testo": id_battuta(s["codice"], k), "area": meta, "quest": -1, "scena": i,
                          "dove": b["dove"], "frase": b["frase"]})
    for qi, d in enumerate(QUEST):
        if not quest or d["id"] not in quest:
            continue
        k = 0
        for _, lista in frasi_della_quest(quest[d["id"]]):
            for b in lista:
                if b["chi"] == "OBIETTIVO":
                    righe.append({"testo": id_frase_quest(d["id"], k), "area": b["meta"] or d["obiettivo"], "quest": qi,
                                  "scena": -1, "dove": b["dove"], "frase": b["frase"]})
                k += 1
    for r in righe:
        if not r["area"]:
            raise ErroreStoria(f"{r['dove']}: riga OBIETTIVO senza area meta: nessuna scena dopo, scrivere «(area: ID)»")
        if r["area"] not in validi:
            raise ErroreStoria(f"{r['dove']}: area meta {r['area']} che il mondo non ha")
    if len(righe) >= 255:
        raise ErroreStoria("troppe righe OBIETTIVO: GameState::obiettivo e' un byte, 255 vuol dire nessuno")
    return righe


def maschera(bandiere):
    v = 0
    for b in bandiere:
        v |= 1 << BANDIERE.index(b)
    return v


def header(scene, npc, posti, quest=None, posti_quest=None, posti_raccolte=None, posti_guardie=None):
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
        libera = 0                  # la prima battuta che una cutscene della scena non ha gia' detto
        for k, codice in sorted(INSERTI.get(s["codice"], {}).items()):
            if not 0 <= k < len(s["battute"]) or codice not in regie:
                raise ValueError(f"inserto {s['codice']}:{k} {codice}: battuta o cutscene che non c'e'")
            if k < libera:
                raise ValueError(f"inserto {s['codice']}:{k} {codice}: la battuta l'ha gia' detta la cutscene prima")
            prima = sum(len(t["battute"]) for t in scene[:scene.index(s)])
            copre = coperte(s, k, codice)
            libera = k + copre
            inserti.append(f"    {{ {prima + k}, {regie.index(codice)}, {copre} }},  // {s['codice']} prima della battuta {k}: {codice}")
    out += ["// Le cutscene dentro le scene: prima della battuta (indice in BATTUTA), la cutscene; le battute del",
            "// narratore che la cutscene dice nelle bande (copre, dalla battuta in poi) non si ripetono nella vista di gioco.",
            "struct Inserto", "{", "    uint16_t battuta;", "    int8_t regia;", "    uint8_t copre;", "};", "",
            f"inline constexpr int INSERTI = {len(inserti)};",
            "inline constexpr Inserto INSERTO[INSERTI > 0 ? INSERTI : 1] = {"] + (inserti or ["    { 0xFFFF, -1, 0 },"]) + ["};", ""]
    ingressi = []
    for codice_scena, codice in sorted(ALL_INGRESSO.items()):
        if codice_scena not in codici or codice not in regie:
            raise ValueError(f"all'ingresso {codice_scena} {codice}: scena o cutscene che non c'e'")
        s = scene[codici.index(codice_scena)]
        if not AREE[codice_scena]:
            raise ValueError(f"all'ingresso {codice_scena} {codice}: la scena e' a schermo intero, non ha un'area")
        if INSERTI.get(codice_scena, {}).get(0) != codice:
            raise ValueError(f"all'ingresso {codice_scena} {codice}: manca l'inserto alla battuta 0 della scena")
        if coperte(s, 0, codice):
            raise ValueError(f"all'ingresso {codice_scena} {codice}: la cutscene copre battute del narratore, "
                             f"che la scena ripeterebbe")
        ingressi.append(f"    {{ {codici.index(codice_scena)}, {regie.index(codice)} }},  "
                        f"// {codice}: entrando in {AREE[codice_scena]} con {codice_scena} pronta")
    out += ["// Le cartoline dei luoghi che partono entrando nell'area della scena (indice in SCENA) quando la scena e'",
            "// pronta e la cutscene (regia::CUTSCENE_DATI) non e' vista; restano anche inserto alla battuta 0.",
            "struct Ingresso", "{", "    int8_t scena;", "    int8_t regia;", "};", "",
            f"inline constexpr int INGRESSI = {len(ingressi)};",
            "inline constexpr Ingresso INGRESSO[INGRESSI > 0 ? INGRESSI : 1] = {"] + (ingressi or ["    { -1, -1 },"]) + ["};", ""]
    a_meta = []
    for s in scene:
        if s["codice"] not in BATTAGLIA_A_META:
            continue
        k = BATTAGLIA_A_META[s["codice"]]
        if s["codice"] not in BATTAGLIE or not 0 < k < len(s["battute"]):
            raise ValueError(f"battaglia a meta' di {s['codice']}:{k}: scena senza battaglia o battuta che non c'e'")
        prima = sum(len(t["battute"]) for t in scene[:scene.index(s)])
        a_meta.append(f"    {{ {codici.index(s['codice'])}, {prima + k}, {TUTTE.index(VINTA_A_META[s['codice']])} }},  "
                      f"// {s['codice']} prima della battuta {k}")
    out += ["// Le battaglie a meta' scena: la battaglia della scena si combatte prima della battuta (indice in BATTUTA),",
            "// non alla fine; vinta, accende la bandiera (64-127) e non si rigioca. B-03: dopo l'ascolto, prima del ragazzo.",
            "struct BattagliaAMeta", "{", "    int8_t scena;                 // indice in SCENA", "    uint16_t battuta;",
            "    uint8_t vinta;", "};", "",
            f"inline constexpr int BATTAGLIE_A_META = {len(a_meta)};",
            "inline constexpr BattagliaAMeta BATTAGLIA_A_META[BATTAGLIE_A_META > 0 ? BATTAGLIE_A_META : 1] = {"] + (
                a_meta or ["    { -1, 0xFFFF, 255 },"]) + ["};", ""]
    righe_ob = obiettivi(scene, quest)
    out += ["// Le righe OBIETTIVO del copione (MOB, menu/PROPOSTA.md sez. 5): il testo, l'area meta (mondo::AreaId: il",
            "// Luogo della scena che segue, o l'area scritta a mano in fondo alla riga), la quest (-1 per la cronaca) e la scena",
            "// (indice in SCENA, -1 per le quest). GameState::obiettivo e' un indice qui; lo aggiorna la recita delle scene.",
            "struct Obiettivo", "{", "    testi::TestoId testo;", "    int8_t area;", "    int8_t quest;", "    int8_t scena;", "};", "",
            f"inline constexpr int OBIETTIVI = {len(righe_ob)};",
            "inline constexpr Obiettivo OBIETTIVO[OBIETTIVI > 0 ? OBIETTIVI : 1] = {"] + [
                f"    {{ testi::TestoId::{r['testo']}, int8_t(mondo::AreaId::{r['area']}), {r['quest']}, {r['scena']} }},"
                f"  // {r['frase'][:60]}" for r in righe_ob] + (
                [] if righe_ob else ["    { testi::TestoId(0), -1, -1, -1 },"]) + ["};", ""]
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
    blocco_quest = parte_quest(quest, npc, posti_quest, posti_raccolte, riga_battuta, figure) if quest else []
    out += [f"inline constexpr int GUARDIE = {len(guardie)};", "inline constexpr Guardia GUARDIA[GUARDIE] = {"]
    out += [f"    {{ TipoGuardia::{g[0]}, {g[1]}, {g[2]}, {g[3]} }}," for g in guardie] + ["};", ""]
    out += ["// Le bandiere delle quest e degli indizi (64-127, GameState::quest), per nome."]
    out += [f"inline constexpr uint8_t {b} = {PRIMA_QUEST + i};" for i, b in enumerate(BANDIERE_QUEST)] + [""]
    out += ["// Le tre quest della v1 (copione/04_quest.md): dove si consegnano, da quale bandiera si prendono, entro",
            "// quale si consegnano, la bandiera della consegna e il premio (indice di GameState::oggetti, come",
            "// battaglia::OggettoId). Le legge storia::consegna_quest().",
            "struct Quest", "{", "    const char* codice;", "    int8_t consegna;             // mondo::AreaId",
            "    Bandiera da;", "    Bandiera entro;", "    uint8_t consegnata;          // bandiera 64-127",
            "    uint8_t oggetto;", "    uint8_t quanti;", "};", "",
            f"inline constexpr int QUEST = {len(QUEST)};", "inline constexpr Quest QUEST_V1[QUEST] = {"]
    out += [f"    {{ \"{q['id']}\", int8_t(mondo::AreaId::{q['consegna']}), Bandiera::{q['da']}, Bandiera::{q['entro']}, "
            f"{q['consegnata']}, {OGGETTI.index(q['premio'][0])}, {q['premio'][1]} }},  // {q['premio'][1]} {q['nome_premio']}"
            for q in QUEST] + ["};", ""]
    out += blocco_quest
    out += parte_gola(codici, posti_raccolte, figure) if posti_raccolte else []
    out += parte_fornaci(posti_guardie) if posti_guardie else []
    out += parte_interni(npc, posti)
    out += ["// Le figure della gente (pezzo VIVA, tools/figure_popolo.py): 16x32, 8 tile in mappatura 1D, con la",
            "// palette della gente (PALETTE_POPOLO). Per ognuna quattro pose: riposo e respiro di fronte (STANDARD A5),",
            "// riposo di schiena e di lato (A7, chi parla si gira; la sinistra e' il lato specchiato).",
            "inline constexpr int POSE_NPC = 4;",
            "inline constexpr int POSA_RIPOSO = 0;", "inline constexpr int POSA_RESPIRO = 1;",
            "inline constexpr int POSA_SCHIENA = 2;", "inline constexpr int POSA_LATO = 3;",
            "inline constexpr int FRAME_RESPIRO = 30;            // vblank per fotogramma del respiro (A5)",
            "inline constexpr uint16_t PALETTE_POPOLO[16] = {",
            "    " + ", ".join(f"0x{v:04X}" for v in FP.bgr555("giorno")) + ",", "};",
            "inline constexpr uint16_t PALETTE_POPOLO_NOTTE[16] = {",
            "    " + ", ".join(f"0x{v:04X}" for v in FP.bgr555("notte")) + ",", "};",
            f"inline constexpr int FIGURE_NPC = {len(figure)};",
            "inline constexpr uint32_t FIGURA_NPC[FIGURE_NPC][POSE_NPC * 8 * 8] = {"]
    for base, accessorio, nome in figure:
        out.append("    {")
        for px in FP.fotogrammi_npc(base, accessorio, nome):
            parole = FP.parole(px)
            out += ["        " + ", ".join(f"0x{v:08X}" for v in parole[k:k + 8]) + "," for k in range(0, 64, 8)]
        out.append(f"    }},  // {nome or base}")
    out += ["};", ""]
    out += ["}", "", "#endif", ""]
    return "\n".join(out)


def npc_dell_indizio(indizio, npc):
    """L'NPC (indice in NPC_AMBIENTE) che dice l'indizio: quello che ha lo stesso parlante nelle sue battute."""
    chi = {b["chi"] for b in indizio["frasi"]} - SENZA_NOME
    trovati = [i for i, p in enumerate(npc) if chi & {b["chi"] for b in p["frasi"]}]
    if len(chi) != 1 or len(trovati) != 1:
        raise ErroreStoria(f"{FILE_QUEST}: l'indizio di {indizio['nome']} ({sorted(chi)}) non ha un solo NPC: {trovati}")
    return trovati[0]


def parte_quest(quest, npc, posti_quest, posti_raccolte, riga_battuta, figure):
    """Le righe di storia.h delle quest giocabili: FRASE_QUEST, QUEST_GIOCO, RACCOLTA, INDIZIO, INFILTRATO."""
    frasi, righe_q, intervalli = [], [], {}

    def righe(lista, codice):
        prima = len(frasi)
        for b in lista:
            frasi.append(riga_battuta(b, id_frase_quest(codice, len(frasi) - inizio[codice]), npc=True))
        return f"{{ {prima}, {len(lista)} }}"

    inizio = {}
    for qi, d in enumerate(QUEST):
        q = quest[d["id"]]
        inizio[d["id"]] = len(frasi)
        intervalli[d["id"]] = {nome: righe(lista, d["id"]) for nome, lista in frasi_della_quest(q)}
        pezzi = [indice(b) for b in d["pezzi"]]
        if pezzi != list(range(pezzi[0], pezzi[0] + len(pezzi))):
            raise ErroreStoria(f"{d['id']}: i pezzi dell'obiettivo devono essere bandiere consecutive")
        (tx, ty) = posti_quest[qi]
        figura = figura_popolo(FN.figura_di(q["datore"]), None, q["datore"])
        if figura not in figure:
            figure.append(figura)
        r = intervalli[d["id"]]
        righe_q.append(f"    {{ {d['presa']}, {pezzi[0]}, {len(pezzi)}, int8_t(mondo::AreaId::{d['consegna']}), {tx}, {ty}, "
                       f"{figure.index(figura)}, {r['proposta']}, {r['attesa']}, {r['consegna']}, {r['raccolta']}, "
                       f"{{ {r['dopo_ULTIMATUM']}, {r['dopo_DIGIUNO']}, {r['dopo_NOTTE']} }} }},  // {d['id']}, {q['datore']}")
    out = ["// --- Le quest giocabili (SV2c, copione/04_quest.md) ----------------------------------------------",
           "// Le battute delle quest: proposta, attesa, consegna, raccolta, dopo (per fase), indizi e infiltrato.",
           "struct Righe", "{", "    uint16_t prima;               // in FRASE_QUEST", "    uint8_t quante;", "};", "",
           f"inline constexpr int FRASI_QUEST = {len(frasi)};", "inline constexpr Battuta FRASE_QUEST[FRASI_QUEST] = {"]
    out += frasi + ["};", ""]
    out += ["// Il datore di ogni quest (nell'ordine di QUEST_V1) e i pezzi dell'obiettivo: bandiere consecutive da",
            "// primo_pezzo, il contatore e' quante sono accese (storia::pezzi_raccolti).",
            "struct QuestGioco", "{", "    uint8_t presa;                // la bandiera della quest presa (la proposta)",
            "    uint8_t primo_pezzo;", "    uint8_t pezzi;", "    int8_t area;                  // dove sta il datore (mondo::AreaId)",
            "    uint8_t tx;", "    uint8_t ty;", "    uint8_t figura;               // FIGURA_NPC",
            "    Righe proposta;", "    Righe attesa;", "    Righe consegna;", "    Righe raccolta;      // dette a ogni pezzo raccolto, con le guardie CONTEGGIO",
            "    Righe dopo[3];               // per fase (ULTIMATUM, DIGIUNO, NOTTE)", "};", "",
            "inline constexpr QuestGioco QUEST_GIOCO[QUEST] = {"] + righe_q + ["};", ""]
    nomi_fig = FN.ORDINE_RACCOLTE
    righe_r = []
    for r, (tx, ty) in zip(RACCOLTE, posti_raccolte):
        qi = next(i for i, d in enumerate(QUEST) if r["bandiera"] in d["pezzi"])
        righe_r.append(f"    {{ int8_t(mondo::AreaId::{r['area']}), {tx}, {ty}, {qi}, {r['bandiera']}, {nomi_fig.index(r['figura'])} }},")
    out += ["// Gli oggetti da raccogliere sulla mappa: ci sono finche' la loro bandiera e' spenta (anche se la quest non",
            "// e' presa); toccarli accende la bandiera e fa dire le battute di raccolta della quest.",
            "struct Raccolta", "{", "    int8_t area;                  // mondo::AreaId", "    uint8_t tx;", "    uint8_t ty;",
            "    uint8_t quest;", "    uint8_t bandiera;", "    uint8_t figura;               // FIGURA_RACCOLTA", "};", "",
            f"inline constexpr int RACCOLTE = {len(RACCOLTE)};", "inline constexpr Raccolta RACCOLTA[RACCOLTE] = {"]
    out += righe_r + ["};", ""]
    out += ["// Le figure degli oggetti da raccogliere, 16x16 (4 tile), con la palette dei popolani (tools/figure_npc.py).",
            f"inline constexpr int FIGURE_RACCOLTA = {len(nomi_fig)};",
            "inline constexpr uint32_t FIGURA_RACCOLTA[FIGURE_RACCOLTA][4 * 8] = {"]
    for nome in nomi_fig:
        parole = FN.parole_16(nome)
        out.append("    {  // " + nome)
        out += ["        " + ", ".join(f"0x{v:08X}" for v in parole[k:k + 8]) + "," for k in range(0, 32, 8)]
        out.append("    },")
    out += ["};", ""]
    # gli indizi e l'infiltrato (Q-SP01)
    qi_sp = next(i for i, d in enumerate(QUEST) if quest[d["id"]]["indizi"])
    q = quest[QUEST[qi_sp]["id"]]
    r = intervalli[QUEST[qi_sp]["id"]]
    righe_i = [f"    {{ {npc_dell_indizio(ind, npc)}, {ind['bandiera']}, {r[f'indizio_{k}']} }},  // {ind['nome']}"
               for k, ind in enumerate(q["indizi"])]
    (ix, iy) = posti_quest[len(QUEST)]
    fig_inf = figura_popolo(*INFILTRATO["figura"])
    if fig_inf not in figure:
        figure.append(fig_inf)
    out += ["// Gli indizi di Q-SP01: l'NPC (NPC_AMBIENTE) che, con la quest presa e la Rosa non ancora ripresa, dopo le",
            "// sue battute dice le righe dell'indizio e accende la bandiera. Con tutti e tre, INDIZI_COMPLETI.",
            "struct Indizio", "{", "    uint8_t npc;", "    uint8_t bandiera;", "    Righe righe;", "};", "",
            f"inline constexpr int QUEST_DEGLI_INDIZI = {qi_sp};", f"inline constexpr int INDIZI = {len(righe_i)};",
            "inline constexpr Indizio INDIZIO[INDIZI] = {"] + righe_i + ["};", "",
            f"inline constexpr Righe INDIZI_COMPLETI = {r['completi']};", "",
            "// L'infiltrato sotto le Logge: compare con i tre indizi; parlargli fa dire le righe di prima, la battaglia,",
            "// e se si vince quelle di dopo e ROSA_RIPRESA.",
            "struct Infiltrato", "{", "    int8_t area;", "    uint8_t tx;", "    uint8_t ty;", "    uint8_t figura;",
            "    int8_t incontro;              // battaglia::INCONTRO", "    Righe prima;", "    Righe dopo;", "};", "",
            f"inline constexpr Infiltrato INFILTRATO = {{ int8_t(mondo::AreaId::{INFILTRATO['area']}), {ix}, {iy}, "
            f"{figure.index(fig_inf)}, {INFILTRATO['incontro']}, {r['infiltrato_prima']}, {r['infiltrato_dopo']} }};", ""]
    return out


def parte_gola(codici, posti_raccolte, figure):
    """Le righe di storia.h della gola (T2): gli inneschi delle scene, i soldati di B-03, i forzieri."""
    import genera_mondo as G  # noqa: E402
    nomi = list(G.CELLE)
    inneschi = [f"    {{ {codici.index(k)}, mondo::Cella::{G.CELLE[c][0]} }},  // {k}" for k, c in INNESCHI.items()]
    figura = figura_popolo(SENTINELLE["figura"])
    if figura not in figure:
        figure.append(figura)
    sentinelle = [f"    {{ int8_t(mondo::AreaId::{SENTINELLE['area']}), {tx}, {ty}, {figure.index(figura)} }},"
                  for tx, ty in posti_delle_sentinelle(posti_raccolte)]
    forzieri = [f"    {{ int8_t(mondo::AreaId::{f['area']}), {tx}, {ty}, {f['bandiera']}, {OGGETTI.index(f['oggetto'])}, "
                f"{f['quanti']}, testi::TestoId::{f['testo']} }},  // {f['quanti']} {f['oggetto']}"
                for f, (tx, ty) in zip(FORZIERI, posti_dei_forzieri(posti_raccolte))]
    assert all(c in nomi for c in INNESCHI.values())
    return ["// --- La gola del Bottaccione (T2) ----------------------------------------------------------------",
            "// Le scene che partono su una cella dell'area (non entrando): B-02 sulla prima nebbia, B-03 sotto l'arco.",
            "struct Innesco", "{", "    int8_t scena;                 // indice in SCENA", "    mondo::Cella cella;", "};", "",
            f"inline constexpr int INNESCHI = {len(inneschi)};", "inline constexpr Innesco INNESCO[INNESCHI] = {"] + inneschi + [
            "};", "",
            "// I soldati di B-03 sulla mappa (FIGURA_NPC): ci sono finche' PIANO_DI_CORRADO e' spenta.",
            "struct Sentinella", "{", "    int8_t area;                  // mondo::AreaId", "    uint8_t tx;", "    uint8_t ty;",
            "    uint8_t figura;", "};", "",
            f"inline constexpr int SENTINELLE = {len(sentinelle)};", "inline constexpr Sentinella SENTINELLA[SENTINELLE] = {"] + sentinelle + [
            "};", "",
            "// I forzieri negli slarghi: toccarli da' 'quanti' dell'oggetto (battaglia::OggettoId, fino al massimo che se",
            "// ne porta), accende la bandiera (64-127) e fa dire il testo; preso, non torna.",
            "struct Forziere", "{", "    int8_t area;                  // mondo::AreaId", "    uint8_t tx;", "    uint8_t ty;",
            "    uint8_t bandiera;", "    uint8_t oggetto;", "    uint8_t quanti;", "    testi::TestoId testo;", "};", "",
            f"inline constexpr int FORZIERI = {len(forzieri)};", "inline constexpr Forziere FORZIERE[FORZIERI] = {"] + forzieri + [
            "};", "",
            "// Le figure del forziere in FIGURA_RACCOLTA: chiuso, e aperto (preso, resta li').",
            f"inline constexpr int FIGURA_FORZIERE = {FN.ORDINE_RACCOLTE.index('forziere')};",
            f"inline constexpr int FIGURA_FORZIERE_APERTO = {FN.ORDINE_RACCOLTE.index('forziere_aperto')};",
            "// La fiamma sopra i ceri dell'altare, con i Ceri risvegliati (CERO_ALTARE di storia_logica.h).",
            f"inline constexpr int FIGURA_FIAMMA_CERO = {FN.ORDINE_RACCOLTE.index('fiamma_cero')};", ""]


def parte_interni(npc, posti):
    """Le righe di storia.h degli interni (INTC): le cose da esaminare (tools/pittore_interni.py) e i doni."""
    import pittore_interni as PI  # noqa: E402
    nomi = [p["nome"] for p in npc]
    evita = {}
    for p, (xy, borgo) in zip(npc, posti):
        evita.setdefault(p["area"], []).append(xy)
    doni = []
    for d in DONI:
        if d["npc"] not in nomi:
            raise ErroreStoria(f"dono {d['bandiera']}: {d['npc']} non e' fra gli NPC")
        doni.append(f"    {{ {nomi.index(d['npc'])}, {d['bandiera']}, {OGGETTI.index(d['oggetto'])}, {d['quanti']}, "
                    f"testi::TestoId::{d['testo']} }},  // {d['npc']}: {d['quanti']} {d['oggetto']}")
    cose = [f"    {{ int8_t(mondo::AreaId::{aid.upper()}), {tx}, {ty}, {fx}, {fy}, testi::TestoId::{testo} }},  // {nome}"
            for (aid, nome, tx, ty, testo), (fx, fy) in zip(PI.cose_di_gioco(evita), PI.segni_delle_cose())]
    return ["// --- Gli interni (INTC) ----------------------------------------------------------------------------",
            "// Le cose da esaminare: a portata di parola dalla cella (tx, ty) il fumetto, e con A il testo di sistema.",
            "struct Cosa", "{", "    int8_t area;                  // mondo::AreaId", "    uint8_t tx;", "    uint8_t ty;",
            "    uint16_t fx;                  // il fumetto: sull'oggetto, in pixel dell'area", "    uint16_t fy;",
            "    testi::TestoId testo;", "};", "",
            f"inline constexpr int COSE = {len(cose)};", "inline constexpr Cosa COSA[COSE] = {"] + cose + ["};", "",
            "// I doni: dopo le battute dell'NPC (indice in NPC_AMBIENTE), una volta sola, l'oggetto e il testo.",
            "struct Dono", "{", "    int8_t npc;", "    uint8_t bandiera;", "    uint8_t oggetto;", "    uint8_t quanti;",
            "    testi::TestoId testo;", "};", "",
            f"inline constexpr int DONI = {len(doni)};", "inline constexpr Dono DONO[DONI] = {"] + doni + ["};", ""]


def parte_fornaci(posti_guardie):
    """Le righe di storia.h delle guardie delle fornaci (F10, Q-SM01)."""
    righe = []
    for gd, (tx, ty) in zip(GUARDIE_FORNACE, posti_guardie):
        k = next(i for i, r in enumerate(RACCOLTE) if r["bandiera"] == gd["raccolta"])
        righe.append(f"    {{ int8_t(mondo::AreaId::{RACCOLTE[k]['area']}), {tx}, {ty}, {gd['bandiera']}, {k} }},  "
                     f"// davanti a {gd['raccolta']}")
    return ["// --- Le guardie delle fornaci (F10, Q-SM01) -----------------------------------------------------",
            "// Un Guerriero della Roccia davanti a ogni blocco di ferro, visibile sulla mappa: toccarlo avvia la battaglia",
            "// (INCONTRO_FORNACE); vinta, la sua bandiera (64-127) si accende, non torna e il blocco si puo' prendere.",
            "struct GuardiaFornace", "{", "    int8_t area;                  // mondo::AreaId", "    uint8_t tx;",
            "    uint8_t ty;", "    uint8_t bandiera;", "    uint8_t raccolta;             // il blocco che guarda (RACCOLTA)",
            "};", "", f"inline constexpr int INCONTRO_FORNACE = {INCONTRO_FORNACE};     // battaglia::INCONTRO",
            f"inline constexpr int GUARDIE_FORNACE = {len(righe)};",
            "inline constexpr GuardiaFornace GUARDIA_FORNACE[GUARDIE_FORNACE] = {"] + righe + ["};", ""]


def testi_delle_quest(quest):
    righe = []
    for d in QUEST:
        k = 0
        for _, lista in frasi_della_quest(quest[d["id"]]):
            for b in lista:
                righe.append(f"{id_frase_quest(d['id'], k):26s}| DIALOGO | {b['frase']}")
                k += 1
    return righe


def posti_della_quest(npc, quest, con_guardie=False):
    """I posti dei datori (nell'ordine di QUEST) e dell'infiltrato, poi quelli degli oggetti da raccogliere (e, con
    'con_guardie', quelli delle guardie delle fornaci)."""
    occupati = {}
    altri = [(quest[d["id"]]["datore"], d["consegna"], d["ancora"]) for d in QUEST]
    altri.append(("infiltrato", INFILTRATO["area"], INFILTRATO["ancora"]))
    posti, posti_quest = posti_degli_npc(npc, altri, occupati)
    posti_raccolte = posti_delle_raccolte(RACCOLTE, occupati)
    if con_guardie:
        return posti, posti_quest, posti_raccolte, posti_delle_guardie(posti_raccolte, occupati)
    return posti, posti_quest, posti_raccolte


def posti_delle_guardie(posti_raccolte, occupati):
    """La cella di ogni guardia di fornace (GUARDIE_FORNACE): a due celle esatte dal suo blocco (Chebyshev), la piu'
    vicina allo spawn 0, raggiungibile, con le otto celle intorno calpestabili e senza varchi (come
    progressione::posto_valido), a 4 celle almeno dagli spawn, a 3 da varchi, NPC, nemici sulla mappa e dagli altri
    oggetti, a 4 dalle altre guardie."""
    import genera_mondo as G  # noqa: E402
    aree = aree_del_mondo()
    nemici = scontri_sulla_mappa()
    posti = []
    for gd in GUARDIE_FORNACE:
        k = next(i for i, r in enumerate(RACCOLTE) if r["bandiera"] == gd["raccolta"])
        area_id = RACCOLTE[k]["area"]
        a = aree[area_id]
        g = a["griglia"]
        bx, by = posti_raccolte[k]
        varchi = [(x, y) for y, riga in enumerate(g) for x, c in enumerate(riga) if c in G.VARCHI]
        altri = [p for i, (r, p) in enumerate(zip(RACCOLTE, posti_raccolte)) if r["area"] == area_id and i != k]
        lontani = varchi + occupati.get(area_id, []) + nemici.get(area_id, []) + altri
        raggiunte = raggiungibili_da(a, *a["spawn"][0], G)
        sx, sy = a["spawn"][0]
        scelto = None
        candidati = [(bx + i, by + j) for i in range(-2, 3) for j in range(-2, 3) if max(abs(i), abs(j)) == 2]
        for x, y in sorted(candidati, key=lambda xy: ((xy[0] - sx) ** 2 + (xy[1] - sy) ** 2, xy[1], xy[0])):
            libero = (x, y) in raggiunte and all(
                0 <= y + j < a["altezza"] and 0 <= x + i < a["larghezza"] and
                not solida_nel_gioco(g[y + j][x + i], G) and g[y + j][x + i] not in G.VARCHI
                for i in (-1, 0, 1) for j in (-1, 0, 1))
            if (libero and all(max(abs(x - u), abs(y - v)) >= 4 for u, v in a["spawn"].values()) and
                    all(max(abs(x - u), abs(y - v)) >= 3 for u, v in lontani) and
                    all(max(abs(x - u), abs(y - v)) >= 4 for u, v in posti)):
                scelto = (x, y)
                break
        if not scelto:
            raise ErroreStoria(f"nessun posto per la guardia di {gd['raccolta']} in {area_id}")
        posti.append(scelto)
    return posti


def leggi_le_quest():
    return leggi_quest(open(os.path.join(COPIONE, FILE_QUEST), encoding="utf-8").read())


def genera():
    scene, npc = leggi_copione()
    controlla(scene)
    quest = leggi_le_quest()
    posti, posti_quest, posti_raccolte, posti_guardie = posti_della_quest(npc, quest, con_guardie=True)
    return (header(scene, npc, posti, quest, posti_quest, posti_raccolte, posti_guardie),
            testi_del_copione(scene, npc) + "\n".join(testi_delle_quest(quest)) + "\n")


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
