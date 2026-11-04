#include "storia_scena.h"

#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_optional.h"
#include "bn_sprite_palette_item.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_shape_size.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_sprite_items_ritratto_antonio.h"
#include "bn_sprite_items_ritratto_giorgio.h"
#include "bn_sprite_items_ritratto_guido.h"
#include "bn_sprite_items_ritratto_ubaldo.h"

#include "aiuti.h"
#include "audio.h"
#include "battaglia_grafica.h"
#include "esplorazione.h"
#include "menu_pagine.h"
#include "negozio.h"
#include "game_state.h"
#include "opzioni.h"
#include "progressione.h"
#include "regia_logica.h"
#include "regia_scena.h"
#include "save_data.h"
#include "scena_battaglia.h"
#include "scontri_mappa.h"
#include "storia_logica.h"
#include "tabella.h"
#include "stile/cornice.h"
#include "vista_testo.h"

namespace gubbio
{

namespace
{
    using testo::Contesto;
    using namespace storia;

    constexpr int INCHIOSTRO_CHIARO = 2;    // sul cartiglio vermiglio e sul nero dei titoli
    constexpr int INCHIOSTRO_SCURO = 1;     // sul fondo chiaro dei riquadri (Guida, scelta 9)
    // Il dialogo della Guida: riquadro 30x7 a y=104, nome nel cartiglio a (8, 96). Il testo ha 4 px di
    // respiro dentro il piombo (interno da (8, 112)): parte da (12, 116), righe da 216 px (genera_testi).
    constexpr int RESPIRO = 4;
    constexpr int TESTO_X = stile::DIALOGO_X + 8 + RESPIRO;
    constexpr int TESTO_Y = stile::DIALOGO_Y + 8 + RESPIRO;

    // STANDARD I3: il testo non copre chi parla. Sulla mappa, se Ubaldo sta nella meta' bassa dello schermo,
    // riquadro, cartiglio del nome, testo e scelte salgono in cima (riquadro a y=16, cartiglio a y=8).
    // Lo decide dialogo_inizio() (e recita()) guardando il giocatore; nelle cutscene resta in basso.
    constexpr int DIALOGO_IN_ALTO_Y = 16;
    bool s_dialogo_in_alto = false;

    int su()
    {
        return s_dialogo_in_alto ? DIALOGO_IN_ALTO_Y - stile::DIALOGO_Y : 0;
    }

    void scegli_il_lato(const Esplorazione* esplorazione)
    {
        s_dialogo_in_alto = esplorazione && esplorazione->giocatore_in_basso();
    }
    constexpr int FRAME_CARTELLO = 90;
    constexpr int FRAME_TITOLI = 300;
    constexpr int FRAME_AUTOMATICA = 3;
    constexpr int DISTANZA_PAROLA = 14;     // pixel fra i piedi del giocatore e quelli dell'NPC per parlarci

    bool s_dialogo_fotografato = false;
    void attendi(int frame)
    {
        for(int f = 0; f < frame; ++f)
        {
            ++g_game_state.frames;
            bn::core::update();
        }
    }

    int s_voce_automatica = 0;              // la voce che prende ogni menu nelle prove senza tasti
    int s_scelte_fotografate = 0;           // le istantanee dei menu nelle prove

    // Le due voci di una scelta dentro il riquadro del dialogo, col cursore a triangolo della Guida a sinistra.
    constexpr int MENU_X = TESTO_X + 12;       // il cursore a x=12, allineato al testo dei dialoghi
    constexpr int MENU_Y = TESTO_Y + 2;
    constexpr int MENU_PASSO = 12;

    // Il cursore della Guida (tile "cursore" della cornice: triangolo vermiglio col piombo).
    bn::sprite_ptr crea_cursore(const bn::sprite_palette_ptr& palette_testo)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(1, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int r = 0; r < 8; ++r)
        {
            vram[0].data[r] = GUBBIO_VOCE(stile::CORNICE_TILE, stile::TILE_CURSORE * 8 + r);
        }

