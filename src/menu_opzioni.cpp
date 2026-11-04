#include "menu_pagine.h"

#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_vector.h"

#include "audio.h"
#include "opzioni.h"
#include "tabella.h"

// Le opzioni (MOP, menu/PROPOSTA.md sez. 3.7; mockup menu/mockup/07_opzioni.png): sei righe, su e giu' per
// scegliere, destra e sinistra per cambiare. Le scelte a parole hanno quella attiva in inchiostro e le altre
// spente; Musica ed Effetti hanno quattro tacche d'oro. Ogni cambio vale subito (volumi e luce compresi); uscendo
// dalla pagina, se qualcosa e' cambiato, il record delle opzioni si riscrive.
namespace gubbio::menu
{

namespace
{
    using testo::TestoId;
    using opzioni::Opzioni;

    constexpr int RIGHE = 6;
    constexpr int RIGA_Y = 26;
    constexpr int RIGA_PASSO = 14;
    constexpr int SCELTE_X = 100;
    constexpr int SCELTE_STACCO = 8;
    constexpr int TACCA_PASSO = 12;

    struct Riga
    {
        TestoId nome;
        int scelte;             // 0: tacche
        TestoId parole[3];
    };

    constexpr Riga RIGA[RIGHE] = {
        { TestoId::OPZ_TESTO, 3, { TestoId::OPZ_LENTO, TestoId::OPZ_NORMALE, TestoId::OPZ_SUBITO } },
        { TestoId::OPZ_MUSICA, 0, {} },
        { TestoId::OPZ_EFFETTI, 0, {} },
        { TestoId::OPZ_CORRERE, 2, { TestoId::OPZ_TIENI_B, TestoId::OPZ_SEMPRE } },
        { TestoId::OPZ_SCHERMO, 2, { TestoId::OPZ_NORMALE, TestoId::OPZ_PIU_CHIARO } },
        { TestoId::OPZ_CARTELLI, 2, { TestoId::OPZ_SI, TestoId::OPZ_NO } },
    };

    // il valore della riga i, come indice della scelta (o numero di tacche)
    uint8_t& valore(Opzioni& o, int i)
    {
        uint8_t* campi[RIGHE] = { &o.testo, &o.musica, &o.effetti, &o.sempre_corre, &o.piu_chiaro, &o.cartelli };
        return *GUBBIO_VOCE(campi, i);
    }

    // i Cartelli dicono «Si'» per primo: il valore 1 e' la scelta 0
    int scelta(Opzioni& o, int i)
    {
        int v = valore(o, i);
        return i == RIGHE - 1 ? 1 - v : v;
    }

    void cambia(Opzioni& o, int i, int verso)
    {
        const Riga& r = GUBBIO_VOCE(RIGA, i);
        int massimo = r.scelte ? r.scelte - 1 : opzioni::TACCHE;
        int s = scelta(o, i) + verso;
        s = s < 0 ? 0 : (s > massimo ? massimo : s);
        valore(o, i) = uint8_t(i == RIGHE - 1 ? 1 - s : s);
    }

    // Le parole di una riga, quella scelta in inchiostro.
    class Parole
    {
    public:
        Parole(const Riga& r, int scelta, int y, const bn::sprite_palette_ptr& palette)
        {
            int x = SCELTE_X;

            for(int k = 0; k < r.scelte; ++k)
            {
                TestoId t = GUBBIO_VOCE(r.parole, k);
                _parole.emplace_back(t, x, y, k == scelta ? INCHIOSTRO : SPENTO, palette);
                x += larghezza_testo(t) + SCELTE_STACCO;
            }
        }

    private:
        bn::vector<Scritta, 3> _parole;
    };

    // Le quattro tacche: bordo scuro, dentro oro fino al valore e grigio oltre.
    void disegna_tacche(Striscia& s, int v)
    {
        s.pulisci();

        for(int k = 0; k < opzioni::TACCHE; ++k)
        {
            s.rett(k * TACCA_PASSO, 1, k * TACCA_PASSO + 8, 7, BORDO);
            s.rett(k * TACCA_PASSO + 1, 2, k * TACCA_PASSO + 7, 6, k < v ? ORO : GRIGIO);
        }
    }
}

Esito pagina_opzioni(const bn::sprite_palette_ptr& palette, bool istantanea)
{
    Opzioni& o = opzioni::g_opzioni;
    Opzioni prima = o;
    Pagina pagina(PAGINA_OPZIONI, TestoId::OPZ_AIUTO, palette);
    bn::optional<Scritta> nomi[RIGHE];
    bn::optional<Parole> parole[RIGHE];
    bn::optional<Striscia> tacche[RIGHE];

    for(int i = 0; i < RIGHE; ++i)
    {
        const Riga& r = GUBBIO_VOCE(RIGA, i);
        int y = RIGA_Y + i * RIGA_PASSO;
        nomi[i].emplace(r.nome, 23, y, INCHIOSTRO, palette);

        if(r.scelte)
        {
            parole[i].emplace(r, scelta(o, i), y, palette);
        }
        else
        {
            tacche[i].emplace(SCELTE_X, y, (opzioni::TACCHE - 1) * TACCA_PASSO + 9, palette);
            disegna_tacche(*tacche[i], valore(o, i));
        }
    }

    Scritta nota(TestoId::OPZ_NOTA, 13, 118, NOTA, palette);
    bn::sprite_ptr cursore = crea_cursore(palette);
    int voce = 0;
    Esito esito = Esito::INDIETRO;

    while(true)
    {
        colloca(cursore, MARGINE_X, RIGA_Y + voce * RIGA_PASSO, 8, 8);

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa_opzioni");
            attendi(30);
            return Esito::INDIETRO;
        }

        attendi(1);

        if(navigazione(esito))
        {
            audio::suona(colonna::Suono::ANNULLA);
            break;
        }

        if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
        {
            voce = (voce + (bn::keypad::down_pressed() ? 1 : RIGHE - 1)) % RIGHE;
            audio::suona(colonna::Suono::CURSORE);
        }
        else if(bn::keypad::left_pressed() || bn::keypad::right_pressed())
        {
            int s = scelta(o, voce);
            cambia(o, voce, bn::keypad::right_pressed() ? 1 : -1);

            if(scelta(o, voce) == s)
            {
                continue;
            }

            const Riga& r = GUBBIO_VOCE(RIGA, voce);

            if(r.scelte)
            {
                parole[voce].reset();
                parole[voce].emplace(r, scelta(o, voce), RIGA_Y + voce * RIGA_PASSO, palette);
            }
            else
            {
                disegna_tacche(*tacche[voce], valore(o, voce));
            }

            // si sente subito: il volume nuovo, e il cursore come prova degli effetti
            opzioni::applica();
            audio::suona(colonna::Suono::CURSORE);
        }
    }

    bool cambiate = false;

    for(int i = 0; i < RIGHE; ++i)
    {
        cambiate |= valore(o, i) != valore(prima, i);
    }

    if(cambiate)
    {
        opzioni::salva();
    }

    return esito;
}

}
