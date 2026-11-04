#include "titolo.h"

#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"

#include "aiuti.h"
#include "audio.h"
#include "battaglia_dati.h"
#include "esplorazione.h"
#include "game_state.h"
#include "progressione.h"
#include "save_data.h"
#include "menu_pagine.h"
#include "storia_logica.h"
#include "tabella.h"
#include "vista_menu.h"
#include "vista_testo.h"

// Il menu di pausa (MPA, menu/PROPOSTA.md sez. 3.1; mockup menu/mockup/01_pausa.png e 06_salva.png). Start apre
// la pausa sopra la scena scurita: in alto a sinistra i tre compagni (ritratto, nome, livello, PV e Fervore), a
// destra le sei voci, in basso l'obiettivo della cronaca nel riquadro del dialogo. A apre la pagina della voce;
// nelle pagine L e R passano alla pagina accanto, B torna alla pausa; B o Start dalla pausa tornano al gioco.
namespace gubbio::menu
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using salvataggio::StatoSlot;

    // ------------------------------------------------------------------ la pagina Salva (mockup 06)
    TestoId testo_dello_stato(StatoSlot s)
    {
        return s == StatoSlot::VUOTO ? TestoId::SALVA_VUOTO :
               (s == StatoSlot::ALTRA_VERSIONE ? TestoId::SLOT_ALTRA_VERSIONE : TestoId::SLOT_CORROTTO);
    }

    BN_DATA_EWRAM_BSS GameState s_slot[salvataggio::SLOT];

    // Uno slot: «Slot 1» in vermiglio e il tempo a destra, poi area e livelli, poi la fase (o «Vuoto»).
    class RigaSlot
    {
    public:
        RigaSlot(int k, int y, const bn::sprite_palette_ptr& palette) :
            _palette(palette),
            _nome(Contesto::HUD, 23, y, menu::TITOLO, palette),
            _tempo(0, y, menu::INCHIOSTRO, palette),
            _livelli(0, y + 11, menu::NOTA, palette),
            _k(k),
            _y(y)
        {
            _nome.mostra(k == 0 ? TestoId::SALVA_SLOT_1 : TestoId::SALVA_SLOT_2);
            _nome.rivela_tutto();
            aggiorna();
        }

        void aggiorna()
        {
            StatoSlot s = salvataggio::stato(_k);
            _valido = s == StatoSlot::VALIDO && salvataggio::carica(_k, s_slot[_k]);
            _fase.reset();
            _liv.reset();

            if(! _valido)
            {
                TestoId id = testo_dello_stato(s == StatoSlot::VALIDO ? StatoSlot::CORROTTO : s);
                _area.emplace(testo::dati(id).contesto, 23, _y + 11, menu::NOTA, _palette);
                _area->mostra(id);
                _area->rivela_tutto();
                _tempo.nascondi();
                _livelli.nascondi();
                return;
            }

            GameState& p = s_slot[_k];
            storia::dopo_il_caricamento(p);
            _area.emplace(Contesto::AREA, 23, _y + 11, menu::INCHIOSTRO, _palette);
            _area->mostra(testo_dell_area(p));
            _area->rivela_tutto();
            _fase.emplace(Contesto::AREA, 23, _y + 22, menu::NOTA, _palette);
            _fase->mostra(testo_della_fase(aiuti::fase_della_cronaca(p)));
            _fase->rivela_tutto();
            _tempo.mostra_tempo(int(p.tempo_frames / 60));
            _tempo.colloca_a_destra(DESTRA_X, _y);
            _livelli.mostra_livelli(p.livello[0], p.livello[1], p.livello[2]);
            _livelli.colloca_a_destra(DESTRA_X, _y + 11);
            int liv_x = DESTRA_X + 1 - _livelli.larghezza() - 4 - larghezza_testo(TestoId::TITOLO_LIVELLI);
            _liv.emplace(Contesto::HUD, liv_x, _y + 11, menu::NOTA, _palette);
            _liv->mostra(TestoId::TITOLO_LIVELLI);
            _liv->rivela_tutto();
        }

        [[nodiscard]] bool valido() const
        {
            return _valido;
        }

    private:
        const bn::sprite_palette_ptr& _palette;
        VistaTesto _nome;
        bn::optional<VistaTesto> _area;
        bn::optional<VistaTesto> _fase;
        bn::optional<VistaTesto> _liv;
        VistaNumero _tempo;
        VistaNumero _livelli;
        int _k;
        int _y;
        bool _valido = false;
    };
}