        bn::sprite_ptr cursore = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(8, 8), bn::move(tiles), palette_testo);
        cursore.set_bg_priority(PRIORITA_RIQUADRI);
        return cursore;
    }

    // RITc: il ritratto 32x32 di chi parla (Ubaldo, Giorgio, Antonio, Guido), nella sua cornice 5x5 a destra,
    // appoggiata al bordo del riquadro: sopra quando il dialogo e' in basso, sotto quando e' in alto (I3).
    // Il testo non si sposta: le righe restano da 216 px. Un fotogramma per espressione (calmo, preoccupato,
    // deciso, come stile/dati/ritratti.json e l'enum Espressione).
    constexpr int RITRATTO_CORNICE_X = 200;
    constexpr int RITRATTO_CORNICE = 5;     // tile per lato: 32 px di ritratto e 4 px di respiro per parte

    int ritratto_cornice_y()
    {
        return s_dialogo_in_alto ? stile::DIALOGO_Y + su() + stile::DIALOGO_RIGHE * 8
                                 : stile::DIALOGO_Y - RITRATTO_CORNICE * 8;
    }

    static_assert(RITRATTO_CORNICE_X + RITRATTO_CORNICE * 8 <= stile::DIALOGO_X + stile::DIALOGO_COLONNE * 8,
                  "la cornice del ritratto esce dal riquadro del dialogo");
    static_assert(stile::DIALOGO_Y - RITRATTO_CORNICE * 8 >= 0 &&
                  DIALOGO_IN_ALTO_Y + stile::DIALOGO_RIGHE * 8 + RITRATTO_CORNICE * 8 <= 160,
                  "la cornice del ritratto esce dallo schermo");
    static_assert(int(Espressione::CALMO) == 0 && int(Espressione::PREOCCUPATO) == 1 && int(Espressione::DECISO) == 2,
                  "i fotogrammi dei ritratti non seguono l'ordine delle espressioni");

    const bn::sprite_item* ritratto_di(testi::TestoId parlante)
    {
        switch(parlante)
        {
            case testi::TestoId::PARLANTE_UBALDO: return &bn::sprite_items::ritratto_ubaldo;
            case testi::TestoId::PARLANTE_GIORGIO: return &bn::sprite_items::ritratto_giorgio;
            case testi::TestoId::PARLANTE_ANTONIO: return &bn::sprite_items::ritratto_antonio;
            case testi::TestoId::PARLANTE_GUIDO: return &bn::sprite_items::ritratto_guido;
            default: return nullptr;
        }
    }

    void mostra_ritratto(Riquadri& riquadri, bn::optional<bn::sprite_ptr>& ritratto, const bn::sprite_item* item,
                         Espressione espressione)
    {
        ritratto.reset();

        if(! item)
        {
            return;
        }

        int y = ritratto_cornice_y();
        riquadri.cornice(RITRATTO_CORNICE_X, y, RITRATTO_CORNICE, RITRATTO_CORNICE);
        int fotogramma = int(espressione) < item->tiles_item().graphics_count() ? int(espressione) : 0;
        ritratto = item->create_sprite(RITRATTO_CORNICE_X + 4 + 16 - 120, y + 4 + 16 - 80, fotogramma);
        ritratto->set_bg_priority(PRIORITA_RIQUADRI);
    }

    // Il riquadro del dialogo; con un nome, il cartiglio largo quanto il nome sopra il bordo.
    void componi_dialogo(Riquadri& riquadri, bn::optional<VistaTesto>& nome, testi::TestoId parlante, bool con_nome,
                         const bn::sprite_palette_ptr& palette_testo)
    {
        riquadri.svuota();
        riquadri.cornice(stile::DIALOGO_X, stile::DIALOGO_Y + su(), stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
        nome.reset();

        if(con_nome)
        {
            int larghezza = larghezza_testo(parlante);
            int colonne = colonne_cartiglio(larghezza);
            riquadri.cartiglio(stile::CARTIGLIO_NOME_X, stile::CARTIGLIO_NOME_Y + su(), colonne);
            nome.emplace(Contesto::HUD, stile::CARTIGLIO_NOME_X + (colonne * 8 - larghezza) / 2,
                         stile::CARTIGLIO_NOME_Y + su() + 4, INCHIOSTRO_CHIARO, palette_testo);
            nome->mostra(parlante);
            nome->rivela_tutto();
        }
    }

    // Un menu sopra la scena, nel riquadro del dialogo: 'quante' voci (2 o 3) in inchiostro scuro sul fondo
    // chiaro, il cursore a triangolo davanti a quella scelta, su e giu' per spostarsi, A per scegliere. Con tre
    // voci (il Riprova dopo il duello, MAI) il menu sale di 4 px: le tre righe stanno dentro il bordo.
    constexpr int VOCI_MAX = 3;
    constexpr int SU_PER_VOCE = 4;

    static_assert(MENU_Y - SU_PER_VOCE >= stile::DIALOGO_Y + 8 &&
                  MENU_Y - SU_PER_VOCE + 2 * MENU_PASSO + 10 <= stile::DIALOGO_Y + 8 * stile::DIALOGO_RIGHE - 8,
                  "le tre voci del menu escono dal riquadro del dialogo");

    // Con 'domanda' il menu ha la sua linguetta: la domanda nel cartiglio sopra il bordo, come il nome di chi parla.
    int menu_voci(const testi::TestoId* testi_voci, int quante, const bn::sprite_palette_ptr& palette_testo, bool automatica,
                  bn::optional<testi::TestoId> domanda = bn::nullopt)
    {
        BN_ASSERT(quante >= 2 && quante <= VOCI_MAX, "menu_voci: voci ", quante);
        int voce = 0;
        bool cambiata = true;
        bn::optional<VistaTesto> voci[VOCI_MAX];
        int attesa = 0;
        int y0 = MENU_Y + su() - (quante - 2) * SU_PER_VOCE;
        Riquadri riquadri;
        riquadri.cornice(stile::DIALOGO_X, stile::DIALOGO_Y + su(), stile::DIALOGO_COLONNE, stile::DIALOGO_RIGHE);
        bn::optional<VistaTesto> linguetta;

        if(domanda)
        {
            int larghezza = larghezza_testo(*domanda);
            int colonne = colonne_cartiglio(larghezza);
            riquadri.cartiglio(stile::CARTIGLIO_NOME_X, stile::CARTIGLIO_NOME_Y + su(), colonne);
            linguetta.emplace(testo::dati(*domanda).contesto, stile::CARTIGLIO_NOME_X + (colonne * 8 - larghezza) / 2,
                              stile::CARTIGLIO_NOME_Y + su() + 4, INCHIOSTRO_CHIARO, palette_testo);
            linguetta->mostra(*domanda);
            linguetta->rivela_tutto();
        }

        bn::sprite_ptr cursore = crea_cursore(palette_testo);

        while(true)
        {
            if(cambiata)
            {
                for(int k = 0; k < quante; ++k)
                {
                    if(! voci[k])
                    {
                        voci[k].emplace(Contesto::SCELTA, MENU_X, y0 + k * MENU_PASSO, INCHIOSTRO_SCURO, palette_testo);
                        voci[k]->mostra(testi_voci[k]);
                        voci[k]->rivela_tutto();
                    }
                }

                // le coordinate degli sprite partono dal centro dello schermo; il triangolo e' alto 7 px e
                // sta a meta' della riga di testo
                cursore.set_position(MENU_X - 12 - 120 + 4, y0 + voce * MENU_PASSO + 1 - 80 + 4);

                cambiata = false;
            }

            attendi(1);

            if(automatica)
            {
                // la prova: un secondo col menu aperto e il cursore sulla prima voce, l'istantanea, poi la voce
                if(++attesa == 60)
                {
                    BN_LOG("Istantanea scelta_", s_scelte_fotografate++);
                }
                else if(attesa == 80)
                {
                    int scelta = s_voce_automatica < quante ? s_voce_automatica : 0;
                    BN_LOG("Scelta ", scelta);
                    return scelta;
                }

                continue;
            }

            if(bn::keypad::up_pressed())
            {
                voce = (voce + quante - 1) % quante;
                cambiata = true;
                audio::suona(colonna::Suono::CURSORE);
            }
            else if(bn::keypad::down_pressed())
            {
                voce = (voce + 1) % quante;
                cambiata = true;
                audio::suona(colonna::Suono::CURSORE);
            }
            else if(bn::keypad::a_pressed())
            {
                audio::suona(colonna::Suono::CONFERMA);
                BN_LOG("Scelta ", voce);
                return voce;
            }
        }
    }

    // Il menu di una scelta del copione: le due voci della battuta SCELTA.
    int menu_scelta(const Battuta& b, const bn::sprite_palette_ptr& palette_testo, bool automatica)
    {
        const testi::TestoId voci[2] = { b.testo, b.parlante };
        return menu_voci(voci, 2, palette_testo, automatica);
    }

    // Le battute a schermo: il nome di chi parla sopra, il testo a macchina da scrivere sotto, A per
    // completare e poi per andare avanti. Lo sfondo si scurisce, il testo resta chiaro.
    void recita_battute(const Battuta* tabella, int prima, int quante, const bn::sprite_palette_ptr& palette_testo,
                        bool automatica, bool npc = false)
    {
        bn::optional<Riquadri> riquadri;
        bn::optional<VistaTesto> nome;
        bn::optional<VistaTesto> testo;
        bn::optional<bn::sprite_ptr> ritratto;
        int scelta = -1;

        // un NPC: la prima variante "(se BANDIERA)" che vale parla da sola, se no le altre righe
        int sola = npc ? variante_che_vale(g_game_state, tabella, prima, quante) : -1;

        if(sola >= 0)
        {
            prima = sola;
            quante = 1;
        }

        for(int i = prima; i < prima + quante; ++i)
        {
            const Battuta& b = tabella[i];

            if((sola < 0 && variante(b.guardia)) || (sola < 0 && ! vale(g_game_state, b.guardia, scelta)))
            {
                continue;
            }

            if(b.tipo == TipoBattuta::SCELTA)
            {
                // il menu ha il suo riquadro: quello del dialogo si toglie, per non averne due uno sull'altro
                nome.reset();
                testo.reset();
                ritratto.reset();
                riquadri.reset();
                scelta = menu_scelta(b, palette_testo, automatica);
                scegli(g_game_state, b, scelta);
                continue;
            }

            // una riga OBIETTIVO di una scena diventa l'obiettivo della cronaca (MOB); quelle degli incarichi
            // restano dell'incarico. Tutte e due si leggono col cartiglio «Obiettivo»
            if(tabella == BATTUTA)
            {
                segna_obiettivo(g_game_state, b);
            }

            if(! riquadri)
            {
                riquadri.emplace();
            }

            bool obiettivo = b.tipo != TipoBattuta::PERSONAGGIO && obiettivo_del_testo(b.testo) >= 0;
            componi_dialogo(*riquadri, nome, obiettivo ? testi::TestoId::ETICHETTA_OBIETTIVO : b.parlante,
                            b.tipo == TipoBattuta::PERSONAGGIO || obiettivo, palette_testo);
            mostra_ritratto(*riquadri, ritratto, b.tipo == TipoBattuta::PERSONAGGIO ? ritratto_di(b.parlante) : nullptr,
                            b.espressione);

            if(! testo)
            {
                testo.emplace(Contesto::DIALOGO, TESTO_X, TESTO_Y + su(), INCHIOSTRO_SCURO, palette_testo);
            }

            testo->mostra(b.testo);

            if(automatica)
            {
                testo->rivela_tutto();
                attendi(FRAME_AUTOMATICA);

                // la prima battuta di un personaggio nella prova: l'istantanea del dialogo a schermo
                if(b.tipo == TipoBattuta::PERSONAGGIO && ! s_dialogo_fotografato)
                {
                    s_dialogo_fotografato = true;
                    attendi(20);
                    BN_LOG("Istantanea storia_dialogo");
                    attendi(30);
                }

                continue;
            }

            attendi(1);

            while(true)
            {
                if(! testo->completo())
                {
                    // la velocita' delle opzioni (MOP): una lettera a frame, una ogni due, o tutta
                    int lettere = opzioni::lettere_nel_frame(opzioni::g_opzioni, g_game_state.frames);

                    if(lettere < 0)
                    {
                        testo->rivela_tutto();
                    }
                    else if(lettere > 0)
                    {
                        testo->avanza();
                    }

                    if(bn::keypad::a_pressed())
                    {
                        testo->rivela_tutto();
                    }
                }
                else if(bn::keypad::a_pressed())
                {
                    audio::suona(colonna::Suono::TESTO);
                    break;
                }

                attendi(1);
            }

            attendi(1);
        }
    }

    bn::sprite_palette_ptr palette_npc()
    {
        bn::color c[16];

        for(int i = 0; i < 16; ++i)
        {
            c[i] = bn::color(GUBBIO_VOCE(battaglia::grafica::PALETTE_NEMICI, i));
        }

        return bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(c), bn::bpp_mode::BPP_4));
    }

    // La palette della gente (pezzo VIVA, tools/figure_popolo.py): di notte le stesse voci con le rampe notte
    // (STANDARD_GRAFICO L5), come i fondali della citta'.
    bn::sprite_palette_ptr palette_popolo()
    {
        bool notte = fase_npc(g_game_state) == Fase::NOTTE;
        bn::color c[16];

        for(int i = 0; i < 16; ++i)
        {
            c[i] = bn::color(notte ? GUBBIO_VOCE(PALETTE_POPOLO_NOTTE, i) : GUBBIO_VOCE(PALETTE_POPOLO, i));
        }

        return bn::sprite_palette_ptr::create(bn::sprite_palette_item(bn::span<const bn::color>(c), bn::bpp_mode::BPP_4));
    }

    constexpr int ALTEZZA_NPC = 31;      // lo sprite e' 16x32: i piedi sull'ultima riga (pose.json, linea_piedi)
    constexpr int ALTEZZA_PERSONA = 24;  // la persona dentro lo sprite (STANDARD M2): il fumetto le sta sopra

    // Una posa di FIGURA_NPC (POSA_RIPOSO, POSA_RESPIRO, POSA_SCHIENA, POSA_LATO) nei tile dello sprite.
    void carica_posa(bn::sprite_ptr& sprite, int figura, int posa)
    {
        bn::sprite_tiles_ptr tiles = sprite.tiles();
        bn::span<bn::tile> vram = *tiles.vram();
        int base = posa * 64;

        for(int t = 0; t < 8; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_NPC, figura), base + t * 8 + r);
            }
        }
    }

    // Un NPC con la sua figura (FIGURA_NPC, 16x32) nella posa di riposo, con la palette della gente.
    bn::sprite_ptr crea_npc(const bn::sprite_palette_ptr& palette, int figura)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(8, bn::bpp_mode::BPP_4);
        bn::sprite_ptr sprite = bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 32), bn::move(tiles), palette);
        carica_posa(sprite, figura, POSA_RIPOSO);
        return sprite;
    }

    // Dove sta un NPC adesso: quelli del borgo, con BORGO_DENTRO, nel digiuno e nella notte stanno
    // accampati in Sant'Andrea, dietro Porta Romana.
    struct Posto
    {
        int area;
        int tx;
        int ty;
    };

    Posto posto(const Npc& n)
    {
        if(n.del_borgo && accesa(g_game_state, Bandiera::BORGO_DENTRO) && fase_npc(g_game_state) != Fase::ULTIMATUM)
        {
            return { int(mondo::AreaId::SANT_ANDREA), n.tx_borgo, n.ty_borgo };
        }

        return { n.area, n.tx, n.ty };
    }

    // Dove sta una persona della lista di Storia: un NPC d'ambiente, un datore (NPC + quest), l'infiltrato.
    Posto posto_di(int indice)
    {
        if(indice < NPC)
        {
            return posto(GUBBIO_VOCE(NPC_AMBIENTE, indice));
        }

        if(indice < NPC + QUEST)
        {
            const QuestGioco& g = GUBBIO_VOCE(QUEST_GIOCO, indice - NPC);
            return { g.area, g.tx, g.ty };
        }

        return { INFILTRATO.area, INFILTRATO.tx, INFILTRATO.ty };
    }

    constexpr int ALTEZZA_RACCOLTA = 14;    // l'oggetto 16x16 poggia sui piedi della sua cella

    // Un oggetto da raccogliere con la sua figura (FIGURA_RACCOLTA, 16x16) e i colori dei popolani.
    bn::sprite_ptr crea_raccolta(const bn::sprite_palette_ptr& palette, int figura)
    {
        bn::sprite_tiles_ptr tiles = bn::sprite_tiles_ptr::allocate(4, bn::bpp_mode::BPP_4);
        bn::span<bn::tile> vram = *tiles.vram();

        for(int t = 0; t < 4; ++t)
        {
            for(int r = 0; r < 8; ++r)
            {
                vram[t].data[r] = GUBBIO_VOCE(GUBBIO_VOCE(FIGURA_RACCOLTA, figura), t * 8 + r);
            }
        }

        return bn::sprite_ptr::create(0, 0, bn::sprite_shape_size(16, 16), bn::move(tiles), palette);
    }

    // Le righe di FRASE_QUEST nel riquadro del dialogo, sopra la scena: il riquadro e' opaco, la scena non
    // si scurisce (scurirla scuriva anche la cornice, che sta fra le palette dei fondi).
    void dialogo_inizio(Esplorazione* esplorazione)
    {
        scegli_il_lato(esplorazione);

        if(esplorazione)
        {
            esplorazione->nascondi_etichetta();
        }

        attendi(1);
    }

    void dialogo_fine()
    {
        s_dialogo_in_alto = false;
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        attendi(1);
    }

    void recita_righe(const Righe& r, const bn::sprite_palette_ptr& palette_testo)
    {
        if(r.quante > 0)
        {
            recita_battute(FRASE_QUEST, r.prima, r.quante, palette_testo, false);
        }
    }

    // Una riga del SISTEMA nel riquadro del dialogo (i forzieri, l'uscita chiusa del Condotto).
    void di_sistema(testi::TestoId id, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo)
    {
        const Battuta b = { id, id, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { NESSUNA_BANDIERA, NESSUNA_BANDIERA }, -1 };
        dialogo_inizio(esplorazione);
        recita_battute(&b, 0, 1, palette_testo, false);
        dialogo_fine();
    }

    // Il lampo dei miasmi: lo schermo vira verso il verde della nebbia (la voce 11 della palette cupa) e torna.
    // Forte e due volte alla prima nebbia (B-02), appena accennato a ogni ferita.
    void lampo(int volte, bn::fixed forza)
    {
        bn::color verde(GUBBIO_VOCE(mondo::PALETTE_FONDALI_CUPA, 11));
        constexpr int PASSI = 8;

        for(int v = 0; v < volte; ++v)
        {
            for(int f = 0; f < PASSI; ++f)
            {
                bn::bg_palettes::set_fade(verde, forza * (PASSI - f) / PASSI);
                bn::sprite_palettes::set_fade(verde, forza * (PASSI - f) / PASSI / 2);
                attendi(1);
            }
        }

        bn::bg_palettes::set_fade(verde, 0);
        bn::sprite_palettes::set_fade(verde, 0);
    }

    // La riga di SISTEMA dopo una sconfitta che riporta indietro (MAI): dove si e' stati riportati.
    testi::TestoId testo_della_ritirata(aiuti::Ritirata r)
    {
        return r == aiuti::Ritirata::ARCO ? testi::TestoId::SCONFITTA_ARCO :
               (r == aiuti::Ritirata::SUBITO ? testi::TestoId::SCONFITTA_SUBITO : testi::TestoId::SCONFITTA_INGRESSO);
    }

    // Chi sale di livello con l'esperienza di una quest: le stesse frasi della battaglia, come SISTEMA.
    void annuncia_livelli(const bool (&saliti)[battaglia::EROI], const bn::sprite_palette_ptr& palette_testo)
    {
        constexpr testi::TestoId SALE[battaglia::EROI] = { testi::TestoId::BATT_SALE_UBALDO, testi::TestoId::BATT_SALE_GIORGIO,
                                                          testi::TestoId::BATT_SALE_ANTONIO };

        for(int e = 0; e < battaglia::EROI; ++e)
        {
            if(saliti[e])
            {
                const Battuta b = { GUBBIO_VOCE(SALE, e), GUBBIO_VOCE(SALE, e), TipoBattuta::SISTEMA, Espressione::CALMO, 0,
                                    { NESSUNA_BANDIERA, NESSUNA_BANDIERA }, -1 };
                recita_battute(&b, 0, 1, palette_testo, false);
            }
        }
    }
}

