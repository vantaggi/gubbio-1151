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
#include "bn_vector.h"

#include "esplorazione.h"
#include "game_state.h"
#include "save_data.h"
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

    // si parte da "Continua" se c'e' un salvataggio valido, se no da "Nuova partita"
    int scelta = stati[0] == StatoSlot::VALIDO ? 1 : (stati[1] == StatoSlot::VALIDO ? 2 : 0);
    aiuto.mostra(TestoId::TITOLO_AIUTO);
    aiuto.rivela_tutto();

    while(true)
    {
        voce.mostra(VOCI[scelta]);
        voce.rivela_tutto();

        if(scelta > 0 && stati[scelta - 1] != StatoSlot::VALIDO)
        {
            nota.mostra(testo_dello_stato(stati[scelta - 1]));
            nota.rivela_tutto();
        }
        else
        {
            nota.nascondi();
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
                attendi(1);
                return -1;
            }

            if(stati[scelta - 1] == StatoSlot::VALIDO && salvataggio::carica(scelta - 1, g_game_state))
            {
                attendi(1);
                return scelta - 1;
            }
        }
        else
        {
            scelta = (scelta + (bn::keypad::down_pressed() ? 1 : 2)) % 3;
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
            break;
        }

        if(bn::keypad::a_pressed())
        {
            annota_posizione(esplorazione);
            bool fatto = salvataggio::salva(scelta - 1, g_game_state);
            nota.mostra(fatto ? TestoId::PAUSA_SALVATO : TestoId::PAUSA_NON_SALVATO);
            nota.rivela_tutto();
            attendi(FRAME_MESSAGGIO);
            nota.nascondi();
        }
        else
        {
            scelta = (scelta + (bn::keypad::down_pressed() ? 1 : 2)) % 3;
        }

        attendi(1);
    }

    bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    attendi(1);
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
