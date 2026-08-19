#!/usr/bin/env python3
"""
Da FOTOGRAFIA a TILE del GBA: converte una foto di un monumento reale in pixel art indicizzata,
alla palette e ai vincoli del progetto.

    python tools/photo_to_tiles.py

PERCHE' ESISTE. Il progetto non ha budget e nessuno che sappia disegnare. L'unica via che resta
per avere una Gubbio riconoscibile e' partire dalle fotografie — che abbiamo, libere e con
licenza tracciata (docs/riferimenti/FONTI.md) — e portarle a 8 pixel per tile con uno strumento
invece che con una mano. Provato: una conversione di questo tipo produce un Palazzo dei Consoli
piu' riconoscibile di quanto si ottenga disegnandolo proceduralmente, perche' conserva le
PROPORZIONI vere, che sono cio' che l'occhio riconosce.

I TRE PROBLEMI CHE UNA CONVERSIONE INGENUA NON RISOLVE, e come li affronta questo strumento:

1. **Una foto non ha ripetizione.** Ridimensionare e quantizzare da' quasi tanti tile unici
   quante sono le celle — misurato sul Palazzo dei Consoli: 381 tile su 418 celle. Un tileset
   vive del contrario. Qui i tile quasi identici vengono UNIFICATI, con una soglia che cresce
   finche' il risultato non rientra nel budget dichiarato: si degrada il dettaglio fino a stare
   nei limiti, invece di scoprire troppo tardi che non ci si sta.

2. **La palette non puo' essere scelta dalla foto.** Un background a 4bpp ha SEDICI colori per
   tutto: se ogni monumento portasse i suoi, non ne basterebbero. La palette e' un parametro,
   condivisa da tutti gli asset dell'area.

3. **Il rumore fotografico diventa sporcizia.** A 8 px per tile la grana di un muro non e'
   texture, e' rumore che moltiplica i tile unici senza aggiungere nulla. Si sfoca PRIMA di
   ridurre: la sfocatura toglie dettaglio che comunque andrebbe perso, ma lo toglie in modo
   ordinato.
"""

import os
import struct
import sys

from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RIFERIMENTI = os.path.join(ROOT, "riferimenti")

# GLI ESITI NON VANNO IN graphics/. Quella cartella e' il territorio di grit, che pretende un
# `.json` accanto a ogni `.bmp` e li trasforma in asset di Butano: mettendoci gli ingredienti si
# rompe la build. Questi sono materiali intermedi che `make_piazza_art.py` incolla dentro gli
# asset veri, e stanno in una cartella loro.
INGREDIENTI = os.path.join(ROOT, "ingredienti")

# La palette dell'area, condivisa da suolo, edifici e cornici. Sedici colori per TUTTO cio' che
# sta su un background a 4bpp: e' il vincolo piu' stretto della grafica GBA, ed e' per questo che
# le sfumature vanno spese dove l'occhio guarda — sei per la pietra dei palazzi, tre per il cotto.
PALETTE_PIAZZA = [
    (0, 0, 0),          # 0  fuori mappa / nero dei vani
    (166, 86, 58),      # 1  cotto della pavimentazione
    (148, 74, 50),      # 2  cotto, seconda tinta
    (112, 56, 40),      # 3  fuga fra le lastre
    (238, 232, 216),    # 4  pietra in piena luce
    (216, 208, 190),    # 5  pietra
    (194, 184, 164),    # 6  pietra in mezz'ombra
    (168, 158, 138),    # 7  pietra in ombra
    (132, 122, 106),    # 8  ombra profonda
    (92, 84, 74),       # 9  vani delle finestre, sottogronda
    (110, 72, 40),      # 10 legno dei portoni
    (64, 118, 152),     # 11 acqua della fontana
    (74, 92, 60),       # 12 vegetazione
    (46, 42, 38),       # 13 nero dei passaggi voltati
    (206, 172, 74),     # 14 bronzo e dettagli
    (150, 140, 120),    # 15 parapetto
]


