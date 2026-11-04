#include "titolo.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_regular_bg_items_logo.h"
#include "bn_regular_bg_items_titolo_fondo.h"
#include "bn_bg_palette_ptr.h"
#include "bn_optional.h"
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
#include "menu_pagine.h"
#include "stile/cornice.h"
#include "stile/palette.h"
#include "tabella.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using testo::Contesto;
    using testo::TestoId;
    using salvataggio::StatoSlot;

    constexpr int INCHIOSTRO_CHIARO = 2;

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

    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
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

int titolo(const bn::sprite_palette_ptr&, bool istantanea)
{
    // Il titolo (mockup 10 e 10b, animazione A7): Gubbio al crepuscolo (graphics/titolo_fondo.bmp, palette di
    // notte), il logo a x2 in alto, il sottotitolo in oro, la lista col cursore della Guida e l'aiuto sulle mura.
    // «Continua» apre lo slot giocato piu' a lungo e ne mostra l'anteprima; con due slot validi destra e sinistra
    // passano all'altro. Senza salvataggi c'e' solo «Nuova partita», gia' scelta. Il cursore lampeggia ogni mezzo
    // secondo, e con lui trema una finestra su quattro (il colore segnaposto oro 1 del fondo).
    using menu::Scritta;
    constexpr int LISTA_X = 74;
    constexpr int CURSORE_X = 62;
    constexpr int CONTINUA_Y = 66;
    constexpr int ANTEPRIMA_1_Y = 77;
    constexpr int ANTEPRIMA_2_Y = 87;
    constexpr int NUOVA_Y = 100;
    constexpr int PRIMA_Y = 80;             // 10b: «Nuova partita» da sola
    constexpr int SOTTOTITOLO_Y = 46;
    constexpr int AIUTO_Y = 149;
    constexpr int STACCO = 12;
    constexpr int LAMPO = 30;
    constexpr int ORO_ACCESO = 9;           // oro e bronzo 3, nella palette dei menu (cornice, indice 9)

    bn::regular_bg_ptr fondo = bn::regular_bg_items::titolo_fondo.create_bg(8, 48);
    fondo.set_priority(3);
    // il logo: in alto a 14 px, centrato (la tela ha il logo a y 12 e centrato su 240)
    bn::regular_bg_ptr logo = bn::regular_bg_items::logo.create_bg(8, 50);
    logo.set_priority(2);
    bn::bg_palette_ptr palette_fondo = fondo.palette();
    int candela = -1;

    for(int k = 0; k < 16; ++k)
    {
        if(palette_fondo.colors()[k] == bn::color(GUBBIO_VOCE(stile::PALETTE_GIORNO, stile::RAMPA_ORO_E_BRONZO + 1)))
        {
            candela = k;
        }
    }

    bn::sprite_palette_ptr palette = menu::crea_palette();
    Scritta sottotitolo(TestoId::TITOLO_SOTTOTITOLO, (240 - larghezza_testo(TestoId::TITOLO_SOTTOTITOLO)) / 2,
                        SOTTOTITOLO_Y, menu::ORO, palette);
    StatoSlot stati[salvataggio::SLOT] = { salvataggio::stato(0), salvataggio::stato(1) };
    int validi = 0;
    int slot = -1;

    for(int k = 0; k < salvataggio::SLOT; ++k)
    {
        if(stati[k] == StatoSlot::VALIDO && salvataggio::carica(k, s_anteprima[k]))
        {
            storia::dopo_il_caricamento(s_anteprima[k]);
            ++validi;

            if(slot < 0 || s_anteprima[k].tempo_frames > s_anteprima[slot].tempo_frames)
            {
                slot = k;
            }
        }
    }

    // il titolo ha il suo brano: il Campanone apre, poi il Tema di Gubbio
    audio::brano(colonna::BRANO_TITOLO);

    bn::sprite_ptr cursore = menu::crea_cursore(palette);
    bn::optional<VistaTesto> continua;
    bn::optional<VistaTesto> nuova;
    bn::optional<Scritta> anteprima_area;
    bn::optional<Scritta> anteprima_fase;
    bn::optional<VistaNumero> livelli;
    bn::optional<VistaNumero> tempo;
    bn::optional<Scritta> virgola_1;
    bn::optional<Scritta> virgola_2;
    bn::optional<Scritta> liv;
    bn::optional<Scritta> aiuto_a;
    bn::optional<Scritta> aiuto_b;
    bn::optional<Scritta> aiuto_c;
    int voce = validi > 0 ? 0 : 1;      // 0 Continua, 1 Nuova partita
    bool cambiata = true;
    int f = 0;

    while(true)
    {
        if(cambiata)
        {
            cambiata = false;
            continua.reset();
            nuova.reset();
            anteprima_area.reset();
            anteprima_fase.reset();
            livelli.reset();
            tempo.reset();
            virgola_1.reset();
            virgola_2.reset();
            liv.reset();

            if(validi > 0)
            {
                continua.emplace(Contesto::DIALOGO, LISTA_X, CONTINUA_Y, voce == 0 ? ORO_ACCESO : menu::GRIGIO, palette);
                continua->mostra(slot == 0 ? TestoId::TITOLO_SLOT_1 : TestoId::TITOLO_SLOT_2);
                continua->rivela_tutto();

                // «Piazza Grande, Liv. 4 4 3» e «Il digiuno, 1:42», in grigio
                const GameState& p = s_anteprima[slot];
                TestoId area = testo_dell_area(p);
                TestoId fase = testo_della_fase(aiuti::fase_della_cronaca(p));
                int x = LISTA_X;
                anteprima_area.emplace(area, x, ANTEPRIMA_1_Y, menu::GRIGIO, palette);
                x += larghezza_testo(area) + 1;
                virgola_1.emplace(TestoId::VIRGOLA, x, ANTEPRIMA_1_Y, menu::GRIGIO, palette);
                x += larghezza_testo(TestoId::VIRGOLA) + 4;
                liv.emplace(TestoId::TITOLO_LIVELLI, x, ANTEPRIMA_1_Y, menu::GRIGIO, palette);
                x += larghezza_testo(TestoId::TITOLO_LIVELLI) + 4;
                livelli.emplace(x, ANTEPRIMA_1_Y, menu::GRIGIO, palette);
                livelli->mostra_livelli(p.livello[0], p.livello[1], p.livello[2]);
                livelli->colloca(x, ANTEPRIMA_1_Y);
                x = LISTA_X;
                anteprima_fase.emplace(fase, x, ANTEPRIMA_2_Y, menu::GRIGIO, palette);
                x += larghezza_testo(fase) + 1;
                virgola_2.emplace(TestoId::VIRGOLA, x, ANTEPRIMA_2_Y, menu::GRIGIO, palette);
                x += larghezza_testo(TestoId::VIRGOLA) + 4;
                tempo.emplace(x, ANTEPRIMA_2_Y, menu::GRIGIO, palette);
                tempo->mostra_tempo(int(p.tempo_frames / 60));
                tempo->colloca(x, ANTEPRIMA_2_Y);
            }

            int nuova_y = validi > 0 ? NUOVA_Y : PRIMA_Y;
            nuova.emplace(Contesto::DIALOGO, LISTA_X, nuova_y, voce == 1 ? ORO_ACCESO : menu::GRIGIO, palette);
            nuova->mostra(TestoId::TITOLO_NUOVA);
            nuova->rivela_tutto();
            menu::colloca(cursore, CURSORE_X, voce == 0 ? CONTINUA_Y : nuova_y, 8, 8);

            // l'aiuto sulle mura, centrato: «Su e giu': scegli   A: conferma», con due slot anche «Destra: slot»
            aiuto_a.reset();
            aiuto_b.reset();
            aiuto_c.reset();
            TestoId pezzi[3] = { TestoId::TITOLO_AIUTO_SCEGLI, TestoId::TITOLO_AIUTO_SLOT, TestoId::TITOLO_AIUTO_CONFERMA };
            int quanti = validi == 0 ? 1 : (validi == 2 ? 3 : 2);

            if(validi == 0)
            {
                pezzi[0] = TestoId::TITOLO_AIUTO_COMINCIA;
            }
            else if(validi == 1)
            {
                pezzi[1] = TestoId::TITOLO_AIUTO_CONFERMA;
            }

            int largo = (quanti - 1) * STACCO;

            for(int k = 0; k < quanti; ++k)
            {
                largo += larghezza_testo(pezzi[k]);
            }

            int x = (240 - largo) / 2;
            bn::optional<Scritta>* aiuti_r[3] = { &aiuto_a, &aiuto_b, &aiuto_c };

            for(int k = 0; k < quanti; ++k)
            {
                aiuti_r[k]->emplace(pezzi[k], x, AIUTO_Y, menu::SPENTO, palette);
                x += larghezza_testo(pezzi[k]) + STACCO;
            }
        }

        // il cursore lampeggia, una finestra su quattro trema con lui
        bool acceso = (f / LAMPO) % 2 == 0;
        cursore.set_visible(acceso);

        if(candela >= 0)
        {
            palette_fondo.set_color(candela, bn::color(GUBBIO_VOCE(stile::PALETTE_GIORNO,
                                                                   stile::RAMPA_ORO_E_BRONZO + (acceso ? 2 : 1))));
        }

        if(istantanea)
        {
            cursore.set_visible(true);
            attendi(30);
            BN_LOG("Istantanea titolo");
            attendi(30);
            return -1;
        }

        attendi(1);
        ++f;

        if(bn::keypad::a_pressed())
        {
            if(voce == 1)
            {
                audio::suona(colonna::Suono::CONFERMA);
                attendi(1);
                return -1;
            }

            if(salvataggio::carica(slot, g_game_state))
            {
                audio::suona(colonna::Suono::CONFERMA);
                attendi(1);
                return slot;
            }

            audio::suona(colonna::Suono::ANNULLA);
        }
        else if(validi > 0 && (bn::keypad::up_pressed() || bn::keypad::down_pressed()))
        {
            voce = 1 - voce;
            cambiata = true;
            f = 0;
            audio::suona(colonna::Suono::CURSORE);
        }
        else if(validi == 2 && voce == 0 && (bn::keypad::left_pressed() || bn::keypad::right_pressed()))
        {
            slot = 1 - slot;
            cambiata = true;
            f = 0;
            audio::suona(colonna::Suono::CURSORE);
        }
    }
}

