#ifndef DIALOGUE_VIEW_H
#define DIALOGUE_VIEW_H

#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_vector.h"

#include "dialogue_box.h"

namespace gubbio {

// Disegno della finestra di dialogo: cornice su BG0 e testo con sprite.
//
// PERCHE' IL TESTO E' FATTO DI SPRITE E LA CORNICE NO. La Sez. 25 GDD dice "il sistema sfrutta
// BG0 per visualizzare una text box": alla lettera non e' realizzabile, perche' in Butano il
// testo e' fatto di SPRITE (OAM) e non di tile di background. La lettura adottata e' quella che
// rispetta l'intenzione: la CORNICE sta su BG0 — costa un blocco di mappa e 12 tile ripetuti —
// e il testo sta sugli sprite, dove il budget e' contato qui sotto.
//
// IL TETTO VERO NON SONO I TILE, SONO LE ALLOCAZIONI. `BN_CFG_SPRITE_TILES_MAX_ITEMS` e' 128 e
// ogni sprite di testo e' un'allocazione a se': tre righe piene valgono ~15-21 sprite, cioe'
// altrettante allocazioni, ma solo 60-84 tile su 1024. Si esaurisce prima il conteggio degli
// item che la VRAM, ed e' per questo che la strategia di rigenerazione conta.
//
// COME SI EVITA IL CHURN DELL'ALLOCATORE. Rigenerare tutto il testo a ogni carattere sarebbe
// ~21 create/release ogni 2 frame, cioe' oltre 300 operazioni al secondo sull'allocatore
// best-fit. Qui gli sprite gia' composti non si toccano piu' e si rigenera **solo la coda in
// crescita**, un solo sprite. La coda si "chiude" — diventa stabile — quando la sua larghezza
// supererebbe i 32 px di uno sprite di testo.
//
// **Il confine si misura in PIXEL, non contando i caratteri.** Il piano prescriveva "4 caratteri
// a 32 px": e' sbagliato, perche' il font del progetto e' a larghezza variabile (le minuscole
// stanno in 5 px, le maiuscole in 7-8). Contando 4 caratteri i pezzi verrebbero posizionati a
// x sbagliate — 4 minuscole sono 20 px, non 32 — e il testo scivolerebbe verso destra riga dopo
// riga, senza alcun assert a segnalarlo.
class DialogueView
{
public:
    DialogueView();

    // Allinea il disegno allo stato del motore. Da chiamare a ogni frame: internamente tocca
    // l'allocatore solo quando il testo cresce oltre il confine di uno sprite.
    void update(const DialogueManager& dialogue);

private:
    // Tre righe da 28 caratteri stanno in 21 sprite nel caso peggiore (tutto maiuscolo); in
    // prosa italiana sono ~15. Il vettore e' dimensionato sul caso peggiore piu' un margine,
    // perche' `sprite_text_generator::generate` fa scattare un assert su vettore pieno.
    static constexpr int MAX_TEXT_SPRITES = 24;

    bn::regular_bg_ptr _frame;
    bn::sprite_text_generator _generator;

    // Sprite gia' composti: righe concluse e pezzi chiusi della riga in corso. Non si toccano.
    bn::vector<bn::sprite_ptr, MAX_TEXT_SPRITES> _stable;

    // La coda che cresce carattere per carattere: un solo sprite, rigenerato ogni volta.
    bn::vector<bn::sprite_ptr, 2> _tail;

    int _row = -1;             // riga della macchina da scrivere attualmente disegnata
    int _stable_bytes = 0;     // byte della riga in corso gia' finiti negli sprite stabili
    int _tail_bytes = 0;       // byte attualmente nella coda
    int _tail_x = 0;           // x a cui comincia la coda
    bool _visible = false;

    void _reset();
    void _close_tail(bn::string_view riga);
    [[nodiscard]] int _row_y(int row) const;
};

} // namespace gubbio

#endif // DIALOGUE_VIEW_H
