#include "bn_bg_maps.h"
#include "bn_bg_tiles.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_memory.h"
#include "bn_optional.h"
#include "bn_sprite_tiles.h"
#include "bn_sprites.h"

#include "esplorazione.h"
#include "mondo_autotest.h"
#include "schermate.h"

namespace gubbio
{

namespace
{
    constexpr int PIXEL_PER_FRAME = 4;
    constexpr int INCHIOSTRO = 2;

    struct Picchi
    {
        int sprite = 0;
        int tile_obj = 0;
        int blocchi_bg = 0;
        int stack_iwram = 0;
        int cpu_centesimi = 0;     // il frame piu' pesante, in centesimi del budget di un frame
        int frame_oltre = 0;       // frame che hanno sforato il budget
    };

    int massimo(int a, int b)
    {
        return a > b ? a : b;
    }

    // Ridisegna la scena dopo ogni passo dell'autotest e, una volta ogni PIXEL_PER_FRAME pixel o a
    // ogni evento, chiude il frame misurando i picchi.
    class OsservatoreGba
    {

    public:
        Esplorazione* esplorazione = nullptr;
        Picchi picchi;
        int pixel = 0;

        void operator()(const mondo::Esploratore& e, mondo::Evento evento)
        {
            esplorazione->esploratore() = e;
            esplorazione->sincronizza(evento);

            if(++pixel % PIXEL_PER_FRAME && evento == mondo::Evento::NESSUNO)
            {
                return;
            }

            esplorazione->aggiorna();
            picchi.sprite = massimo(picchi.sprite, bn::sprites::used_items_count());
            picchi.tile_obj = massimo(picchi.tile_obj, bn::sprite_tiles::used_tiles_count());
            picchi.blocchi_bg = massimo(picchi.blocchi_bg, bn::bg_tiles::used_blocks_count() + bn::bg_maps::used_blocks_count());
            picchi.stack_iwram = massimo(picchi.stack_iwram, bn::memory::used_stack_iwram());
            bn::core::update();

            // last_cpu_usage(): la frazione del frame appena chiuso spesa a lavorare (1 = tutto il
            // frame). Comprende i passi del navigatore, quindi e' una stima per eccesso.
            int cpu = (bn::core::last_cpu_usage() * 100).right_shift_integer();
            picchi.cpu_centesimi = massimo(picchi.cpu_centesimi, cpu);
            picchi.frame_oltre += cpu >= 100 ? 1 : 0;
        }

        // La ricerca della strada (fino a 128x128 celle) e' dell'autotest: chiude un frame suo, che
        // non si misura, e il frame dopo contiene solo cammino e scena.
        void strada_pronta()
        {
            bn::core::update();
        }
    };

    // ~96 KB: il navigatore tiene tre tabelle da LATO_MAX x LATO_MAX celle. Sta in EWRAM, non sullo stack, e
    // nella parte azzerata (BSS): si costruisce solo quando la camminata parte. Prima era nella EWRAM
    // inizializzata, cioe' anche 96 KB di ROM copiati in EWRAM a ogni accensione, anche nel gioco vero
    // (Loop 8 della revisione).
    BN_DATA_EWRAM_BSS bn::optional<mondo::AutotestMondo<OsservatoreGba>> g_camminata;
}

void camminata_automatica(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette)
{
    OsservatoreGba osservatore;
    osservatore.esplorazione = &esplorazione;
    esplorazione.entra(mondo::AreaId::PIAZZA_GRANDE, 0);

    g_camminata.emplace();
    mondo::EsitoMondo esito = g_camminata->esegui(osservatore);
    esplorazione.nascondi_etichetta();
    const Picchi& p = osservatore.picchi;
    BN_LOG("Camminata: ", esito.archi, " archi, ", esito.pixel, " pixel, errore ", int(esito.errore),
           ", picchi: sprite ", p.sprite, ", tile OBJ ", p.tile_obj, ", blocchi BG ", p.blocchi_bg,
           ", stack IWRAM ", p.stack_iwram, ", CPU massima ", p.cpu_centesimi, "%, frame oltre il budget ",
           p.frame_oltre);

    struct Riga
    {
        testi::TestoId etichetta;
        int valore;
    };

    const Riga righe[] = {
        { testi::TestoId::HUD_ARCHI, esito.archi },
        { testi::TestoId::HUD_ERRORI, int(esito.errore) },
        { testi::TestoId::HUD_PIXEL, esito.pixel > 32767 ? 32767 : esito.pixel },
        { testi::TestoId::HUD_SPRITE, p.sprite },
        { testi::TestoId::HUD_TILE_OBJ, p.tile_obj },
        { testi::TestoId::HUD_BLOCCHI_BG, p.blocchi_bg },
        { testi::TestoId::HUD_STACK, p.stack_iwram },
    };

    bn::vector<VistaTesto, 8> etichette;
    bn::vector<VistaNumero, 8> numeri;
    int y = 24;

    for(const Riga& r : righe)
    {
        etichette.emplace_back(testo::Contesto::HUD, 16, y, INCHIOSTRO, palette);
        etichette.back().mostra(r.etichetta);
        etichette.back().rivela_tutto();
        numeri.emplace_back(128, y, INCHIOSTRO, palette);
        numeri.back().mostra(r.valore);
        y += 14;
    }

    etichette.emplace_back(testo::Contesto::HUD, 16, y + 8, INCHIOSTRO, palette);
    etichette.back().mostra(testi::TestoId::HUD_PREMI_A);
    etichette.back().rivela_tutto();

    while(! bn::keypad::a_pressed())
    {
        bn::core::update();
    }
}

}
