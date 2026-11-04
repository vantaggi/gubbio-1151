#include "titolo.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_regular_bg_items_logo.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sram.h"
#include "bn_string_view.h"
#include "bn_vector.h"

#include "aiuti.h"
#include "audio.h"
#include "esplorazione.h"
#include "game_state.h"
#include "mondo.h"
#include "progressione.h"
#include "save_data.h"
#include "storia_logica.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using salvataggio::StatoSlot;

    constexpr int INCHIOSTRO_CHIARO = 2;
    constexpr int FRAME_MESSAGGIO = 60;

    // il record vuoto della prova del salvataggio: in EWRAM, non sullo stack
    BN_DATA_EWRAM_BSS salvataggio::SaveData s_vuota;

    // MAI: lo stato di ogni slot valido, per l'anteprima del titolo
    BN_DATA_EWRAM_BSS GameState s_anteprima[salvataggio::SLOT];

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

    // L'anteprima di uno slot sotto la voce «Continua» (mockup 10): area e livelli, fase e tempo di gioco.
    constexpr int ANTEPRIMA_X = 24;
    constexpr int ANTEPRIMA_Y = 110;
    constexpr int ANTEPRIMA_PASSO = 12;
    constexpr int ANTEPRIMA_LIV_X = 140;
    constexpr int ANTEPRIMA_NUMERI_X = 158;

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    TestoId testo_dello_stato(StatoSlot s)
    {
        return s == StatoSlot::VUOTO ? TestoId::SLOT_VUOTO :
               (s == StatoSlot::ALTRA_VERSIONE ? TestoId::SLOT_ALTRA_VERSIONE : TestoId::SLOT_CORROTTO);
    }

    // Uno stato di prova riconoscibile: tests/test_save_system.py ritrova questi numeri nel .sav.
    GameState stato_di_prova(int n)
    {
        GameState s = {};
        s.frames = uint32_t(1000 * n);
        s.tempo_frames = uint32_t(3600 * n + 7);
        s.x = int16_t(100 + n);
        s.y = int16_t(200 + n);
        s.area = uint8_t(n);

        for(int e = 0; e < 3; ++e)
        {
            s.esperienza[e] = uint16_t(50 * n + e);
            s.livello[e] = uint8_t(n);
        }

        s.oggetti[0] = uint8_t(n);
        s.scontri_vinti[0] = uint8_t(n);
        // v4 (MOB): i campi nuovi, riconoscibili anche loro
        s.obiettivo = uint8_t(n);
        s.aree_viste[0] = uint8_t(n);
        s.denari = uint16_t(10 * n);
        return s;
    }
}

