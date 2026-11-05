#include "menu_pagine.h"

#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_vector.h"

#include "audio.h"
#include "storia_logica.h"
#include "tabella.h"

// La bisaccia (MBI, menu/PROPOSTA.md sez. 3.4; mockup menu/mockup/04_bisaccia.png): in alto i viveri che si hanno,
// con la quantita'; sotto le cose degli incarichi in corso, calcolate dalle bandiere, con la bandierina del
// quartiere e il contatore; in fondo, sotto un filo, la riga che spiega il viveri scelto. Fuori battaglia A sulla
// Crescia cura le ferite dei miasmi (GameState::ferite); gli altri viveri si usano in battaglia.
namespace gubbio::menu
{

namespace
{
    using testo::TestoId;
    using stile::IconaMenu;
    using battaglia::OggettoId;

    struct Viveri
    {
        OggettoId oggetto;
        TestoId nome;
        TestoId descrizione;
        IconaMenu icona;
    };

    // I consumabili che si trovano nella v1 (forzieri e premi delle quest). Il Baccala' e il Vino non li da'
    // ancora nessuno: quando arriveranno avranno la loro icona e la loro riga qui.
    constexpr Viveri VIVERI[] = {
        { OggettoId::CRESCIA, TestoId::BATT_CRESCIA, TestoId::DESCR_CRESCIA, IconaMenu::CRESCIA },
        { OggettoId::CENERE, TestoId::OGG_CENERE, TestoId::DESCR_CENERE, IconaMenu::CENERE },
        { OggettoId::BISCOTTI, TestoId::BATT_BISCOTTI, TestoId::DESCR_BISCOTTI, IconaMenu::BISCOTTI },
    };

    constexpr int N_VIVERI = int(sizeof(VIVERI) / sizeof(VIVERI[0]));

    // Una cosa dell'incarico: per quest presa e non ancora consegnata. Q-SP01 mostra gli indizi finche' la Rosa
    // non e' ripresa, poi la Rosa.
    // dal campo piu' grande al piu' piccolo (docs/regole_sviluppo_gba.md, punto 7): 12 byte invece di 16
    struct Cosa
    {
        int fatti;
        int totale;
        TestoId nome;
        IconaMenu icona;
        IconaMenu bandiera;

        constexpr Cosa(TestoId n, IconaMenu i, IconaMenu b, int f, int t) :
            fatti(f), totale(t), nome(n), icona(i), bandiera(b)
        {
        }
    };

    constexpr int COSE_MAX = storia::QUEST;
    static_assert(storia::QUEST == 3, "la bisaccia conosce tre incarichi: aggiungere i nuovi in cose()");

    bn::vector<Cosa, COSE_MAX> cose(const GameState& p)
    {
        bn::vector<Cosa, COSE_MAX> v;

        for(int q = 0; q < storia::QUEST; ++q)
        {
            if(! storia::presa(p, q) || storia::accesa(p, int(GUBBIO_VOCE(storia::QUEST_V1, q).consegnata)))
            {
                continue;
            }

            int fatti = storia::pezzi_raccolti(p, q);
            int tot = GUBBIO_VOCE(storia::QUEST_GIOCO, q).pezzi;

            if(q == 0)
            {
                v.push_back({ TestoId::COSA_FERRO, IconaMenu::FERRO, IconaMenu::INCARICO_SM, fatti, tot });
            }
            else if(q == 1)
            {
                v.push_back({ TestoId::COSA_ELLEBORO, IconaMenu::ELLEBORO, IconaMenu::INCARICO_SA, fatti, tot });
            }
            else if(storia::obiettivo_fatto(p, q))
            {
                v.push_back({ TestoId::COSA_ROSA, IconaMenu::ROSA, IconaMenu::INCARICO_SP, fatti, tot });
            }
            else
            {
                v.push_back({ TestoId::COSA_INDIZI, IconaMenu::INDIZIO, IconaMenu::INCARICO_SP,
                              storia::indizi_trovati(p), storia::INDIZI });
            }
        }

        return v;
    }

    bool qualcuno_ferito(const GameState& p)
    {
        for(uint8_t f : p.ferite)
        {
            if(f > 0)
            {
                return true;
            }
        }

        return false;
    }

    // A su un viveri: la Crescia cura le ferite dei miasmi, se ce ne sono; gli altri restano per la battaglia.
    TestoId usa(GameState& p, const Viveri& v)
    {
        if(v.oggetto != OggettoId::CRESCIA)
        {
            audio::suona(colonna::Suono::ANNULLA);
            return TestoId::BISACCIA_NON_ORA;
        }

        if(! qualcuno_ferito(p))
        {
            audio::suona(colonna::Suono::ANNULLA);
            return TestoId::BISACCIA_SANI;
        }

        --p.oggetti[int(OggettoId::CRESCIA)];
        storia::guarisci(p);
        audio::suona(colonna::Suono::RACCOLTA);
        return TestoId::BISACCIA_GUARITI;
    }

    constexpr int RIGA = 11;

    // Una riga dei viveri: icona, nome, «x2» a destra.
    class RigaViveri
    {
    public:
        RigaViveri(const Viveri& v, int quanti, int y, const bn::sprite_palette_ptr& palette,
                   const bn::sprite_palette_ptr& icone) :
            _icona(crea_icona(v.icona, 22, y, icone)),
            _nome(v.nome, 33, y, INCHIOSTRO, palette),
            _quanti(0, y, INCHIOSTRO, palette)
        {
            _quanti.mostra_volte(quanti);
            _quanti.colloca_a_destra(DESTRA_X, y);
        }