// Una cutscene del copione di regia: usa tutti e quattro i BG, lo sfondo dell'area si libera e torna
// dopo. Una gia' vista non riparte da sola (e ritorna false).
bool Storia::recita_regia(int regia, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                          bool automatica)
{
    if(regia::vista(g_game_state, regia))
    {
        BN_LOG("Cutscene ", GUBBIO_VOCE(regia::CUTSCENE_DATI, regia).codice, " gia' vista");
        return false;
    }

    if(esplorazione)
    {
        svuota();
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        esplorazione->sospendi();
        attendi(1);
    }

    recita_cutscene(regia, palette_testo, false, automatica);

    if(esplorazione)
    {
        esplorazione->ricompari();
    }

    return true;
}

// Le battute della scena da 'da' ad 'a' (indici in BATTUTA, 'a' escluso), spezzate dove entra una cutscene
// (INSERTO). Una scena con la battaglia a meta' (B-03) si recita in due tratti, prima e dopo la battaglia.
void Storia::recita_tratto(int da, int a, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                           bool automatica)
{
    for(int i = 0; i < INSERTI; ++i)
    {
        const Inserto& n = GUBBIO_VOCE(INSERTO, i);

        if(n.battuta >= da && n.battuta < a)
        {
            recita_battute(BATTUTA, da, n.battuta - da, palette_testo, automatica);
            da = n.battuta;

            // le battute del narratore che la cutscene ha detto nelle bande non si ripetono; se era gia'
            // vista (la scena rigiocata dopo una battaglia persa) si leggono nella vista di gioco
            if(recita_regia(n.regia, esplorazione, palette_testo, automatica))
            {
                da += n.copre;
            }

            // dopo la cutscene la scena torna com'era: niente velo scuro sotto il riquadro del dialogo
            if(esplorazione)
            {
                bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
            }
        }
    }

    recita_battute(BATTUTA, da, a - da, palette_testo, automatica);
}

