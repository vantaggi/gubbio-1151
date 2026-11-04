#include "menu_pagine.h"

#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_vector.h"

#include "audio.h"
#include "progressione.h"
#include "storia_logica.h"
#include "tabella.h"

// I compagni (MBI, menu/PROPOSTA.md sez. 3.5; mockup menu/mockup/05_santi.png): una pagina per compagno del
// gruppo, su e giu' passano all'altro. Ritratto, nome, livello e la barra dell'esperienza con «mancano N»; le
// sette statistiche al livello (i PV come alla prossima battaglia, con le ferite dei miasmi); le abilita' col
// costo in Fervore, le stesse del menu di battaglia (src/scena_battaglia.cpp).
namespace gubbio::menu
{

namespace
{
    using testo::TestoId;
    using battaglia::AbilitaId;

    struct Proprie
    {
        int quante;
        AbilitaId abilita[2];
        TestoId nomi[2];
    };

    // nell'ordine dei compagni, come nel menu di battaglia
    constexpr Proprie PROPRIE[battaglia::EROI] = {
        { 2, { AbilitaId::GIUDIZIO_DELLA_VERGA, AbilitaId::MURO_DELLA_FEDE }, { TestoId::BATT_GIUDIZIO, TestoId::BATT_MURO } },
        { 2, { AbilitaId::FENDENTE_DEL_DRAGO, AbilitaId::BASTIONE_AZZURRO }, { TestoId::BATT_FENDENTE, TestoId::BATT_BASTIONE } },
        { 1, { AbilitaId::FUOCO_DI_SANTANTONIO, AbilitaId::FUOCO_DI_SANTANTONIO }, { TestoId::BATT_FUOCO, TestoId::BATT_FUOCO } },
    };

    constexpr int STATISTICHE = 7;
    constexpr TestoId NOMI_STATISTICHE[STATISTICHE] = {
        TestoId::MENU_PV, TestoId::COMP_FERVORE, TestoId::COMP_ATTACCO, TestoId::COMP_DIFESA,
        TestoId::COMP_MISTICO, TestoId::COMP_RESISTENZA, TestoId::COMP_VELOCITA };

    constexpr int TESTO_X = 52;
    constexpr int ESPERIENZA_LARGA = 90;
    constexpr int COSTO_DESTRA = 140;

    // Una statistica: il nome in grigio, il valore allineato a destra 96 px piu' in la'.
    class RigaStatistica
    {
    public:
        RigaStatistica(int i, const Forze& f, const bn::sprite_palette_ptr& palette) :
            _nome(GUBBIO_VOCE(NOMI_STATISTICHE, i), x(i), y(i), NOTA, palette),
            _valore(0, y(i), INCHIOSTRO, palette)
        {
            const battaglia::Statistiche& s = f.al_livello;
            const int valori[STATISTICHE] = { 0, s.fervore, s.attacco, s.difesa, s.mistico, s.resistenza, s.velocita };

            // i PV sono «331/437»: troppo larghi per uno sprite, la prima meta' ne ha uno suo
            _valore.mostra(i == 0 ? s.pv : GUBBIO_VOCE(valori, i));
            _valore.colloca_a_destra(x(i) + 96, y(i));

            if(i == 0)
            {
                _ora.emplace(0, y(i), INCHIOSTRO, palette);
                _ora->mostra_su(f.pv);
                _ora->colloca_a_destra(x(i) + 96 - _valore.larghezza(), y(i));
            }
        }

    private:
        Scritta _nome;
        VistaNumero _valore;
        bn::optional<VistaNumero> _ora;

        static int x(int i)
        {
            return i < 4 ? 12 : 128;
        }

        static int y(int i)
        {
            return 62 + (i % 4) * 10;
        }
    };

    // Un'abilita': il nome e, allineato a COSTO_DESTRA, «20 Fe».
    class RigaAbilita
    {
    public:
        RigaAbilita(TestoId nome, int costo, int y, const bn::sprite_palette_ptr& palette) :
            _nome(nome, 15, y, INCHIOSTRO, palette),
            _fe(TestoId::MENU_FE, COSTO_DESTRA + 1 - larghezza_testo(TestoId::MENU_FE), y, INCHIOSTRO, palette),
            _costo(0, y, INCHIOSTRO, palette)
        {
            _costo.mostra(costo);
            _costo.colloca_a_destra(COSTO_DESTRA - larghezza_testo(TestoId::MENU_FE) - 3, y);
        }

