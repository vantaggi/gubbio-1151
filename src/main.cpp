#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"

#include "audio.h"
#include "esplorazione.h"
#include "game_state.h"
#include "opzioni.h"
#include "scena_battaglia.h"
#include "scontri_mappa.h"
#include "regia_scena.h"
#include "storia_scena.h"
#include "titolo.h"
#include "menu_pagine.h"
#include "schermate.h"
#include "vista_testo.h"

// All'avvio: con L premuto la schermata dei testi (F1), con SELECT la camminata automatica del
// mondo (F2), con R le istantanee delle aree (F2), altrimenti l'esplorazione da Piazza Grande.
// Croce per muoversi, B per correre. Per le prove senza tastiera, GUBBIO_AVVIO in compilazione
// sceglie il modo come se il tasto fosse premuto: 1 camminata, 2 istantanee, 3 prova della battaglia,
// 4 i tre scontri giocabili a mano, 5 le istantanee della battaglia, 6 la prova del salvataggio,
// 7 le istantanee del titolo e della pausa, 8 la storia intera senza camminare, 9 il prologo giocabile
// col pilota, 10 le cutscene con le istantanee, 11 le figure degli NPC, 12 la citta' viva (NPC e folla),
// 14 la partita senza titolo ne' prologo, 15 il gioco vero con due slot di prova gia' scritti (le foto degli aiuti)
// (make USERFLAGS=-DGUBBIO_AVVIO=1). Senza modo di prova: il titolo, poi la partita; Start apre la pausa.
#ifndef GUBBIO_AVVIO
    #define GUBBIO_AVVIO 0
#endif

// Gli aiuti al giocatore (cartelli ai varchi, promemoria di Select): il gioco vero (0), la partita senza
// titolo ne' prologo (14) e quella con gli slot di prova (15), per fotografarli. Spenti negli altri modi.
constexpr bool AIUTI_ATTIVI = GUBBIO_AVVIO == 0 || GUBBIO_AVVIO == 14 || GUBBIO_AVVIO == 15;
// Il titolo, «Dove eravamo» e gli scontri della storia: il gioco vero e il modo 15, che scrive prima due slot di
// prova (gubbio::prepara_slot_di_prova) e poi va come il gioco vero, senza il prologo.
constexpr bool COL_TITOLO = GUBBIO_AVVIO == 0 || GUBBIO_AVVIO == 15;

