#ifndef FONT_GUBBIO_H
#define FONT_GUBBIO_H

// GENERATO DA tools/make_font.py — non modificare a mano.
//
// Font 8x8 del progetto: i 94 glifi ASCII di `common_variable_8x8_font` di Butano piu' le
// 12 lettere accentate italiane, che quel font non ha (i suoi 16 caratteri non ASCII sono
// tutti spagnoli). Un carattere non mappato non e' un errore di compilazione: e' un `BN_ERROR`
// a runtime, davanti al giocatore.
//
// Le minuscole sono derivate senza ridisegno — lo spazio sopra c'era gia'; le maiuscole sono
// compresse di una riga eliminando una riga duplicata. Vedi il commento in testa al generatore.

#include "bn_sprite_font.h"
#include "bn_utf8_characters_map.h"
#include "bn_sprite_items_font_gubbio.h"

namespace gubbio {

inline constexpr bn::utf8_character FONT_UTF8_CHARACTERS[] = {
    "à", "è", "é", "ì", "ò", "ù", "À", "È", "É", "Ì", "Ò", "Ù"
};

// La tabella parte dal carattere 32, LO SPAZIO, che ha una larghezza ma non ha una cella
// nell'immagine (le celle partono da '!'). Sbagliare questo scarto di uno fa scivolare ogni
// lettera di una posizione: e' il difetto della Sessione 05, per cui "Sant'Ubaldo" usciva
// "Tbou...".
inline constexpr int8_t FONT_CHARACTER_WIDTHS[] = {
    6,  // spazio
    3,  // !
    6,  // "
    7,  // #
    8,  // $
    8,  // %
    8,  // &
    3,  // '
    4,  // (
    4,  // )
    6,  // *
    7,  // +
    3,  // ,
    7,  // -
    3,  // .
    8,  // /
    7,  // 0
    7,  // 1
    7,  // 2
    7,  // 3
    7,  // 4
    7,  // 5
    7,  // 6
    7,  // 7
    7,  // 8
    7,  // 9
    3,  // :
    3,  // ;
    7,  // <
    7,  // =
    7,  // >
    7,  // ?
    8,  // @
    7,  // A
    7,  // B
    7,  // C
    7,  // D
    7,  // E
    7,  // F
    7,  // G
    7,  // H
    7,  // I
    7,  // J
    7,  // K
    7,  // L
    8,  // M
    7,  // N
    7,  // O
    7,  // P
    8,  // Q
    7,  // R
    7,  // S
    7,  // T
    7,  // U
    8,  // V
    8,  // W
    7,  // X
    7,  // Y
    7,  // Z
    4,  // [
    8,  // backslash
    4,  // ]
    7,  // ^
    7,  // _
    3,  // `
    5,  // a
    5,  // b
    5,  // c
    5,  // d
    5,  // e
    5,  // f
    5,  // g
    5,  // h
    5,  // i
    5,  // j
    5,  // k
    5,  // l
    6,  // m
    5,  // n
    5,  // o
    5,  // p
    5,  // q
    5,  // r
    5,  // s
    5,  // t
    6,  // u
    5,  // v
    6,  // w
    5,  // x
    5,  // y
    5,  // z
    5,  // {
    3,  // |
    5,  // }
    8,  // ~
    5,  // à
    5,  // è
    5,  // é
    5,  // ì
    5,  // ò
    6,  // ù
    7,  // À
    7,  // È
    7,  // É
    7,  // Ì
    7,  // Ò
    7,  // Ù
};

inline constexpr bn::span<const bn::utf8_character> FONT_UTF8_SPAN(FONT_UTF8_CHARACTERS);

inline constexpr auto FONT_UTF8_MAP = bn::utf8_characters_map<FONT_UTF8_SPAN>();

inline constexpr bn::sprite_font FONT_GUBBIO(
        bn::sprite_items::font_gubbio, FONT_UTF8_MAP.reference(), FONT_CHARACTER_WIDTHS);

} // namespace gubbio

#endif // FONT_GUBBIO_H