bool Storia::recita(int k, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo, bool automatica,
                    bool battaglia_col_pilota)
{
    const Scena& s = GUBBIO_VOCE(SCENA, k);
    BN_LOG("Scena ", s.codice);
    // il duello gia' incontrato (CORRADO_INCONTRATO): al secondo tentativo niente battute, dritti alla battaglia
    bool salta_le_battute = gia_incontrata(g_game_state, k);
    scegli_il_lato(esplorazione);

    if(esplorazione)
    {
        esplorazione->nascondi_etichetta();
    }

    if(s.cutscene && s.regia >= 0)
    {
        // la cutscene del copione di regia; una gia' vista non riparte da sola
        if(regia::vista(g_game_state, s.regia))
        {
            BN_LOG("Cutscene ", s.codice, " gia' vista");
        }
        else
        {
            recita_regia(s.regia, esplorazione, palette_testo, automatica);
        }
    }
    else if(s.cutscene && s.regia == -2)
    {
        BN_LOG("Cutscene ", s.codice, " dentro la precedente");
    }
    else if(s.cutscene)
    {
        // il nodo segnaposto: il cartello col titolo, poi si passa oltre
        Riquadri riquadri;
        riquadri.cornice(0, 64, 30, 4);
        VistaTesto cartello(Contesto::DIALOGO, TESTO_X, 72, INCHIOSTRO_SCURO, palette_testo);
        cartello.mostra(s.titolo);
        cartello.rivela_tutto();
        BN_LOG("Cutscene ", s.codice, " (segnaposto)");

        for(int f = 0; f < (automatica ? FRAME_AUTOMATICA : FRAME_CARTELLO) && ! bn::keypad::a_pressed(); ++f)
        {
            attendi(1);
        }
    }
    else if(salta_le_battute)
    {
        BN_LOG("Scena ", s.codice, " gia' incontrata: si torna al duello");
    }
    else
    {
        // le battute fino alla battaglia (alla fine, o a meta' scena come in B-03)
        recita_tratto(s.prima_battuta, battuta_della_battaglia(k), esplorazione, palette_testo, automatica);
    }

    if(esplorazione)
    {
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
    }

    attendi(1);

    if(s.battaglia >= 0)
    {
        // l'incontro e' avvenuto anche se la battaglia si perde: l'uscita del Condotto si chiude (varco_chiuso)
        all_incontro(g_game_state, k);

        if(! battaglia_da_combattere(g_game_state, k))
        {
            BN_LOG("Battaglia ", int(s.battaglia), " gia' vinta");
        }
        else if(automatica && ! battaglia_col_pilota)
        {
            BN_LOG("Battaglia ", int(s.battaglia), " data per vinta");
        }
        else if(esplorazione)
        {
            svuota();
            esplorazione->sospendi();
            attendi(1);
            battaglia::Esito esito = scena_battaglia(s.battaglia, automatica ? 1u : (uint32_t(g_game_state.frames) | 1u),
                                                     automatica ? Guida::PILOTA : Guida::GIOCATORE, palette_testo,
                                                     automatica, &g_game_state);

            // il duello con Corrado perso (MAI): Riprova lo scontro, Carica uno slot o Torna al titolo, invece di
            // tornare all'ingresso del Condotto con l'uscita chiusa
            while(esito != battaglia::Esito::VITTORIA && ! automatica && aiuti::riprova_dopo_la_sconfitta(k))
            {
                mondo::colloca(esplorazione->esploratore(), esplorazione->esploratore().area, 1);
                esplorazione->ricompari();

                if(_dopo_il_duello_perso(*esplorazione, palette_testo))
                {
                    return false;
                }

                svuota();
                esplorazione->sospendi();
                attendi(1);
                esito = scena_battaglia(s.battaglia, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE, palette_testo,
                                        false, &g_game_state);
            }

            // a meta' scena (B-03) vinta si resta sotto l'arco e la scena va avanti; persa si torna indietro, allo
            // spawn 0 (dalla parte dei miasmi: lo spawn 1 e' oltre i guerrieri), e si ripassa sotto l'arco
            if(a_meta_della_scena(k) >= 0)
            {
                if(esito != battaglia::Esito::VITTORIA)
                {
                    mondo::colloca(esplorazione->esploratore(), esplorazione->esploratore().area, 0);
                }
            }
            else
            {
                mondo::colloca(esplorazione->esploratore(), esplorazione->esploratore().area,
                               esito == battaglia::Esito::VITTORIA ? 0 : 1);
            }

            esplorazione->ricompari();

            if(esito != battaglia::Esito::VITTORIA)
            {
                // dove si e' stati riportati, con una riga di SISTEMA (MAI)
                if(! automatica)
                {
                    di_sistema(testo_della_ritirata(aiuti::ritirata_della_scena(k)), esplorazione, palette_testo);
                }

                return false;   // la scena resta da giocare: si riprova rientrando nell'area
            }
        }

        // la battaglia a meta' scena vinta non si rigioca (B-03, GUERRIERI_VINTI)
        vinta_a_meta(g_game_state, k);

        // lo scontro della scena e' quello sulla mappa: vinto, il nemico non torna
        if(s.battaglia < progressione::SCONTRI)
        {
            progressione::segna_vinto(g_game_state, progressione::Bandiera(s.battaglia));
        }
    }

    // il resto della scena dopo una battaglia a meta' (B-03: il ragazzo eugubino, il dilemma)
    int dopo = battuta_della_battaglia(k);

    if(! s.cutscene && ! salta_le_battute && dopo < s.prima_battuta + s.battute)
    {
        if(esplorazione)
        {
            esplorazione->nascondi_etichetta();
        }

        recita_tratto(dopo, s.prima_battuta + s.battute, esplorazione, palette_testo, automatica);

        if(esplorazione)
        {
            bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        }

        attendi(1);
    }

    bool finita_prima = accesa(g_game_state, Bandiera::CRONACA_V1_FINITA);
    chiudi_scena(g_game_state, k);

    // i titoli di coda: la cronaca della v1 e' finita (il resto arriva con gli aggiornamenti)
    if(! finita_prima && accesa(g_game_state, Bandiera::CRONACA_V1_FINITA))
    {
        BN_LOG("Titoli di coda");
        VistaTesto fine(Contesto::DIALOGO, 16, 72, INCHIOSTRO_CHIARO, palette_testo);
        fine.mostra(testi::TestoId::STORIA_FINE);
        fine.rivela_tutto();
        attendi(automatica ? FRAME_AUTOMATICA : FRAME_TITOLI);
    }

    return true;
}

