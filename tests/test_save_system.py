"""Verifica indipendente del salvataggio (F5), ripresa dal prototipo (tag prototipo-v0).

Due oracoli esterni al C++:
1. Il CRC32 del gioco (include/save_crc32.h, tabella a nibble) contro zlib, scritto da altri: una
   convenzione sbagliata darebbe checksum coerenti con se stessi, e solo qui verrebbe a galla.
2. Il .sav scritto davvero da mGBA con la ROM GUBBIO_AVVIO=6 (src/titolo.cpp, prova_salvataggio),
   salvato in tests/dati/salvataggio_mgba.sav insieme al suo log: magic leggibile, offset, CRC
   ricalcolato con zlib, ping-pong delle banche, lo stato ritrovato byte per byte.
Le tre negative del piano: una banca corrotta (si carica l'altra), entrambe corrotte (niente da
caricare), un byte alterato che il CRC di zlib non riconosce piu'.

Per rigenerare il .sav: compilare con USERFLAGS=-DGUBBIO_AVVIO=6, avviare la ROM in mGBA fino alla
riga "Salvataggio: ..." del log, copiare rom.sav e le righe del log in tests/dati.

MOB (v4, GameState di 80 byte): il .sav di mGBA in tests/dati e' ancora della v3 (scritto prima di MOB).
Resta qui di proposito: e' la prova che un salvataggio v3 vero si carica aggiornato (i 59 byte comuni
uguali, i campi nuovi ai valori di partenza). Il formato v4 e' provato col gemello Python qui sotto e con
gli static_assert di src/autotest_salvataggio.cpp.
"""
import os
import re
import struct
import unittest
import zlib

from _stile import RADICE

SAV = os.path.join(RADICE, "tests", "dati", "salvataggio_mgba.sav")
LOG = os.path.join(RADICE, "tests", "dati", "salvataggio_mgba.txt")
HEADER = open(os.path.join(RADICE, "include", "save_data.h"), encoding="utf-8").read()
STATO_H = open(os.path.join(RADICE, "include", "game_state.h"), encoding="utf-8").read()

# Il gemello di include/save_data.h: se il C++ cambia e questo no, i test cadono (voluto).
PAYLOAD_BYTE = 256
RECORD = 276
SLOT, BANCHE = 2, 2
VERSIONE = 4
VERSIONE_V3 = 3
MAGIC = b"G115"
OFF_MAGIC, OFF_CONTATORE, OFF_TEMPO, OFF_VERSIONE, OFF_PAYLOAD_BYTE, OFF_PAYLOAD, OFF_CHECKSUM = 0, 4, 8, 12, 14, 16, 272
STATO = 80                  # sizeof(GameState) nella v4
STATO_V3 = 64               # sizeof(GameState) nella v3
COMUNI = 59                 # i byte uguali, allo stesso offset, in v3 e v4 (fino a ferite compreso)
NESSUN_OBIETTIVO = 255
# frames, tempo_frames, esperienza x3, x, y, area, livello x3, oggetti x8, scontri_vinti x4, il resto
FORMATO_STATO_V3 = "<II3HhhB3B8B4B30x"
# v4: ... storia x8, scene_fatte x4, cutscene_viste x2, quest x8, ferite x3, obiettivo, aree_viste x3,
# scorte_comprate, denari, riservato x14
FORMATO_STATO = "<II3HhhB3B8B4B8s4s2s8s3sB3sBH14x"
OFF_OBIETTIVO, OFF_AREE_VISTE, OFF_SCORTE, OFF_DENARI = 59, 60, 63, 64


def crc32_nibble(dati):
    """Il CRC del gioco, riscritto: tabella a nibble dal polinomio riflesso 0xEDB88320."""
    tabella = []
    for i in range(16):
        v = i
        for _ in range(4):
            v = (v >> 1) ^ 0xEDB88320 if v & 1 else v >> 1
        tabella.append(v)
    crc = 0xFFFFFFFF
    for b in dati:
        crc ^= b
        crc = (crc >> 4) ^ tabella[crc & 0x0F]
        crc = (crc >> 4) ^ tabella[crc & 0x0F]
    return crc ^ 0xFFFFFFFF


def versione(record):
    return struct.unpack_from("<H", record, OFF_VERSIONE)[0]


def banca_valida(record):
    """Il gemello di salvataggio::banca_valida: la v4 con 80 byte di payload, o la v3 con 64 (si aggiorna)."""
    misura = (versione(record), struct.unpack_from("<H", record, OFF_PAYLOAD_BYTE)[0])
    return (record[OFF_MAGIC:OFF_MAGIC + 4] == MAGIC and misura in ((VERSIONE, STATO), (VERSIONE_V3, STATO_V3))
            and zlib.crc32(record[:OFF_CHECKSUM]) & 0xFFFFFFFF == struct.unpack_from("<I", record, OFF_CHECKSUM)[0])