Esito pagina_salva(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette, bool istantanea)
{
    constexpr int RIGA_Y[2] = { 26, 78 };
    constexpr int FILO_Y = 66;
    constexpr int MESSAGGIO_Y = 118;
    Pagina pagina(PAGINA_SALVA, TestoId::SALVA_AIUTO_A, TestoId::MENU_INDIETRO, palette);
    menu::Striscia filo(MARGINE_X, FILO_Y, DESTRA_X - MARGINE_X + 1, palette);
    filo.rett(0, 0, DESTRA_X - MARGINE_X, 0, menu::GRIGIO);
    bn::optional<RigaSlot> righe[2];

    for(int k = 0; k < 2; ++k)
    {
        righe[k].emplace(k, RIGA_Y[k], palette);
    }

    VistaTesto messaggio(Contesto::DIALOGO, 23, MESSAGGIO_Y, menu::INCHIOSTRO, palette);
    bn::sprite_ptr cursore = menu::crea_cursore(palette);
    int voce = 0;
    bool conferma = false;
    Esito esito = Esito::INDIETRO;

    while(true)
    {
        menu::colloca(cursore, MARGINE_X, RIGA_Y[voce], 8, 8);

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa_salva");
            attendi(30);
            return Esito::INDIETRO;
        }

        attendi(1);

        if(conferma)
        {
            if(! bn::keypad::a_pressed() && ! bn::keypad::b_pressed())
            {
                continue;
            }

            conferma = false;
            messaggio.nascondi();

            if(bn::keypad::b_pressed())
            {
                audio::suona(colonna::Suono::ANNULLA);
                continue;
            }
        }
        else
        {
            if(navigazione(esito))
            {
                audio::suona(colonna::Suono::ANNULLA);
                return esito;
            }

            if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
            {
                voce = 1 - voce;
                audio::suona(colonna::Suono::CURSORE);
                continue;
            }

            if(! bn::keypad::a_pressed())
            {
                continue;
            }

            // sovrascrivere una partita chiede conferma (PROPOSTA sez. 3.6)
            if(righe[voce]->valido())
            {
                conferma = true;
                messaggio.mostra(TestoId::SALVA_SOVRASCRIVI);
                messaggio.rivela_tutto();
                audio::suona(colonna::Suono::CURSORE);
                continue;
            }
        }

        annota_posizione(esplorazione);
        bool fatto = salvataggio::salva(voce, g_game_state);
        audio::suona(fatto ? colonna::Suono::SALVA : colonna::Suono::ANNULLA);
        righe[voce]->aggiorna();
        messaggio.mostra(fatto ? TestoId::PAUSA_SALVATO : TestoId::PAUSA_NON_SALVATO);
        messaggio.rivela_tutto();
        attendi(FRAME_MESSAGGIO);
        messaggio.nascondi();
    }
}

}

