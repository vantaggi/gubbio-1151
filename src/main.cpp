#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"

#include "esplorazione.h"
#include "game_state.h"
#include "scena_battaglia.h"
#include "titolo.h"
#include "schermate.h"
#include "vista_testo.h"

// All'avvio: con L premuto la schermata dei testi (F1), con SELECT la camminata automatica del
// mondo (F2), con R le istantanee delle aree (F2), altrimenti l'esplorazione da Piazza Grande.
// Croce per muoversi, B per correre. Per le prove senza tastiera, GUBBIO_AVVIO in compilazione
// sceglie il modo come se il tasto fosse premuto: 1 camminata, 2 istantanee, 3 prova della battaglia,
// 4 i tre scontri giocabili a mano, 5 le istantanee della battaglia, 6 la prova del salvataggio,
// 7 le istantanee del titolo e della pausa
// (make USERFLAGS=-DGUBBIO_AVVIO=1). Senza modo di prova: il titolo, poi la partita; Start apre la pausa.
#ifndef GUBBIO_AVVIO
    #define GUBBIO_AVVIO 0
#endif

int main()
{
    bn::core::init();
    bn::core::update();

    gubbio::g_game_state.frames = 0;
    bn::sprite_palette_ptr palette = gubbio::crea_palette_testo();

    if(bn::keypad::l_held())
    {
        gubbio::schermata_testi(palette);
    }

    bn::bg_palettes::set_transparent_color(bn::color(0, 0, 0));

    if(GUBBIO_AVVIO == 4)
    {
        gubbio::menu_battaglie(palette);
    }

    if(GUBBIO_AVVIO == 5)
    {
        gubbio::istantanee_battaglie(palette);
    }

    if(GUBBIO_AVVIO == 6)
    {
        gubbio::prova_salvataggio();

        while(true)
        {
            bn::core::update();
        }
    }

    // il titolo solo nel gioco vero (e per le sue istantanee): i modi di prova partono subito
    int slot = GUBBIO_AVVIO == 0 && ! bn::keypad::select_held() && ! bn::keypad::r_held() ? gubbio::titolo(palette) :
               (GUBBIO_AVVIO == 7 ? gubbio::titolo(palette, true) : -1);

    gubbio::Esplorazione esplorazione(palette);

    if(GUBBIO_AVVIO == 1 || bn::keypad::select_held())
    {
        gubbio::camminata_automatica(esplorazione, palette);
    }

    if(GUBBIO_AVVIO == 3)
    {
        gubbio::prova_battaglia();
    }

    if(GUBBIO_AVVIO == 2 || bn::keypad::r_held())
    {
        gubbio::istantanee(esplorazione);
    }

    if(slot >= 0)
    {
        esplorazione.riprendi(gubbio::mondo::AreaId(gubbio::g_game_state.area), gubbio::g_game_state.x,
                              gubbio::g_game_state.y);
    }
    else
    {
        gubbio::g_game_state.tempo_frames = 0;
        esplorazione.entra(gubbio::mondo::AreaId::PIAZZA_GRANDE, 0);
    }

    if(GUBBIO_AVVIO == 7)
    {
        for(int f = 0; f < 60; ++f)
        {
            esplorazione.aggiorna();
            bn::core::update();
        }

        gubbio::pausa(esplorazione, palette, true);
        BN_LOG("Istantanee finite");
    }

    while(true)
    {
        ++gubbio::g_game_state.frames;
        ++gubbio::g_game_state.tempo_frames;

        if(bn::keypad::start_pressed() && ! esplorazione.in_dissolvenza())
        {
            gubbio::pausa(esplorazione, palette);
        }

        int dx = bn::keypad::left_held() ? -1 : (bn::keypad::right_held() ? 1 : 0);
        int dy = bn::keypad::up_held() ? -1 : (bn::keypad::down_held() ? 1 : 0);
        esplorazione.muovi(dx, dy, bn::keypad::b_held() ? 2 : 1);
        esplorazione.aggiorna();

        bn::core::update();
    }
}
