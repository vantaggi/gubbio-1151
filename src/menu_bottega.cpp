#include "menu_pagine.h"

#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"

#include "audio.h"
#include "negozio.h"
#include "stile/cornice.h"
#include "tabella.h"

// La bottega del Venditore delle Logge (MNEG, menu/PROPOSTA.md sez. 3.9; mockup menu/mockup/11_bottega.png): sopra
// la scena, che resta com'e', un riquadro con i Denari, le due merci col prezzo e quante ne restano; sotto, il
// riquadro del dialogo col cartiglio «Venditore», la sua riga e gli aiuti. Su e giu' per scegliere, A compra, B
// esce. Se Ubaldo sta nella meta' bassa dello schermo (STANDARD I3) il dialogo sale in cima e la merce scende.
namespace gubbio::menu
{

namespace
{
    using testo::TestoId;
    using stile::IconaMenu;

    constexpr TestoId NOME[negozio::MERCI] = { TestoId::BOTTEGA_CRESCIA, TestoId::BOTTEGA_BISCOTTI };
    constexpr IconaMenu ICONA[negozio::MERCI] = { IconaMenu::CRESCIA, IconaMenu::BISCOTTI };

    // il riquadro della merce: 13 x 10 tile in alto a destra (in basso col dialogo in cima)
    constexpr int MERCE_X = 136;
    constexpr int MERCE_COLONNE = 13;
    constexpr int MERCE_RIGHE = 10;
    constexpr int MERCE_IN_BASSO_Y = 160 - MERCE_RIGHE * 8;
    constexpr int DENTRO_X = MERCE_X + 12;
    constexpr int DENTRO_DESTRA = MERCE_X + MERCE_COLONNE * 8 - 13;
    constexpr int DENARI_Y = 12;
    constexpr int RIGA_Y = 29;
    constexpr int RIGA_PASSO = 12;
    constexpr int RESTANO_Y = 58;

    // il dialogo, dove lo mette storia_scena.cpp: riquadro 30x7 a y 104 (o 16), cartiglio a 8 px sopra
    constexpr int DIALOGO_IN_ALTO_Y = 16;
    constexpr int TESTO_X = stile::DIALOGO_X + 12;
    constexpr int TESTO_DY = 12;
    constexpr int AIUTO_DY = PIEDE_Y - stile::DIALOGO_Y;

    static_assert(MERCE_IN_BASSO_Y >= DIALOGO_IN_ALTO_Y + stile::DIALOGO_RIGHE * 8,
                  "col dialogo in cima la merce non ci sta sotto");

    TestoId esito_in_parole(negozio::Esito e)
    {
        switch(e)
        {
            case negozio::Esito::COMPRATO:
                return TestoId::BOTTEGA_COMPRATO;

            case negozio::Esito::FINITE:
                return TestoId::BOTTEGA_FINITE;

            case negozio::Esito::POCHI_DENARI:
                return TestoId::BOTTEGA_POCHI_DENARI;

            default:
                return TestoId::BOTTEGA_PIENO;
        }
    }

    // Il riquadro della merce: quello che cambia a ogni compera (Denari, inchiostri, «Ne restano»).
    class Merce
    {
    public:
        Merce(int y0, const GameState& p, const bn::sprite_palette_ptr& palette, const bn::sprite_palette_ptr& icone) :
            _denari_nome(TestoId::BOTTEGA_DENARI, DENTRO_X, y0 + DENARI_Y, INCHIOSTRO, palette),
            _denari(0, y0 + DENARI_Y, INCHIOSTRO, palette),
            _filo_alto(DENTRO_X, y0 + DENARI_Y + 11, DENTRO_DESTRA - DENTRO_X + 1, palette),
            _filo_basso(DENTRO_X, y0 + RESTANO_Y - 4, DENTRO_DESTRA - DENTRO_X + 1, palette),
            _restano(TestoId::BOTTEGA_RESTANO, DENTRO_X, y0 + RESTANO_Y, NOTA, palette),
            _quante{ VistaNumero(0, y0 + RESTANO_Y, NOTA, palette), VistaNumero(0, y0 + RESTANO_Y, NOTA, palette) },
            _icone{ crea_icona(ICONA[0], DENTRO_X + 10, y0 + RIGA_Y, icone),
                    crea_icona(ICONA[1], DENTRO_X + 10, y0 + RIGA_Y + RIGA_PASSO, icone) },
            _prezzi{ VistaNumero(0, y0 + RIGA_Y, INCHIOSTRO, palette),
                     VistaNumero(0, y0 + RIGA_Y + RIGA_PASSO, INCHIOSTRO, palette) },
            _y0(y0),
            _palette(palette)
        {
            _filo_alto.rett(0, 0, DENTRO_DESTRA - DENTRO_X, 0, GRIGIO);
            _filo_basso.rett(0, 0, DENTRO_DESTRA - DENTRO_X, 0, GRIGIO);

            for(int m = 0; m < negozio::MERCI; ++m)
            {
                _prezzi[m].mostra(GUBBIO_VOCE(negozio::PREZZO, m));
                _prezzi[m].colloca_a_destra(DENTRO_DESTRA, y0 + RIGA_Y + m * RIGA_PASSO);
            }

            aggiorna(p);
        }

