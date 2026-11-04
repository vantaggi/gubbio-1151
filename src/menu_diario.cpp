#include "menu_pagine.h"

#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_vector.h"

#include "audio.h"
#include "storia_logica.h"

// Il diario (MDI, menu/PROPOSTA.md sez. 3.2; mockup menu/mockup/02_diario.png e 02b_diario_scheda.png): in alto
// la cronaca, cioe' l'obiettivo della storia; sotto gli incarichi presi, con la bandierina nel colore del
// quartiere di chi l'ha dato, il pezzo da raccogliere e il contatore. A apre la scheda dell'incarico.
namespace gubbio::menu
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using stile::IconaMenu;

    struct Incarico
    {
        TestoId titolo;
        TestoId da;
        TestoId storia;
        TestoId premio;
        IconaMenu bandiera;
        IconaMenu consegna;
        IconaMenu pezzo;
    };

    // nell'ordine di storia::QUEST_V1: Q-SM01, Q-SA01, Q-SP01
    constexpr Incarico INCARICHI[storia::QUEST] = {
        { TestoId::INC_SM01_TITOLO, TestoId::INC_SM01_DA, TestoId::INC_SM01_STORIA, TestoId::INC_SM01_PREMIO,
          IconaMenu::INCARICO_SM, IconaMenu::CONSEGNA_SM, IconaMenu::FERRO },
        { TestoId::INC_SA01_TITOLO, TestoId::INC_SA01_DA, TestoId::INC_SA01_STORIA, TestoId::INC_SA01_PREMIO,
          IconaMenu::INCARICO_SA, IconaMenu::CONSEGNA_SA, IconaMenu::ELLEBORO },
        { TestoId::INC_SP01_TITOLO, TestoId::INC_SP01_DA, TestoId::INC_SP01_STORIA, TestoId::INC_SP01_PREMIO,
          IconaMenu::INCARICO_SP, IconaMenu::CONSEGNA_SP, IconaMenu::ROSA },
    };

    static_assert(storia::QUEST == 3, "il diario conosce tre incarichi: aggiungere i nuovi a INCARICHI");

    bool consegnata(const GameState& p, int q)
    {
        return storia::accesa(p, int(storia::QUEST_V1[q].consegnata));
    }

    // la bandierina: con l'oro al centro quando c'e' da tornare a riferire
    IconaMenu bandiera(const GameState& p, int q)
    {
        return storia::obiettivo_fatto(p, q) && ! consegnata(p, q) ? INCARICHI[q].consegna : INCARICHI[q].bandiera;
    }

    TestoId nota(const GameState& p, int q)
    {
        return consegnata(p, q) ? TestoId::DIARIO_CONSEGNATO :
               (storia::obiettivo_fatto(p, q) ? TestoId::DIARIO_COMPIUTO : INCARICHI[q].da);
    }

    // Una riga dell'elenco: bandierina, titolo, il pezzo e il contatore a destra, sotto la nota in grigio.
    class Riga
    {
    public:
        Riga(int q, int y, const bn::sprite_palette_ptr& palette, const bn::sprite_palette_ptr& icone) :
            _bandiera(crea_icona(bandiera(g_game_state, q), 22, y, icone)),
            _pezzo(crea_icona(INCARICHI[q].pezzo, 196, y, icone)),
            _titolo(INCARICHI[q].titolo, 33, y, consegnata(g_game_state, q) ? SPENTO : INCHIOSTRO, palette),
            _nota(nota(g_game_state, q), 33, y + 10, NOTA, palette),
            _conto(0, y, INCHIOSTRO, palette)
        {
            _conto.mostra_frazione(storia::pezzi_raccolti(g_game_state, q), storia::QUEST_GIOCO[q].pezzi);
            _conto.colloca_a_destra(DESTRA_X, y);
        }

    private:
        bn::sprite_ptr _bandiera;
        bn::sprite_ptr _pezzo;
        Scritta _titolo;
        Scritta _nota;
        VistaNumero _conto;
    };

    // La scheda di un incarico: la storia in tre righe, i pezzi uno per uno (pieni quelli raccolti), il premio.
    Esito scheda(int q, const bn::sprite_palette_ptr& palette, const bn::sprite_palette_ptr& icone, bool istantanea)
    {
        const GameState& p = g_game_state;
        const Incarico& inc = INCARICHI[q];
        Pagina pagina(PAGINA_DIARIO, TestoId::MENU_INDIETRO, palette);
        bn::sprite_ptr ban = crea_icona(bandiera(p, q), 13, 24, icone);
        Scritta titolo(inc.titolo, 24, 24, TITOLO, palette);
        Scritta da(nota(p, q), 24, 35, NOTA, palette);
        Scritta storia_q(inc.storia, MARGINE_X, 52, INCHIOSTRO, palette);
        int fatti = storia::pezzi_raccolti(p, q);
        int tot = storia::QUEST_GIOCO[q].pezzi;
        bn::vector<bn::sprite_ptr, 8> pezzi;

        for(int k = 0; k < tot && k < 8; ++k)
        {
            pezzi.push_back(crea_icona(k < fatti ? inc.pezzo : IconaMenu::VUOTO, MARGINE_X + k * 14, 90, icone));
        }

        VistaNumero conto(0, 89, INCHIOSTRO, palette);
        conto.mostra_frazione(fatti, tot);
        conto.colloca(MARGINE_X + tot * 14 + 2, 89);
        Scritta premio(inc.premio, MARGINE_X, 110, NOTA, palette);

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa_diario_scheda");
            attendi(30);
            return Esito::INDIETRO;
        }

        Esito esito = Esito::INDIETRO;

        while(true)
        {
            attendi(1);

            if(navigazione(esito))
            {
                audio::suona(colonna::Suono::ANNULLA);
                return esito;
            }
        }
    }
}