namespace gubbio
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using namespace menu;

    // tutte le sei pagine sono costruite (MDI, MMA, MBI, MOP e Salva); la funzione resta per le prossime
    constexpr bool pagina_pronta(int p)
    {
        return p >= 0 && p < PAGINE;
    }

    // ------------------------------------------------------------------ la pausa (mockup 01)
    constexpr int COMPAGNO_X0 = 12;
    constexpr int COMPAGNO_PASSO = 45;
    constexpr int VOCI_X = 184;
    constexpr int VOCI_Y = 13;
    constexpr int VOCI_PASSO = 12;
    constexpr int CURSORE_X = 173;

    // Un compagno nel riquadro della pausa: ritratto, nome, «Liv. 4», le barre di PV e Fervore come li avra'
    // alla prossima battaglia (i PV tolti dai miasmi della gola, il Fervore iniziale, piu' alto coi Ceri).
    class Compagno
    {
    public:
        Compagno(int e, const bn::sprite_palette_ptr& palette) :
            _x(COMPAGNO_X0 + GUBBIO_VOCE(POSTO_IN_FILA, e) * COMPAGNO_PASSO),
            _ritratto(crea_ritratto(e, _x + 4, 12)),
            _nome(Contesto::HUD, _x, 45, menu::INCHIOSTRO, palette),
            _liv(Contesto::HUD, _x, 55, menu::INCHIOSTRO, palette),
            _livello(0, 55, menu::INCHIOSTRO, palette),
            _pv(Contesto::HUD, _x, 65, menu::NOTA, palette),
            _fe(Contesto::HUD, _x, 75, menu::NOTA, palette),
            _barre(_x + 14, 68, 32, palette),
            _barre_fe(_x + 14, 78, 32, palette)
        {
            Forze f = forze(g_game_state, e);
            int livello = f.livello;
            _nome.mostra(GUBBIO_VOCE(NOMI_COMPAGNI, e));
            _liv.mostra(TestoId::TITOLO_LIVELLI);
            _pv.mostra(TestoId::MENU_PV);
            _fe.mostra(TestoId::MENU_FE);

            for(VistaTesto* v : { &_nome, &_liv, &_pv, &_fe })
            {
                v->rivela_tutto();
            }

            _livello.mostra(livello);
            _livello.colloca(_x + larghezza_testo(TestoId::TITOLO_LIVELLI) + 4, 55);
            menu::disegna_barra(_barre, 0, 0, 26, f.pv, f.al_livello.pv, menu::VERDE);
            menu::disegna_barra(_barre_fe, 0, 0, 26, f.fervore, f.al_livello.fervore, menu::ORO);
        }

    private:
        int _x;
        bn::sprite_ptr _ritratto;
        VistaTesto _nome;
        VistaTesto _liv;
        VistaNumero _livello;
        VistaTesto _pv;
        VistaTesto _fe;
        menu::Striscia _barre;
        menu::Striscia _barre_fe;
    };

    // La schermata della pausa. Ritorna la pagina da aprire, o -1 per tornare al gioco.
    int schermata_pausa(int voce, const bn::sprite_palette_ptr& palette, bool istantanea)
    {
        const GameState& p = g_game_state;
        Riquadri riquadri;
        riquadri.cornice(0, 0, 20, 12);
        riquadri.cornice(160, 0, 10, 12);
        riquadri.cornice(0, 96, 30, 8);    // tocca i due riquadri in alto: niente fessura sulla scena
        int larghezza = larghezza_testo(TestoId::ETICHETTA_OBIETTIVO);
        int colonne = colonne_cartiglio(larghezza);
        riquadri.cartiglio(8, 96, colonne);
        bn::optional<Compagno> compagni[3];
        uint8_t gruppo = storia::gruppo(p, -1);

        for(int e = 0; e < 3; ++e)
        {
            if((gruppo >> e) & 1)
            {
                compagni[e].emplace(e, palette);
            }
        }

        bn::optional<VistaTesto> voci[PAGINE];

        for(int k = 0; k < PAGINE; ++k)
        {
            voci[k].emplace(Contesto::HUD, VOCI_X, VOCI_Y + k * VOCI_PASSO,
                            pagina_pronta(k) ? menu::INCHIOSTRO : menu::SPENTO, palette);
            voci[k]->mostra(VOCI[k]);
            voci[k]->rivela_tutto();
        }

        VistaTesto etichetta(Contesto::HUD, 8 + (colonne * 8 - larghezza) / 2, 100, menu::CHIARO, palette);
        etichetta.mostra(TestoId::ETICHETTA_OBIETTIVO);
        etichetta.rivela_tutto();
        bool con_obiettivo = storia::area_dell_obiettivo(p) >= 0;
        TestoId obiettivo = con_obiettivo ? storia::OBIETTIVO[p.obiettivo].testo : TestoId::PROMEMORIA_NESSUNO;
        VistaTesto testo_obiettivo(Contesto::DIALOGO, MARGINE_X, 116, menu::INCHIOSTRO, palette);
        testo_obiettivo.mostra(obiettivo);
        testo_obiettivo.rivela_tutto();
        // sotto l'obiettivo, area e fase in grigio; se l'obiettivo va su due righe, restano solo nel Salva
        int righe = testo::dati(obiettivo).righe;
        TestoId area = testo_dell_area(p);
        VistaTesto luogo(Contesto::AREA, MARGINE_X, 127, menu::NOTA, palette);
        VistaTesto fase(Contesto::AREA, MARGINE_X + larghezza_testo(area) + 8, 127, menu::NOTA, palette);

        if(righe == 1)
        {
            luogo.mostra(area);
            fase.mostra(testo_della_fase(aiuti::fase_della_cronaca(p)));
            luogo.rivela_tutto();
            fase.rivela_tutto();
        }

        AiutoTasti aiuto(TestoId::MENU_AIUTO_A, TestoId::MENU_AIUTO_B, MARGINE_X, 140, palette);
        VistaNumero tempo(0, 140, menu::NOTA, palette);
        tempo.mostra_tempo(int(p.tempo_frames / 60));
        tempo.colloca_a_destra(DESTRA_X, 140);
        VistaTesto tempo_t(Contesto::HUD, DESTRA_X + 1 - tempo.larghezza() - 4 -
                           larghezza_testo(TestoId::DOVE_ERAVAMO_TEMPO), 140, menu::NOTA, palette);
        tempo_t.mostra(TestoId::DOVE_ERAVAMO_TEMPO);
        tempo_t.rivela_tutto();
        bn::sprite_ptr cursore = menu::crea_cursore(palette);

        while(true)
        {
            menu::colloca(cursore, CURSORE_X, VOCI_Y + 1 + voce * VOCI_PASSO, 8, 8);

            if(istantanea)
            {
                attendi(30);
                BN_LOG("Istantanea pausa");
                attendi(30);
                return -1;
            }

            attendi(1);

            if(bn::keypad::start_pressed() || bn::keypad::b_pressed())
            {
                audio::suona(colonna::Suono::ANNULLA);
                return -1;
            }

            if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
            {
                voce = (voce + (bn::keypad::down_pressed() ? 1 : PAGINE - 1)) % PAGINE;
                audio::suona(colonna::Suono::CURSORE);
            }
            else if(bn::keypad::a_pressed())
            {
                if(pagina_pronta(voce))
                {
                    audio::suona(colonna::Suono::CONFERMA);
                    return voce;
                }

                audio::suona(colonna::Suono::ANNULLA);
            }
        }
    }

    Esito apri_pagina(int p, Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette, bool istantanea)
    {
        switch(p)
        {
            case PAGINA_SALVA:
                return pagina_salva(esplorazione, palette, istantanea);

            case PAGINA_DIARIO:
                return pagina_diario(palette, istantanea);

            case PAGINA_MAPPA:
                return pagina_mappa(palette, istantanea);

            case PAGINA_BISACCIA:
                return pagina_bisaccia(palette, istantanea);

            case PAGINA_COMPAGNI:
                return pagina_compagni(palette, istantanea);

            case PAGINA_OPZIONI:
                return pagina_opzioni(palette, istantanea);

            default:
                return Esito::INDIETRO;
        }
    }

    // L e R saltano le pagine non ancora costruite
    int accanto(int p, int passo)
    {
        for(int k = 0; k < PAGINE; ++k)
        {
            p = (p + passo + PAGINE) % PAGINE;

            if(pagina_pronta(p))
            {
                return p;
            }
        }

        return p;
    }
}

