"""Libreria dello stile bloccato (fase FS): legge i dati di stile/dati/ e li controlla.

Ogni scelta della Guida di stile (https://claude.ai/artifact/5Pw6CLTog1JH9u1uvhNmpm) e' qui
un file JSON piu' una funzione `controlla_*` che restituisce l'elenco dei difetti (vuoto se
il dato rispetta la guida). I test chiamano queste funzioni sui dati veri e su copie
guastate apposta: un controllo che non ha mai visto un difetto non sa di funzionare.

Solo libreria standard: i test girano anche nell'immagine devkitARM della CI, dove PIL non c'e'.
I numeri decimali stanno solo qui (strumenti sul PC); nel gioco entrano interi BGR555 e
tabelle constexpr generate da esporta_cpp.py.
"""

import colorsys
import copy
import json
import os

RADICE = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(RADICE, "dati")


def carica(nome):
    with open(os.path.join(DATI, nome + ".json"), encoding="utf-8") as f:
        return json.load(f)


def salva(nome, dati):
    with open(os.path.join(DATI, nome + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)
        f.write("\n")


def guasta(dati):
    """Copia profonda per le prove negative."""
    return copy.deepcopy(dati)


# ================================================================================================
# Scelta 3: palette
# ================================================================================================

def a5(v8):
    """Canale a 8 bit -> 5 bit, come la tavola della scelta 3."""
    return min(31, round(v8 / 255 * 31))


def da5(v5):
    return v5 * 255 // 31


def bgr555(r8, g8, b8):
    return a5(r8) | (a5(g8) << 5) | (a5(b8) << 10)


def rgb_di(parola):
    """BGR555 -> (r, g, b) a 8 bit."""
    return (da5(parola & 31), da5((parola >> 5) & 31), da5((parola >> 10) & 31))


def calcola_rampa(h, n, smax, vmin, vmax, shift):
    """Metodo di Slynyrd (scelta 3): luminosita' crescente, saturazione massima al centro,
    tinta che ruota di `shift` gradi per tono verso i toni chiari."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        hue = (h + (t - 0.5) * shift * (n - 1)) % 360
        sat = smax * (1 - abs(t - 0.5) * 1.1)
        val = vmin + (vmax - vmin) * t
        r, g, b = colorsys.hsv_to_rgb(hue / 360, max(0, sat), val)
        out.append(bgr555(int(r * 255), int(g * 255), int(b * 255)))
    return out


def calcola_notte(parola, p):
    """Variante notturna (notte e Bottaccione): stessa grafica, palette trasformata."""
    r, g, b = [v / 255 for v in rgb_di(parola)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l * p["luce"], s * p["saturazione"])
    k = p["canali"]
    return bgr555(int(r2 * k[0][0] + k[0][1]), int(g2 * k[1][0] + k[1][1]),
                  int(min(1, b2 * p["blu"]) * k[2][0] + k[2][1]))


def calcola_palette(parametri):
    rampe = []
    for r in parametri["rampe"]:
        giorno = calcola_rampa(r["tinta"], r["toni"], r["saturazione_max"], r["luce_min"],
                               r["luce_max"], parametri["hue_shift_per_tono"])
        rampe.append({"nome": r["nome"], "giorno": giorno,
                      "notte": [calcola_notte(c, parametri["notte"]) for c in giorno]})
    return rampe


def luminanza(parola):
    r, g, b = rgb_di(parola)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def colore(palette, rif, notte=False):
    """[nome rampa, tono] -> parola BGR555."""
    nome, tono = rif
    for r in palette["rampe"]:
        if r["nome"] == nome:
            return r["notte" if notte else "giorno"][tono]
    raise KeyError(nome)


def controlla_palette(p):
    err = []
    par = p["parametri"]
    if par["hue_shift_per_tono"] != 10:
        err.append("hue shifting diverso dai 10 gradi per tono della scelta 3")
    if len(p["rampe"]) != 9:
        err.append(f"{len(p['rampe'])} rampe invece di 9")
    totale = sum(len(r["giorno"]) for r in p["rampe"])
    if not 38 <= totale <= 46:
        err.append(f"{totale} colori, la guida ne vuole circa 42")
    attese = calcola_palette(par)
    if [a["giorno"] for a in attese] != [r["giorno"] for r in p["rampe"]]:
        err.append("rampe di giorno non allineate ai parametri: rigenerare con genera.py")
    if [a["notte"] for a in attese] != [r["notte"] for r in p["rampe"]]:
        err.append("rampe di notte non allineate ai parametri: rigenerare con genera.py")
    for r in p["rampe"]:
        for chiave in ("giorno", "notte"):
            if len(r[chiave]) != len(r["giorno"]):
                err.append(f"{r['nome']}: {chiave} ha un numero di toni diverso")
            for c in r[chiave]:
                if not isinstance(c, int) or not 0 <= c < 0x8000:
                    err.append(f"{r['nome']}: {c!r} non e' una parola BGR555")
        lum = [luminanza(c) for c in r["giorno"]]
        if any(b <= a for a, b in zip(lum, lum[1:])):
            err.append(f"{r['nome']}: la luminosita' non cresce lungo la rampa")
        if len(set(r["giorno"])) != len(r["giorno"]):
            err.append(f"{r['nome']}: due toni identici dopo l'arrotondamento a BGR555")
        # la notte e' piu' scura del giorno, tono per tono
        for g, n in zip(r["giorno"], r["notte"]):
            if luminanza(n) >= luminanza(g) and luminanza(g) > 40:
                err.append(f"{r['nome']}: tono notturno non piu' scuro di quello diurno")
                break
    return err


# ================================================================================================
# Scelta 8: font proporzionale
# ================================================================================================

ALTEZZA_CELLA = 10        # righe 0-1 accenti delle maiuscole, 2-8 corpo, 9 discendenti
RIGA_MAIUSCOLE = 2        # prima riga delle maiuscole (7 px: righe 2-8)
RIGA_X = 4                # prima riga del corpo minuscolo (5 px: righe 4-8)
LINEA_BASE = 8

MINUSCOLE_BASSE = "acemnorsuvwxz"
DISCENDENTI = "gpqy"


def inchiostro(glifo):
    """Righe che contengono almeno un pixel acceso."""
    return [i for i, r in enumerate(glifo) if "#" in r]


def larghezza_glifo(font, ch):
    return len(font["glifi"][ch][0])


def avanzamento(font, ch):
    return larghezza_glifo(font, ch) + font["spaziatura"]


def larghezza_testo(font, testo):
    return sum(avanzamento(font, c) for c in testo)


def normalizza(font, testo):
    """Sostituzioni dichiarate nel file (es. apostrofo tipografico -> apostrofo)."""
    return "".join(font["equivalenze"].get(c, c) for c in testo)


def a_capo(font, testo, larghezza_max):
    """Divide il testo in righe che stanno in larghezza_max pixel (a capo sugli spazi)."""
    righe, cur = [], ""
    for parola in testo.split():
        prova = (cur + " " + parola).strip()
        if cur and larghezza_testo(font, prova) > larghezza_max:
            righe.append(cur)
            cur = parola
        else:
            cur = prova
    righe.append(cur)
    return righe


def caratteri_mancanti(font, testo):
    testo = normalizza(font, testo)
    return sorted({c for c in testo if c not in font["glifi"] and c not in "\n"})


def controlla_font(f):
    err = []
    if f["altezza"] != ALTEZZA_CELLA or f["interlinea"] != 10:
        err.append("cella o interlinea diverse da 10 px")
    glifi = f["glifi"]
    if not 90 <= len(glifi) <= 110:
        err.append(f"{len(glifi)} glifi, la guida ne vuole circa 100")
    for ch, g in glifi.items():
        if len(g) != ALTEZZA_CELLA:
            err.append(f"{ch!r}: {len(g)} righe invece di {ALTEZZA_CELLA}")
            continue
        if len({len(r) for r in g}) != 1:
            err.append(f"{ch!r}: righe di lunghezza diversa")
            continue
        if not 1 <= len(g[0]) <= 8:
            err.append(f"{ch!r}: larghezza {len(g[0])} fuori da 1..8 (un byte per riga)")
        if any(set(r) - {".", "#"} for r in g):
            err.append(f"{ch!r}: caratteri diversi da '.' e '#'")
        ink = inchiostro(g)
        if ch == " ":
            if ink:
                err.append("lo spazio ha pixel accesi")
            continue
        if not ink:
            err.append(f"{ch!r}: glifo vuoto")
            continue
        # metrica: maiuscole alte 7 px, corpo minuscolo 5 px, linea di base sotto la riga 8
        if "A" <= ch <= "Z" and ch not in "Q" and (ink[0] != RIGA_MAIUSCOLE or ink[-1] != LINEA_BASE):
            err.append(f"{ch!r}: la maiuscola non e' alta 7 px sulle righe 2-8")
        if ch in "ÀÈÉÌÒÙ" and (ink[0] != 0 or ink[-1] != LINEA_BASE):
            err.append(f"{ch!r}: maiuscola accentata senza accento sulle righe 0-1")
        if ch in MINUSCOLE_BASSE and (ink[0] != RIGA_X or ink[-1] != LINEA_BASE):
            err.append(f"{ch!r}: il corpo minuscolo non e' di 5 px sulle righe 4-8")
        if ch in DISCENDENTI and ink[-1] != ALTEZZA_CELLA - 1:
            err.append(f"{ch!r}: discendente che non scende alla riga 9")
        if ch in "0123456789" and (ink[0] != RIGA_MAIUSCOLE or ink[-1] != LINEA_BASE):
            err.append(f"{ch!r}: la cifra non e' alta come le maiuscole")
        # nessuna colonna vuota ai lati: la spaziatura la mette il motore
        if all(r[0] == "." for r in g) or all(r[-1] == "." for r in g):
            err.append(f"{ch!r}: colonna vuota sul bordo")
    for ch in f["obbligatori"]:
        if ch not in glifi:
            err.append(f"manca il glifo obbligatorio {ch!r}")
    for da, a in f["equivalenze"].items():
        if a not in glifi:
            err.append(f"equivalenza {da!r} -> {a!r} verso un glifo che non c'e'")
    return err


# ================================================================================================
# Scelta 9: cornici a vetrata 9-slice
# ================================================================================================

def componi_cornice(c, colonne, righe):
    """Mappa di tile (nome, hflip, vflip) di un riquadro colonne x righe tile."""
    if colonne < 3 or righe < 3:
        raise ValueError("una cornice 9-slice vuole almeno 3x3 tile")
    r = c["regole"]
    mappa = []
    for y in range(righe):
        riga = []
        for x in range(colonne):
            bordo_x = x in (0, colonne - 1)
            bordo_y = y in (0, righe - 1)
            if bordo_x and bordo_y:
                riga.append((r["angolo"], x != 0, y != 0))
            elif bordo_y:
                seq = r["lato_orizzontale"]
                riga.append((seq[(x - 1) % len(seq)], False, False))
            elif bordo_x:
                seq = r["lato_verticale"]
                riga.append((seq[(y - 1) % len(seq)], False, False))
            else:
                riga.append((r["centro"], False, False))
        mappa.append(riga)
    return mappa


def pixel_tile(c, nome, hflip=False, vflip=False):
    t = [[int(v, 16) for v in riga] for riga in c["tile"][nome]]
    if hflip:
        t = [riga[::-1] for riga in t]
    if vflip:
        t = t[::-1]
    return t


def disegna_mappa(c, mappa):
    """Indici di palette (0-15) del riquadro intero, riga per riga."""
    h = len(mappa) * 8
    w = len(mappa[0]) * 8
    img = [[0] * w for _ in range(h)]
    for ty, riga in enumerate(mappa):
        for tx, (nome, hf, vf) in enumerate(riga):
            px = pixel_tile(c, nome, hf, vf)
            for y in range(8):
                for x in range(8):
                    img[ty * 8 + y][tx * 8 + x] = px[y][x]
    return img


def controlla_cornice(c, palette):
    err = []
    ruoli = c["ruoli"]
    if len(c["colori"]) != 16 or c["colori"][0] is not None:
        err.append("la sottopalette deve avere 16 voci, la 0 trasparente")
    for i, rif in enumerate(c["colori"][1:], 1):
        if rif is None:
            continue
        try:
            colore(palette, rif)
        except (KeyError, IndexError, TypeError):
            err.append(f"colore {i} {rif!r} non e' nella palette")
    for nome, t in c["tile"].items():
        if len(t) != 8 or any(len(r) != 8 for r in t):
            err.append(f"tile {nome}: non e' 8x8")
            return err
        if any(set(r) - set("0123456789abcdef") for r in t):
            err.append(f"tile {nome}: indice non esadecimale")
            return err
        for v in {int(ch, 16) for r in t for ch in r} - {0}:
            if c["colori"][v] is None:
                err.append(f"tile {nome}: usa l'indice {v}, che non ha colore")
    P, F, R = ruoli["piombo"], ruoli["fondo"], ruoli["riflesso"]
    tessere = set(ruoli["tessere"])
    for col, rig in ((30, 7), (9, 6), (3, 3), (12, 4)):
        img = disegna_mappa(c, componi_cornice(c, col, rig))
        h, w = len(img), len(img[0])
        nome = f"riquadro {col}x{rig}"
        # piombi continui: bordo esterno e filo interno, senza buchi
        esterno = img[0] + img[-1] + [img[y][0] for y in range(h)] + [img[y][-1] for y in range(h)]
        if any(v != P for v in esterno):
            err.append(f"{nome}: piombo esterno interrotto")
        interno = (img[7][7:w - 7] + img[h - 8][7:w - 7] +
                   [img[y][7] for y in range(7, h - 7)] + [img[y][w - 8] for y in range(7, h - 7)])
        if any(v != P for v in interno):
            err.append(f"{nome}: filo di piombo interno interrotto")
        # fondo opaco, chiaro e uniforme dentro
        dentro = {img[y][x] for y in range(8, h - 8) for x in range(8, w - 8)}
        if dentro and dentro != {F}:
            err.append(f"{nome}: fondo interno non uniforme ({sorted(dentro)})")
        if any(0 in r for r in img):
            err.append(f"{nome}: pixel trasparenti, il riquadro deve essere opaco")
        # ogni tessera dei lati (tra due piombi) ha un solo riflesso, in alto a sinistra
        for nome_t in set(c["regole"]["lato_orizzontale"]) | set(c["regole"]["lato_verticale"]):
            px = pixel_tile(c, nome_t)
            vetro = [(x, y) for y in range(8) for x in range(8) if px[y][x] != P]
            rifl = [(x, y) for (x, y) in vetro if px[y][x] == R]
            colori_vetro = {px[y][x] for (x, y) in vetro} - {R}
            if len(rifl) != 1:
                err.append(f"tile {nome_t}: {len(rifl)} riflessi invece di 1")
            elif rifl[0] != (min(x for x, _ in vetro) + 1, min(y for _, y in vetro) + 1):
                err.append(f"tile {nome_t}: riflesso non in alto a sinistra (luce della scelta 4)")
            if len(colori_vetro) != 1 or not colori_vetro <= tessere:
                err.append(f"tile {nome_t}: la tessera non e' un solo colore della palette")
    # le tessere alternano colori diversi lungo i lati
    for lato in ("lato_orizzontale", "lato_verticale"):
        seq = c["regole"][lato]
        col = [next(v for r in pixel_tile(c, t) for v in r if v not in (P, R)) for t in seq]
        if any(a == b for a, b in zip(col, col[1:])):
            err.append(f"{lato}: due tessere vicine dello stesso colore")
    return err


# ================================================================================================
# Scelta 10: ritratti a strati
# ================================================================================================

LATO_RITRATTO = 32


def componi_ritratto(rt, palette, nome, espressione):
    """Restituisce la matrice 32x32 di parole BGR555 (None = trasparente) e lo strato di ogni
    pixel. Il contorno quasi nero si aggiunge in automatico (scelta 5)."""
    p = rt["personaggi"][nome]
    img = [[None] * LATO_RITRATTO for _ in range(LATO_RITRATTO)]
    strato = [[None] * LATO_RITRATTO for _ in range(LATO_RITRATTO)]
    colori_ruolo = dict(rt["ruoli_fissi"])
    colori_ruolo.update(p["colori"])
    for s in rt["ordine"]:
        variante = espressione if s in rt["strati_espressione"] else p["strati"].get(s)
        if variante is None:
            continue
        maschera = rt["strati"][s][variante]
        for y, riga in enumerate(maschera):
            for x, v in enumerate(riga):
                if v != ".":
                    img[y][x] = colore(palette, colori_ruolo[v])
                    strato[y][x] = s
    contorno = colore(palette, rt["contorno"])
    pieni = [[c is not None for c in r] for r in img]
    for y in range(LATO_RITRATTO):
        for x in range(LATO_RITRATTO):
            if pieni[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < LATO_RITRATTO and 0 <= ny < LATO_RITRATTO and pieni[ny][nx]:
                    img[y][x] = contorno
                    strato[y][x] = "contorno"
                    break
    return img, strato


def controlla_ritratti(rt, palette):
    err = []
    if sorted(rt["espressioni"]) != sorted(["calmo", "preoccupato", "deciso"]):
        err.append("le espressioni devono essere calmo, preoccupato, deciso")
    if sorted(rt["strati_espressione"]) != ["bocca", "sopracciglia"]:
        err.append("le espressioni devono cambiare solo sopracciglia e bocca")
    x0, y0, x1, y1 = rt["zona_espressione"]
    for s in rt["strati_espressione"]:
        if sorted(rt["strati"][s]) != sorted(rt["espressioni"]):
            err.append(f"lo strato {s} non ha una variante per ogni espressione")
        for v, m in rt["strati"][s].items():
            fuori = [(x, y) for y, r in enumerate(m) for x, ch in enumerate(r)
                     if ch != "." and not (x0 <= x <= x1 and y0 <= y <= y1)]
            if fuori:
                err.append(f"strato {s}/{v}: pixel {fuori[0]} fuori dalla zona del viso")
    attesi = ["veste", "viso", "occhi", "sopracciglia", "bocca", "barba", "capelli", "copricapo"]
    if sorted(rt["ordine"]) != sorted(attesi):
        err.append("strati diversi da quelli della scelta 10")
    for s, varianti in rt["strati"].items():
        for v, m in varianti.items():
            if len(m) != LATO_RITRATTO or any(len(r) != LATO_RITRATTO for r in m):
                err.append(f"strato {s}/{v}: non e' 32x32")
                return err
    for nome, p in rt["personaggi"].items():
        for s, v in p["strati"].items():
            if v is not None and v not in rt["strati"].get(s, {}):
                err.append(f"{nome}: variante {s}/{v} inesistente")
        for s in rt["strati"]:
            for v, m in rt["strati"][s].items():
                if (s in rt["strati_espressione"] or p["strati"].get(s) == v):
                    usati = {ch for r in m for ch in r} - {"."}
                    mancanti = usati - set(rt["ruoli_fissi"]) - set(p["colori"])
                    if mancanti:
                        err.append(f"{nome}: ruoli di colore senza valore {sorted(mancanti)}")
        if err:
            return err
        immagini = {}
        for e in rt["espressioni"]:
            try:
                img, strato = componi_ritratto(rt, palette, nome, e)
            except (KeyError, IndexError) as x:
                err.append(f"{nome}/{e}: colore fuori palette ({x})")
                continue
            immagini[e] = (img, strato)
            usati = {c for r in img for c in r if c is not None}
            if len(usati) > 15:
                err.append(f"{nome}/{e}: {len(usati)} colori, uno sprite 4bpp ne tiene 15")
            if colore(palette, rt["contorno"]) not in usati:
                err.append(f"{nome}/{e}: manca il contorno quasi nero")
        # luce da alto-sinistra: la veste in ombra e' piu' scura e sta a destra di quella in luce
        luce, ombra = p["colori"].get("V"), p["colori"].get("v")
        if luce and ombra and immagini:
            if luminanza(colore(palette, ombra)) >= luminanza(colore(palette, luce)):
                err.append(f"{nome}: la veste in ombra (v) non e' piu' scura di quella in luce (V)")
            m = rt["strati"]["veste"][p["strati"]["veste"]]
            xl = [x for r in m for x, ch in enumerate(r) if ch == "V"]
            xo = [x for r in m for x, ch in enumerate(r) if ch == "v"]
            if xl and xo and sum(xo) / len(xo) <= sum(xl) / len(xl):
                err.append(f"{nome}: l'ombra della veste non sta a destra (luce da sinistra)")
        # le espressioni cambiano solo strati confinati nella zona del viso (controllato sopra)
        if len(immagini) == 3:
            if len({str(i[0]) for i in immagini.values()}) != 3:
                err.append(f"{nome}: due espressioni identiche")
    return err


# ================================================================================================
# Scelta 11: scheletro delle pose
# ================================================================================================

def controlla_pose(ps):
    err = []
    w, h = ps["sprite"]
    if (w, h) != (16, 32) or ps["corpo"] != [16, 24]:
        err.append("sprite 16x32 con corpo 16x24 (scelta 6)")
    if ps["vblank_al_secondo"] != 60:
        err.append("i tempi si scrivono in vblank a 60 Hz")
    if sorted(ps["direzioni"]) != ["destra", "giu", "su"] or ps["specchiate"] != {"sinistra": "destra"}:
        err.append("direzioni giu/su/destra disegnate, sinistra = destra specchiata in hardware")
        return err
    an = ps["animazioni"]
    attese = {
        "camminata": [6] * 6,
        "riposo": [30, 30],
        "attacco": [12, 10, 3, 12, 8],
    }
    for nome, durate in attese.items():
        if nome not in an:
            err.append(f"manca l'animazione {nome}")
            continue
        if [f["vblank"] for f in an[nome]["fotogrammi"]] != durate:
            err.append(f"{nome}: durate {[f['vblank'] for f in an[nome]['fotogrammi']]} invece di {durate}")
    if "attacco" in an and [f["posa"] for f in an["attacco"]["fotogrammi"]] != \
            ["pronto", "anticipa", "colpo", "tenuta", "rientro"]:
        err.append("attacco: pose diverse da pronto, anticipa, colpo, tenuta, rientro")
    if "colpito" not in an or len(an["colpito"]["fotogrammi"]) != 2:
        err.append("colpo subito: 2 fotogrammi (lampo e arretramento)")
    piede = ps["linea_piedi"]
    testa_min = h - ps["corpo"][1]
    for nome, a in an.items():
        if a.get("ciclo") not in (True, False):
            err.append(f"{nome}: manca 'ciclo'")
        for d in ps["direzioni"]:
            frames = [f["giunti"][d] for f in a["fotogrammi"]]
            for i, g in enumerate(frames):
                if sorted(g) != sorted(ps["giunti"]):
                    err.append(f"{nome}/{d}/{i}: giunti {sorted(g)} diversi dallo scheletro")
                    continue
                for j, (x, y) in g.items():
                    if not (0 <= x < w and testa_min - 2 <= y < h):
                        err.append(f"{nome}/{d}/{i}: giunto {j} fuori dal corpo ({x},{y})")
                if max(g["piede_a"][1], g["piede_b"][1]) != piede and nome != "colpito":
                    err.append(f"{nome}/{d}/{i}: nessun piede a terra")
                if g["testa"][1] >= g["bacino"][1]:
                    err.append(f"{nome}/{d}/{i}: testa sotto il bacino")
            if nome == "camminata" and frames:
                # il ciclo deve richiudersi: fra l'ultimo e il primo fotogramma un passo normale
                passi = [max(abs(a_[k][0] - b[k][0]) + abs(a_[k][1] - b[k][1]) for k in a_)
                         for a_, b in zip(frames, frames[1:] + frames[:1])]
                if max(passi) > 3:
                    err.append(f"camminata/{d}: salto di {max(passi)} px fra due fotogrammi")
                if len({str(f) for f in frames}) != len(frames):
                    err.append(f"camminata/{d}: fotogrammi ripetuti")
                ytesta = [f["testa"][1] for f in frames]
                if max(ytesta) - min(ytesta) > 1:
                    err.append(f"camminata/{d}: la testa oscilla piu' di 1 px")
    if "attacco" in an:
        d = an["attacco"]["fotogrammi"]
        if d[2]["vblank"] >= min(f["vblank"] for i, f in enumerate(d) if i != 2):
            err.append("attacco: il colpo deve essere la posa piu' breve")
        if not d[2].get("scia"):
            err.append("attacco: il colpo porta la scia")
    return err


# ================================================================================================
# Scelta 12: logo in capitali lombarde
# ================================================================================================

def disegna_logo(lg, testo, monocromatico=False):
    """Matrice di ruoli ('.', 'luce', 'alto', 'basso', 'contorno') del logo a scala 1."""
    gl = lg["glifi"]
    h = len(next(iter(gl.values())))
    w = sum(len(gl[c][0]) + lg["spaziatura"] for c in testo) - lg["spaziatura"] + 2
    img = [["."] * (w + 2) for _ in range(h + 2)]
    x = 1
    for c in testo:
        for r, riga in enumerate(gl[c]):
            for k, v in enumerate(riga):
                if v != "#":
                    continue
                ruolo = "alto" if r < lg["righe_alte"] else "basso"
                if r == 0 or (r < 3 and k > 0 and riga[k - 1] == "."):
                    ruolo = "luce"
                img[r + 1][x + k + 1] = "pieno" if monocromatico else ruolo
        x += len(gl[c][0]) + lg["spaziatura"]
    pieni = [[v != "." for v in r] for r in img]
    for y in range(len(img)):
        for xx in range(len(img[0])):
            if not pieni[y][xx] and any(
                    0 <= y + dy < len(img) and 0 <= xx + dx < len(img[0]) and pieni[y + dy][xx + dx]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img[y][xx] = "contorno"
    return img


def controlla_logo(lg, palette):
    err = []
    gl = lg["glifi"]
    for c in lg["testo"]:
        if c not in gl:
            err.append(f"manca la lettera lombarda {c!r}")
    if err:
        return err
    altezze = {len(g) for g in gl.values()}
    if len(altezze) != 1:
        err.append("lettere di altezze diverse")
    for c, g in gl.items():
        if len({len(r) for r in g}) != 1:
            err.append(f"{c!r}: righe di lunghezza diversa")
    if err:
        return err
    for ruolo in ("luce", "alto", "basso", "contorno", "pieno"):
        try:
            colore(palette, lg["colori"][ruolo])
        except (KeyError, IndexError):
            err.append(f"colore {ruolo} fuori palette")
    img = disegna_logo(lg, lg["testo"])
    ruoli = {v for r in img for v in r} - {"."}
    if ruoli != {"luce", "alto", "basso", "contorno"}:
        err.append(f"il logo usa i ruoli {sorted(ruoli)}: oro a due toni, riflesso e contorno")
    if len({lg["colori"][r][0] for r in ("alto", "basso")}) != 1 or lg["colori"]["alto"][0] != "oro e bronzo":
        err.append("i due toni del corpo devono venire dalla rampa oro e bronzo")
    if lg["colori"]["contorno"] != ["legno e cuoio", 0]:
        err.append("il contorno e' il quasi nero della scelta 5 (legno e cuoio, tono 0)")
    mono = disegna_logo(lg, lg["testo"], monocromatico=True)
    if {v for r in mono for v in r} - {"."} != {"pieno", "contorno"}:
        err.append("la versione monocromatica deve avere un colore solo piu' il contorno")
    larghezza = len(img[0]) * lg["scala_titolo"]
    if larghezza > 240:
        err.append(f"il logo a x{lg['scala_titolo']} e' largo {larghezza} px: non sta nei 240 dello schermo")
    return err