int main()
{
    bn::core::init();
    // le opzioni (MOP) valgono da subito, anche nel titolo
    gubbio::opzioni::carica();
    gubbio::opzioni::applica();
    bn::core::update();

    // ritorno al titolo con A+B+Select+Start (MAI): si riparte coi tasti ancora premuti, e Select tenuto
    // all'avvio vorrebbe dire la camminata automatica. Si aspetta che li lascino tutti.
    if(bn::keypad::a_held() && bn::keypad::b_held() && bn::keypad::select_held() && bn::keypad::start_held())
    {
        while(bn::keypad::a_held() || bn::keypad::b_held() || bn::keypad::select_held() || bn::keypad::start_held())
        {
            bn::core::update();
        }
    }

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

    if(GUBBIO_AVVIO == 10)
    {
        gubbio::prova_regia(palette);
    }

    if(GUBBIO_AVVIO == 8)
    {
        gubbio::prova_storia(palette);
    }

    if(GUBBIO_AVVIO == 6)
    {
        gubbio::prova_salvataggio();

        while(true)
        {
            bn::core::update();
        }
    }

    if(GUBBIO_AVVIO == 15)
    {
        gubbio::prepara_slot_di_prova();
    }

    // il titolo solo nel gioco vero (e per le sue istantanee): i modi di prova partono subito
    int slot = COL_TITOLO && ! bn::keypad::select_held() && ! bn::keypad::r_held() ? gubbio::titolo(palette) :
               (GUBBIO_AVVIO == 7 ? gubbio::titolo(palette, true) : -1);

    // Butano rende gli elementi dei tile degli sprite al prossimo update: senza, quelli del titolo (81 su 128)
    // contano ancora mentre l'esplorazione e «Dove eravamo» creano i loro, e dopo Continua il gioco si fermava
    // con «No more sprite tiles items available»
    if(COL_TITOLO || GUBBIO_AVVIO == 7)
    {
        bn::core::update();
    }

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
        // un salvataggio v3 aggiornato ritrova obiettivo e aree viste dalle scene fatte (MOB)
        gubbio::storia::dopo_il_caricamento(gubbio::g_game_state);
        esplorazione.riprendi(gubbio::mondo::AreaId(gubbio::g_game_state.area), gubbio::g_game_state.x,
                              gubbio::g_game_state.y);

        // «Dove eravamo» (MAI): una volta, dopo Continua
        if(COL_TITOLO)
        {
            gubbio::dove_eravamo(esplorazione, palette);
        }
    }
    else
    {
        gubbio::progressione::partita_nuova(gubbio::g_game_state);

        // la partita nuova del gioco vero comincia dal prologo (le scene a schermo intero)
        if(GUBBIO_AVVIO == 0)
        {
            gubbio::Storia prologo;
            prologo.prologo(palette);
        }

        esplorazione.entra(gubbio::mondo::AreaId::PIAZZA_GRANDE, 0);
    }

    if(GUBBIO_AVVIO == 9)
    {
        gubbio::prova_prologo(esplorazione, palette);
    }

    if(GUBBIO_AVVIO == 11)
    {
        gubbio::prova_figure_npc(esplorazione, palette);
    }

    if(GUBBIO_AVVIO == 12)
    {
        gubbio::prova_folla(esplorazione);
    }

    if(GUBBIO_AVVIO == 7)
    {
        for(int f = 0; f < 60; ++f)
        {
            esplorazione.aggiorna();
            bn::core::update();
        }

        // la pausa e le sue pagine sulla partita d'esempio dei mockup, poi lo stato torna quello di prima
        gubbio::GameState prima = gubbio::g_game_state;
        gubbio::partita_d_esempio(gubbio::g_game_state);
        gubbio::pausa(esplorazione, palette, true);

        // la bottega del Venditore come il mockup 11: 84 Denari, il borgo dentro le mura (2 Crescia e 3 Biscotti)
        gubbio::g_game_state.denari = 84;
        gubbio::storia::accendi_una(gubbio::g_game_state, int(gubbio::storia::Bandiera::BORGO_DENTRO));
        esplorazione.entra(gubbio::mondo::AreaId::PIAZZA_QUARANTA_MARTIRI, 0);

        for(int f = 0; f < 30; ++f)
        {
            esplorazione.aggiorna();
            bn::core::update();
        }

        esplorazione.nascondi_etichetta();

        gubbio::menu::bottega(false, true);
        bn::core::update();
        gubbio::menu::bottega(true, true);
        bn::core::update();
        gubbio::g_game_state = prima;

        // un nemico sulla mappa: la Pattuglia al Teatro Romano, vista dall'ingresso dalla citta'
        gubbio::progressione::partita_nuova(gubbio::g_game_state);
        esplorazione.entra(gubbio::mondo::AreaId::TEATRO_ROMANO, 2);
        gubbio::ScontriSullaMappa nemici;

        for(int f = 0; f < 220; ++f)
        {
            if(f == 200)
            {
                BN_LOG("Istantanea nemico_sulla_mappa");
            }

            bool passo = f < 160 && f % 2 == 0;
            esplorazione.muovi(passo ? 1 : 0, passo ? -1 : 0, 1);
            esplorazione.aggiorna();
            nemici.aggiorna(esplorazione, palette);
            bn::core::update();
        }

        BN_LOG("Istantanee finite");
    }

    gubbio::Storia storia;
    gubbio::ScontriSullaMappa scontri(COL_TITOLO ? &storia : nullptr);

    // gli aiuti (MAI: cartelli ai varchi, promemoria di Select) nel gioco vero e nelle partite di prova 14 e 15,
    // che servono a fotografarli; spenti negli altri modi di prova
    esplorazione.attiva_aiuti(AIUTI_ATTIVI);

    while(true)
    {
        ++gubbio::g_game_state.frames;
        ++gubbio::g_game_state.tempo_frames;

        // A+B+Select+Start: si torna al titolo (la convenzione dei giochi GBA), prima della pausa e del promemoria
        if(bn::keypad::a_held() && bn::keypad::b_held() && bn::keypad::select_held() && bn::keypad::start_held())
        {
            bn::core::reset();
        }

        if(bn::keypad::start_pressed() && ! esplorazione.in_dissolvenza())
        {
            // la gente e i nemici sulla mappa si tolgono, come per una battaglia: i loro sprite servono alla
            // pausa (gli sprite sono 128 in tutto). Al frame dopo si rifanno quelli dell'area.
            storia.svuota();
            scontri.svuota();
            gubbio::pausa(esplorazione, palette);
        }

        if(bn::keypad::select_pressed() && AIUTI_ATTIVI)
        {
            esplorazione.promemoria();
        }

        int dx = bn::keypad::left_held() ? -1 : (bn::keypad::right_held() ? 1 : 0);
        int dy = bn::keypad::up_held() ? -1 : (bn::keypad::down_held() ? 1 : 0);
        esplorazione.muovi(dx, dy, gubbio::opzioni::passi(gubbio::opzioni::g_opzioni, bn::keypad::b_held()));
        esplorazione.aggiorna();
        // la musica dell'area, della fase e del luogo (include/colonna_sonora.h); non riparte se e' la stessa
        const gubbio::mondo::Esploratore& qui = esplorazione.esploratore();
        gubbio::audio::esplorazione(gubbio::g_game_state, int(qui.area), gubbio::mondo::cella_x(qui),
                                    gubbio::mondo::cella_y(qui));
        // la storia prima degli scontri: una scena con la sua battaglia vale piu' del nemico sulla mappa
        if((COL_TITOLO || GUBBIO_AVVIO == 14) && storia.aggiorna(esplorazione, palette))
        {
            scontri.svuota();
        }

        scontri.aggiorna(esplorazione, palette);

        bn::core::update();
    }
}
