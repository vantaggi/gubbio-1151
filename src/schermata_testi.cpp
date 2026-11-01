#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"

#include "game_state.h"
#include "stile/cornice.h"
#include "testo_autotest.h"
#include "schermate.h"
#include "vista_testo.h"

// Schermata di prova della fase F1 (all'avvio con L premuto): fa scorrere i nomi delle aree, l'HUD con i numeri e le
// battute piu' lunghe e piu' accentate nel riquadro del dialogo, per il controllo a occhio.
// A completa la battuta o passa alla successiva; senza tasti va avanti da sola.
namespace gubbio
{

namespace
{
    using gubbio::testo::Contesto;
    using gubbio::testo::TestoId;

    constexpr TestoId ELENCO_AREE[] = {
        TestoId::AREA_PIAZZA_GRANDE, TestoId::AREA_BOTTACCIONE, TestoId::AREA_MONTE_INGINO,
        TestoId::AREA_LARGO_BARGELLO, TestoId::AREA_VIA_DEI_CONSOLI, TestoId::AREA_VIA_XX_SETTEMBRE,
        TestoId::AREA_SANT_AGOSTINO, TestoId::AREA_SANT_ANDREA, TestoId::AREA_SAN_MARTINO,
        TestoId::AREA_QUARANTA_MARTIRI, TestoId::AREA_SAN_PIETRO, TestoId::AREA_DUOMO_DUCALE,
        TestoId::AREA_BASILICA, TestoId::AREA_TEATRO_ROMANO,
    };

    constexpr TestoId BATTUTE[] = {
        TestoId::PROVA_ANNO_1151, TestoId::PROVA_ACCENTI, TestoId::PROVA_MAIUSCOLE_LUNGHE,
        TestoId::PROVA_UBALDO, TestoId::PROVA_CORTA, TestoId::PROVA_PUNTEGGIATURA,
    };

    constexpr int ELENCO_AREE_CONTEGGIO = int(sizeof(ELENCO_AREE) / sizeof(ELENCO_AREE[0]));
    constexpr int BATTUTE_CONTEGGIO = int(sizeof(BATTUTE) / sizeof(BATTUTE[0]));

    constexpr int INCHIOSTRO_SCURO = 1;    // ruolo "testo" della cornice: sul fondo chiaro
    constexpr int INCHIOSTRO_CHIARO = 2;   // ruolo "testo_cartiglio": sullo sfondo scuro
    constexpr int ATTESA_DOPO_TESTO = 120; // frame prima di passare da sola al testo successivo
}

void schermata_testi(const bn::sprite_palette_ptr& palette)
{
    bn::bg_palettes::set_transparent_color(bn::color(GUBBIO_VOCE(gubbio::stile::CORNICE_PALETTE, 1)));

    // Il conteggio dell'autotest, rifatto sul GBA: lo stesso che a tempo di compilazione deve
    // dare zero errori.
    gubbio::testo::EsitoAutotest esito = gubbio::testo::autotest_testi();
    BN_LOG("Autotest testi: ", esito.passi, " passi, ", esito.pixel, " pixel, errore ", int(esito.errore));

    bn::regular_bg_ptr riquadro = gubbio::crea_riquadro_dialogo();

    gubbio::VistaTesto area(Contesto::AREA, 24, 8, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaTesto etichetta_pv(Contesto::HUD, 8, 32, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaTesto etichetta_oro(Contesto::HUD, 8, 46, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaTesto etichetta_passi(Contesto::HUD, 8, 60, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaTesto etichetta_errori(Contesto::HUD, 8, 74, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaNumero numero_pv(64, 32, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaNumero numero_oro(64, 46, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaNumero numero_passi(64, 60, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaNumero numero_errori(64, 74, INCHIOSTRO_CHIARO, palette);
    gubbio::VistaTesto dialogo(Contesto::DIALOGO, gubbio::stile::DIALOGO_X + 8, gubbio::stile::DIALOGO_Y + 8,
                               INCHIOSTRO_SCURO, palette);

    etichetta_pv.mostra(TestoId::HUD_PV);
    etichetta_oro.mostra(TestoId::HUD_ORO);
    etichetta_passi.mostra(TestoId::HUD_AUTOTEST);
    etichetta_errori.mostra(TestoId::HUD_ERRORI);
    etichetta_pv.rivela_tutto();
    etichetta_oro.rivela_tutto();
    etichetta_passi.rivela_tutto();
    etichetta_errori.rivela_tutto();
    numero_passi.mostra(esito.passi > 32767 ? 32767 : esito.passi);
    numero_errori.mostra(int(esito.errore));

    int indice_area = 0;
    int indice_battuta = 0;
    int attesa_area = 0;
    int attesa_battuta = 0;
    int valore = -32768;

    area.mostra(ELENCO_AREE[indice_area]);
    dialogo.mostra(BATTUTE[indice_battuta]);

    while(true)
    {
        ++gubbio::g_game_state.frames;

        // Macchina da scrivere: un glifo ogni due frame.
        if(gubbio::g_game_state.frames % 2 == 0)
        {
            area.avanza();
            dialogo.avanza();
        }

        if(bn::keypad::a_pressed())
        {
            if(dialogo.completo())
            {
                attesa_battuta = ATTESA_DOPO_TESTO;
            }
            else
            {
                dialogo.rivela_tutto();
            }
        }

        if(area.completo() && ++attesa_area >= ATTESA_DOPO_TESTO)
        {
            attesa_area = 0;
            indice_area = (indice_area + 1) % ELENCO_AREE_CONTEGGIO;
            area.mostra(ELENCO_AREE[indice_area]);
        }

        if(dialogo.completo() && ++attesa_battuta >= ATTESA_DOPO_TESTO)
        {
            attesa_battuta = 0;
            indice_battuta = (indice_battuta + 1) % BATTUTE_CONTEGGIO;
            dialogo.mostra(BATTUTE[indice_battuta]);
        }

        // I numeri dell'HUD percorrono tutto int16, a passi che toccano anche gli estremi.
        valore += 257;

        if(valore > 32767)
        {
            valore = -32768;
        }

        numero_pv.mostra(valore);
        numero_oro.mostra(valore < 0 ? -valore - 1 : valore);

        bn::core::update();
    }
}

}