void Storia::prologo(const bn::sprite_palette_ptr& palette_testo, bool automatica)
{
    for(int k = prossima_scena(g_game_state, NESSUNA_AREA); k >= 0; k = prossima_scena(g_game_state, NESSUNA_AREA))
    {
        recita(k, nullptr, palette_testo, automatica);
    }
}

void Storia::svuota()
{
    _npc.clear();
    _indici.clear();
    _figura.clear();
    _posa.clear();
    _parla = -1;
    _folla.svuota();
    _raccolte.clear();
    _gola.clear();
    _area = -1;
}

void Storia::_prepara_npc(const Esplorazione& esplorazione)
{
    svuota();
    _area = int(esplorazione.esploratore().area);
    int fase = int(fase_npc(g_game_state));
    bn::sprite_palette_ptr palette = palette_npc();        // gli oggetti (raccolte, forzieri, fiamme)
    bn::sprite_palette_ptr gente = palette_popolo();       // le persone (VIVA)
    _folla.prepara(_area, fase, esplorazione, gente);

    for(int i = 0; i < NPC; ++i)
    {
        const Npc& n = GUBBIO_VOCE(NPC_AMBIENTE, i);

        Posto qui = posto(n);

        if(qui.area == _area && GUBBIO_VOCE(n.frasi, fase) > 0)
        {
            bn::sprite_ptr sprite = crea_npc(gente, n.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(qui.tx), mondo::piedi_y(qui.ty), ALTEZZA_NPC);
            _npc.push_back(bn::move(sprite));
            _indici.push_back(i);
            _figura.push_back(n.figura);
            _posa.push_back(POSA_RIPOSO);
        }
    }

    // i datori delle quest, da quando la quest si prende (e, consegnata, per il dopo)
    for(int q = 0; q < QUEST; ++q)
    {
        const QuestGioco& g = GUBBIO_VOCE(QUEST_GIOCO, q);

        if(g.area == _area && momento_del_datore(g_game_state, q) != Momento::ASSENTE)
        {
            bn::sprite_ptr sprite = crea_npc(gente, g.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(g.tx), mondo::piedi_y(g.ty), ALTEZZA_NPC);
            _npc.push_back(bn::move(sprite));
            _indici.push_back(NPC + q);
            _figura.push_back(g.figura);
            _posa.push_back(POSA_RIPOSO);
        }
    }

    // l'infiltrato sotto le Logge, con i tre indizi
    if(INFILTRATO.area == _area && infiltrato_presente(g_game_state))
    {
        bn::sprite_ptr sprite = crea_npc(gente, INFILTRATO.figura);
        esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(INFILTRATO.tx), mondo::piedi_y(INFILTRATO.ty), ALTEZZA_NPC);
        _npc.push_back(bn::move(sprite));
        _indici.push_back(NPC + QUEST);
        _figura.push_back(INFILTRATO.figura);
        _posa.push_back(POSA_RIPOSO);
    }

    // i soldati di B-03 oltre l'arco, finche' il piano di Corrado non e' ascoltato
    for(int k = 0; k < SENTINELLE && sentinelle_presenti(g_game_state); ++k)
    {
        const Sentinella& s = GUBBIO_VOCE(SENTINELLA, k);

        if(s.area == _area)
        {
            bn::sprite_ptr sprite = crea_npc(gente, s.figura);
            carica_posa(sprite, s.figura, POSA_LATO);
            sprite.set_horizontal_flip(true);       // guardano verso valle, verso l'arco
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(s.tx), mondo::piedi_y(s.ty), ALTEZZA_NPC);
            _gola.push_back(bn::move(sprite));
        }
    }

    // i forzieri negli slarghi: chiusi, o aperti se gia' presi
    for(int k = 0; k < FORZIERI; ++k)
    {
        const Forziere& f = GUBBIO_VOCE(FORZIERE, k);

        if(f.area == _area)
        {
            bn::sprite_ptr sprite = crea_raccolta(palette, forziere_chiuso(g_game_state, k) ? FIGURA_FORZIERE
                                                                                             : FIGURA_FORZIERE_APERTO);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(f.tx), mondo::piedi_y(f.ty), ALTEZZA_RACCOLTA);
            _gola.push_back(bn::move(sprite));
        }
    }

    // i tre ceri dell'altare della Basilica (F10): con i Ceri risvegliati (A1-08) una fiamma sopra ognuno, al
    // centro dei suoi due tile; prima restano spenti, solo il disegno del fondale
    for(int k = 0; k < CERI_ALTARE && ceri_accesi(g_game_state); ++k)
    {
        const CeroAltare& c = GUBBIO_VOCE(CERO_ALTARE, k);

        if(c.area == _area)
        {
            bn::sprite_ptr sprite = crea_raccolta(palette, FIGURA_FIAMMA_CERO);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(c.tx) + mondo::TILE_PX / 2, mondo::piedi_y(c.ty),
                                             ALTEZZA_RACCOLTA);
            _gola.push_back(bn::move(sprite));
        }
    }

    // le guardie delle fornaci (F10): un Guerriero della Roccia davanti a ogni blocco, finche' non e' battuto;
    // la figura e' quella della battaglia, come i nemici sulla mappa (ScontriSullaMappa)
    for(int k = 0; k < GUARDIE_FORNACE; ++k)
    {
        const GuardiaFornace& g = GUBBIO_VOCE(GUARDIA_FORNACE, k);

        if(g.area == _area && guardia_presente(g_game_state, k))
        {
            bn::sprite_ptr sprite = sprite_sulla_mappa(INCONTRO_FORNACE);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(g.tx), mondo::piedi_y(g.ty),
                                             sprite.shape_size().height());
            _gola.push_back(bn::move(sprite));
        }
    }

    // gli oggetti da raccogliere ancora al loro posto
    for(int k = 0; k < RACCOLTE; ++k)
    {
        const Raccolta& r = GUBBIO_VOCE(RACCOLTA, k);

        if(r.area == _area && raccolta_presente(g_game_state, k))
        {
            bn::sprite_ptr sprite = crea_raccolta(palette, r.figura);
            esplorazione.colloca_sulla_mappa(sprite, mondo::piedi_x(r.tx), mondo::piedi_y(r.ty), ALTEZZA_RACCOLTA);
            _raccolte.push_back(bn::move(sprite));
        }
    }
}

