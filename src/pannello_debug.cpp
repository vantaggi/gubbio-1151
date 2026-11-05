#include "pannello_debug.h"

#include "bn_core.h"
#include "bn_fixed.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_memory.h"

namespace gubbio
{

namespace
{
    constexpr int X = 2;            // pixel dello schermo, dall'angolo in alto a sinistra
    constexpr int Y = 2;
    constexpr int PASSO = 12;       // fra una riga e l'altra
    constexpr int CHIARO = 2;       // gli indici della palette del testo: chiaro col contorno scuro, si legge
    constexpr int CONTORNO = 1;     // su ogni fondo (STANDARD_GRAFICO P1, C6)
    constexpr int Z_SOPRA = -32767; // sopra tutti gli altri sprite
}

Misure misura_ora()
{
    Misure m;
    m.cpu_percento = (bn::core::last_cpu_usage() * 100).right_shift_integer();
    // KB come x / 1024: uno shift, niente divisione software
    m.ewram_libera_kb = bn::memory::available_alloc_ewram() >> 10;
    m.iwram_usata_kb = (bn::memory::used_static_iwram() + bn::memory::used_stack_iwram()) >> 10;
    return m;
}

PannelloDebug::PannelloDebug(const bn::sprite_palette_ptr& palette) :
    _palette(palette)
{
}

bool PannelloDebug::aggiorna()
{
    bool tasti = bn::keypad::l_held() && bn::keypad::select_pressed();

    if(tasti)
    {
        if(acceso())
        {
            spegni();
        }
        else
        {
            _cpu.emplace(X, Y, CHIARO, _palette, CONTORNO);
            _ewram.emplace(X, Y + PASSO, CHIARO, _palette, CONTORNO);
            _iwram.emplace(X, Y + 2 * PASSO, CHIARO, _palette, CONTORNO);
            _attesa = 0;
        }
    }

    if(acceso() && --_attesa <= 0)
    {
        _attesa = OGNI;
        _misura();
    }

    return tasti;
}

void PannelloDebug::spegni()
{
    _cpu.reset();
    _ewram.reset();
    _iwram.reset();
}

void PannelloDebug::_misura()
{
    Misure m = misura_ora();
    VistaNumero* righe[] = { &*_cpu, &*_ewram, &*_iwram };
    char lettere[] = { 'C', 'E', 'I' };
    int valori[] = { m.cpu_percento, m.ewram_libera_kb, m.iwram_usata_kb };

    for(int i = 0; i < 3; ++i)
    {
        righe[i]->mostra_con_lettera(lettere[i], valori[i]);
        righe[i]->colloca(X, Y + i * PASSO);
        righe[i]->porta_sopra(Z_SOPRA);
    }

    BN_LOG("DEBUG cpu ", m.cpu_percento, " ewram_kb ", m.ewram_libera_kb, " iwram_kb ", m.iwram_usata_kb);
}

}