# Il fondale panoramico NON puo' condividere la palette della piazza: un panorama ha cielo, bosco
# e citta' lontana, e la palette urbana non ha ne' azzurri ne' verdi a sufficienza. Provato: lo
# skyline quantizzato sulla palette della piazza collassava a UN SOLO tile unico, cioe' a una
# macchia uniforme. Ogni FAMIGLIA di asset ha la sua palette; e' anche il modo in cui il GBA
# vuole essere usato, perche' i banchi di palette sono per background, non per gioco.
PALETTE_PANORAMA = [
    (0, 0, 0),
    (120, 168, 214), (98, 148, 200), (78, 128, 186),     # cielo, tre fasce
    (226, 220, 204), (196, 188, 170), (160, 152, 136),   # citta' lontana, pietra
    (140, 96, 72), (110, 70, 52),                        # tetti in cotto, visti da lontano
    (96, 118, 76), (72, 96, 58), (52, 74, 44),           # bosco del monte, tre profondita'
    (38, 54, 34),                                        # ombra del versante
    (150, 150, 140), (100, 100, 94),                     # rovine e mura sul crinale
    (28, 26, 24),
]


# La palette del FONDALE DI BATTAGLIA (make_placeholder_art.make_battle_bg): notturna, perche'
# l'assedio e' di notte. Convertire lo skyline diurno su questi colori invece che su quelli del
# panorama non e' un ripiego — e' cio' che fa somigliare la fotografia a una scena del gioco
# invece che a una cartolina incollata sopra.
PALETTE_ASSEDIO = [
    (18, 20, 34), (30, 32, 52), (48, 46, 68),            # cielo notturno, tre fasce
    (34, 32, 46), (24, 24, 36),                          # monte lontano e vicino
    (66, 62, 80),                                        # nebbia
    (44, 40, 38), (58, 52, 46),                          # terreno
    (14, 15, 12), (26, 28, 22),                          # pannello HUD
    (138, 110, 44), (90, 72, 30),                        # bordo bronzo
    (10, 11, 9), (72, 78, 66),                           # nero pannello, divisorio
    (0, 0, 0), (0, 0, 0),
]


def quantizza(img, palette):
    """Riporta l'immagine sulla palette data, senza dithering.

    Il dithering e' controproducente qui: a questa scala sparpaglia i colori e MOLTIPLICA i tile
    unici, che sono la risorsa scarsa."""
    # Le entry non usate ripetono l'ULTIMO colore invece di essere nere: riempiendole di zeri,
    # PIL puo' assegnare a qualche pixel un indice oltre la palette reale — e con `solo_indici`
    # quell'indice finisce fuori dalla lista. Ripetendo, ogni indice resta nel dominio.
    tavolozza = Image.new("P", (1, 1))
    piatta = [c for colore in palette for c in colore]
    piatta += list(palette[-1]) * (256 - len(palette))
    tavolozza.putpalette(piatta)
    return img.convert("RGB").quantize(palette=tavolozza, dither=Image.NONE)


def piccola_o_foto(foto, w, h):
    return foto.resize((w, h), Image.LANCZOS)


def riduci_tile(indici, larghezza, altezza, tetto):
    """Unifica i tile quasi identici finche' non si rientra nel tetto.

    La soglia parte da zero — solo i duplicati esatti — e cresce: e' la forma piu' onesta di
    degrado, perche' il dettaglio si perde a partire da dove si nota di meno. Ritorna i tile
    modificati e la soglia a cui si e' fermata, che vale la pena stampare: dice quanto si e'
    dovuto rinunciare."""
    tw, th = larghezza // 8, altezza // 8

    def celle():
        return [[tuple(indici[(ty * 8 + y) * larghezza + tx * 8 + x] for y in range(8)
                       for x in range(8)) for tx in range(tw)] for ty in range(th)]

    griglia = celle()

    # LA SOGLIA NON PUO' SALIRE OLTRE UN QUARTO DEI PIXEL DI UN TILE. Un tile ha 64 pixel:
    # con soglia 64 "qualunque tile e' uguale a qualunque altro", e la fusione greedy collassa
    # l'immagine intera su un solo rappresentante. E' successo davvero — basilica e teatro
    # romano sono usciti a UN tile unico, cioe' a una macchia — e il difetto e' insidioso
    # perche' il conteggio finale sembra un ottimo risultato invece che un disastro.
    # Oltre 16 si preferisce FALLIRE dicendo quanti tile servirebbero.
    for soglia in (0, 1, 2, 4, 8, 12, 16):
        rappresentanti = []
        mappa = {}

        for ty in range(th):
            for tx in range(tw):
                cella = griglia[ty][tx]

                if cella in mappa:
                    continue

                for indice, rif in enumerate(rappresentanti):
                    if sum(1 for p, q in zip(cella, rif) if p != q) <= soglia:
                        mappa[cella] = indice
                        break
                else:
                    mappa[cella] = len(rappresentanti)
                    rappresentanti.append(cella)

        if len(rappresentanti) <= tetto:
            fuori = list(indici)

            for ty in range(th):
                for tx in range(tw):
                    scelto = rappresentanti[mappa[griglia[ty][tx]]]

                    for y in range(8):
                        for x in range(8):
                            fuori[(ty * 8 + y) * larghezza + tx * 8 + x] = scelto[y * 8 + x]

            return fuori, len(rappresentanti), soglia

    return list(indici), -len(rappresentanti), -1