        void aggiorna(const GameState& p)
        {
            _denari.mostra(p.denari);
            _denari.colloca_a_destra(DENTRO_DESTRA, _y0 + DENARI_Y);

            // le merci finite in grigio; «Ne restano 2 e 3» composto a pezzi
            int x = DENTRO_X + larghezza_testo(TestoId::BOTTEGA_RESTANO) + 4;

            for(int m = 0; m < negozio::MERCI; ++m)
            {
                bool c_e = negozio::restano(p, m) > 0;
                _nomi[m].reset();
                _nomi[m].emplace(GUBBIO_VOCE(NOME, m), DENTRO_X + 21, _y0 + RIGA_Y + m * RIGA_PASSO,
                                 c_e ? INCHIOSTRO : SPENTO, _palette);
                _quante[m].mostra(negozio::restano(p, m));
                _quante[m].colloca(x, _y0 + RESTANO_Y);
                x += _quante[m].larghezza() + 4;

                if(m == 0)
                {
                    _e.reset();
                    _e.emplace(TestoId::BOTTEGA_E, x, _y0 + RESTANO_Y, NOTA, _palette);
                    x += larghezza_testo(TestoId::BOTTEGA_E) + 4;
                }
            }
        }

        [[nodiscard]] int y_riga(int m) const
        {
            return _y0 + RIGA_Y + m * RIGA_PASSO;
        }

    private:
        Scritta _denari_nome;
        VistaNumero _denari;
        Striscia _filo_alto;
        Striscia _filo_basso;
        Scritta _restano;
        bn::optional<Scritta> _e;
        VistaNumero _quante[negozio::MERCI];
        bn::sprite_ptr _icone[negozio::MERCI];
        VistaNumero _prezzi[negozio::MERCI];
        bn::optional<Scritta> _nomi[negozio::MERCI];
        int _y0;
        bn::sprite_palette_ptr _palette;
    };
}

void bottega(bool dialogo_in_alto, bool istantanea)
{
    GameState& p = g_game_state;
    bn::sprite_palette_ptr palette = crea_palette();
    bn::sprite_palette_ptr icone = crea_palette_icone();
    int dialogo_y = dialogo_in_alto ? DIALOGO_IN_ALTO_Y : stile::DIALOGO_Y;
    int merce_y = dialogo_in_alto ? MERCE_IN_BASSO_Y : 0;

    Riquadri riquadri;
    riquadri.cornice(MERCE_X, merce_y, MERCE_COLONNE, MERCE_RIGHE);
    riquadri.cornice(stile::DIALOGO_X, dialogo_y, stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
    int larghezza = larghezza_testo(TestoId::BOTTEGA_VENDITORE);
    int colonne = colonne_cartiglio(larghezza);
    riquadri.cartiglio(stile::CARTIGLIO_NOME_X, dialogo_y - 8, colonne);
    VistaTesto nome(testo::Contesto::HUD, stile::CARTIGLIO_NOME_X + (colonne * 8 - larghezza) / 2, dialogo_y - 4, CHIARO,
                    palette);
    nome.mostra(TestoId::BOTTEGA_VENDITORE);
    nome.rivela_tutto();

    Merce merce(merce_y, p, palette, icone);
    VistaTesto riga(testo::Contesto::DIALOGO, TESTO_X, dialogo_y + TESTO_DY, INCHIOSTRO, palette);
    riga.mostra(negozio::ha_merce(p) ? TestoId::BOTTEGA_SALUTO : TestoId::BOTTEGA_VUOTA);
    AiutoTasti aiuto(TestoId::BOTTEGA_AIUTO_A, TestoId::BOTTEGA_AIUTO_B, MARGINE_X, dialogo_y + AIUTO_DY, palette);
    bn::sprite_ptr cursore = crea_cursore(palette);
    int voce = negozio::restano(p, 0) > 0 || negozio::restano(p, 1) <= 0 ? 0 : 1;

    while(true)
    {
        colloca(cursore, DENTRO_X, merce.y_riga(voce), 8, 8);

        if(istantanea)
        {
            riga.rivela_tutto();
            attendi(30);
            BN_LOG("Istantanea bottega", dialogo_in_alto ? "_in_alto" : "");
            attendi(30);
            return;
        }

        attendi(1);

        if(! riga.completo())
        {
            riga.avanza();

            if(bn::keypad::a_pressed())
            {
                riga.rivela_tutto();
            }

            continue;
        }

        if(bn::keypad::b_pressed())
        {
            audio::suona(colonna::Suono::ANNULLA);
            return;
        }

        if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
        {
            voce = 1 - voce;
            audio::suona(colonna::Suono::CURSORE);
        }
        else if(bn::keypad::a_pressed())
        {
            negozio::Esito e = negozio::compra(p, voce);
            audio::suona(e == negozio::Esito::COMPRATO ? colonna::Suono::RACCOLTA : colonna::Suono::ANNULLA);
            merce.aggiorna(p);
            bool vuota = e == negozio::Esito::COMPRATO && ! negozio::ha_merce(p);
            riga.mostra(vuota ? TestoId::BOTTEGA_VUOTA : esito_in_parole(e));
        }
    }
}

}