    private:
        bn::sprite_ptr _icona;
        Scritta _nome;
        VistaNumero _quanti;
    };

    // Una riga delle cose dell'incarico: icona, nome, la bandierina del quartiere e il contatore.
    class RigaCosa
    {
    public:
        RigaCosa(const Cosa& c, int y, const bn::sprite_palette_ptr& palette, const bn::sprite_palette_ptr& icone) :
            _icona(crea_icona(c.icona, 22, y, icone)),
            _bandiera(crea_icona(c.bandiera, 196, y, icone)),
            _nome(c.nome, 33, y, INCHIOSTRO, palette),
            _conto(0, y, INCHIOSTRO, palette)
        {
            _conto.mostra_frazione(c.fatti, c.totale);
            _conto.colloca_a_destra(DESTRA_X, y);
        }

    private:
        bn::sprite_ptr _icona;
        bn::sprite_ptr _bandiera;
        Scritta _nome;
        VistaNumero _conto;
    };
}

Esito pagina_bisaccia(const bn::sprite_palette_ptr& palette, bool istantanea)
{
    GameState& p = g_game_state;
    bn::sprite_palette_ptr icone = crea_palette_icone();
    int voce = 0;
    bn::optional<TestoId> messaggio;

    while(true)
    {
        bn::vector<int, N_VIVERI> avuti;

        for(int k = 0; k < N_VIVERI; ++k)
        {
            if(p.oggetti[int(GUBBIO_VOCE(VIVERI, k).oggetto)] > 0)
            {
                avuti.push_back(k);
            }
        }

        if(voce >= avuti.size())
        {
            voce = avuti.empty() ? 0 : avuti.size() - 1;
        }

        bn::vector<Cosa, COSE_MAX> roba = cose(p);
        Esito esito = Esito::INDIETRO;
        bool rifai = false;

        {
            Pagina pagina(PAGINA_BISACCIA, avuti.empty() ? TestoId::MENU_INDIETRO : TestoId::BISACCIA_AIUTO_A,
                          TestoId::MENU_INDIETRO, palette);
            Scritta titolo_viveri(TestoId::BISACCIA_VIVERI, 13, 24, TITOLO, palette);
            bn::optional<RigaViveri> righe[N_VIVERI];
            bn::optional<Scritta> vuota;

            for(int i = 0; i < avuti.size(); ++i)
            {
                int k = avuti[i];
                righe[i].emplace(GUBBIO_VOCE(VIVERI, k), p.oggetti[int(GUBBIO_VOCE(VIVERI, k).oggetto)],
                                 35 + i * RIGA, palette, icone);
            }

            if(avuti.empty())
            {
                vuota.emplace(TestoId::BISACCIA_VUOTA, MARGINE_X, 35, NOTA, palette);
            }

            int y = 35 + (avuti.empty() ? 1 : avuti.size()) * RIGA + 4;
            bn::optional<Scritta> titolo_cose;
            bn::optional<RigaCosa> righe_cose[COSE_MAX];

            if(! roba.empty())
            {
                titolo_cose.emplace(TestoId::BISACCIA_COSE, 13, y, TITOLO, palette);
                y += RIGA;

                for(int i = 0; i < roba.size(); ++i)
                {
                    righe_cose[i].emplace(roba[i], y, palette, icone);
                    y += RIGA;
                }
            }

            // il filo e la riga che spiega: dove li vuole il mockup, o sotto l'ultima riga se l'elenco e' lungo
            int filo_y = y + 2 > 98 ? y + 2 : 98;
            Striscia filo(MARGINE_X, filo_y, DESTRA_X - MARGINE_X + 1, palette);
            filo.rett(0, 0, DESTRA_X - MARGINE_X, 0, GRIGIO);
            bn::optional<Scritta> spiega;
            bn::optional<bn::sprite_ptr> cursore;

            if(! avuti.empty())
            {
                cursore = crea_cursore(palette);
            }

            while(true)
            {
                if(cursore)
                {
                    colloca(*cursore, MARGINE_X, 35 + voce * RIGA, 8, 8);
                }

                if(messaggio)
                {
                    spiega.reset();
                    spiega.emplace(*messaggio, 13, filo_y + 6, INCHIOSTRO, palette);
                }
                else if(! avuti.empty())
                {
                    spiega.reset();
                    spiega.emplace(GUBBIO_VOCE(VIVERI, avuti[voce]).descrizione, 13, filo_y + 6, INCHIOSTRO, palette);
                }

                if(istantanea)
                {
                    attendi(30);
                    BN_LOG("Istantanea pausa_bisaccia");
                    attendi(30);
                    return Esito::INDIETRO;
                }

                bool cambia = false;

                while(! cambia)
                {
                    attendi(1);

                    if(navigazione(esito))
                    {
                        audio::suona(colonna::Suono::ANNULLA);
                        return esito;
                    }

                    if(avuti.empty())
                    {
                        continue;
                    }

                    if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
                    {
                        voce = (voce + (bn::keypad::down_pressed() ? 1 : avuti.size() - 1)) % avuti.size();
                        messaggio.reset();
                        audio::suona(colonna::Suono::CURSORE);
                        cambia = true;
                    }
                    else if(bn::keypad::a_pressed())
                    {
                        messaggio = usa(p, GUBBIO_VOCE(VIVERI, avuti[voce]));
                        // una Crescia mangiata cambia i numeri: si ricompone la pagina
                        rifai = *messaggio == TestoId::BISACCIA_GUARITI;
                        cambia = true;
                    }
                }

                if(rifai)
                {
                    break;
                }
            }
        }

        attendi(1);
    }
}

}