int titolo(const bn::sprite_palette_ptr& palette_testo, bool istantanea)
{
    // la mappa 256x256 ha l'angolo in (-8, -48): (12, 80) mette il logo a 4 pixel dal bordo sinistro e a 32 dall'alto
    bn::regular_bg_ptr logo = bn::regular_bg_items::logo.create_bg(128 - 120 + 4, 128 - 80 + 32);
    VistaTesto voce(Contesto::DIALOGO, 24, 96, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto nota(Contesto::DIALOGO, 24, 112, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto aiuto(Contesto::DIALOGO, 8, 140, INCHIOSTRO_CHIARO, palette_testo);
    constexpr TestoId VOCI[3] = { TestoId::TITOLO_NUOVA, TestoId::TITOLO_SLOT_1, TestoId::TITOLO_SLOT_2 };
    StatoSlot stati[2] = { salvataggio::stato(0), salvataggio::stato(1) };
    VistaTesto anteprima_area(Contesto::AREA, ANTEPRIMA_X, ANTEPRIMA_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto anteprima_fase(Contesto::AREA, ANTEPRIMA_X, ANTEPRIMA_Y + ANTEPRIMA_PASSO, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto anteprima_liv(Contesto::HUD, ANTEPRIMA_LIV_X, ANTEPRIMA_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaNumero livelli(ANTEPRIMA_NUMERI_X, ANTEPRIMA_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaNumero tempo(ANTEPRIMA_NUMERI_X, ANTEPRIMA_Y + ANTEPRIMA_PASSO, INCHIOSTRO_CHIARO, palette_testo);

    for(int k = 0; k < salvataggio::SLOT; ++k)
    {
        if(stati[k] == StatoSlot::VALIDO && salvataggio::carica(k, s_anteprima[k]))
        {
            storia::dopo_il_caricamento(s_anteprima[k]);
        }
        else if(stati[k] == StatoSlot::VALIDO)
        {
            stati[k] = StatoSlot::CORROTTO;
        }
    }

    // il titolo ha il suo brano: il Campanone apre, poi il Tema di Gubbio
    audio::brano(colonna::BRANO_TITOLO);

    // si parte da "Continua" se c'e' un salvataggio valido, se no da "Nuova partita"
    int scelta = stati[0] == StatoSlot::VALIDO ? 1 : (stati[1] == StatoSlot::VALIDO ? 2 : 0);
    aiuto.mostra(TestoId::TITOLO_AIUTO);
    aiuto.rivela_tutto();

    while(true)
    {
        voce.mostra(VOCI[scelta]);
        voce.rivela_tutto();

        bool anteprima = scelta > 0 && stati[scelta - 1] == StatoSlot::VALIDO;

        if(scelta > 0 && ! anteprima)
        {
            nota.mostra(testo_dello_stato(stati[scelta - 1]));
            nota.rivela_tutto();
        }
        else
        {
            nota.nascondi();
        }

        if(anteprima)
        {
            const GameState& p = s_anteprima[scelta - 1];
            anteprima_area.mostra(testo_dell_area(p));
            anteprima_area.rivela_tutto();
            anteprima_fase.mostra(testo_della_fase(aiuti::fase_della_cronaca(p)));
            anteprima_fase.rivela_tutto();
            anteprima_liv.mostra(TestoId::TITOLO_LIVELLI);
            anteprima_liv.rivela_tutto();
            livelli.mostra_livelli(p.livello[0], p.livello[1], p.livello[2]);
            livelli.colloca(ANTEPRIMA_NUMERI_X, ANTEPRIMA_Y);
            tempo.mostra_tempo(int(p.tempo_frames / 60));
            tempo.colloca(ANTEPRIMA_NUMERI_X, ANTEPRIMA_Y + ANTEPRIMA_PASSO);
        }
        else
        {
            anteprima_area.nascondi();
            anteprima_fase.nascondi();
            anteprima_liv.nascondi();
            livelli.nascondi();
            tempo.nascondi();
        }

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea titolo");
            attendi(30);
            return -1;
        }

        while(! bn::keypad::up_pressed() && ! bn::keypad::down_pressed() && ! bn::keypad::a_pressed())
        {
            attendi(1);
        }

        if(bn::keypad::a_pressed())
        {
            if(scelta == 0)
            {
                audio::suona(colonna::Suono::CONFERMA);
                attendi(1);
                return -1;
            }

            if(stati[scelta - 1] == StatoSlot::VALIDO && salvataggio::carica(scelta - 1, g_game_state))
            {
                audio::suona(colonna::Suono::CONFERMA);
                attendi(1);
                return scelta - 1;
            }

            // uno slot vuoto o rovinato non si apre
            audio::suona(colonna::Suono::ANNULLA);
        }
        else
        {
            scelta = (scelta + (bn::keypad::down_pressed() ? 1 : 2)) % 3;
            audio::suona(colonna::Suono::CURSORE);
        }

        attendi(1);
    }
}

void annota_posizione(const Esplorazione& esplorazione)
{
    const mondo::Esploratore& e = esplorazione.esploratore();
    g_game_state.area = uint8_t(e.area);
    g_game_state.x = int16_t(e.x);
    g_game_state.y = int16_t(e.y);
}

void dove_eravamo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea)
{
    // «Dove eravamo» (MAI, mockup 08): dopo «Continua», una volta, sullo sfondo scurito come nei dialoghi
    constexpr int X = 8;
    constexpr int TITOLO_Y = 92;
    constexpr int LUOGO_Y = 106;
    constexpr int FASE_X = 120;
    constexpr int OBIETTIVO_Y = 120;
    constexpr int CONTI_Y = 144;
    constexpr int INCARICHI_N_X = 80;
    constexpr int TEMPO_X = 160;
    constexpr int TEMPO_N_X = 192;
    const GameState& p = g_game_state;
    esplorazione.nascondi_etichetta();
    bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.65));
    VistaTesto titolo_r(Contesto::HUD, X, TITOLO_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto luogo(Contesto::AREA, X, LUOGO_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto fase(Contesto::AREA, FASE_X, LUOGO_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto obiettivo(Contesto::DIALOGO, X, OBIETTIVO_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto incarichi(Contesto::HUD, X, CONTI_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaNumero incarichi_n(INCARICHI_N_X, CONTI_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto tempo(Contesto::HUD, TEMPO_X, CONTI_Y, INCHIOSTRO_CHIARO, palette_testo);
    VistaNumero tempo_n(TEMPO_N_X, CONTI_Y, INCHIOSTRO_CHIARO, palette_testo);
    titolo_r.mostra(TestoId::DOVE_ERAVAMO);
    luogo.mostra(testo_dell_area(p));
    fase.mostra(testo_della_fase(aiuti::fase_della_cronaca(p)));
    obiettivo.mostra(storia::area_dell_obiettivo(p) >= 0 ? storia::OBIETTIVO[p.obiettivo].testo : TestoId::PROMEMORIA_NESSUNO);
    incarichi.mostra(TestoId::DOVE_ERAVAMO_INCARICHI);
    tempo.mostra(TestoId::DOVE_ERAVAMO_TEMPO);

    for(VistaTesto* v : { &titolo_r, &luogo, &fase, &obiettivo, &incarichi, &tempo })
    {
        v->rivela_tutto();
    }

    incarichi_n.mostra(aiuti::incarichi_aperti(p));
    incarichi_n.colloca(INCARICHI_N_X, CONTI_Y);
    tempo_n.mostra_tempo(int(p.tempo_frames / 60));
    tempo_n.colloca(TEMPO_N_X, CONTI_Y);
    attendi(1);

    if(istantanea)
    {
        attendi(30);
        BN_LOG("Istantanea dove_eravamo");
        attendi(30);
    }
    else
    {
        while(! bn::keypad::a_pressed() && ! bn::keypad::b_pressed() && ! bn::keypad::start_pressed())
        {
            attendi(1);
        }
    }

    bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    attendi(1);
}

void pausa(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo, bool istantanea)
{
    esplorazione.nascondi_etichetta();
    bn::bg_palettes::set_fade(bn::color(0, 0, 0), bn::fixed(0.65));
    VistaTesto titolo_pausa(Contesto::DIALOGO, 24, 32, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto voce(Contesto::DIALOGO, 32, 64, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto nota(Contesto::DIALOGO, 32, 84, INCHIOSTRO_CHIARO, palette_testo);
    VistaTesto aiuto(Contesto::DIALOGO, 8, 128, INCHIOSTRO_CHIARO, palette_testo);
    constexpr TestoId VOCI[3] = { TestoId::PAUSA_RIPRENDI, TestoId::PAUSA_SALVA_1, TestoId::PAUSA_SALVA_2 };
    titolo_pausa.mostra(TestoId::PAUSA_TITOLO);
    titolo_pausa.rivela_tutto();
    aiuto.mostra(TestoId::PAUSA_AIUTO);
    aiuto.rivela_tutto();
    int scelta = 0;
    attendi(1);

    while(true)
    {
        voce.mostra(VOCI[scelta]);
        voce.rivela_tutto();

        if(istantanea)
        {
            attendi(30);
            BN_LOG("Istantanea pausa");
            attendi(30);
            break;
        }

        while(! bn::keypad::up_pressed() && ! bn::keypad::down_pressed() && ! bn::keypad::a_pressed() &&
              ! bn::keypad::start_pressed())
        {
            attendi(1);
        }

        if(bn::keypad::start_pressed() || (bn::keypad::a_pressed() && scelta == 0))
        {
            audio::suona(bn::keypad::start_pressed() ? colonna::Suono::ANNULLA : colonna::Suono::CONFERMA);
            break;
        }

        if(bn::keypad::a_pressed())
        {
            annota_posizione(esplorazione);
            bool fatto = salvataggio::salva(scelta - 1, g_game_state);
            audio::suona(fatto ? colonna::Suono::SALVA : colonna::Suono::ANNULLA);
            nota.mostra(fatto ? TestoId::PAUSA_SALVATO : TestoId::PAUSA_NON_SALVATO);
            nota.rivela_tutto();
            attendi(FRAME_MESSAGGIO);
            nota.nascondi();
        }
        else
        {
            scelta = (scelta + (bn::keypad::down_pressed() ? 1 : 2)) % 3;
            audio::suona(colonna::Suono::CURSORE);
        }

        attendi(1);
    }

    bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    attendi(1);
}

namespace
{
    // La partita di prova: nuova, con le scene fino a 'ultima' (codice del copione) chiuse come nel giro della
    // storia (storia::chiudi_scena), il giocatore allo spawn dell'area, i livelli e il tempo dati.
    GameState partita_fino_a(const char* ultima, mondo::AreaId area, int spawn, int livello, uint32_t secondi)
    {
        GameState p = {};
        progressione::partita_nuova(p);

        for(int k = 0; k < storia::SCENE; ++k)
        {
            storia::chiudi_scena(p, k);

            if(bn::string_view(GUBBIO_VOCE(storia::SCENA, k).codice) == bn::string_view(ultima))
            {
                break;
            }
        }

        mondo::Esploratore e;
        mondo::colloca(e, area, spawn);
        p.area = uint8_t(e.area);
        p.x = int16_t(e.x);
        p.y = int16_t(e.y);
        p.tempo_frames = secondi * 60;

        for(int eroe = 0; eroe < 3; ++eroe)
        {
            p.livello[eroe] = uint8_t(livello - (eroe == 2 && livello > 1 ? 1 : 0));
        }

        storia::dopo_il_caricamento(p);
        return p;
    }
}

void prepara_slot_di_prova()
{
    // slot 1: il digiuno, in Piazza Grande dopo A1-05 (come i mockup 08 e 10: livelli 4 4 3, 1:42)
    bool uno = salvataggio::salva(0, partita_fino_a("A1-05", mondo::AreaId::PIAZZA_GRANDE, 0, 4, 6120));
    // slot 2: dopo B-03, all'ingresso del Condotto, coi livelli d'inizio e le ferite al massimo (si parte con
    // 1 PV, battaglia.h): il duello con Corrado si perde e si vede il Riprova
    GameState condotto = partita_fino_a("B-03", mondo::AreaId::CONDOTTO, 0, 1, 9000);

    for(uint8_t& f : condotto.ferite)
    {
        f = 255;
    }

    bool due = salvataggio::salva(1, condotto);
    BN_LOG("Slot di prova: ", uno ? "1 OK " : "1 FALLITO ", due ? "2 OK" : "2 FALLITO");
}

void prova_salvataggio()
{
    using namespace salvataggio;
    int riuscite = 0;
    int fallite = 0;

    auto esito = [&](const char* nome, bool ok) {
        BN_LOG("SALVATAGGIO ", nome, ok ? " OK" : " FALLITA");
        riuscite += ok ? 1 : 0;
        fallite += ok ? 0 : 1;
    };

    // la SRAM pulita: i due slot vuoti
    s_vuota = SaveData{};

    for(int b = 0; b < SLOT * BANCHE; ++b)
    {
        bn::sram::write_offset(s_vuota, b * int(sizeof(SaveData)));
    }

    esito("vuoto", stato(0) == StatoSlot::VUOTO && stato(1) == StatoSlot::VUOTO);

    // salva, ricarica, confronta byte per byte
    GameState a = stato_di_prova(1);
    GameState b = stato_di_prova(2);
    GameState letto = {};
    esito("salva", salva(0, a));
    esito("ricarica uguale", carica(0, letto) && stessi_byte(letto, a));
    esito("ping-pong", salva(0, b) && carica(0, letto) && stessi_byte(letto, b));

    // negativa 1: la banca piu' recente corrotta (b sta nella banca 1): si ricarica a, intatto
    bn::sram::write_offset(uint8_t(0x5A), 1 * int(sizeof(SaveData)) + 16 + 3);
    esito("banca corrotta", stato(0) == StatoSlot::VALIDO && carica(0, letto) && stessi_byte(letto, a));

    // negativa 2: corrotte tutte e due: lo slot e' CORROTTO e carica non tocca lo stato
    bn::sram::write_offset(uint8_t(0x5A), 0 * int(sizeof(SaveData)) + 16 + 3);
    GameState intatto = stato_di_prova(7);
    letto = intatto;
    esito("entrambe corrotte", stato(0) == StatoSlot::CORROTTO && ! carica(0, letto) && stessi_byte(letto, intatto));

    // dopo una corruzione si torna a salvare: la scrittura va su una banca e lo slot torna valido
    esito("risalva", salva(0, a) && carica(0, letto) && stessi_byte(letto, a));

    // v4 (MOB): un salvataggio v3 nello slot 1 si carica aggiornato. I 59 byte comuni restano, il residuo
    // nei byte che erano riservati non diventa un obiettivo; la banca 1 vuota
    s_vuota = SaveData{};
    bn::sram::write_offset(s_vuota, (1 * BANCHE + 1) * int(sizeof(SaveData)));
    s_vuota = componi_v3(stato_di_prova(5), 1, 0x77);
    bn::sram::write_offset(s_vuota, (1 * BANCHE + 0) * int(sizeof(SaveData)));
    GameState atteso = stato_di_prova(5);
    atteso.obiettivo = NESSUN_OBIETTIVO;
    atteso.aree_viste[0] = 0;
    atteso.denari = 0;
    esito("v3 aggiornato", stato(1) == StatoSlot::VALIDO && carica(1, letto) && stessi_byte(letto, atteso));

    // gli slot finali per tests/test_save_system.py: slot 0 = stato 3 (due banche, l'ultima e' 3),
    // slot 1 = stato 4 (nella banca 1: nella banca 0 resta il record v3, piu' vecchio)
    esito("slot finali", salva(0, stato_di_prova(3)) && salva(1, stato_di_prova(4)) &&
          carica(0, letto) && stessi_byte(letto, stato_di_prova(3)) && carica(1, letto) &&
          stessi_byte(letto, stato_di_prova(4)));

    BN_LOG("Salvataggio: ", riuscite, " prove riuscite, ", fallite, " fallite");
}

}
