#!/usr/bin/env python3
"""
Verifica INDIPENDENTE del formato di salvataggio (Passo 8 del piano).

Due oracoli distinti, che e' il punto di questo file:

1. **Il CRC32 del C++ contro quello di `zlib`.** `include/save_crc32.h` calcola il CRC con una
   tabella a nibble derivata dal polinomio; se il verso dei bit o le convenzioni di
   init/complemento fossero sbagliati, il gioco produrrebbe checksum coerenti *con se stesso* e
   nessuna verifica interna se ne accorgerebbe. `zlib.crc32` e' un'implementazione scritta da
   altri: e' li' che una convenzione sbagliata viene a galla.

2. **Il `.sav` prodotto dall'hardware emulato.** Non si controlla una struttura teorica ma i byte
   che mGBA ha davvero scritto su FRAM: magic leggibile in hex dump, offset dei campi, checksum
   ricalcolato, monotonia del contatore di scrittura, alternanza delle banche.

    python tests/test_save_system.py

Il secondo gruppo di test richiede `gubbio1151.sav` non vuoto, che si ottiene eseguendo la ROM
di autotest (lo script preme SELECT durante l'esplorazione):

    bash tools/build_rom.sh "USERFLAGS=-DGUBBIO_BATTLE_AUTOTEST"
    C:/Users/cioti/mGBA-0.10.5/mgba-sdl.exe gubbio1151.gba

Senza quel file i test dichiarano `skip` invece di passare in silenzio: un test verde su un file
assente sarebbe esattamente il tipo di oracolo che non puo' fallire.
"""

import os
import struct
import unittest
import zlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SAV = os.path.join(ROOT, "gubbio1151.sav")

# Mirror di include/save_data.h. Se il C++ cambia e questo file no, i test cadono: e' voluto.
PAYLOAD_BYTES = 256
RECORD_SIZE = 276
SLOT_COUNT = 2
BANK_COUNT = 2
SAVE_VERSION = 1
MAGIC_BYTES = b"G115"

OFF_MAGIC, OFF_COUNTER, OFF_PLAYTIME = 0, 4, 8
OFF_VERSION, OFF_PAYLOAD_SIZE, OFF_PAYLOAD = 12, 14, 16
OFF_CHECKSUM = 272

GAME_STATE_SIZE = 140      # sizeof(GameState), verificato dal compilatore in game_state.h


def crc32_nibble(data):
    """Port fedele di gubbio::crc32 (tabella a nibble, polinomio riflesso 0xEDB88320)."""
    table = []
    for i in range(16):
        value = i
        for _ in range(4):
            value = (value >> 1) ^ 0xEDB88320 if value & 1 else value >> 1
        table.append(value)

    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        crc = (crc >> 4) ^ table[crc & 0x0F]
        crc = (crc >> 4) ^ table[crc & 0x0F]
    return crc ^ 0xFFFFFFFF


class Crc32Test(unittest.TestCase):
    def test_vettore_di_prova_standard(self):
        """Lo stesso vettore su cui il C++ ha una static_assert."""
        self.assertEqual(crc32_nibble(b"123456789"), 0xCBF43926)

    def test_concorda_con_zlib(self):
        """L'oracolo esterno: un'implementazione scritta da altri."""
        for campione in (b"", b"G115", b"Gubbio 1151", bytes(range(256)), b"\x00" * 276):
            self.assertEqual(crc32_nibble(campione), zlib.crc32(campione) & 0xFFFFFFFF,
                             f"divergenza da zlib su {campione[:16]!r}")

    def test_e_sensibile_a_ogni_byte(self):
        """Un CRC che ignorasse parte dei dati passerebbe i test qui sopra."""
        base = bytes(range(64))
        for i in range(len(base)):
            alterato = bytearray(base)
            alterato[i] ^= 0x01
            self.assertNotEqual(crc32_nibble(base), crc32_nibble(bytes(alterato)),
                                f"il byte {i} non influenza il checksum")