    private:
        Scritta _nome;
        Scritta _fe;
        VistaNumero _costo;
    };

    // La pagina di un compagno; ritorna quando si esce (Esito) o si passa a un altro (su: -1, giu': +1).
    Esito scheda_compagno(int e, int compagni, int& passo, const bn::sprite_palette_ptr& palette, bool istantanea)
    {
        const GameState& p = g_game_state;
        Forze f = forze(p, e);
        Pagina pagina(PAGINA_COMPAGNI, compagni > 1 ? TestoId::COMP_AIUTO : TestoId::MENU_INDIETRO, palette);
        bn::sprite_ptr ritratto = crea_ritratto(e, 15, 24);
        Scritta nome(GUBBIO_VOCE(NOMI_COMPAGNI, e), TESTO_X, 24, TITOLO, palette);
        Scritta livello(TestoId::COMP_LIVELLO, TESTO_X, 35, INCHIOSTRO, palette);
        VistaNumero numero(0, 35, INCHIOSTRO, palette);
        numero.mostra(f.livello);
        numero.colloca(TESTO_X + larghezza_testo(TestoId::COMP_LIVELLO) + 4, 35);

        // l'esperienza: la barra dal livello attuale al prossimo, e quanto manca
        int esperienza = p.esperienza[e];
        bool al_massimo = f.livello >= progressione::LIVELLO_MAX;
        int da = GUBBIO_VOCE(progressione::ESPERIENZA_PER_LIVELLO, f.livello - 1);
        int a = al_massimo ? da : GUBBIO_VOCE(progressione::ESPERIENZA_PER_LIVELLO, f.livello);
        Striscia barra(TESTO_X, 49, ESPERIENZA_LARGA + 2, palette);
        disegna_barra(barra, 0, 0, ESPERIENZA_LARGA, al_massimo ? 1 : esperienza - da, al_massimo ? 1 : a - da, ORO);
        Scritta mancano(al_massimo ? TestoId::COMP_AL_MASSIMO : TestoId::COMP_MANCANO, 150, 46, NOTA, palette);
        bn::optional<VistaNumero> quanti;

        if(! al_massimo)
        {
            quanti.emplace(0, 46, NOTA, palette);
            quanti->mostra(a - esperienza);
            quanti->colloca(150 + larghezza_testo(TestoId::COMP_MANCANO) + 4, 46);
        }

        bn::optional<RigaStatistica> statistiche[STATISTICHE];

        for(int i = 0; i < STATISTICHE; ++i)
        {
            statistiche[i].emplace(i, f, palette);
        }

        Scritta titolo_abilita(TestoId::COMP_ABILITA, 15, 104, TITOLO, palette);
        const Proprie& proprie = GUBBIO_VOCE(PROPRIE, e);
        bn::optional<RigaAbilita> abilita[2];

        for(int k = 0; k < proprie.quante; ++k)
        {
            AbilitaId id = GUBBIO_VOCE(proprie.abilita, k);
            abilita[k].emplace(GUBBIO_VOCE(proprie.nomi, k), GUBBIO_VOCE(battaglia::ABILITA, int(id)).costo,
                               115 + k * 10, palette);
        }

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa_compagni");
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
                passo = 0;
                return esito;
            }

            if(compagni > 1 && (bn::keypad::up_pressed() || bn::keypad::down_pressed()))
            {
                audio::suona(colonna::Suono::CURSORE);
                passo = bn::keypad::down_pressed() ? 1 : -1;
                return Esito::INDIETRO;
            }
        }
    }
}

Esito pagina_compagni(const bn::sprite_palette_ptr& palette, bool istantanea)
{
    uint8_t chi = storia::gruppo(g_game_state, -1);
    bn::vector<int, battaglia::EROI> compagni;

    for(int e = 0; e < battaglia::EROI; ++e)
    {
        if((chi >> e) & 1)
        {
            compagni.push_back(e);
        }
    }

    if(compagni.empty())
    {
        compagni.push_back(battaglia::UBALDO);
    }

    // nell'istantanea il secondo compagno, come nel mockup (Giorgio), se c'e'
    int i = istantanea && compagni.size() > 1 ? 1 : 0;

    while(true)
    {
        int passo = 0;
        Esito esito = scheda_compagno(compagni[i], compagni.size(), passo, palette, istantanea);

        if(istantanea || passo == 0)
        {
            return esito;
        }

        i = (i + passo + compagni.size()) % compagni.size();
        attendi(1);
    }
}

}