// Il datore di una quest: la proposta (la quest e' presa e, se l'obiettivo e' gia' finito, segue la
// consegna), l'attesa, la consegna (storia::consegna_quest(): premio, 55 punti, una volta sola), il dopo.
void Storia::_parla_col_datore(int q, const bn::sprite_palette_ptr& palette_testo)
{
    Momento m = momento_del_datore(g_game_state, q);
    BN_LOG("Datore ", GUBBIO_VOCE(QUEST_V1, q).codice, " momento ", int(m));

    if(m == Momento::PROPOSTA)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
        prendi_quest(g_game_state, q);
        m = momento_del_datore(g_game_state, q) == Momento::CONSEGNA ? Momento::CONSEGNA : Momento::ASSENTE;
    }
    else if(m == Momento::ATTESA || m == Momento::DOPO)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
    }

    if(m == Momento::CONSEGNA)
    {
        recita_righe(righe_del_datore(g_game_state, q, m), palette_testo);
        bool saliti[battaglia::EROI] = {};

        if(consegna_quest(g_game_state, q, saliti))
        {
            BN_LOG("Quest ", GUBBIO_VOCE(QUEST_V1, q).codice, " consegnata");
            annuncia_livelli(saliti, palette_testo);
        }
    }
}

// L'infiltrato: le sue battute, la battaglia (non si fugge: persa, si torna all'ingresso dell'area e lui
// resta), vinta la Rosa e le battute di dopo.
void Storia::_affronta_l_infiltrato(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    recita_righe(INFILTRATO.prima, palette_testo);
    dialogo_fine();
    mondo::AreaId area = esplorazione.esploratore().area;
    svuota();
    esplorazione.sospendi();
    attendi(1);
    battaglia::Esito esito = scena_battaglia(INFILTRATO.incontro, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE,
                                             palette_testo, false, &g_game_state);
    BN_LOG("Infiltrato: esito ", int(esito));

    if(esito != battaglia::Esito::VITTORIA)
    {
        mondo::colloca(esplorazione.esploratore(), area, 1);
    }

    esplorazione.ricompari();

    if(esito != battaglia::Esito::VITTORIA)
    {
        di_sistema(testi::TestoId::SCONFITTA_INGRESSO, &esplorazione, palette_testo);
    }

    if(esito == battaglia::Esito::VITTORIA && riprendi_la_rosa(g_game_state))
    {
        dialogo_inizio(&esplorazione);
        recita_righe(INFILTRATO.dopo, palette_testo);
    }
}

// Una guardia di fornace: la battaglia (INCONTRO_FORNACE, un Guerriero della Roccia). Vinta, la guardia non torna;
// persa, si torna all'ingresso dell'area (spawn 1) e la guardia resta davanti al suo blocco, come un nemico sulla mappa.
void Storia::_affronta_la_guardia(int guardia, Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    mondo::AreaId area = esplorazione.esploratore().area;
    esplorazione.nascondi_etichetta();
    svuota();
    esplorazione.sospendi();
    attendi(1);
    battaglia::Esito esito = scena_battaglia(INCONTRO_FORNACE, uint32_t(g_game_state.frames) | 1u, Guida::GIOCATORE,
                                             palette_testo, false, &g_game_state);
    BN_LOG("Guardia della fornace ", guardia, ": esito ", int(esito));

    if(esito == battaglia::Esito::VITTORIA)
    {
        batti_la_guardia(g_game_state, guardia);
    }
    else
    {
        mondo::colloca(esplorazione.esploratore(), area, 1);
    }

    esplorazione.ricompari();

    if(esito != battaglia::Esito::VITTORIA)
    {
        di_sistema(testi::TestoId::SCONFITTA_INGRESSO, &esplorazione, palette_testo);
    }
}

bool Storia::_dopo_il_duello_perso(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    constexpr testi::TestoId VOCI[3] = { testi::TestoId::RIPROVA_SCONTRO, testi::TestoId::RIPROVA_CARICA,
                                         testi::TestoId::RIPROVA_TITOLO };
    constexpr testi::TestoId SLOT[salvataggio::SLOT] = { testi::TestoId::CARICA_SLOT_1, testi::TestoId::CARICA_SLOT_2 };

    while(true)
    {
        // per i copioni del banco (tools/banco.sh): da qui il menu aspetta i tasti
        BN_LOG("Duello perso: il menu");
        dialogo_inizio(&esplorazione);
        // la domanda nella linguetta del menu, sopra il bordo, in basso o in alto che sia (STANDARD I3, su())
        int voce = menu_voci(VOCI, 3, palette_testo, false, testi::TestoId::RIPROVA_DOMANDA);

        BN_LOG("Duello perso: voce ", voce);

        if(voce == 0)
        {
            dialogo_fine();
            return false;
        }

        if(voce == 2)
        {
            bn::core::reset();
        }

        int slot = menu_voci(SLOT, salvataggio::SLOT, palette_testo, false);

        if(salvataggio::carica(slot, g_game_state))
        {
            storia::dopo_il_caricamento(g_game_state);
            dialogo_fine();
            esplorazione.riprendi(mondo::AreaId(g_game_state.area), g_game_state.x, g_game_state.y);
            svuota();
            BN_LOG("Duello perso: caricato lo slot ", slot);
            return true;
        }

        dialogo_fine();
        di_sistema(testi::TestoId::CARICA_FALLITO, &esplorazione, palette_testo);
    }
}

// Il respiro di chi sta fermo (STANDARD A5): due pose da FRAME_RESPIRO vblank, sfasate per posizione (x 17) cosi'
// due vicini non respirano insieme. Chi ha appena parlato torna nella posa di riposo, di fronte (A7).
void Storia::_anima_npc()
{
    if(_parla >= 0 && _parla < _npc.size())
    {
        _npc[_parla].set_horizontal_flip(false);
        _posa[_parla] = POSA_RIPOSO;
        carica_posa(_npc[_parla], _figura[_parla], POSA_RIPOSO);
    }

    _parla = -1;

    for(int j = 0; j < _npc.size(); ++j)
    {
        if(_posa[j] != POSA_RIPOSO && _posa[j] != POSA_RESPIRO)
        {
            continue;
        }

        Posto qui = posto_di(_indici[j]);
        int fase = ((int(g_game_state.frames) + (qui.tx + qui.ty) * 17) / FRAME_RESPIRO) % 2;
        int posa = fase ? POSA_RESPIRO : POSA_RIPOSO;

        if(posa != _posa[j])
        {
            _posa[j] = uint8_t(posa);
            carica_posa(_npc[j], _figura[j], posa);
        }
    }
}

// Chi parla si gira verso il giocatore (STANDARD A7): di lato (la sinistra e' il lato specchiato), di schiena se
// il giocatore sta sopra, di fronte se sta sotto. dx, dy: i piedi del giocatore meno quelli dell'NPC.
void Storia::_gira_verso(int j, int dx, int dy)
{
    int ax = dx < 0 ? -dx : dx;
    int ay = dy < 0 ? -dy : dy;
    int posa = ax > ay ? POSA_LATO : (dy < 0 ? POSA_SCHIENA : POSA_RIPOSO);
    _npc[j].set_horizontal_flip(posa == POSA_LATO && dx < 0);
    _posa[j] = uint8_t(posa);
    carica_posa(_npc[j], _figura[j], posa);
    _parla = j;
}

void Storia::anima_la_gente(const Esplorazione& esplorazione)
{
    const mondo::Esploratore& e = esplorazione.esploratore();

    if(int(e.area) != _area)
    {
        _prepara_npc(esplorazione);
    }

    _anima_npc();
    _folla.aggiorna(esplorazione, e.x, e.y, int(g_game_state.frames));
}

