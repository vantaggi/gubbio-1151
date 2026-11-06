#include "limiti.h"

#include "bn_assert.h"
#include "bn_bg_maps.h"
#include "bn_bg_palettes.h"
#include "bn_bg_tiles.h"
#include "bn_bgs.h"
#include "bn_core.h"
#include "bn_log.h"
#include "bn_memory.h"
#include "bn_sprite_affine_mats.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_tiles.h"
#include "bn_sprites.h"

#include "game_state.h"

namespace gubbio::limiti
{

namespace
{
    // l'ultimo posto noto, per la riga dell'assert
    int g_area = -1;
    int g_x = 0;
    int g_y = 0;

    void all_assert()
    {
        // niente allocazioni ne' altri assert qui: Butano si sta fermando
        BN_LOG("ASSERT scattato area ", g_area, " x ", g_x, " y ", g_y, " frame ", int(g_game_state.frames));
    }

#if defined(GUBBIO_LIMITI) || defined(GUBBIO_PALETTE)
    constexpr int IWRAM_TOTALE = 32 * 1024;

    // Una risorsa: quanta se ne usa e quanta ne resta libera (il tetto e' la somma).
    struct Risorsa
    {
        const char* nome;
        int (*usata)();
        int (*libera)();
    };

    int sprite_usati() { return bn::sprites::used_items_count(); }
    int sprite_liberi() { return bn::sprites::available_items_count(); }
    int tile_sprite_usati() { return bn::sprite_tiles::used_tiles_count(); }
    int tile_sprite_liberi() { return bn::sprite_tiles::available_tiles_count(); }
    int pezzi_tile_sprite_usati() { return bn::sprite_tiles::used_items_count(); }
    int pezzi_tile_sprite_liberi() { return bn::sprite_tiles::available_items_count(); }
    int colori_sprite_usati() { return bn::sprite_palettes::used_colors_count(); }
    int colori_sprite_liberi() { return bn::sprite_palettes::available_colors_count(); }
    int matrici_usate() { return bn::sprite_affine_mats::used_count(); }
    int matrici_libere() { return bn::sprite_affine_mats::available_count(); }
    int fondali_usati() { return bn::bgs::used_items_count(); }
    int fondali_liberi() { return bn::bgs::available_items_count(); }
    int tile_fondali_usati() { return bn::bg_tiles::used_tiles_count(); }
    int tile_fondali_liberi() { return bn::bg_tiles::available_tiles_count(); }
    int celle_mappe_usate() { return bn::bg_maps::used_cells_count(); }
    int celle_mappe_libere() { return bn::bg_maps::available_cells_count(); }
    // i 32 blocchi da 2 KB della VRAM dei fondali, divisi fra tile e mappe
    int blocchi_vram_usati() { return bn::bg_tiles::used_blocks_count() + bn::bg_maps::used_blocks_count(); }
    int blocchi_vram_liberi() { return bn::bg_maps::available_blocks_count(); }
    int colori_fondali_usati() { return bn::bg_palettes::used_colors_count(); }
    int colori_fondali_liberi() { return bn::bg_palettes::available_colors_count(); }
    int stack_usato() { return bn::memory::used_stack_iwram(); }
    int stack_libero() { return IWRAM_TOTALE - bn::memory::used_static_iwram() - bn::memory::used_stack_iwram(); }
    int ewram_usata() { return bn::memory::used_alloc_ewram(); }
    int ewram_libera() { return bn::memory::available_alloc_ewram(); }

    constexpr Risorsa RISORSE[] = {
        { "sprite", sprite_usati, sprite_liberi },
        { "tile_sprite", tile_sprite_usati, tile_sprite_liberi },
        { "pezzi_tile_sprite", pezzi_tile_sprite_usati, pezzi_tile_sprite_liberi },
        { "colori_sprite", colori_sprite_usati, colori_sprite_liberi },
        { "matrici_affini", matrici_usate, matrici_libere },
        { "fondali", fondali_usati, fondali_liberi },
        { "tile_fondali", tile_fondali_usati, tile_fondali_liberi },
        { "celle_mappe", celle_mappe_usate, celle_mappe_libere },
        { "blocchi_vram_fondali", blocchi_vram_usati, blocchi_vram_liberi },
        { "colori_fondali", colori_fondali_usati, colori_fondali_liberi },
        { "stack_iwram", stack_usato, stack_libero },
        { "ewram_allocata", ewram_usata, ewram_libera },
    };
    constexpr int QUANTE = int(sizeof(RISORSE) / sizeof(RISORSE[0]));