Esito pagina_diario(const bn::sprite_palette_ptr& palette, bool istantanea)
{
    const GameState& p = g_game_state;
    bn::sprite_palette_ptr icone = crea_palette_icone();
    bn::vector<int, storia::QUEST> prese;

    for(int q = 0; q < storia::QUEST; ++q)
    {
        if(storia::presa(p, q))
        {
            prese.push_back(q);
        }
    }

    int voce = 0;

    while(true)
    {
        Esito esito = Esito::INDIETRO;
        bool apri = false;

        {
            Pagina pagina(PAGINA_DIARIO, prese.empty() ? TestoId::MENU_INDIETRO : TestoId::MENU_SCHEDA,
                          TestoId::MENU_INDIETRO, palette);
            // la cronaca: l'obiettivo della storia, come nella pausa
            bn::sprite_ptr stella = crea_icona(IconaMenu::OBIETTIVO, 13, 24, icone);
            Scritta cronaca(TestoId::DIARIO_CRONACA, 24, 24, TITOLO, palette);
            bool con_obiettivo = storia::area_dell_obiettivo(p) >= 0;
            TestoId obiettivo = con_obiettivo ? storia::OBIETTIVO[p.obiettivo].testo : TestoId::PROMEMORIA_NESSUNO;
            Scritta testo_obiettivo(obiettivo, MARGINE_X, 35, INCHIOSTRO, palette);
            int incarichi_y = 35 + testo::dati(obiettivo).righe * 10 + 5;
            Scritta incarichi(TestoId::DIARIO_INCARICHI, 13, incarichi_y, TITOLO, palette);
            bn::optional<Riga> righe[storia::QUEST];
            bn::optional<Scritta> nessuno;

            for(int i = 0; i < prese.size(); ++i)
            {
                righe[i].emplace(prese[i], incarichi_y + 12 + i * 22, palette, icone);
            }

            if(prese.empty())
            {
                nessuno.emplace(TestoId::DIARIO_NESSUNO, MARGINE_X, incarichi_y + 12, NOTA, palette);
            }

            bn::optional<bn::sprite_ptr> cursore;

            if(! prese.empty())
            {
                cursore = crea_cursore(palette);
            }

            if(istantanea)
            {
                if(cursore)
                {
                    colloca(*cursore, MARGINE_X, incarichi_y + 12, 8, 8);
                }

                attendi(30);
                BN_LOG("Istantanea pausa_diario");
                attendi(30);
            }

            while(! istantanea)
            {
                if(cursore)
                {
                    colloca(*cursore, MARGINE_X, incarichi_y + 12 + voce * 22, 8, 8);
                }

                attendi(1);

                if(navigazione(esito))
                {
                    audio::suona(colonna::Suono::ANNULLA);
                    break;
                }

                if(prese.empty())
                {
                    continue;
                }

                if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
                {
                    voce = (voce + (bn::keypad::down_pressed() ? 1 : prese.size() - 1)) % prese.size();
                    audio::suona(colonna::Suono::CURSORE);
                }
                else if(bn::keypad::a_pressed())
                {
                    audio::suona(colonna::Suono::CONFERMA);
                    apri = true;
                    break;
                }
            }
        }

        if(istantanea)
        {
            if(! prese.empty())
            {
                attendi(1);
                [[maybe_unused]] Esito e = scheda(prese[0], palette, icone, true);
            }

            return Esito::INDIETRO;
        }

        if(! apri)
        {
            return esito;
        }

        // la scheda: B torna all'elenco, Start, L e R valgono come nell'elenco
        attendi(1);
        esito = scheda(prese[voce], palette, icone, false);
        attendi(1);

        if(esito != Esito::INDIETRO)
        {
            return esito;
        }
    }
}

}
