#include "menu_pagine.h"

#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_sprite_items_ritratto_antonio.h"
#include "bn_sprite_items_ritratto_giorgio.h"
#include "bn_sprite_items_ritratto_ubaldo.h"

#include "mondo.h"
#include "progressione.h"
#include "storia_logica.h"

namespace gubbio::menu
{

using testo::Contesto;
using testo::TestoId;

void attendi(int frame)
{
    for(int f = 0; f < frame; ++f)
    {
        ++g_game_state.frames;
        bn::core::update();
    }
}

bool navigazione(Esito& esito)
{
    if(bn::keypad::start_pressed())
    {
        esito = Esito::CHIUDI;
    }
    else if(bn::keypad::b_pressed())
    {
        esito = Esito::INDIETRO;
    }
    else if(bn::keypad::l_pressed())
    {
        esito = Esito::SINISTRA;
    }
    else if(bn::keypad::r_pressed())
    {
        esito = Esito::DESTRA;
    }
    else
    {
        return false;
    }

    return true;
}

TestoId testo_della_fase(aiuti::FaseCronaca f)
{
    constexpr TestoId FASI[4] = { TestoId::FASE_ULTIMATUM, TestoId::FASE_DIGIUNO, TestoId::FASE_NOTTE,
                                  TestoId::FASE_DOPO_L_ALBA };
    return FASI[int(f)];
}

TestoId testo_dell_area(const GameState& p)
{
    int a = p.area < mondo::AREE_CONTEGGIO ? p.area : 0;
    return mondo::area(mondo::AreaId(a)).etichetta;
}

bn::sprite_ptr crea_ritratto(int e, int x, int y)
{
    bn::sprite_ptr s = e == 0 ? bn::sprite_items::ritratto_ubaldo.create_sprite(0, 0) :
                       (e == 1 ? bn::sprite_items::ritratto_giorgio.create_sprite(0, 0) :
                                 bn::sprite_items::ritratto_antonio.create_sprite(0, 0));
    colloca(s, x, y, 32, 32);
    s.set_bg_priority(PRIORITA_RIQUADRI);
    return s;
}

Forze forze(const GameState& p, int e)
{
    Forze f;
    f.livello = p.livello[e] < 1 ? 1 : (p.livello[e] > progressione::LIVELLO_MAX ? progressione::LIVELLO_MAX : p.livello[e]);
    f.al_livello = progressione::statistiche_al_livello(battaglia::STATISTICHE_EROI[e], f.livello);
    f.pv = f.al_livello.pv - p.ferite[e] < 1 ? 1 : f.al_livello.pv - p.ferite[e];
    int percento = battaglia::FERVORE_INIZIALE[e] + (storia::ceri_accesi(p) ? battaglia::FERVORE_CERI : 0);
    f.fervore = f.al_livello.fervore * (percento > 100 ? 100 : percento) / 100;
    return f;
}

Scritta::Scritta(TestoId id, int x, int y, int inchiostro, const bn::sprite_palette_ptr& palette) :
    _vista(testo::dati(id).contesto, x, y, inchiostro, palette)
{
    _vista.mostra(id);
    _vista.rivela_tutto();
}

namespace
{
    constexpr int AIUTI_STACCO = 12;

    constexpr int colonne_titolo(TestoId titolo)
    {
        return colonne_cartiglio(larghezza_testo(titolo));
    }

    // R contro il bordo destro, le tessere 4 px prima, L 4 px prima delle tessere
    int r_x()
    {
        return DESTRA_X + 1 - larghezza_testo(TestoId::MENU_R);
    }

    int tessere_x()
    {
        return r_x() - 4 - 6 * 9 + 2;
    }

    int l_x()
    {
        return tessere_x() - 4 - larghezza_testo(TestoId::MENU_L);
    }

    int titolo_x(int indice)
    {
        return 8 + (colonne_titolo(VOCI[indice]) * 8 - larghezza_testo(VOCI[indice])) / 2;
    }
}

AiutoTasti::AiutoTasti(TestoId a, TestoId b, int x, int y, const bn::sprite_palette_ptr& palette) :
    _a(testo::dati(a).contesto, x, y, SPENTO, palette)
{
    _a.mostra(a);
    _a.rivela_tutto();
    _b.emplace(testo::dati(b).contesto, x + larghezza_testo(a) + AIUTI_STACCO, y, SPENTO, palette);
    _b->mostra(b);
    _b->rivela_tutto();
}

AiutoTasti::AiutoTasti(TestoId solo, int x, int y, const bn::sprite_palette_ptr& palette) :
    _a(testo::dati(solo).contesto, x, y, SPENTO, palette)
{
    _a.mostra(solo);
    _a.rivela_tutto();
}

Pagina::Pagina(int indice, TestoId aiuto_a, TestoId aiuto_b, const bn::sprite_palette_ptr& palette) :
    _titolo(Contesto::HUD, titolo_x(indice), CARTIGLIO_Y + 4, CHIARO, palette),
    _aiuto(aiuto_a, aiuto_b, MARGINE_X, PIEDE_Y, palette),
    _l(Contesto::HUD, l_x(), PIEDE_Y, SPENTO, palette),
    _r(Contesto::HUD, r_x(), PIEDE_Y, SPENTO, palette),
    _filo(MARGINE_X, PIEDE_Y - 3, DESTRA_X - MARGINE_X + 1, palette),
    _tessere(tessere_x(), PIEDE_Y + 2, 64, palette)
{
    _componi(indice);
}

Pagina::Pagina(int indice, TestoId aiuto, const bn::sprite_palette_ptr& palette) :
    _titolo(Contesto::HUD, titolo_x(indice), CARTIGLIO_Y + 4, CHIARO, palette),
    _aiuto(aiuto, MARGINE_X, PIEDE_Y, palette),
    _l(Contesto::HUD, l_x(), PIEDE_Y, SPENTO, palette),
    _r(Contesto::HUD, r_x(), PIEDE_Y, SPENTO, palette),
    _filo(MARGINE_X, PIEDE_Y - 3, DESTRA_X - MARGINE_X + 1, palette),
    _tessere(tessere_x(), PIEDE_Y + 2, 64, palette)
{
    _componi(indice);
}

void Pagina::_componi(int indice)
{
    _riquadri.cornice(0, 0, 30, 20);
    _riquadri.cartiglio(8, CARTIGLIO_Y, colonne_titolo(VOCI[indice]));
    _titolo.mostra(VOCI[indice]);
    _r.mostra(TestoId::MENU_R);
    _l.mostra(TestoId::MENU_L);
    _filo.rett(0, 0, DESTRA_X - MARGINE_X, 0, GRIGIO);
    disegna_tessere(_tessere, 0, indice);

    for(VistaTesto* v : { &_titolo, &_l, &_r })
    {
        v->rivela_tutto();
    }
}

}