def estrai(record):
    """Il gemello di salvataggio::estrai: gli 80 byte di GameState; da una v3, i 59 byte comuni e i campi nuovi ai
    valori di partenza (obiettivo 255, il resto a zero), senza leggere i 5 byte che nella v3 erano riservati."""
    if versione(record) == VERSIONE_V3:
        stato = bytearray(STATO)
        stato[:COMUNI] = record[OFF_PAYLOAD:OFF_PAYLOAD + COMUNI]
        stato[OFF_OBIETTIVO] = NESSUN_OBIETTIVO
        return bytes(stato)
    return bytes(record[OFF_PAYLOAD:OFF_PAYLOAD + STATO])


def componi(stato, contatore, ver=VERSIONE):
    """Il gemello di salvataggio::componi (e di componi_v3 con ver=3): un record di 276 byte."""
    misura = STATO if ver == VERSIONE else STATO_V3
    r = bytearray(RECORD)
    r[0:4] = MAGIC
    struct.pack_into("<IIHH", r, OFF_CONTATORE, contatore, struct.unpack_from("<I", stato, 4)[0] // 60, ver, misura)
    r[OFF_PAYLOAD:OFF_PAYLOAD + misura] = stato[:misura]
    struct.pack_into("<I", r, OFF_CHECKSUM, zlib.crc32(bytes(r[:OFF_CHECKSUM])) & 0xFFFFFFFF)
    return bytes(r)


def banca_da_caricare(a, b):
    """Il gemello di salvataggio::banca_da_caricare: la piu' recente fra le valide, None se nessuna."""
    valide = [(struct.unpack_from("<I", r, OFF_CONTATORE)[0], i) for i, r in enumerate((a, b)) if banca_valida(r)]
    return max(valide)[1] if valide else None


def banche(dati, slot):
    return [dati[(slot * BANCHE + k) * RECORD:(slot * BANCHE + k + 1) * RECORD] for k in range(BANCHE)]


def stato(record):
    """I campi di GameState come li ha scritti la versione del record (v3 o v4), senza aggiornarli."""
    return struct.unpack_from(FORMATO_STATO_V3 if versione(record) == VERSIONE_V3 else FORMATO_STATO, record, OFF_PAYLOAD)


def guasta(record, posizione):
    r = bytearray(record)
    r[posizione] ^= 0x5A
    return bytes(r)


class Crc32(unittest.TestCase):

    def test_vettore_standard(self):
        self.assertEqual(crc32_nibble(b"123456789"), 0xCBF43926)
        self.assertIn("0xCBF43926", open(os.path.join(RADICE, "include", "save_crc32.h"), encoding="utf-8").read())

    def test_uguale_a_zlib(self):
        for campione in (b"", b"G115", b"Gubbio 1151", bytes(range(256)), b"\x00" * RECORD):
            self.assertEqual(crc32_nibble(campione), zlib.crc32(campione) & 0xFFFFFFFF, campione[:16])

    def test_negativa_un_bit_cambia_il_crc(self):
        base = bytes(range(64))
        for i in range(len(base)):
            self.assertNotEqual(crc32_nibble(base), crc32_nibble(guasta(base, i)), i)


class Formato(unittest.TestCase):
    """Il gemello Python e il C++ dicono le stesse misure."""

    def test_misure_del_header(self):
        self.assertIn(f"PAYLOAD_BYTE = {PAYLOAD_BYTE};", HEADER)
        self.assertIn(f"sizeof(SaveData) == {RECORD}", HEADER)
        self.assertIn(f"VERSIONE = {VERSIONE};", HEADER)
        self.assertIn(f"SLOT = {SLOT};", HEADER)
        self.assertIn(f"BANCHE = {BANCHE};", HEADER)
        self.assertIn(f"offsetof(SaveData, checksum) == {OFF_CHECKSUM}", HEADER)
        self.assertIn(f"VERSIONE_V3 = {VERSIONE_V3};", HEADER)
        self.assertIn(f"STATO_V3_BYTE = {STATO_V3};", HEADER)
        self.assertIn(f"BYTE_COMUNI_V3 == {COMUNI}", HEADER)
        self.assertIn(f"sizeof(GameState) == {STATO}", STATO_H)
        self.assertIn(f"offsetof(GameState, obiettivo) == {OFF_OBIETTIVO}", STATO_H)
        self.assertIn(f"offsetof(GameState, aree_viste) == {OFF_AREE_VISTE}", STATO_H)
        self.assertIn(f"offsetof(GameState, scorte_comprate) == {OFF_SCORTE}", STATO_H)
        self.assertIn(f"offsetof(GameState, denari) == {OFF_DENARI}", STATO_H)
        self.assertIn(f"NESSUN_OBIETTIVO = {NESSUN_OBIETTIVO};", STATO_H)
        self.assertEqual(struct.calcsize(FORMATO_STATO), STATO)
        self.assertEqual(struct.calcsize(FORMATO_STATO_V3), STATO_V3)

    def test_negativa_misura_diversa(self):
        self.assertNotIn(f"sizeof(SaveData) == {RECORD + 4}", HEADER)


class FormatoV4(unittest.TestCase):
    """La v4 col gemello Python: i campi nuovi fanno andata e ritorno; v3 e v4 nello stesso slot."""

    @staticmethod
    def uno_stato():
        s = bytearray(range(1, STATO + 1))
        s[OFF_OBIETTIVO] = 4
        struct.pack_into("<H", s, OFF_DENARI, 513)
        s[66:] = bytes(STATO - 66)
        return bytes(s)

    def test_andata_e_ritorno(self):
        s = self.uno_stato()
        r = componi(s, 7)
        self.assertTrue(banca_valida(r))
        self.assertEqual(estrai(r), s)
        campi = stato(r)
        self.assertEqual(campi[-1], 513)
        self.assertEqual(campi[-4], 4)

    def test_v3_si_aggiorna(self):
        s = self.uno_stato()
        r = componi(s, 7, VERSIONE_V3)
        self.assertTrue(banca_valida(r))
        aggiornato = estrai(r)
        self.assertEqual(aggiornato[:COMUNI], s[:COMUNI])
        self.assertEqual(aggiornato[OFF_OBIETTIVO], NESSUN_OBIETTIVO)
        self.assertEqual(aggiornato[OFF_AREE_VISTE:], bytes(STATO - OFF_AREE_VISTE))

    def test_negativa_residuo_dei_riservati_v3(self):
        # nei byte 59-63 della v3 c'e' 60..64 (uno_stato): copiati cosi' com'erano darebbero l'obiettivo 4
        r = componi(self.uno_stato(), 7, VERSIONE_V3)
        self.assertEqual(r[OFF_PAYLOAD + OFF_OBIETTIVO], 4)
        self.assertNotEqual(estrai(r)[OFF_OBIETTIVO], 4)

    def test_negativa_misura_sbagliata(self):
        for ver, misura in ((VERSIONE_V3, STATO), (VERSIONE, STATO_V3), (2, STATO_V3), (5, STATO)):
            r = bytearray(componi(self.uno_stato(), 1))
            struct.pack_into("<HH", r, OFF_VERSIONE, ver, misura)
            struct.pack_into("<I", r, OFF_CHECKSUM, zlib.crc32(bytes(r[:OFF_CHECKSUM])) & 0xFFFFFFFF)
            self.assertFalse(banca_valida(bytes(r)), (ver, misura))

    def test_ping_pong_fra_versioni(self):
        s = self.uno_stato()
        self.assertEqual(banca_da_caricare(componi(s, 5, VERSIONE_V3), componi(s, 6)), 1)
        self.assertEqual(banca_da_caricare(componi(s, 6, VERSIONE_V3), componi(s, 5)), 0)


class VecchiSalvataggi(unittest.TestCase):
    """Un .sav della versione 2 (prima delle bandiere delle quest, tests/dati/salvataggio_v2.sav) si
    rifiuta pulito: le banche portano il magic ma un'altra versione, nessuna si carica."""

    def setUp(self):
        with open(os.path.join(RADICE, "tests", "dati", "salvataggio_v2.sav"), "rb") as f:
            self.dati = f.read()

    def test_versione_2_rifiutata(self):
        for slot in range(SLOT):
            a, b = banche(self.dati, slot)
            if a[:4] == MAGIC or b[:4] == MAGIC:
                self.assertIn(2, {struct.unpack_from("<H", r, OFF_VERSIONE)[0] for r in (a, b) if r[:4] == MAGIC})
                self.assertIsNone(banca_da_caricare(a, b), slot)

    def test_negativa_la_stessa_banca_con_la_versione_nuova_si_carica(self):
        a, b = banche(self.dati, 0)
        r = bytearray(a)
        # la v2 aveva gia' 64 byte di payload: rietichettata v3 si carica, quindi a rifiutarla e' solo la versione
        struct.pack_into("<H", r, OFF_VERSIONE, VERSIONE_V3)
        struct.pack_into("<I", r, OFF_CHECKSUM, zlib.crc32(bytes(r[:OFF_CHECKSUM])) & 0xFFFFFFFF)
        self.assertEqual(banca_da_caricare(bytes(r), b), 0)


class SavDiMgba(unittest.TestCase):
    """I byte che mGBA ha scritto davvero, con la ROM GUBBIO_AVVIO=6 di prima di MOB: un .sav della v3, che
    oggi si carica aggiornato alla v4."""

    @classmethod
    def setUpClass(cls):
        with open(SAV, "rb") as f:
            cls.dati = f.read()
        with open(LOG, encoding="utf-8") as f:
            cls.log = f.read()

    def test_la_prova_sul_gba_e_riuscita(self):
        self.assertIn("Salvataggio: 8 prove riuscite, 0 fallite", self.log)
        self.assertEqual(len(re.findall(r"^SALVATAGGIO .* OK$", self.log, re.M)), 8)

    def test_file_intero_e_magic_leggibile(self):
        self.assertEqual(len(self.dati), 32 * 1024)
        self.assertEqual(self.dati[0:4], MAGIC)

    def test_ogni_banca_regge_il_crc_di_zlib(self):
        viste = 0
        for slot in range(SLOT):
            for record in banche(self.dati, slot):
                if record[:4] == MAGIC:
                    viste += 1
                    self.assertTrue(banca_valida(record), slot)
                    self.assertEqual(self.dati.count(b"\x00", 0, 0), 0)
                    misura = STATO_V3 if versione(record) == VERSIONE_V3 else STATO
                    self.assertEqual(record[OFF_PAYLOAD + misura:OFF_CHECKSUM], bytes(PAYLOAD_BYTE - misura),
                                     "oltre GameState il payload e' azzerato")
        self.assertEqual(viste, 3, "slot 0 con due banche, slot 1 con una")

    def test_gli_stati_ritrovati(self):
        """Lo slot 0 carica lo stato 3 (la banca piu' recente), lo slot 1 lo stato 4: i numeri di
        stato_di_prova() in src/titolo.cpp."""
        def atteso(n):
            return ((1000 * n, 3600 * n + 7, 50 * n, 50 * n + 1, 50 * n + 2, 100 + n, 200 + n, n, n, n, n, n)
                    + (0,) * 7 + (n, 0, 0, 0))
        attesi = {0: atteso(3), 1: atteso(4)}
        for slot, atteso in attesi.items():
            a, b = banche(self.dati, slot)
            k = banca_da_caricare(a, b)
            self.assertIsNotNone(k)
            self.assertEqual(stato((a, b)[k]), atteso)
            self.assertEqual(struct.unpack_from("<I", (a, b)[k], OFF_TEMPO)[0], atteso[1] // 60)

    def test_e_della_v3_e_si_carica_aggiornato(self):
        for slot in range(SLOT):
            a, b = banche(self.dati, slot)
            k = banca_da_caricare(a, b)
            r = (a, b)[k]
            self.assertEqual(versione(r), VERSIONE_V3)
            aggiornato = estrai(r)
            self.assertEqual(len(aggiornato), STATO)
            self.assertEqual(aggiornato[:COMUNI], r[OFF_PAYLOAD:OFF_PAYLOAD + COMUNI])
            self.assertEqual(struct.unpack_from(FORMATO_STATO, aggiornato)[-4:], (NESSUN_OBIETTIVO, bytes(3), 0, 0))

    def test_negativa_banca_corrotta(self):
        """La banca piu' recente dello slot 0 alterata: si carica l'altra (lo stato 1, rimasto da prima)."""
        a, b = banche(self.dati, 0)
        recente = banca_da_caricare(a, b)
        guaste = [a, b]
        guaste[recente] = guasta(guaste[recente], OFF_PAYLOAD + 2)
        self.assertFalse(banca_valida(guaste[recente]))
        self.assertEqual(banca_da_caricare(*guaste), 1 - recente)

    def test_negativa_entrambe_corrotte(self):
        a, b = banche(self.dati, 0)
        self.assertIsNone(banca_da_caricare(guasta(a, OFF_PAYLOAD), guasta(b, OFF_CONTATORE)))

    def test_negativa_crc_di_zlib_su_un_byte_alterato(self):
        a = banche(self.dati, 1)[0]
        self.assertNotEqual(zlib.crc32(guasta(a, 40)[:OFF_CHECKSUM]) & 0xFFFFFFFF,
                            struct.unpack_from("<I", a, OFF_CHECKSUM)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