bool Storia::aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    const mondo::Esploratore& e = esplorazione.esploratore();

    if(int(e.area) != _area)
    {
        all_ingresso(g_game_state, int(e.area));
        _prepara_npc(esplorazione);
    }

    // la notte (dal rientro da Porta Metauro): anche i fondali con le rampe notte, come la gente (pezzo EDI)
    esplorazione.imposta_notte(fase_npc(g_game_state) == Fase::NOTTE);

    _anima_npc();
    _folla.aggiorna(esplorazione, e.x, e.y, int(g_game_state.frames));

    // l'uscita del Condotto chiusa durante il duello (T2): si urta come un muro, e lo si dice
    esplorazione.chiudi_varco(varco_chiuso(g_game_state, int(e.area)));

    if(esplorazione.in_dissolvenza())
    {
        return false;
    }

    if(esplorazione.urto_al_varco_chiuso() && g_game_state.frames - _ultimo_urto > 120)
    {
        _ultimo_urto = g_game_state.frames;
        di_sistema(testi::TestoId::CONDOTTO_CHIUSO, &esplorazione, palette_testo);
        return true;
    }

    // la cartolina del luogo entrando nell'area (C7S agli Stradoni, F10): prima di ogni scena e di ogni nemico
    // sulla mappa (gli scontri si aggiornano dopo la storia), una volta sola; l'inserto della scena la trovera'
    // gia' vista. Gli NPC dell'area si rifanno al frame dopo (recita_regia svuota).
    int cartolina = cutscene_all_ingresso(g_game_state, int(e.area));

    if(cartolina >= 0)
    {
        BN_LOG("Cutscene all'ingresso: ", GUBBIO_VOCE(regia::CUTSCENE_DATI, cartolina).codice);
        esplorazione.nascondi_etichetta();
        recita_regia(cartolina, &esplorazione, palette_testo, false);
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), 0);
        attendi(1);
        return true;
    }

    // la cella sotto i piedi: le scene della gola partono su una cella (la nebbia, l'arco), i miasmi la leggono
    int cella = mondo::cella(mondo::area(e.area), mondo::cella_x(e), mondo::cella_y(e));

    // le scene con una battaglia partono toccando il loro nemico sulla mappa (ScontriSullaMappa);
    // quelle con una battaglia senza nemico sulla mappa (il rito) partono entrando, come le altre
    int k = -1;

    for(int j = 0; j < SCENE && k < 0; ++j)
    {
        int b = GUBBIO_VOCE(SCENA, j).battaglia;

        if((b < 0 || b >= progressione::SCONTRI) && pronta_qui(g_game_state, j, int(e.area), cella))
        {
            k = j;
        }
    }

    if(k >= 0)
    {
        // la prima nebbia (B-02): il lampo verde, poi l'avviso di Ubaldo, che accende MIASMI_VISTI
        if(cella_dell_innesco(k) == int(mondo::Cella::MIASMA))
        {
            esplorazione.nascondi_etichetta();
            lampo(2, bn::fixed(0.6));
        }

        // le scene a schermo intero che quella appena finita rende pronte partono subito, senza camminare:
        // la vetrata di E-02 dopo la terza alba (E-01), come il prologo all'avvio
        if(recita(k, &esplorazione, palette_testo))
        {
            for(int j = prossima_scena(g_game_state, NESSUNA_AREA); j >= 0; j = prossima_scena(g_game_state, NESSUNA_AREA))
            {
                recita(j, &esplorazione, palette_testo);
            }
        }

        svuota();       // la fase puo' essere cambiata: gli NPC si rifanno al prossimo frame
        return true;
    }

    // i miasmi: chi corre nella nebbia lascia indietro Ubaldo e si ferisce (poco, mai a morte)
    bool corre = bn::keypad::b_held() && (bn::keypad::left_held() || bn::keypad::right_held() ||
                                          bn::keypad::up_held() || bn::keypad::down_held());

    if(respira_i_miasmi(g_game_state, cella, corre, _respiro))
    {
        BN_LOG("Miasmi: ferite ", int(g_game_state.ferite[1]), " ", int(g_game_state.ferite[2]));
        lampo(1, bn::fixed(0.25));
    }

    // un forziere si apre toccandolo: l'oggetto, la bandiera; resta li' aperto
    int z = forziere_toccato(g_game_state, int(e.area), e.x, e.y);

    if(z >= 0 && apri_forziere(g_game_state, z))
    {
        BN_LOG("Forziere ", z);
        audio::suona(colonna::Suono::RACCOLTA);
        di_sistema(GUBBIO_VOCE(FORZIERE, z).testo, &esplorazione, palette_testo);
        svuota();       // il forziere si rifa' aperto al prossimo frame
        return true;
    }

    // una guardia di fornace si affronta toccandola (F10, Q-SM01): vinta, il blocco che guardava si puo' prendere
    int guardia = guardia_toccata(g_game_state, int(e.area), e.x, e.y);

    if(guardia >= 0)
    {
        _affronta_la_guardia(guardia, esplorazione, palette_testo);
        svuota();       // la guardia battuta sparisce: si rifa' tutto al prossimo frame
        return true;
    }

    // un oggetto da raccogliere si prende toccandolo: il contatore sale, le righe di raccolta della quest
    int r = raccolta_toccata(g_game_state, int(e.area), e.x, e.y);

    if(r >= 0)
    {
        raccogli(g_game_state, r);
        BN_LOG("Raccolta ", r);
        audio::suona(colonna::Suono::RACCOLTA);
        dialogo_inizio(&esplorazione);
        recita_righe(GUBBIO_VOCE(QUEST_GIOCO, GUBBIO_VOCE(RACCOLTA, r).quest).raccolta, palette_testo);
        dialogo_fine();
        svuota();       // l'oggetto sparisce: si rifa' tutto al prossimo frame
        return true;
    }

    // il fumetto coi tre puntini (STANDARD I2) sopra la prima persona a portata di parola: e' la stessa
    // che risponde ad A qui sotto.
    bool a_portata = false;

    for(int j = 0; j < _indici.size() && ! a_portata; ++j)
    {
        Posto qui = posto_di(_indici[j]);
        int dx = e.x - mondo::piedi_x(qui.tx);
        int dy = e.y - mondo::piedi_y(qui.ty);

        if(dx > -DISTANZA_PAROLA && dx < DISTANZA_PAROLA && dy > -DISTANZA_PAROLA && dy < DISTANZA_PAROLA)
        {
            esplorazione.segnala(mondo::piedi_x(qui.tx), mondo::piedi_y(qui.ty), ALTEZZA_PERSONA);
            a_portata = true;
        }
    }

    // nessuno a portata: il cartello del varco, se e' a portata, accende lo stesso fumetto (STANDARD I2)
    if(! a_portata && ! esplorazione.segnala_cartello())
    {
        esplorazione.spegni_segnale();
    }

    if(! bn::keypad::a_pressed())
    {
        return false;
    }

    for(int j = 0; j < _indici.size(); ++j)
    {
        int indice = _indici[j];
        Posto qui = posto_di(indice);
        int dx = e.x - mondo::piedi_x(qui.tx);
        int dy = e.y - mondo::piedi_y(qui.ty);

        if(dx > -DISTANZA_PAROLA && dx < DISTANZA_PAROLA && dy > -DISTANZA_PAROLA && dy < DISTANZA_PAROLA)
        {
            _gira_verso(j, dx, dy);
            dialogo_inizio(&esplorazione);

            if(indice == NPC + QUEST)
            {
                _affronta_l_infiltrato(esplorazione, palette_testo);
                dialogo_fine();
                svuota();
                return true;
            }

            if(indice >= NPC)
            {
                _parla_col_datore(indice - NPC, palette_testo);
                dialogo_fine();
                svuota();   // il datore puo' essere passato al dopo
                return true;
            }

            const Npc& n = GUBBIO_VOCE(NPC_AMBIENTE, indice);
            int fase = int(fase_npc(g_game_state));
            recita_battute(FRASE_NPC, GUBBIO_VOCE(n.prima_frase, fase), GUBBIO_VOCE(n.frasi, fase), palette_testo, false,
                           true);

            if((n.imposta_fasi >> fase) & 1)
            {
                accendi_una(g_game_state, n.imposta);
            }

            // Q-SP01: dopo le sue battute (Giordano ha gia' acceso INDIZIO_ACQUA), l'indizio; col terzo, l'infiltrato
            int quale = indizio_dell_npc(g_game_state, indice);

            if(quale >= 0)
            {
                recita_righe(GUBBIO_VOCE(INDIZIO, quale).righe, palette_testo);

                if(trova_indizio(g_game_state, quale))
                {
                    recita_righe(INDIZI_COMPLETI, palette_testo);
                }

                svuota();   // l'infiltrato puo' essere comparso
            }

            // MNEG: dopo le battute e l'indizio, la bottega del Venditore
            if(indice == negozio::NPC_VENDITORE)
            {
                attendi(1);
                menu::bottega(s_dialogo_in_alto, false);
            }

            dialogo_fine();
            return true;
        }
    }

    return false;
}

