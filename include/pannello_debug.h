#ifndef GUBBIO_PANNELLO_DEBUG_H
#define GUBBIO_PANNELLO_DEBUG_H

#include "bn_optional.h"
#include "bn_sprite_palette_ptr.h"

#include "vista_testo.h"

// Il pannello di debug (docs/regole_sviluppo_gba.md, punto 5): L+Select lo accende e lo spegne, in esplorazione.
// In alto a sinistra tre misure, aggiornate ogni 15 frame per non falsare la CPU con il disegno stesso:
//   C  la CPU dell'ultimo frame, in percento
//   E  la EWRAM ancora libera per l'allocatore di Butano, in KB (il gioco non ne usa: deve restare piena)
//   I  la IWRAM usata (statica + stack), in KB (su 32)
// Spento non occupa niente: gli sprite (tre, sui 128) si creano quando si accende e si rendono quando si spegne.
namespace gubbio
{

class PannelloDebug
{
public:
    static constexpr int OGNI = 15;         // frame fra due aggiornamenti

    explicit PannelloDebug(const bn::sprite_palette_ptr& palette);

    // Una volta per frame, prima di bn::core::update(). Dice se il pannello ha usato i tasti (L tenuto e
    // Select appena premuto): allora Select non vale per il resto del gioco in questo frame.
    bool aggiorna();
    void spegni();

    [[nodiscard]] bool acceso() const
    {
        return _cpu.has_value();
    }

private:
    bn::sprite_palette_ptr _palette;
    bn::optional<VistaNumero> _cpu;
    bn::optional<VistaNumero> _ewram;
    bn::optional<VistaNumero> _iwram;
    int _attesa = 0;

    void _misura();
};

// Le misure, in numeri gia' pronti da mostrare (separate dal disegno per poterle provare da sole).
struct Misure
{
    int cpu_percento;
    int ewram_libera_kb;
    int iwram_usata_kb;
};

[[nodiscard]] Misure misura_ora();

}

#endif
