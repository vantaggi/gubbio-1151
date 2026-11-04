#include "titolo.h"

#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_sprite_items_ritratto_antonio.h"
#include "bn_sprite_items_ritratto_giorgio.h"
#include "bn_sprite_items_ritratto_ubaldo.h"

#include "aiuti.h"
#include "audio.h"
#include "battaglia_dati.h"
#include "esplorazione.h"
#include "game_state.h"
#include "progressione.h"
#include "save_data.h"
#include "storia_logica.h"
#include "vista_menu.h"
#include "vista_testo.h"

// Il menu di pausa (MPA, menu/PROPOSTA.md sez. 3.1; mockup menu/mockup/01_pausa.png e 06_salva.png). Start apre
// la pausa sopra la scena scurita: in alto a sinistra i tre compagni (ritratto, nome, livello, PV e Fervore), a
// destra le sei voci, in basso l'obiettivo della cronaca nel riquadro del dialogo. A apre la pagina della voce;
// nelle pagine L e R passano alla pagina accanto, B torna alla pausa; B o Start dalla pausa tornano al gioco.
namespace gubbio
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using salvataggio::StatoSlot;

    constexpr int PAGINE = 6;
    constexpr int PAGINA_SALVA = 4;
    constexpr TestoId VOCI[PAGINE] = { TestoId::MENU_DIARIO, TestoId::MENU_MAPPA, TestoId::MENU_BISACCIA,
                                       TestoId::MENU_COMPAGNI, TestoId::MENU_SALVA, TestoId::MENU_OPZIONI };
    constexpr int FRAME_MESSAGGIO = 60;

    // le pagine gia' costruite; le altre arrivano coi loro pezzi (MDI, MMA, MBI, MOP)
    constexpr bool pagina_pronta(int p)
    {
        return p == PAGINA_SALVA;
    }

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    enum class Esito : uint8_t
    {
        INDIETRO,       // B: alla pausa
        CHIUDI,         // Start: al gioco
        SINISTRA,       // L: alla pagina prima
        DESTRA,         // R: alla pagina dopo
    };

    // Aspetta un tasto fra quelli che interessano a una pagina; true se e' uno di quelli di navigazione (e
    // allora 'esito' dice quale). Su, giu' e A restano alla pagina.
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

    // ------------------------------------------------------------------ lo schema comune delle pagine
    // Riquadro pieno, cartiglio col nome in alto a sinistra, in fondo il filo, gli aiuti dei tasti a sinistra e
    // le sei tessere delle pagine a destra fra L e R (mockup: pagina() e piede()).
    constexpr int PIEDE_Y = 141;
    constexpr int MARGINE_X = 12;
    constexpr int DESTRA_X = 227;
    // il cartiglio sta sulla griglia dei tile (Riquadri): sopra il bordo alto, il nome a 4 px dall'alto
    constexpr int CARTIGLIO_Y = 0;

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

    // Gli aiuti dei tasti, «A: apri» e «B: indietro» a 12 px uno dall'altro (il font non tiene gli spazi doppi).
    constexpr int AIUTI_STACCO = 12;

    class AiutoTasti
    {
    public:
        AiutoTasti(TestoId a, TestoId b, int x, int y, const bn::sprite_palette_ptr& palette) :
            _a(Contesto::HUD, x, y, menu::SPENTO, palette),
            _b(testo::dati(b).contesto, x + larghezza_testo(a) + AIUTI_STACCO, y, menu::SPENTO, palette)
        {
            _a.mostra(a);
            _b.mostra(b);
            _a.rivela_tutto();
            _b.rivela_tutto();
        }

    private:
        VistaTesto _a;
        VistaTesto _b;
    };

    class Pagina
    {
    public:
        Pagina(int indice, TestoId aiuto_a, TestoId aiuto_b, const bn::sprite_palette_ptr& palette) :
            _titolo(Contesto::HUD, 8 + (colonne_titolo(VOCI[indice]) * 8 - larghezza_testo(VOCI[indice])) / 2,
                    CARTIGLIO_Y + 4, menu::CHIARO, palette),
            _aiuto(aiuto_a, aiuto_b, MARGINE_X, PIEDE_Y, palette),
            _l(Contesto::HUD, l_x(), PIEDE_Y, menu::SPENTO, palette),
            _r(Contesto::HUD, r_x(), PIEDE_Y, menu::SPENTO, palette),
            _filo(MARGINE_X, PIEDE_Y - 3, DESTRA_X - MARGINE_X + 1, palette),
            _tessere(tessere_x(), PIEDE_Y + 2, 64, palette)
        {
            _riquadri.cornice(0, 0, 30, 20);
            _riquadri.cartiglio(8, CARTIGLIO_Y, colonne_titolo(VOCI[indice]));
            _titolo.mostra(VOCI[indice]);
            _r.mostra(TestoId::MENU_R);
            _l.mostra(TestoId::MENU_L);
            _filo.rett(0, 0, DESTRA_X - MARGINE_X, 0, menu::GRIGIO);
            menu::disegna_tessere(_tessere, 0, indice);

            for(VistaTesto* v : { &_titolo, &_l, &_r })
            {
                v->rivela_tutto();
            }
        }

    private:
        Riquadri _riquadri;
        VistaTesto _titolo;
        AiutoTasti _aiuto;
        VistaTesto _l;
        VistaTesto _r;
        menu::Striscia _filo;
        menu::Striscia _tessere;
    };

    // ------------------------------------------------------------------ la pagina Salva (mockup 06)
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

    // ------------------------------------------------------------------ la pausa (mockup 01)
    constexpr int COMPAGNO_X0 = 12;
    constexpr int COMPAGNO_PASSO = 45;
    constexpr int VOCI_X = 184;
    constexpr int VOCI_Y = 13;
    constexpr int VOCI_PASSO = 12;
    constexpr int CURSORE_X = 173;

    bn::sprite_ptr crea_ritratto(int e, int x, int y)
    {
        // nell'ordine di sempre: Ubaldo, Giorgio, Antonio
        bn::sprite_ptr s = e == 0 ? bn::sprite_items::ritratto_ubaldo.create_sprite(0, 0) :
                           (e == 1 ? bn::sprite_items::ritratto_giorgio.create_sprite(0, 0) :
                                     bn::sprite_items::ritratto_antonio.create_sprite(0, 0));
        menu::colloca(s, x, y, 32, 32);
        s.set_bg_priority(PRIORITA_RIQUADRI);
        return s;
    }

    // Un compagno nel riquadro della pausa: ritratto, nome, «Liv. 4», le barre di PV e Fervore come li avra'
    // alla prossima battaglia (i PV tolti dai miasmi della gola, il Fervore iniziale, piu' alto coi Ceri).
    class Compagno
    {
    public:
        Compagno(int e, const bn::sprite_palette_ptr& palette) :
            _x(COMPAGNO_X0 + e * COMPAGNO_PASSO),
            _ritratto(crea_ritratto(e, _x + 4, 12)),
            _nome(Contesto::HUD, _x, 45, menu::INCHIOSTRO, palette),
            _liv(Contesto::HUD, _x, 55, menu::INCHIOSTRO, palette),
            _livello(0, 55, menu::INCHIOSTRO, palette),
            _pv(Contesto::HUD, _x, 65, menu::NOTA, palette),
            _fe(Contesto::HUD, _x, 75, menu::NOTA, palette),
            _barre(_x + 14, 68, 32, palette),
            _barre_fe(_x + 14, 78, 32, palette)
        {
            constexpr TestoId NOMI[3] = { TestoId::PARLANTE_UBALDO, TestoId::PARLANTE_GIORGIO, TestoId::PARLANTE_ANTONIO };
            const GameState& p = g_game_state;
            int livello = p.livello[e] < 1 ? 1 : p.livello[e];
            battaglia::Statistiche s = progressione::statistiche_al_livello(battaglia::STATISTICHE_EROI[e], livello);
            int pv = s.pv - p.ferite[e] < 1 ? 1 : s.pv - p.ferite[e];
            int percento = battaglia::FERVORE_INIZIALE[e] + (storia::ceri_accesi(p) ? battaglia::FERVORE_CERI : 0);
            int fe = s.fervore * (percento > 100 ? 100 : percento) / 100;
            _nome.mostra(NOMI[e]);
            _liv.mostra(TestoId::TITOLO_LIVELLI);
            _pv.mostra(TestoId::MENU_PV);
            _fe.mostra(TestoId::MENU_FE);

            for(VistaTesto* v : { &_nome, &_liv, &_pv, &_fe })
            {
                v->rivela_tutto();
            }

            _livello.mostra(livello);
            _livello.colloca(_x + larghezza_testo(TestoId::TITOLO_LIVELLI) + 4, 55);
            menu::disegna_barra(_barre, 0, 0, 26, pv, s.pv, menu::VERDE);
            menu::disegna_barra(_barre_fe, 0, 0, 26, fe, s.fervore, menu::ORO);
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
        riquadri.cornice(0, 104, 30, 7);
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