def scrivi_bmp4(path, width, height, indici, palette):
    rb = width // 2
    pad = (4 - rb % 4) % 4
    body = bytearray()

    for y in range(height - 1, -1, -1):
        riga = indici[y * width:(y + 1) * width]
        for x in range(0, width, 2):
            body.append(((riga[x] & 0xF) << 4) | (riga[x + 1] & 0xF))
        body.extend(b"\x00" * pad)

    off = 14 + 40 + 16 * 4
    header = b"BM" + struct.pack("<IHHI", off + len(body), 0, 0, off)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0, len(body), 2835, 2835, 16, 0)
    pal = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in palette)
    open(path, "wb").write(header + dib + pal + bytes(body))


def converti(sorgente, ritaglio, tile_w, tile_h, tetto_tile, sfocatura=2.0,
             palette=None, solo_indici=None, specchia=False):
    """Da file fotografico a lista di indici di palette, pronta per essere incollata in un BG."""
    percorso = os.path.join(RIFERIMENTI, sorgente)

    if not os.path.exists(percorso):
        sys.exit(f"[foto] manca {percorso}\n       eseguire prima: python tools/fetch_riferimenti.py")

    foto = Image.open(percorso).convert("RGB").crop(ritaglio)

    if specchia:
        # La mappa e' RUOTATA con l'ovest in alto, quindi il nord cade a destra dello schermo.
        # Una facciata fotografata dalla piazza guardando a EST ha pero' il nord alla propria
        # sinistra: incollata cosi' com'e' rovescerebbe il palazzo rispetto al resto della
        # pianta. Le facciate riprese guardando a OVEST — i Consoli — non vanno specchiate.
        foto = foto.transpose(Image.FLIP_LEFT_RIGHT)

    w, h = tile_w * 8, tile_h * 8

    if sfocatura:
        # La sfocatura e' proporzionale al fattore di riduzione: sfocare di un valore fisso
        # sarebbe troppo su una foto piccola e troppo poco su una grande.
        raggio = max(1.0, sfocatura * foto.width / w / 4)
        foto = foto.filter(ImageFilter.GaussianBlur(raggio))

    tavolozza = palette or PALETTE_PIAZZA

    # `solo_indici` restringe la conversione a un sottoinsieme di colori. Serve quando la foto
    # inganna la quantizzazione: la pavimentazione di Piazza Grande e' in COTTO, ma scattata
    # all'ombra i suoi grigi somigliano piu' alla pietra dei palazzi che al rosso — e la
    # quantizzazione, che guarda i pixel e non sa cosa siano, sceglieva la pietra.
    if solo_indici:
        ridotta = [tavolozza[i] for i in solo_indici]
        convertita = quantizza(piccola_o_foto(foto, w, h), ridotta)
        indici = [solo_indici[i] for i in convertita.getdata()]
    else:
        indici = list(quantizza(piccola_o_foto(foto, w, h), tavolozza).getdata())
    ridotti, unici, soglia = riduci_tile(indici, w, h, tetto_tile)

    if unici < 0:
        sys.exit(f"[foto] {sorgente}: non rientra in {tetto_tile} tile senza collassare "
                 f"l'immagine. Alla massima fusione ammessa ne servono {-unici}: "
                 f"alzare il tetto, o ritagliare un'area piu' piccola.")

    print(f"  {sorgente[:34]:34s} -> {tile_w}x{tile_h} tile, {unici:3d} unici "
          f"(tetto {tetto_tile}, soglia di fusione {soglia} px)")
    return ridotti, w, h


