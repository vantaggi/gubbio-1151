#ifndef GUBBIO_TITOLO_H
#define GUBBIO_TITOLO_H

#include "bn_sprite_palette_ptr.h"

namespace gubbio
{

class Esplorazione;
struct GameState;

// Il titolo: il logo, "Nuova partita" e i due slot. Ritorna -1 per una partita nuova, oppure lo
// slot (0 o 1) da cui continuare, gia' caricato in g_game_state.
// Con istantanea=true non aspetta tasti: si mostra, scrive "Istantanea titolo" e ritorna -1.
[[nodiscard]] int titolo(const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// La pausa (Start durante l'esplorazione, MPA, src/menu_pausa.cpp): i compagni, le sei voci e l'obiettivo; A apre
// la pagina della voce. Ritorna quando il giocatore riprende.
// Con istantanea=true non aspetta tasti: mostra la pausa e ogni pagina, con "Istantanea pausa..." nel log.
void pausa(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// «Dove eravamo» (MAI): dopo «Continua», una volta, area, fase della cronaca, obiettivo, incarichi aperti e
// tempo di gioco sullo sfondo scurito; A (o B, o Start) per riprendere. Con istantanea=true non aspetta tasti.
void dove_eravamo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea = false);

// La partita d'esempio dei mockup (menu/mockup_menu.py): a meta' dell'Atto I, la citta' in digiuno, i tre
// compagni ai livelli 4 4 3, i tre incarichi presi e due blocchi di ferro su tre. Per le istantanee dei menu.
void partita_d_esempio(GameState& p);

// Lo stato di partita dalla posizione dell'esploratore, prima di salvare.
void annota_posizione(const Esplorazione& esplorazione);

// GUBBIO_AVVIO=6: salva, ricarica e confronta GameState byte per byte, corrompe una banca e poi
// entrambe, controlla che ogni volta si carichi quel che si deve; una riga di log per prova e il
// riepilogo ("Salvataggio: ... prove riuscite"). Alla fine lascia i due slot validi e noti, per
// tests/test_save_system.py.
void prova_salvataggio();

// GUBBIO_AVVIO=15: scrive due slot di prova per le foto degli aiuti (tools/banco.sh): il primo nel digiuno in
// Piazza Grande, il secondo all'ingresso del Condotto prima del duello con Corrado. Poi si va al titolo.
void prepara_slot_di_prova();

}

#endif
