"""Ogni carattere di ogni testo mostrato a schermo deve esistere nel font.

PERCHE' ESISTE. Butano fa scattare `BN_ERROR("Invalid character: ...")` in
`sprite_text_generator::_paint` quando incontra un codepoint che non sta ne' fra gli ASCII
stampabili ne' nella lista UTF-8 dichiarata dal font. Non e' un glifo mancante disegnato come
quadratino: e' il **gioco che si ferma davanti al giocatore**, con una schermata rossa.

E' successo davvero: il committente, giocando, ha visto quell'errore ogni volta che parlava con
un personaggio, mentre l'autotest riportava zero assert. La ragione e' che l'autotest RECITA
alcune battute, non tutte: basta che il carattere fuori lista stia in una riga che quella
particolare corsa non ha renderizzato, e l'oracolo tace. Un carattere invisibile a occhio — un
apostrofo tipografico al posto di quello dritto, uno spazio unificatore, una lineetta lunga —
non si distingue rileggendo il file.

Questo test non campiona: legge TUTTE le stringhe di TUTTE le tabelle di testo e verifica ogni
singolo codepoint. E' esaustivo, gira in millisecondi e non ha bisogno dell'emulatore.

Copre le battute dei dialoghi, i nomi delle aree, i nomi dei personaggi e delle abilita': tutto
cio' che finisce dentro un `sprite_text_generator::generate`.
"""

import os
import re
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# I file che contengono stringhe destinate allo schermo.
SORGENTI_TESTO = [
    ("include/dialogue_data.h", "le battute dei dialoghi"),
    ("include/map_id.h", "i nomi delle aree"),
    ("include/npc_registry.h", "i nomi degli NPC"),
    ("include/hero_data.h", "i nomi dei Ceri"),
    ("include/enemy_data.h", "i nomi dei nemici"),
    ("include/skill_data.h", "i nomi delle abilita'"),
]


def caratteri_del_font():
    """Gli ASCII stampabili piu' la lista UTF-8 dichiarata in font_gubbio.h.

    La lista si LEGGE dal font invece di essere ricopiata qui: due elenchi che divergono
    darebbero un test che passa mentre il gioco si ferma, che e' il difetto peggiore possibile
    per un test.
    """
    testo = open(os.path.join(RADICE, "include", "font_gubbio.h"), encoding="utf-8").read()
    blocco = re.search(r"FONT_UTF8_CHARACTERS\[\]\s*=\s*\{(.*?)\}", testo, re.S).group(1)
    extra = set(re.findall(r'"([^"]+)"', blocco))

    ammessi = {chr(c) for c in range(32, 127)}
    ammessi |= extra
    return ammessi, extra


def stringhe_di(percorso):
    """Le stringhe letterali di un header, saltando include, commenti e direttive."""
    fuori = []

    for riga in open(os.path.join(RADICE, percorso), encoding="utf-8"):
        spoglia = riga.strip()

        if spoglia.startswith("#") or spoglia.startswith("//"):
            continue

        # Il commento di coda non finisce a schermo: le accentate ci stanno di casa.
        senza_commento = riga.split("//")[0]

        for s in re.findall(r'"((?:[^"\\]|\\.)*)"', senza_commento):
            if s:
                fuori.append((s, riga.strip()))

    return fuori


class CaratteriStampabiliTest(unittest.TestCase):

    def test_ogni_carattere_a_schermo_esiste_nel_font(self):
        ammessi, extra = caratteri_del_font()
        colpevoli = []

        for percorso, cosa in SORGENTI_TESTO:
            if not os.path.exists(os.path.join(RADICE, percorso)):
                continue

            for testo, riga in stringhe_di(percorso):
                for ch in testo:
                    if ch not in ammessi:
                        colpevoli.append(
                            "%s (%s): U+%04X %r nella riga:\n      %s"
                            % (percorso, cosa, ord(ch), ch, riga[:90]))

        self.assertFalse(
            colpevoli,
            "Caratteri che il font non conosce: Butano ferma il gioco con "
            "\"Invalid character\" nel momento in cui prova a disegnarli.\n"
            "  Rimediare sostituendoli con l'equivalente ASCII, oppure aggiungendoli a "
            "FONT_UTF8_CHARACTERS in include/font_gubbio.h e disegnandone il glifo.\n\n    "
            + "\n    ".join(sorted(set(colpevoli))))

    def test_la_lista_utf8_del_font_non_e_vuota(self):
        """Guardia contro il caso in cui la regex smetta di trovare la lista.

        Senza, il test qui sopra continuerebbe a passare confrontando i testi con i soli ASCII
        — o peggio, con un insieme vuoto — e non misurerebbe piu' nulla.
        """
        _, extra = caratteri_del_font()
        self.assertGreaterEqual(len(extra), 6,
                                "FONT_UTF8_CHARACTERS sembra vuota o illeggibile: il test dei "
                                "caratteri non starebbe piu' misurando niente")


if __name__ == "__main__":
    unittest.main(verbosity=2)