void prova_storia(const bn::sprite_palette_ptr& palette_testo)
{
    // due giri: nel primo ogni menu prende la prima voce, nel secondo la seconda
    int visitate = 0;
    int mancanti = 0;

    for(int giro = 0; giro < 2; ++giro)
    {
    g_game_state = GameState{};
    progressione::partita_nuova(g_game_state);
    s_voce_automatica = giro;
    Storia storia;
    BN_LOG("Giro ", giro);
    bool avanti = true;
    visitate = 0;

    // lo stesso giro di storia::gioca_tutta, ma recitando ogni scena a schermo
    while(avanti)
    {
        avanti = false;

        for(int k = 0; k < SCENE && ! avanti; ++k)
        {
            if(pronta(g_game_state, k, GUBBIO_VOCE(SCENA, k).area) && storia.recita(k, nullptr, palette_testo, true))
            {
                ++visitate;
                avanti = true;
            }
        }

        // con «Non ancora» in B-05 la conferma dell'alba la da' il console Guido
        if(! avanti && risposta_di_un_npc(g_game_state))
        {
            BN_LOG("Risposta a un NPC");
            avanti = true;
        }
    }

    for(int k = 0; k < SCENE; ++k)
    {
        if(! fatta(g_game_state, k))
        {
            BN_LOG("Scena NON visitata: ", GUBBIO_VOCE(SCENA, k).codice);
            ++mancanti;
        }
    }

    BN_LOG("Giro ", giro, ": ", visitate, " scene, borgo ", accesa(g_game_state, Bandiera::BORGO_DENTRO) ? "dentro" : "fuori",
           ", esule ", accesa(g_game_state, Bandiera::ESULE_PRIGIONIERO) ? "prigioniero" : "liberato",
           ", giustizia ", accesa(g_game_state, Bandiera::GIUSTIZIA_OFFERTA) ? "offerta" : "no");
    }

    BN_LOG("Istantanee finite");
    BN_LOG("Storia: ", visitate, " scene visitate su ", SCENE, ", ", mancanti, " mancanti, titoli di coda ",
           accesa(g_game_state, Bandiera::CRONACA_V1_FINITA) ? "raggiunti" : "NON raggiunti");

    while(true)
    {
        bn::core::update();
    }
}

}

namespace gubbio
{

void prova_figure_npc(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);
    bn::sprite_palette_ptr palette = palette_popolo();
    bn::vector<bn::sprite_ptr, FIGURE_NPC> figure;
    const mondo::Esploratore& e = esplorazione.esploratore();

    // tutte le figure in file da dieci davanti al giocatore
    for(int f = 0; f < FIGURE_NPC; ++f)
    {
        bn::sprite_ptr sprite = crea_npc(palette, f);
        esplorazione.colloca_sulla_mappa(sprite, e.x + (f % 10) * 22 - 99, e.y - 44 + (f / 10) * 34, ALTEZZA_NPC);
        figure.push_back(bn::move(sprite));
    }

    for(int f = 0; f < 90; ++f)
    {
        esplorazione.aggiorna();
        bn::core::update();
    }

    BN_LOG("Istantanea figure_npc");

    for(int f = 0; f < 60; ++f)
    {
        esplorazione.aggiorna();
        bn::core::update();
    }

    // il menu del dilemma della popolana (D3), come lo vede chi le parla col pane in tasca
    figure.clear();

    for(int i = 0; i < FRASI_NPC; ++i)
    {
        if(GUBBIO_VOCE(FRASE_NPC, i).tipo == TipoBattuta::SCELTA)
        {
            menu_scelta(GUBBIO_VOCE(FRASE_NPC, i), palette_testo, true);
            break;
        }
    }

    BN_LOG("Istantanee finite");

    while(true)
    {
        bn::core::update();
    }
}

void prova_prologo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo)
{
    progressione::partita_nuova(g_game_state);
    Storia storia;

    // il prologo (la cutscene C1) prima di entrare in citta': lo sfondo dell'area non c'e' ancora
    esplorazione.sospendi();
    attendi(1);
    storia.prologo(palette_testo, true);

    // l'ultimatum a Piazza Grande
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);
    attendi(30);
    storia.recita(prossima_scena(g_game_state, int(mondo::AreaId::PIAZZA_GRANDE)), &esplorazione, palette_testo, true);

    // la postierla di San Martino
    esplorazione.entra(mondo::AreaId::SAN_MARTINO, 1);
    attendi(30);
    storia.recita(prossima_scena(g_game_state, int(mondo::AreaId::SAN_MARTINO)), &esplorazione, palette_testo, true);

    // il Teatro: la Pattuglia sulla mappa, che adesso c'e'
    esplorazione.entra(mondo::AreaId::TEATRO_ROMANO, 1);
    ScontriSullaMappa scontri(&storia);

    for(int f = 0; f < 90; ++f)
    {
        esplorazione.aggiorna();
        scontri.aggiorna(esplorazione, palette_testo);

        if(f == 70)
        {
            BN_LOG("Istantanea prologo_pattuglia");
        }

        attendi(1);
    }

    bool pattuglia_vista = scontri.visibili() > 0;
    scontri.svuota();
    bool salvato = storia.recita(scena_dello_scontro(INCONTRO_DEL_TEATRO), &esplorazione, palette_testo, true, true);

    BN_LOG("Prologo: Giorgio nel gruppo ", accesa(g_game_state, Bandiera::GIORGIO_NEL_GRUPPO) ? "si" : "NO",
           ", Pattuglia sulla mappa ", pattuglia_vista ? "si" : "NO",
           ", Antonio salvato ", salvato && accesa(g_game_state, Bandiera::ANTONIO_NEL_GRUPPO) ? "si" : "NO",
           ", gruppo ", int(gruppo(g_game_state, 1)), ", Pattuglia sulla mappa dopo ",
           scontro_attivo(g_game_state, INCONTRO_DEL_TEATRO) ? "ANCORA" : "sparita");
    BN_LOG("Istantanee finite");
}


void prova_folla(Esplorazione& esplorazione)
{
    constexpr mondo::AreaId AREE[] = {
        mondo::AreaId::PIAZZA_GRANDE, mondo::AreaId::VIA_DEI_CONSOLI, mondo::AreaId::LARGO_BARGELLO,
        mondo::AreaId::SAN_MARTINO, mondo::AreaId::PIAZZA_QUARANTA_MARTIRI, mondo::AreaId::SAN_PIETRO,
        mondo::AreaId::VIA_XX_SETTEMBRE, mondo::AreaId::SANT_AGOSTINO, mondo::AreaId::SANT_ANDREA,
        mondo::AreaId::DUOMO_DUCALE,
    };
    constexpr const char* FASI[] = { "ultimatum", "digiuno", "notte" };

    for(int fase = 0; fase < 3; ++fase)
    {
        if(fase == 1)
        {
            accendi_una(g_game_state, int(Bandiera::CITTA_IN_DIGIUNO));
        }

        if(fase == 2)
        {
            accendi_una(g_game_state, int(Bandiera::RIENTRO_PORTA_METAURO));
        }

        for(mondo::AreaId area : AREE)
        {
            Storia gente;
            esplorazione.entra(area, 0);
            esplorazione.imposta_notte(fase == 2);

            for(int f = 0; f < 200; ++f)
            {
                ++g_game_state.frames;
                esplorazione.aggiorna();
                gente.anima_la_gente(esplorazione);

                if(f == 100 || f == 180)
                {
                    BN_LOG("Istantanea folla_", int(area), "_", FASI[fase], "_", f == 100 ? 1 : 2);
                }

                bn::core::update();
            }
        }
    }

    BN_LOG("Istantanee finite");

    while(true)
    {
        bn::core::update();
    }
}

}