    BN_DATA_EWRAM_BSS int g_picco[QUANTE];
    BN_DATA_EWRAM_BSS int g_prima[QUANTE];
    BN_DATA_EWRAM_BSS int g_picco_sprite_palette;
    BN_DATA_EWRAM_BSS int g_picco_bg_palette;
    BN_DATA_EWRAM_BSS int g_area_segnata;
    BN_DATA_EWRAM_BSS int g_battito;

    void misura()
    {
#ifdef GUBBIO_PALETTE
        // il formato di sempre delle prove "palette_*" (tests/mgba/prove.json)
        {
            int s = bn::sprite_palettes::used_colors_count();
            int b = bn::bg_palettes::used_colors_count();

            if(s > g_picco_sprite_palette || b > g_picco_bg_palette)
            {
                g_picco_sprite_palette = s > g_picco_sprite_palette ? s : g_picco_sprite_palette;
                g_picco_bg_palette = b > g_picco_bg_palette ? b : g_picco_bg_palette;
                BN_LOG("PALETTE picco sprite ", g_picco_sprite_palette, " fondali ", g_picco_bg_palette);

                if(s >= 224)
                {
                    bn::sprite_palettes::log_status();
                }
            }
        }
#endif

#ifdef GUBBIO_LIMITI
#ifdef GUBBIO_PROVA_ASSERT
        // la prova della rete (prova "rete" in tests/mgba/prove.json): un assert voluto, che il banco deve vedere
        BN_ASSERT(g_battito < 600, "Prova della rete: assert voluto");
#endif

        // il battito: il banco dice "!! bloccato" se il gioco non chiama piu' bn::core::update()
        if(++g_battito == 7200)
        {
            g_battito = 0;
            BN_LOG("LIMITI vivo frame ", int(g_game_state.frames));
        }

        if(g_area != g_area_segnata)
        {
            g_area_segnata = g_area;
            BN_LOG("LIMITI area ", g_area);
        }

        for(int i = 0; i < QUANTE; ++i)
        {
            const Risorsa& r = RISORSE[i];
            // Butano rende la VRAM lasciata (tile, mappe, palette) solo dentro bn::core::update(), dopo questa
            // misura, o subito se ne serve per crearne altra: nel frame del cambio d'area si contano insieme
            // l'area vecchia e la nuova, che non stanno mai davvero insieme. Conta l'uso di due frame di fila.
            int ora = r.usata();
            int usata = ora < g_prima[i] ? ora : g_prima[i];
            g_prima[i] = ora;

            if(usata > g_picco[i])
            {
                g_picco[i] = usata;
                int tetto = ora + r.libera();
                // la percentuale solo al nuovo picco (poche volte per partita): la divisione qui non pesa
                int percento = tetto > 0 ? usata * 100 / tetto : 0;
                BN_LOG("LIMITI picco ", r.nome, " ", usata, " su ", tetto, " (", percento, "%) area ", g_area,
                       " frame ", int(g_game_state.frames));
            }
        }
#endif
    }
#endif
}

void installa()
{
    bn::assert::set_callback(all_assert);

#if defined(GUBBIO_LIMITI) || defined(GUBBIO_PALETTE)
    g_picco_sprite_palette = 0;
    g_picco_bg_palette = 0;
    g_area_segnata = -2;
    g_battito = 0;

    for(int i = 0; i < QUANTE; ++i)
    {
        g_picco[i] = 0;
        g_prima[i] = 0;
    }

    bn::core::set_update_callback(misura);
#endif
}

void segna_area(int area, int x, int y)
{
    g_area = area;
    g_x = x;
    g_y = y;
}

}
