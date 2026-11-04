#include "opzioni.h"

#include "bn_bg_palettes.h"
#include "bn_common.h"
#include "bn_fixed.h"
#include "bn_sprite_palettes.h"
#include "bn_sram.h"

#include "audio.h"

namespace gubbio::opzioni
{

BN_DATA_EWRAM_BSS Opzioni g_opzioni;

namespace
{
    // la luminosita' di Butano (0..1) per «piu' chiaro»: abbastanza da leggere senza luce, non da sbiadire
    constexpr bn::fixed CHIARO = 0.15;
}

void carica()
{
    Record r;
    bn::sram::read_offset(r, SCOSTAMENTO);
    g_opzioni = da_record(r);
}

void salva()
{
    Record r = componi(g_opzioni);
    bn::sram::write_offset(r, SCOSTAMENTO);
}

void applica()
{
    audio::volumi(g_opzioni.musica, g_opzioni.effetti);
    bn::fixed luce = g_opzioni.piu_chiaro ? CHIARO : bn::fixed(0);
    bn::bg_palettes::set_brightness(luce);
    bn::sprite_palettes::set_brightness(luce);
}

}