def leggi_banche():
    with open(SAV, "rb") as f:
        dati = f.read()

    banche = []
    for slot in range(SLOT_COUNT):
        for bank in range(BANK_COUNT):
            off = (slot * BANK_COUNT + bank) * RECORD_SIZE
            record = dati[off:off + RECORD_SIZE]
            if len(record) == RECORD_SIZE and record[OFF_MAGIC:OFF_MAGIC + 4] == MAGIC_BYTES:
                banche.append((slot, bank, record))
    return dati, banche


@unittest.skipUnless(os.path.exists(SAV) and os.path.getsize(SAV) > 0,
                     "gubbio1151.sav assente o vuoto: eseguire prima la ROM di autotest")
class SavRealeTest(unittest.TestCase):
    def setUp(self):
        self.dati, self.banche = leggi_banche()
        self.assertTrue(self.banche, "nessuna banca con magic G115 nel .sav")

    def test_dimensione_del_file(self):
        """La FRAM del GBA e' 32 KB: mGBA scrive il file intero."""
        self.assertEqual(len(self.dati), 32 * 1024)

    def test_magic_leggibile_in_hex_dump(self):
        """Il magic e' un array di caratteri proprio per essere riconoscibile a occhio."""
        self.assertEqual(self.dati[0:4], MAGIC_BYTES,
                         f"primi 4 byte {self.dati[0:4]!r}, attesi {MAGIC_BYTES!r}")

    def test_checksum_di_ogni_banca(self):
        """Il controllo centrale: i byte scritti dall'hardware reggono il ricalcolo esterno."""
        for slot, bank, record in self.banche:
            atteso = struct.unpack_from("<I", record, OFF_CHECKSUM)[0]
            calcolato = zlib.crc32(record[:OFF_CHECKSUM]) & 0xFFFFFFFF
            self.assertEqual(calcolato, atteso,
                             f"slot {slot} banca {bank}: checksum {atteso:#x}, ricalcolato {calcolato:#x}")

    def test_involucro_coerente(self):
        for slot, bank, record in self.banche:
            versione = struct.unpack_from("<H", record, OFF_VERSION)[0]
            payload_size = struct.unpack_from("<H", record, OFF_PAYLOAD_SIZE)[0]
            counter = struct.unpack_from("<I", record, OFF_COUNTER)[0]

            self.assertEqual(versione, SAVE_VERSION, f"slot {slot} banca {bank}: versione")
            self.assertEqual(payload_size, GAME_STATE_SIZE, f"slot {slot} banca {bank}: payload_size")
            self.assertGreater(counter, 0, "il contatore di scrittura parte da 1")

    def test_coda_del_payload_azzerata(self):
        """Oltre GameState il payload e' riservato e deve essere zero: byte residui di un
        salvataggio precedente entrerebbero nel CRC rendendo il record dipendente dal passato."""
        for slot, bank, record in self.banche:
            coda = record[OFF_PAYLOAD + GAME_STATE_SIZE:OFF_CHECKSUM]
            self.assertEqual(set(coda), {0}, f"slot {slot} banca {bank}: coda del payload sporca")

    def test_ping_pong_fra_le_banche(self):
        """Due scritture consecutive sullo stesso slot non devono finire nella stessa banca:
        e' l'unica cosa che protegge la copia buona da un'interruzione a meta' scrittura."""
        per_slot = {}
        for slot, bank, record in self.banche:
            counter = struct.unpack_from("<I", record, OFF_COUNTER)[0]
            per_slot.setdefault(slot, []).append((counter, bank))

        for slot, voci in per_slot.items():
            if len(voci) < 2:
                continue
            voci.sort()
            for (c1, b1), (c2, b2) in zip(voci, voci[1:]):
                self.assertNotEqual(c1, c2, f"slot {slot}: due banche con lo stesso contatore")
                self.assertNotEqual(b1, b2, f"slot {slot}: scritture consecutive sulla stessa banca")


if __name__ == "__main__":
    unittest.main(verbosity=2)