void partita_d_esempio(GameState& p)
{
    using storia::Bandiera;
    p = GameState{};
    p.area = uint8_t(mondo::AreaId::PIAZZA_GRANDE);
    p.tempo_frames = uint32_t((60 + 42) * 60 * 60);
    constexpr int LIVELLI[3] = { 4, 4, 3 };

    for(int e = 0; e < 3; ++e)
    {
        p.livello[e] = uint8_t(LIVELLI[e]);
        p.esperienza[e] = uint16_t(progressione::ESPERIENZA_PER_LIVELLO[LIVELLI[e] - 1] + 30);
    }

    for(Bandiera b : { Bandiera::ULTIMATUM_RICEVUTO, Bandiera::GIORGIO_NEL_GRUPPO, Bandiera::ANTONIO_NEL_GRUPPO,
                       Bandiera::CITTA_IN_DIGIUNO })
    {
        storia::accendi_una(p, int(b));
    }

    for(int q = 0; q < storia::QUEST; ++q)
    {
        storia::accendi_una(p, int(storia::QUEST_GIOCO[q].presa));
    }

    // due blocchi di ferro su tre (Q-SM01)
    storia::accendi_una(p, int(storia::QUEST_GIOCO[0].primo_pezzo));
    storia::accendi_una(p, int(storia::QUEST_GIOCO[0].primo_pezzo) + 1);
    // le aree viste del mockup 03: la citta' dentro le mura e il Teatro, non ancora il Duomo, il monte e la gola
    for(mondo::AreaId a : { mondo::AreaId::PIAZZA_GRANDE, mondo::AreaId::VIA_DEI_CONSOLI, mondo::AreaId::LARGO_BARGELLO,
                            mondo::AreaId::SAN_MARTINO, mondo::AreaId::TEATRO_ROMANO, mondo::AreaId::PIAZZA_QUARANTA_MARTIRI,
                            mondo::AreaId::VIA_XX_SETTEMBRE, mondo::AreaId::SANT_ANDREA, mondo::AreaId::SAN_PIETRO,
                            mondo::AreaId::SANT_AGOSTINO })
    {
        storia::segna_area_vista(p, int(a));
    }

    // un indizio sul falso pellegrino, e i viveri del mockup 04: 2 Crescia, 1 Biscotto
    storia::accendi_una(p, int(storia::INDIZIO[0].bandiera));
    p.oggetti[int(battaglia::OggettoId::CRESCIA)] = 2;
    p.oggetti[int(battaglia::OggettoId::BISCOTTI)] = 1;
    constexpr int SALITA = 3;
    static_assert(GUBBIO_VOCE(storia::OBIETTIVO, SALITA).testo == testo::TestoId::C_A1_05_13,
                  "l'obiettivo d'esempio e' «Sali al Monte Ingino passando dal Duomo.»");
    p.obiettivo = uint8_t(SALITA);
    p.ferite[0] = 40;
}