void annota_posizione(const Esplorazione& esplorazione)
{
    const mondo::Esploratore& e = esplorazione.esploratore();
    g_game_state.area = uint8_t(e.area);
    g_game_state.x = int16_t(e.x);
    g_game_state.y = int16_t(e.y);
}

void dove_eravamo(Esplorazione& esplorazione, const bn::sprite_palette_ptr&, bool istantanea)
{
    // «Dove eravamo» (MAI, mockup 08): dopo «Continua», una volta, nel riquadro del dialogo a vetrata col cartiglio
    // vermiglio. Una frase sola per luogo e fase («Piazza Grande. Il digiuno.»), la stella e l'obiettivo, sotto in
    // grigio gli incarichi aperti e il tempo. La scena non si scurisce: quando il riquadro sparisce non c'e' uno
    // stacco di luce. Con un obiettivo su due righe il riquadro sale di una riga.
    using menu::CHIARO;
    using menu::DESTRA_X;
    using menu::INCHIOSTRO;
    using menu::MARGINE_X;
    using menu::NOTA;
    using menu::PIEDE_Y;
    using menu::Scritta;
    constexpr int SPAZIO = 4;
    constexpr int OBIETTIVO_X = 23;
    constexpr int OBIETTIVO_MAX = DESTRA_X - OBIETTIVO_X + 1;
    const GameState& p = g_game_state;
    esplorazione.nascondi_etichetta();
    bn::sprite_palette_ptr palette = menu::crea_palette();
    bn::sprite_palette_ptr icone = menu::crea_palette_icone();
    TestoId meta = storia::area_dell_obiettivo(p) >= 0 ? storia::OBIETTIVO[p.obiettivo].testo : TestoId::PROMEMORIA_NESSUNO;
    const testo::Testo& t = testo::dati(meta);
    bool con_stella = testo::riga(testo::indice_riga(t, 0)).larghezza <= OBIETTIVO_MAX;
    int su = t.righe > 1 ? 8 : 0;
    int y0 = stile::DIALOGO_Y - su;

    Riquadri riquadri;
    riquadri.cornice(stile::DIALOGO_X, y0, stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE + su / 8);
    int largo_titolo = larghezza_testo(TestoId::DOVE_ERAVAMO);
    int colonne = colonne_cartiglio(largo_titolo);
    riquadri.cartiglio(stile::CARTIGLIO_NOME_X, y0 - 8, colonne);
    Scritta titolo_r(TestoId::DOVE_ERAVAMO, stile::CARTIGLIO_NOME_X + (colonne * 8 - largo_titolo) / 2, y0 - 4, CHIARO,
                     palette);

    // «Piazza Grande. Il digiuno.»: l'area, il punto, la fase, il punto
    TestoId area = testo_dell_area(p);
    TestoId fase = testo_della_fase(aiuti::fase_della_cronaca(p));
    int x = MARGINE_X;
    int y = y0 + 12;
    Scritta luogo(area, x, y, INCHIOSTRO, palette);
    x += larghezza_testo(area) + 1;
    Scritta punto_1(TestoId::PUNTO, x, y, INCHIOSTRO, palette);
    x += larghezza_testo(TestoId::PUNTO) + SPAZIO;
    Scritta fase_r(fase, x, y, INCHIOSTRO, palette);
    x += larghezza_testo(fase) + 1;
    Scritta punto_2(TestoId::PUNTO, x, y, INCHIOSTRO, palette);

    // la stella e l'obiettivo (senza stella, dal margine, se la prima riga non ci sta accanto)
    bn::optional<bn::sprite_ptr> stella;

    if(con_stella)
    {
        stella = menu::crea_icona(stile::IconaMenu::OBIETTIVO, MARGINE_X, y0 + 24, icone);
    }

    VistaTesto obiettivo(Contesto::DIALOGO, con_stella ? OBIETTIVO_X : MARGINE_X, y0 + 23, INCHIOSTRO, palette);
    obiettivo.mostra(meta);
    obiettivo.rivela_tutto();

    // in grigio: gli incarichi aperti a sinistra, il tempo allineato a destra
    int conti_y = PIEDE_Y - 1;
    Scritta incarichi(TestoId::DOVE_ERAVAMO_INCARICHI, MARGINE_X, conti_y, NOTA, palette);
    VistaNumero incarichi_n(0, conti_y, NOTA, palette);
    incarichi_n.mostra(aiuti::incarichi_aperti(p));
    incarichi_n.colloca(MARGINE_X + larghezza_testo(TestoId::DOVE_ERAVAMO_INCARICHI) + SPAZIO, conti_y);
    VistaNumero tempo_n(0, conti_y, NOTA, palette);
    tempo_n.mostra_tempo(int(p.tempo_frames / 60));
    tempo_n.colloca_a_destra(DESTRA_X, conti_y);
    Scritta tempo(TestoId::DOVE_ERAVAMO_TEMPO,
                  DESTRA_X + 1 - tempo_n.larghezza() - SPAZIO - larghezza_testo(TestoId::DOVE_ERAVAMO_TEMPO), conti_y, NOTA,
                  palette);
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
