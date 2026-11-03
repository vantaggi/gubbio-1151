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
VERSIONE = 3
MAGIC = b"G115"
OFF_MAGIC, OFF_CONTATORE, OFF_TEMPO, OFF_VERSIONE, OFF_PAYLOAD_BYTE, OFF_PAYLOAD, OFF_CHECKSUM = 0, 4, 8, 12, 14, 16, 272
STATO = 64                  # sizeof(GameState)
# frames, tempo_frames, esperienza x3, x, y, area, livello x3, oggetti x8, scontri_vinti x4, riservato
FORMATO_STATO = "<II3HhhB3B8B4B30x"


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


def banca_valida(record):
    return (record[OFF_MAGIC:OFF_MAGIC + 4] == MAGIC and struct.unpack_from("<H", record, OFF_VERSIONE)[0] == VERSIONE
            and struct.unpack_from("<H", record, OFF_PAYLOAD_BYTE)[0] == STATO
            and zlib.crc32(record[:OFF_CHECKSUM]) & 0xFFFFFFFF == struct.unpack_from("<I", record, OFF_CHECKSUM)[0])


def banca_da_caricare(a, b):
    """Il gemello di salvataggio::banca_da_caricare: la piu' recente fra le valide, None se nessuna."""
    valide = [(struct.unpack_from("<I", r, OFF_CONTATORE)[0], i) for i, r in enumerate((a, b)) if banca_valida(r)]
    return max(valide)[1] if valide else None


def banche(dati, slot):
    return [dati[(slot * BANCHE + k) * RECORD:(slot * BANCHE + k + 1) * RECORD] for k in range(BANCHE)]


def stato(record):
    return struct.unpack_from(FORMATO_STATO, record, OFF_PAYLOAD)


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
        self.assertIn(f"sizeof(GameState) == {STATO}", STATO_H)
        self.assertEqual(struct.calcsize(FORMATO_STATO), STATO)

    def test_negativa_misura_diversa(self):
        self.assertNotIn(f"sizeof(SaveData) == {RECORD + 4}", HEADER)


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
        struct.pack_into("<H", r, OFF_VERSIONE, VERSIONE)
        struct.pack_into("<I", r, OFF_CHECKSUM, zlib.crc32(bytes(r[:OFF_CHECKSUM])) & 0xFFFFFFFF)
        self.assertEqual(banca_da_caricare(bytes(r), b), 0)


class SavDiMgba(unittest.TestCase):
    """I byte che mGBA ha scritto davvero, con la ROM GUBBIO_AVVIO=6."""

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
                    self.assertEqual(record[OFF_PAYLOAD + STATO:OFF_CHECKSUM], bytes(PAYLOAD_BYTE - STATO),
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
