#ifndef GUBBIO_TITOLO_H
#define GUBBIO_TITOLO_H

#include "bn_sprite_palette_ptr.h"

namespace gubbio
{

class Esplorazione;

// Il titolo: il logo, "Nuova partita" e i due slot. Ritorna -1 per una partita nuova, oppure lo
// slot (0 o 1) da cui continuare, gia' caricato in g_game_state.
// Con istantanea=true non aspetta tasti: si mostra, scrive "Istantanea titolo" e ritorna -1.
[[nodiscard]] int titolo(const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// La pausa (Start durante l'esplorazione): riprendere o salvare in uno dei due slot. Lo sfondo si
// scurisce, il testo resta chiaro. Ritorna quando il giocatore riprende.
// Con istantanea=true non aspetta tasti: si mostra, scrive "Istantanea pausa" e ritorna.
void pausa(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// «Dove eravamo» (MAI): dopo «Continua», una volta, area, fase della cronaca, obiettivo, incarichi aperti e
// tempo di gioco sullo sfondo scurito; A (o B, o Start) per riprendere. Con istantanea=true non aspetta tasti.
void dove_eravamo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// Lo stato di partita dalla posizione dell'esploratore, prima di salvare.
void annota_posizione(const Esplorazione& esplorazione);

// GUBBIO_AVVIO=6: salva, ricarica e confronta GameState byte per byte, corrompe una banca e poi
// entrambe, controlla che ogni volta si carichi quel che si deve; una riga di log per prova e il
// riepilogo ("Salvataggio: ... prove riuscite"). Alla fine lascia i due slot validi e noti, per
// tests/test_save_system.py.
void prova_salvataggio();

}

#endif