void pausa(Esplorazione& esplorazione, const bn::sprite_palette_ptr&, bool istantanea)
{
    bn::sprite_palette_ptr palette = menu::crea_palette();
    esplorazione.nascondi_etichetta();
    esplorazione.scurisci(true);
    int voce = 0;

    while(true)
    {
        int p = schermata_pausa(voce, palette, istantanea);

        if(istantanea)
        {
            // le istantanee: la pausa e poi ogni pagina costruita
            for(int k = 0; k < PAGINE; ++k)
            {
                if(pagina_pronta(k))
                {
                    attendi(1);
                    apri_pagina(k, esplorazione, palette, true);
                }
            }

            break;
        }

        if(p < 0)
        {
            break;
        }

        // fra una schermata e l'altra un frame: Butano libera davvero gli sprite e i tile di quella che se ne
        // va, prima che la nuova ci disegni (senza, gli ultimi sprite della pagina restavano vuoti)
        attendi(1);
        voce = p;
        Esito esito = apri_pagina(p, esplorazione, palette, false);

        while(esito == Esito::SINISTRA || esito == Esito::DESTRA)
        {
            attendi(1);
            voce = accanto(voce, esito == Esito::DESTRA ? 1 : -1);
            esito = apri_pagina(voce, esplorazione, palette, false);
        }

        attendi(1);

        if(esito == Esito::CHIUDI)
        {
            break;
        }
    }

    esplorazione.scurisci(false);
    attendi(1);
}

}