# I monumenti da convertire: sorgente, ritaglio nella foto, misura in tile, tetto di tile unici.
# Le misure in tile NON sono libere: vengono dalla scala di `city_reference.h` (1,5 m/tile).
MONUMENTI = {
    # Foto FRONTALE scattata dal committente dentro la piazza: e' quella giusta, perche' in una
    # mappa vista dall'alto una facciata ripresa di tre quarti "punta" nella direzione sbagliata.
    # Il ritaglio prende la parte ALTA — merlatura, archetti pensili, bifore — che e' cio' che si
    # vede dall'alto, nel rapporto esatto dei 22x19 tile: ritagliare fuori rapporto stirerebbe
    # l'edificio, e le proporzioni sono proprio cio' che lo rende riconoscibile.
    "consoli_facciata": {
        "sorgente": "consoli_frontale.jpg",
        # RITAGLIO ALTO: prima prendeva solo la fascia superiore, e in gioco si vedeva mezzo
        # palazzo. Ora entra tutto — dalla cima della torre alla scalinata — compresso in
        # verticale. La compressione e' voluta: e' cio' che fanno i giochi a vista dall'alto,
        # perche' un edificio ripreso di fronte va schiacciato per stare in una fascia di mappa.
        "ritaglio": (405, 40, 1095, 800),
        "tile_w": 22,      # 33 m di fronte, in scala
        "tile_h": 19,      # la fascia nord della piazza
        "tetto_tile": 240,   # misurato: 222 col palazzo intero
        # NIENTE indice 11: e' l'acqua della fontana, e la quantizzazione ci mandava sopra il
        # CIELO della fotografia — che nella mappa compariva come un rettangolo azzurro attorno
        # al palazzo, come se la piazza avesse un buco. Escluso quel colore, il cielo cade sulla
        # pietra chiara e si legge come edificato minore, che e' cio' che c'e' davvero li'.
        "solo_indici": [0, 3, 4, 5, 6, 7, 8, 9, 10, 13],
    },

    # La PAVIMENTAZIONE e' l'asset piu' redditizio di tutti: e' l'unica cosa davvero ripetitiva
    # della piazza, copre meta' schermo e costa pochi tile. Ritaglio quadrato al centro della
    # foto, dove il cotto e' visto piu' da vicino a perpendicolo.
    "piazza_cotto": {
        "sorgente": "pavimentazione.jpg",
        # Ritaglio AMPIO: con un ritaglio stretto i mattoni venivano giganteschi rispetto al
        # giocatore, alto due tile. Un mattone reale e' circa un sesto di tile, quindi la
        # porzione inquadrata dev'essere larga abbastanza da contenerne molti.
        "ritaglio": (0, 280, 768, 1048),
        # TRE tile di lato. Il committente, giocandoci, ha chiesto la trama ancora piu' fine di
        # quattro; provata a due, ma li' la lisca di pesce spariva e restava una macchia rossa
        # picchiettata. Tre e' il punto in cui i mattoni sono piccoli e il disegno a spina si
        # legge ancora: sotto, si perde la cosa stessa che si voleva mostrare.
        "tile_w": 3,
        "tile_h": 3,
        "tetto_tile": 9,
        # Solo cotto e fughe: la spina di pesce e' rossa, e la foto in ombra non basta a dirlo.
        "solo_indici": [1, 2, 3, 4],
    },

    # Palazzo Pretorio: 16 tile di fronte per 6 di profondita', che e' esattamente la fascia che
    # occupa nella griglia (x 26..41, y 34..39). Il primo ritaglio era alto 4 e prendeva solo la
    # fascia delle due finestre: nella mappa il palazzo veniva una macchia chiara senza segni, e
    # sotto restavano due file di riempimento. Qui si prende TUTTA la facciata, dal sottotetto al
    # selciato, e la si schiaccia in verticale — lo stesso compromesso del Palazzo dei Consoli:
    # in una mappa dall'alto la facciata e' vista di scorcio, quindi schiacciarla e' cio' che si
    # vuole, purche' i segni del palazzo (il portale ad arco, le bifore) restino leggibili.
    "pretorio_facciata": {
        "sorgente": "pretorio.jpg",
        "ritaglio": (660, 300, 1075, 670),
        "specchia": True,
        "tile_w": 16,
        "tile_h": 6,
        "tetto_tile": 80,
        "solo_indici": [0, 3, 4, 5, 6, 7, 8, 9, 10, 13],
    },

    # Palazzo del Bargello: 18 m di fronte = 12 tile. La stessa foto della fontana, ritagliata
    # sulla facciata invece che sul bacino.
    "bargello_facciata": {
        "sorgente": "bargello_e_fontana.jpg",
        # Piu' in basso: il primo ritaglio prendeva il tetto e i cavi elettrici invece della
        # facciata. Qui entrano le bifore e il portale, che sono i segni del palazzo.
        "ritaglio": (430, 380, 1024, 776),
        "tile_w": 12,
        "tile_h": 8,
        "tetto_tile": 96,
        "solo_indici": [0, 3, 4, 5, 6, 7, 8, 9, 10, 13],
    },

    # Fontana dei Matti: 4,5 m di diametro = 3 tile (Sez. 23 GDD). Il bacino ottagonale in
    # primo piano nella foto del Bargello.
    "fontana": {
        "sorgente": "bargello_e_fontana.jpg",
        # Centrato sul bacino ottagonale, non sul muro dietro.
        "ritaglio": (170, 1040, 530, 1400),
        "tile_w": 3,
        "tile_h": 3,
        "tetto_tile": 9,
    },

    # Basilica di Sant'Ubaldo: 50 m di fronte = 34 tile. Facciata con la scalinata d'accesso,
    # che e' uno dei suoi tre segni distintivi.
    "basilica_facciata": {
        "sorgente": "basilica.jpg",
        "ritaglio": (270, 80, 918, 660),
        "tile_w": 34,
        "tile_h": 20,
        # 600 e non 200: lo strumento ha detto che alla massima fusione ammessa ne servono 586.
        # Il tetto e' un budget, non un desiderio — e sta comunque nei 1024 di un tileset.
        "tetto_tile": 600,
        "solo_indici": [0, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13],
    },

    # Teatro Romano: 70 m = 46 tile. E' l'unico monumento di cui abbiamo una ripresa DALL'ALTO,
    # cioe' nella stessa vista in cui il gioco lo mostrera': la cavea semicircolare si legge
    # cosi' com'e', senza doverla reinterpretare.
    "teatro_romano": {
        "sorgente": "13-Gubbio-Teatro-Romano-02-696x464.jpg",
        "ritaglio": (170, 40, 660, 420),
        "tile_w": 32,      # ridotto da 46: 1656 celle non stanno in un tileset
        "tile_h": 24,
        "tetto_tile": 700,
        "palette": PALETTE_PANORAMA,
    },

    # Lo stesso skyline, ma per il FONDALE DI BATTAGLIA: stessa foto, palette notturna, e solo i
    # colori di cielo/monte/terreno — i colori dell'HUD restano al pannello, che e' dipinto sopra.
    "skyline_assedio": {
        "sorgente": "skyline.jpg",
        "ritaglio": (0, 10, 735, 262),
        "tile_w": 32,
        "tile_h": 12,
        "tetto_tile": 120,
        "palette": PALETTE_ASSEDIO,
        "solo_indici": [0, 1, 2, 3, 4, 5, 6, 7],
    },

    # Lo skyline della citta' sul fianco del monte: e' il fondale di battaglia (oggi un profilo
    # anonimo) e il parallasse dell'esplorazione.
    "skyline_gubbio": {
        "sorgente": "skyline.jpg",
        "ritaglio": (0, 0, 735, 272),
        "tile_w": 32,
        "tile_h": 12,
        "tetto_tile": 300,   # misurato: 283 al massimo grado di fusione ammesso
        "palette": PALETTE_PANORAMA,
    },
}


def main():
    print("[foto] conversione dei monumenti da fotografia")
    os.makedirs(INGREDIENTI, exist_ok=True)

    for nome, cfg in MONUMENTI.items():
        indici, w, h = converti(cfg["sorgente"], cfg["ritaglio"], cfg["tile_w"], cfg["tile_h"],
                                cfg["tetto_tile"], palette=cfg.get("palette"),
                                solo_indici=cfg.get("solo_indici"),
                                specchia=cfg.get("specchia", False))
        scrivi_bmp4(os.path.join(INGREDIENTI, nome + ".bmp"), w, h, indici,
                    cfg.get("palette") or PALETTE_PIAZZA)

    print("[foto] fatto. Gli asset sono INGREDIENTI: make_piazza_art.py li incolla nella mappa.")


if __name__ == "__main__":
    main()
