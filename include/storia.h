// GENERATO da tools/genera_storia.py dal copione v1 (copione/*.md): non modificare a mano.
#ifndef GUBBIO_STORIA_H
#define GUBBIO_STORIA_H

#include <cstdint>

#include "mondo.h"
#include "testi.h"

namespace gubbio::storia
{

enum class Bandiera : uint8_t
{
    PROLOGO_VISTO,
    ULTIMATUM_RICEVUTO,
    GIORGIO_NEL_GRUPPO,
    CHIACCHIERA_CONSOLI,
    POSTIERLA_APERTA,
    ANTONIO_NEL_GRUPPO,
    CITTA_IN_DIGIUNO,
    PORTA_DEL_MONTE,
    IMBOSCATA_STRADONI,
    SPIA_CATTURATA,
    CERI_RISVEGLIATI,
    SPETTRI_VINTI,
    VISIONE_BOTTACCIONE,
    BOTTACCIONE_ENTRATI,
    MIASMI_VISTI,
    PIANO_DI_CORRADO,
    CORRADO_INCONTRATO,
    CONDOTTO_SALVO,
    RIENTRO_PORTA_METAURO,
    ATTO_I_COMPLETATO,
    CRONACA_V1_FINITA,
    CORRADO_SCONFITTO,
    BORGO_DENTRO,
    BORGO_FUORI,
    ESULE_PRIGIONIERO,
    ESULE_LIBERATO,
    GIUSTIZIA_OFFERTA,
    ALBA_CONFERMATA,
    CONTEGGIO,
};

inline constexpr int SCENE = 20;
inline constexpr int NESSUNA_AREA = -1;

enum class TipoBattuta : uint8_t
{
    PERSONAGGIO,
    NARRATORE,
    AREA,
    SISTEMA,
    OBIETTIVO,
    SCELTA,
};

enum class Espressione : uint8_t
{
    CALMO,
    PREOCCUPATO,
    DECISO,
};

enum class TipoGuardia : uint8_t
{
    SEMPRE,
    BANDIERA,
    NON_BANDIERA,
    SCELTA,
    ALMENO_DUE,
    VARIANTE_BANDIERA,
    VARIANTE_NON_BANDIERA,
    OGGETTO_E_NON_BANDIERA,
    CONTEGGIO,
    CONTEGGIO_E_NON_BANDIERA,
};

// La guardia di una battuta: la si recita solo se vale (le varianti del copione v2). a, b, c sono
// bandiere (0-127), la voce scelta nell'ultimo menu (SCELTA) o l'oggetto (OGGETTO_E_NON_BANDIERA).
struct Guardia
{
    TipoGuardia tipo;
    uint8_t a;
    uint8_t b;
    uint8_t c;
};

inline constexpr uint8_t NESSUNA_BANDIERA = 255;

struct Battuta
{
    testi::TestoId testo;         // per una SCELTA: la prima voce
    testi::TestoId parlante;     // per un PERSONAGGIO; per una SCELTA: la seconda voce
    TipoBattuta tipo;
    Espressione espressione;
    uint8_t guardia;              // GUARDIA
    uint8_t accende[2];          // SCELTA: la bandiera che accende ogni voce, o NESSUNA_BANDIERA
    int8_t consuma;              // SCELTA: l'oggetto che la prima voce consuma, o -1
};

struct Scena
{
    const char* codice;
    testi::TestoId titolo;
    bool cutscene;
    int8_t regia;                // la cutscene (regia::CUTSCENE_DATI), -2 dentro la precedente
    int8_t area;                 // mondo::AreaId, o NESSUNA_AREA (a schermo intero)
    uint64_t richieste;          // tutte accese
    uint64_t vietate;            // nessuna accesa
    uint64_t imposta;            // accese alla fine
    int8_t segue;                // la scena che deve essere gia' fatta, o -1
    int8_t battaglia;            // battaglia::INCONTRO, o -1
    uint16_t prima_battuta;
    uint16_t battute;
};

inline constexpr int BATTUTE = 229;
inline constexpr Battuta BATTUTA[BATTUTE] = {
    { testi::TestoId::C_P_01_00, testi::TestoId::C_P_01_00, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_01_01, testi::TestoId::C_P_01_01, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_01_02, testi::TestoId::C_P_01_02, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_00, testi::TestoId::C_P_02_00, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_01, testi::TestoId::C_P_02_01, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_02, testi::TestoId::C_P_02_02, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_03, testi::TestoId::C_P_02_03, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_04, testi::TestoId::C_P_02_04, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_05, testi::TestoId::C_P_02_05, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_P_02_06, testi::TestoId::C_P_02_06, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_00, testi::TestoId::C_A1_01_00, TipoBattuta::AREA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_01, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_02, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_03, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_04, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_05, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_06, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_07, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_08, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_10, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_11, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_12, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_13, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_14, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_15, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_16, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_17, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_18, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_19, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_20, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_21, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_22, testi::TestoId::C_A1_01_22, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_01_23, testi::TestoId::C_A1_01_23, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_02_00, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_02_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_00, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_02, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_03, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_04, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_06, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_03_07, testi::TestoId::C_A1_03_07, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_00, testi::TestoId::PARLANTE_FANTE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_01, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_02, testi::TestoId::PARLANTE_FANTE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_03, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_04, testi::TestoId::C_A1_04_04, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_05, testi::TestoId::C_A1_04_05, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_06, testi::TestoId::C_A1_04_06, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_07, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_08, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_10, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_11, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_12, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_13, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_14, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_15, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_16, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_17, testi::TestoId::C_A1_04_17, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_04_18, testi::TestoId::C_A1_04_18, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_00, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_04, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_05, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_06, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_08, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_09, testi::TestoId::C_A1_05_09, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_10, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_11, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_12, testi::TestoId::C_A1_05_12, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_13, testi::TestoId::C_A1_05_13, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_00, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_01, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_02, testi::TestoId::PARLANTE_FAZIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_03, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_04, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_05_A, testi::TestoId::C_A1_05B_05_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 22, 23 }, -1 },
    { testi::TestoId::C_A1_05B_06, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_07, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_08, testi::TestoId::C_A1_05B_08, TipoBattuta::SISTEMA, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_10, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05B_11, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_06_00, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_06_01, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_06_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_06_03, testi::TestoId::C_A1_06_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_00, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_02, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_04, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_05, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_06, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_07, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_08, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_09, testi::TestoId::PARLANTE_SPIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_10, testi::TestoId::PARLANTE_SPIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_11, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_12, testi::TestoId::PARLANTE_SPIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_13, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_14, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_07_15, testi::TestoId::C_A1_07_15, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_00, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_02, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_04, testi::TestoId::C_A1_08_04, TipoBattuta::AREA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_06, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_07, testi::TestoId::C_A1_08_07, TipoBattuta::AREA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_08, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_09, testi::TestoId::C_A1_08_09, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_10, testi::TestoId::C_A1_08_10, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_11, testi::TestoId::C_A1_08_11, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_12, testi::TestoId::C_A1_08_12, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_13, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_14, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_15, testi::TestoId::C_A1_08_15, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_16, testi::TestoId::PARLANTE_SPETTRO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_17, testi::TestoId::PARLANTE_SPETTRO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_18, testi::TestoId::PARLANTE_SPETTRO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_19, testi::TestoId::C_A1_08_19, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_20, testi::TestoId::C_A1_08_20, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_21, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_22, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_23, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_08_24, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_00, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 3, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_01, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 3, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 3, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_04, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_05, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_06, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_08, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_10, testi::TestoId::C_A1_09_10, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_09_11, testi::TestoId::C_A1_09_11, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_00, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_01, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_02, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 4, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_03, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 5, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 4, { 255, 255 }, -1 },
    { testi::TestoId::C_B_01_05, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 5, { 255, 255 }, -1 },
    { testi::TestoId::C_B_02_00, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_02_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_02_02, testi::TestoId::C_B_02_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_00, testi::TestoId::PARLANTE_GUERRIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_01, testi::TestoId::PARLANTE_GUERRIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_02, testi::TestoId::PARLANTE_GUERRIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_03, testi::TestoId::PARLANTE_GUERRIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_04, testi::TestoId::PARLANTE_GUERRIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_06, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 6, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_08, testi::TestoId::PARLANTE_RAGAZZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_09, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_10, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_11_A, testi::TestoId::C_B_03_11_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 24, 25 }, -1 },
    { testi::TestoId::C_B_03_12, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_13, testi::TestoId::PARLANTE_RAGAZZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_14, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_15, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_B_03_16, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_00, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_01, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_02, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_04, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 7, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_06, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_07, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_08, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_09, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_10, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_11, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_12, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_13, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_14, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_15, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_16, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_17, testi::TestoId::C_B_04_17, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_18, testi::TestoId::C_B_04_18, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_00, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_02, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_03, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_04, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_05, testi::TestoId::C_B_05_05, TipoBattuta::AREA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_06, testi::TestoId::PARLANTE_FOLLA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 8, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 8, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_08, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 8, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_10, testi::TestoId::C_B_05_10, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_11_A, testi::TestoId::C_B_05_11_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 27, 255 }, -1 },
    { testi::TestoId::C_B_05_12, testi::TestoId::C_B_05_12, TipoBattuta::OBIETTIVO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_13, testi::TestoId::C_B_05_13, TipoBattuta::SISTEMA, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_14, testi::TestoId::C_B_05_14, TipoBattuta::OBIETTIVO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_00, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_01_A, testi::TestoId::C_E_01_01_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 26, 255 }, -1 },
    { testi::TestoId::C_E_01_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_04, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_05, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_06, testi::TestoId::PARLANTE_CIACCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_08, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_09, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_10, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_11, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_12, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_13, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_14, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_15, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 9, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_16, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 10, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_17, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_18, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_19, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_00, testi::TestoId::C_E_02_00, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_01, testi::TestoId::C_E_02_01, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_02, testi::TestoId::C_E_02_02, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
};

inline constexpr Scena SCENA[SCENE] = {
    { "P-00", testi::TestoId::SCENA_P_00, false, -1, NESSUNA_AREA, 0x0u, 0x0u, 0x0u, -1, -1, 0, 0 },
    { "P-01", testi::TestoId::SCENA_P_01, true, 1, NESSUNA_AREA, 0x0u, 0x0u, 0x0u, 0, -1, 0, 3 },
    { "P-02", testi::TestoId::SCENA_P_02, true, -2, NESSUNA_AREA, 0x0u, 0x0u, 0x1u, 1, -1, 3, 7 },
    { "A1-01", testi::TestoId::SCENA_A1_01, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x1u, 0x0u, 0x6u, -1, -1, 10, 24 },
    { "A1-02", testi::TestoId::SCENA_A1_02, false, -1, int8_t(mondo::AreaId::VIA_DEI_CONSOLI), 0x2u, 0x48u, 0x8u, -1, -1, 34, 2 },
    { "A1-03", testi::TestoId::SCENA_A1_03, false, -1, int8_t(mondo::AreaId::SAN_MARTINO), 0x2u, 0x10u, 0x10u, -1, -1, 36, 8 },
    { "A1-04", testi::TestoId::SCENA_A1_04, false, -1, int8_t(mondo::AreaId::TEATRO_ROMANO), 0x10u, 0x20u, 0x20u, -1, 0, 44, 19 },
    { "A1-05", testi::TestoId::SCENA_A1_05, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x20u, 0x40u, 0x40u, -1, -1, 63, 14 },
    { "A1-05b", testi::TestoId::SCENA_A1_05B, false, -1, int8_t(mondo::AreaId::SANT_ANDREA), 0x40u, 0xC00000u, 0x0u, -1, -1, 77, 12 },
    { "A1-06", testi::TestoId::SCENA_A1_06, false, -1, int8_t(mondo::AreaId::DUOMO_DUCALE), 0x40u, 0x80u, 0x80u, -1, -1, 89, 4 },
    { "A1-07", testi::TestoId::SCENA_A1_07, false, -1, int8_t(mondo::AreaId::MONTE_INGINO), 0x80u, 0x0u, 0x300u, -1, 1, 93, 16 },
    { "A1-08", testi::TestoId::SCENA_A1_08, false, -1, int8_t(mondo::AreaId::BASILICA_INTERNO), 0x200u, 0x0u, 0xC00u, -1, 3, 109, 25 },
    { "A1-09", testi::TestoId::SCENA_A1_09, false, -1, int8_t(mondo::AreaId::BASILICA_INTERNO), 0x800u, 0x0u, 0x1000u, -1, -1, 134, 12 },
    { "B-01", testi::TestoId::SCENA_B_01, false, -1, int8_t(mondo::AreaId::GOLA_STRISCIA), 0x1000u, 0x2000u, 0x2000u, -1, -1, 146, 6 },
    { "B-02", testi::TestoId::SCENA_B_02, false, -1, int8_t(mondo::AreaId::GOLA_MIASMI), 0x0u, 0x0u, 0x4000u, 13, -1, 152, 3 },
    { "B-03", testi::TestoId::SCENA_B_03, false, -1, int8_t(mondo::AreaId::GOLA_ARCO), 0x0u, 0x0u, 0x8000u, 14, 4, 155, 17 },
    { "B-04", testi::TestoId::SCENA_B_04, false, -1, int8_t(mondo::AreaId::CONDOTTO), 0x0u, 0x0u, 0x230000u, 15, 2, 172, 19 },
    { "B-05", testi::TestoId::SCENA_B_05, false, -1, int8_t(mondo::AreaId::SAN_MARTINO), 0x20000u, 0x0u, 0x40000u, -1, -1, 191, 15 },
    { "E-01", testi::TestoId::SCENA_E_01, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x8040000u, 0x0u, 0x80000u, -1, -1, 206, 20 },
    { "E-02", testi::TestoId::SCENA_E_02, true, 8, NESSUNA_AREA, 0x80000u, 0x0u, 0x100000u, -1, -1, 226, 3 },
};

// Le cutscene dentro le scene: prima della battuta (indice in BATTUTA), la cutscene; le battute del
// narratore che la cutscene dice nelle bande (copre, dalla battuta in poi) non si ripetono nella vista di gioco.
struct Inserto
{
    uint16_t battuta;
    int8_t regia;
    uint8_t copre;
};

inline constexpr int INSERTI = 10;
inline constexpr Inserto INSERTO[INSERTI > 0 ? INSERTI : 1] = {
    { 11, 7, 0 },  // A1-01 prima della battuta 1: C3U
    { 12, 6, 0 },  // A1-01 prima della battuta 2: C3G
    { 14, 2, 0 },  // A1-01 prima della battuta 4: C2
    { 18, 3, 0 },  // A1-01 prima della battuta 8: C2P
    { 45, 4, 0 },  // A1-04 prima della battuta 1: C3A
    { 93, 12, 0 },  // A1-07 prima della battuta 0: C7S
    { 118, 9, 1 },  // A1-08 prima della battuta 9: C5
    { 137, 10, 0 },  // A1-09 prima della battuta 3: C6
    { 146, 11, 0 },  // B-01 prima della battuta 0: C7B
    { 172, 5, 0 },  // B-04 prima della battuta 0: C3C
};

// Le cartoline dei luoghi che partono entrando nell'area della scena (indice in SCENA) quando la scena e'
// pronta e la cutscene (regia::CUTSCENE_DATI) non e' vista; restano anche inserto alla battuta 0.
struct Ingresso
{
    int8_t scena;
    int8_t regia;
};

inline constexpr int INGRESSI = 1;
inline constexpr Ingresso INGRESSO[INGRESSI > 0 ? INGRESSI : 1] = {
    { 10, 12 },  // C7S: entrando in MONTE_INGINO con A1-07 pronta
};

// Le battaglie a meta' scena: la battaglia della scena si combatte prima della battuta (indice in BATTUTA),
// non alla fine; vinta, accende la bandiera (64-127) e non si rigioca. B-03: dopo l'ascolto, prima del ragazzo.
struct BattagliaAMeta
{
    int8_t scena;                 // indice in SCENA
    uint16_t battuta;
    uint8_t vinta;
};

inline constexpr int BATTAGLIE_A_META = 1;
inline constexpr BattagliaAMeta BATTAGLIA_A_META[BATTAGLIE_A_META > 0 ? BATTAGLIE_A_META : 1] = {
    { 15, 163, 90 },  // B-03 prima della battuta 8
};

enum class Fase : uint8_t
{
    ULTIMATUM,
    DIGIUNO,
    NOTTE,
};

struct Npc
{
    int8_t area;
    uint8_t tx;
    uint8_t ty;
    uint16_t prima_frase[3];     // per fase (ULTIMATUM, DIGIUNO, NOTTE); 0xFFFF: non c'e'
    uint8_t frasi[3];
    uint8_t figura;               // FIGURA_NPC (tools/figure_npc.py)
    uint8_t imposta;              // la bandiera che accende parlando, o NESSUNA_BANDIERA
    uint8_t imposta_fasi;         // in quali fasi (bit 0 ULTIMATUM, 1 DIGIUNO, 2 NOTTE)
    uint8_t tx_borgo;             // del borgo: con BORGO_DENTRO, in DIGIUNO e NOTTE, sta qui in Sant'Andrea
    uint8_t ty_borgo;
    bool del_borgo;
};

inline constexpr int FRASI_NPC = 140;
inline constexpr Battuta FRASE_NPC[FRASI_NPC] = {
    { testi::TestoId::NPC_00_05, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_00, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_01, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 11, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_02, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_03_A, testi::TestoId::NPC_00_03_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 27, 255 }, -1 },
    { testi::TestoId::NPC_00_04, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 1, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_04, testi::TestoId::NPC_01_04, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_01, testi::TestoId::NPC_01_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_02, testi::TestoId::NPC_01_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_03, testi::TestoId::NPC_01_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_00, testi::TestoId::NPC_01_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_08, testi::TestoId::NPC_02_08, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_02, testi::TestoId::NPC_02_02, TipoBattuta::SISTEMA, Espressione::CALMO, 12, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_03, testi::TestoId::NPC_02_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_04_A, testi::TestoId::NPC_02_04_B, TipoBattuta::SCELTA, Espressione::CALMO, 13, { 69, 255 }, 0 },
    { testi::TestoId::NPC_02_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_06, testi::TestoId::NPC_02_06, TipoBattuta::SISTEMA, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_07, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_00, testi::TestoId::NPC_02_00, TipoBattuta::SISTEMA, Espressione::CALMO, 12, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_01, testi::TestoId::NPC_02_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_03_00, testi::TestoId::NPC_03_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_02, testi::TestoId::NPC_04_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_01, testi::TestoId::NPC_04_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_00, testi::TestoId::NPC_04_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_02, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 14, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_03, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_00, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 15, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_01, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_02, testi::TestoId::NPC_06_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_01, testi::TestoId::NPC_06_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_00, testi::TestoId::NPC_06_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_03, testi::TestoId::NPC_07_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_01, testi::TestoId::NPC_07_01, TipoBattuta::SISTEMA, Espressione::CALMO, 16, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_02, testi::TestoId::NPC_07_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_00, testi::TestoId::NPC_07_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_08_00, testi::TestoId::NPC_08_00, TipoBattuta::SISTEMA, Espressione::CALMO, 17, { 255, 255 }, -1 },
    { testi::TestoId::NPC_08_01, testi::TestoId::NPC_08_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_02, testi::TestoId::NPC_09_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_01, testi::TestoId::NPC_09_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_00, testi::TestoId::NPC_09_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_03, testi::TestoId::NPC_10_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_01, testi::TestoId::NPC_10_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_02, testi::TestoId::NPC_10_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_00, testi::TestoId::NPC_10_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_04, testi::TestoId::NPC_11_04, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_02, testi::TestoId::NPC_11_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_03, testi::TestoId::NPC_11_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_00, testi::TestoId::NPC_11_00, TipoBattuta::SISTEMA, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_01, testi::TestoId::NPC_11_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_03, testi::TestoId::NPC_12_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_01, testi::TestoId::NPC_12_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_02, testi::TestoId::NPC_12_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_00, testi::TestoId::NPC_12_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_13_01, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_13_00, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_14_02, testi::TestoId::PARLANTE_CIACCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_14_01, testi::TestoId::PARLANTE_CIACCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_14_00, testi::TestoId::PARLANTE_CIACCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_15_02, testi::TestoId::PARLANTE_GIULIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_15_01, testi::TestoId::PARLANTE_GIULIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_15_00, testi::TestoId::PARLANTE_GIULIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_16_02, testi::TestoId::PARLANTE_FLAVIANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_16_01, testi::TestoId::PARLANTE_FLAVIANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_16_00, testi::TestoId::PARLANTE_FLAVIANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_17_02, testi::TestoId::PARLANTE_MASIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_17_01, testi::TestoId::PARLANTE_MASIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_17_00, testi::TestoId::PARLANTE_MASIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_18_02, testi::TestoId::PARLANTE_MONTANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_18_01, testi::TestoId::PARLANTE_MONTANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_18_00, testi::TestoId::PARLANTE_MONTANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_19_02, testi::TestoId::PARLANTE_GIORDANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_19_01, testi::TestoId::PARLANTE_GIORDANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_19_00, testi::TestoId::PARLANTE_GIORDANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_20_02, testi::TestoId::PARLANTE_FEBO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_20_01, testi::TestoId::PARLANTE_FEBO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_20_00, testi::TestoId::PARLANTE_FEBO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_21_02, testi::TestoId::PARLANTE_GIAMBONO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_21_01, testi::TestoId::PARLANTE_GIAMBONO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_21_00, testi::TestoId::PARLANTE_GIAMBONO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_22_02, testi::TestoId::PARLANTE_RICCIARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_22_01, testi::TestoId::PARLANTE_RICCIARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_22_00, testi::TestoId::PARLANTE_RICCIARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_23_02, testi::TestoId::PARLANTE_AURELIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_23_01, testi::TestoId::PARLANTE_AURELIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_23_00, testi::TestoId::PARLANTE_AURELIA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_24_02, testi::TestoId::PARLANTE_LEONORA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_24_01, testi::TestoId::PARLANTE_LEONORA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_24_00, testi::TestoId::PARLANTE_LEONORA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_25_03, testi::TestoId::PARLANTE_RENZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_25_01, testi::TestoId::PARLANTE_RENZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_25_02, testi::TestoId::PARLANTE_RENZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_25_00, testi::TestoId::PARLANTE_RENZO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_26_02, testi::TestoId::PARLANTE_VALERIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_26_01, testi::TestoId::PARLANTE_VALERIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_26_00, testi::TestoId::PARLANTE_VALERIANA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_27_03, testi::TestoId::PARLANTE_RAGNETTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_27_02, testi::TestoId::PARLANTE_RAGNETTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_27_00, testi::TestoId::PARLANTE_RAGNETTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_27_01, testi::TestoId::PARLANTE_RAGNETTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_28_03, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_28_02, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_28_00, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 16, { 255, 255 }, -1 },
    { testi::TestoId::NPC_28_01, testi::TestoId::PARLANTE_ANDREUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_05, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_01, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 19, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_02, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 20, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_03, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 21, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_04, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_29_00, testi::TestoId::PARLANTE_PADELLINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_30_02, testi::TestoId::PARLANTE_GABRIONE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_30_01, testi::TestoId::PARLANTE_GABRIONE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_30_00, testi::TestoId::PARLANTE_GABRIONE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_31_03, testi::TestoId::PARLANTE_VALENZA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_31_02, testi::TestoId::PARLANTE_VALENZA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_31_00, testi::TestoId::PARLANTE_VALENZA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 12, { 255, 255 }, -1 },
    { testi::TestoId::NPC_31_01, testi::TestoId::PARLANTE_VALENZA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_32_03, testi::TestoId::PARLANTE_CIOTTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_32_02, testi::TestoId::PARLANTE_CIOTTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_32_00, testi::TestoId::PARLANTE_CIOTTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 16, { 255, 255 }, -1 },
    { testi::TestoId::NPC_32_01, testi::TestoId::PARLANTE_CIOTTO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_33_03, testi::TestoId::PARLANTE_FAZIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_33_02, testi::TestoId::PARLANTE_FAZIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_33_00, testi::TestoId::PARLANTE_FAZIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_33_01, testi::TestoId::PARLANTE_FAZIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_05, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_02, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 16, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_03, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_04, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_00, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 18, { 255, 255 }, -1 },
    { testi::TestoId::NPC_34_01, testi::TestoId::PARLANTE_LAURETTA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_35_02, testi::TestoId::PARLANTE_NICOLUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_35_01, testi::TestoId::PARLANTE_NICOLUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_35_00, testi::TestoId::PARLANTE_NICOLUCCIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_36_02, testi::TestoId::PARLANTE_RUFINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_36_01, testi::TestoId::PARLANTE_RUFINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_36_00, testi::TestoId::PARLANTE_RUFINO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_37_02, testi::TestoId::PARLANTE_VANNI, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_37_01, testi::TestoId::PARLANTE_VANNI, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_37_00, testi::TestoId::PARLANTE_VANNI, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
};

inline constexpr int NPC = 38;
inline constexpr Npc NPC_AMBIENTE[NPC] = {
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 25, 30, { 0xFFFF, 0, 1 }, { 0, 1, 5 }, 0, 255, 0, 0, 0, false },  // Il console Guido
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 19, 31, { 6, 7, 10 }, { 1, 3, 1 }, 1, 255, 0, 0, 0, false },  // Berto il Tagliapietre
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 25, 33, { 11, 12, 18 }, { 1, 6, 2 }, 2, 255, 0, 0, 0, false },  // Popolana
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), 10, 35, { 20, 0xFFFF, 0xFFFF }, { 1, 0, 0 }, 0, 255, 0, 0, 0, false },  // Merciaio
    { int8_t(mondo::AreaId::LARGO_BARGELLO), 20, 8, { 21, 22, 23 }, { 1, 1, 1 }, 1, 255, 0, 0, 0, false },  // Mastro Tano
    { int8_t(mondo::AreaId::SAN_MARTINO), 37, 29, { 0xFFFF, 24, 26 }, { 0, 2, 2 }, 3, 255, 0, 0, 0, false },  // Cecco il Balestriere
    { int8_t(mondo::AreaId::SAN_MARTINO), 40, 29, { 28, 29, 30 }, { 1, 1, 1 }, 2, 255, 0, 0, 0, false },  // Lavandaia
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), 64, 51, { 31, 32, 34 }, { 1, 2, 1 }, 0, 255, 0, 0, 0, false },  // Venditore delle Logge dei Tiratori
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), 61, 54, { 0xFFFF, 35, 0xFFFF }, { 0, 2, 0 }, 4, 70, 2, 0, 0, false },  // Fra' Matteo il Pescatore
    { int8_t(mondo::AreaId::SAN_PIETRO), 23, 19, { 37, 38, 39 }, { 1, 1, 1 }, 2, 255, 0, 0, 0, false },  // Lucia la Tessitrice
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), 10, 29, { 40, 42, 44 }, { 2, 2, 1 }, 1, 255, 0, 0, 0, false },  // Vecchio sulla scalinata
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 29, 25, { 45, 46, 48 }, { 1, 2, 2 }, 4, 255, 0, 0, 0, false },  // Frate agostiniano
    { int8_t(mondo::AreaId::SANT_ANDREA), 42, 23, { 50, 51, 53 }, { 1, 2, 1 }, 3, 255, 0, 0, 0, false },  // Sentinella di Porta Romana
    { int8_t(mondo::AreaId::DUOMO_DUCALE), 27, 29, { 54, 0xFFFF, 55 }, { 1, 0, 1 }, 4, 255, 0, 0, 0, false },  // Canonico
    { int8_t(mondo::AreaId::SAN_MARTINO), 123, 32, { 56, 57, 58 }, { 1, 1, 1 }, 5, 255, 0, 0, 0, false },  // Ciaccio
    { int8_t(mondo::AreaId::SAN_MARTINO), 15, 58, { 59, 60, 61 }, { 1, 1, 1 }, 6, 255, 0, 0, 0, false },  // Giuliana
    { int8_t(mondo::AreaId::SAN_MARTINO), 42, 32, { 62, 63, 64 }, { 1, 1, 1 }, 7, 255, 0, 0, 0, false },  // Flaviano
    { int8_t(mondo::AreaId::SAN_MARTINO), 75, 32, { 65, 66, 67 }, { 1, 1, 1 }, 8, 255, 0, 0, 0, false },  // Masio il Romano
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), 7, 52, { 68, 69, 70 }, { 1, 1, 1 }, 9, 255, 0, 0, 0, false },  // Montano
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), 102, 71, { 71, 72, 73 }, { 1, 1, 1 }, 10, 65, 2, 0, 0, false },  // Giordano
    { int8_t(mondo::AreaId::SAN_PIETRO), 31, 30, { 74, 75, 76 }, { 1, 1, 1 }, 11, 255, 0, 0, 0, false },  // Febo
    { int8_t(mondo::AreaId::SAN_PIETRO), 26, 19, { 77, 78, 79 }, { 1, 1, 1 }, 12, 66, 2, 0, 0, false },  // Giambono
    { int8_t(mondo::AreaId::SAN_PIETRO), 29, 33, { 80, 81, 82 }, { 1, 1, 1 }, 13, 67, 7, 0, 0, false },  // Ricciardo
    { int8_t(mondo::AreaId::SAN_PIETRO), 28, 27, { 83, 84, 85 }, { 1, 1, 1 }, 14, 255, 0, 0, 0, false },  // Aurelia
    { int8_t(mondo::AreaId::SAN_PIETRO), 29, 19, { 86, 87, 88 }, { 1, 1, 1 }, 15, 255, 0, 0, 0, false },  // Leonora
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 41, 34, { 89, 90, 92 }, { 1, 2, 1 }, 16, 64, 2, 4, 25, true },  // Renzo
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 54, 28, { 93, 94, 95 }, { 1, 1, 1 }, 17, 255, 0, 11, 25, true },  // Valeriana
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 43, 27, { 96, 97, 98 }, { 1, 1, 2 }, 18, 255, 0, 14, 25, true },  // Ragnetto
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 39, 18, { 100, 101, 102 }, { 1, 1, 2 }, 19, 255, 0, 0, 0, false },  // Andreuccio
    { int8_t(mondo::AreaId::TAVERNA_INTERNO), 20, 14, { 104, 105, 109 }, { 1, 4, 1 }, 20, 255, 0, 0, 0, false },  // Padellino
    { int8_t(mondo::AreaId::SPEZIERIA_INTERNO), 5, 9, { 110, 111, 112 }, { 1, 1, 1 }, 21, 255, 0, 0, 0, false },  // Gabrione
    { int8_t(mondo::AreaId::SPEZIERIA_INTERNO), 20, 12, { 113, 114, 115 }, { 1, 1, 2 }, 22, 255, 0, 0, 0, false },  // Valenza
    { int8_t(mondo::AreaId::BOTTEGA_CONTI_INTERNO), 22, 15, { 117, 118, 119 }, { 1, 1, 2 }, 23, 255, 0, 17, 25, true },  // Ciotto
    { int8_t(mondo::AreaId::BOTTEGA_CONTI_INTERNO), 24, 11, { 121, 122, 123 }, { 1, 1, 2 }, 24, 255, 0, 20, 25, true },  // Fazio
    { int8_t(mondo::AreaId::BOTTEGA_CONTI_INTERNO), 12, 9, { 125, 126, 129 }, { 1, 3, 2 }, 25, 255, 0, 23, 25, true },  // Lauretta
    { int8_t(mondo::AreaId::BOTTEGA_CONTI_INTERNO), 10, 13, { 131, 132, 133 }, { 1, 1, 1 }, 26, 255, 0, 26, 25, true },  // Nicoluccio
    { int8_t(mondo::AreaId::CARRADORE_INTERNO), 19, 13, { 134, 135, 136 }, { 1, 1, 1 }, 27, 68, 2, 0, 0, false },  // Mastro Rufino
    { int8_t(mondo::AreaId::CASA_MEDICO_INTERNO), 13, 10, { 137, 138, 139 }, { 1, 1, 1 }, 28, 255, 0, 0, 0, false },  // Vanni
};

inline constexpr int GUARDIE = 29;
inline constexpr Guardia GUARDIA[GUARDIE] = {
    { TipoGuardia::SEMPRE, 0, 0, 0 },
    { TipoGuardia::SCELTA, 0, 0, 0 },
    { TipoGuardia::SCELTA, 1, 0, 0 },
    { TipoGuardia::ALMENO_DUE, 64, 65, 66 },
    { TipoGuardia::NON_BANDIERA, 66, 0, 0 },
    { TipoGuardia::BANDIERA, 66, 0, 0 },
    { TipoGuardia::BANDIERA, 67, 0, 0 },
    { TipoGuardia::BANDIERA, 68, 0, 0 },
    { TipoGuardia::BANDIERA, 24, 0, 0 },
    { TipoGuardia::BANDIERA, 26, 0, 0 },
    { TipoGuardia::NON_BANDIERA, 26, 0, 0 },
    { TipoGuardia::BANDIERA, 22, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 69, 0, 0 },
    { TipoGuardia::OGGETTO_E_NON_BANDIERA, 0, 69, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 66, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 25, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 22, 0, 0 },
    { TipoGuardia::VARIANTE_NON_BANDIERA, 70, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 23, 0, 0 },
    { TipoGuardia::VARIANTE_NON_BANDIERA, 64, 0, 0 },
    { TipoGuardia::VARIANTE_NON_BANDIERA, 65, 0, 0 },
    { TipoGuardia::VARIANTE_NON_BANDIERA, 66, 0, 0 },
    { TipoGuardia::CONTEGGIO, 0, 1, 255 },
    { TipoGuardia::CONTEGGIO, 0, 2, 255 },
    { TipoGuardia::CONTEGGIO, 0, 3, 255 },
    { TipoGuardia::CONTEGGIO, 0, 1, 5 },
    { TipoGuardia::BANDIERA, 17, 0, 0 },
    { TipoGuardia::CONTEGGIO, 1, 1, 255 },
    { TipoGuardia::CONTEGGIO_E_NON_BANDIERA, 1, 1, 78 },
};

// Le bandiere delle quest e degli indizi (64-127, GameState::quest), per nome.
inline constexpr uint8_t INDIZIO_CARTA = 64;
inline constexpr uint8_t INDIZIO_ACQUA = 65;
inline constexpr uint8_t INDIZIO_ROCCIA = 66;
inline constexpr uint8_t RICCIARDO_ASCOLTATO = 67;
inline constexpr uint8_t RUFINO_ASCOLTATO = 68;
inline constexpr uint8_t PANE_DATO = 69;
inline constexpr uint8_t DONO_MATTEO = 70;
inline constexpr uint8_t INDIZIO_LUCIA = 71;
inline constexpr uint8_t INDIZIO_VENDITORE = 72;
inline constexpr uint8_t INDIZIO_FONTANIERE = 73;
inline constexpr uint8_t Q_SM01_CONSEGNATA = 74;
inline constexpr uint8_t Q_SA01_CONSEGNATA = 75;
inline constexpr uint8_t Q_SP01_CONSEGNATA = 76;
inline constexpr uint8_t Q_SM01_PRESA = 77;
inline constexpr uint8_t Q_SA01_PRESA = 78;
inline constexpr uint8_t Q_SP01_PRESA = 79;
inline constexpr uint8_t FERRO_1 = 80;
inline constexpr uint8_t FERRO_2 = 81;
inline constexpr uint8_t FERRO_3 = 82;
inline constexpr uint8_t ELLEBORO_1 = 83;
inline constexpr uint8_t ELLEBORO_2 = 84;
inline constexpr uint8_t ELLEBORO_3 = 85;
inline constexpr uint8_t ELLEBORO_4 = 86;
inline constexpr uint8_t ROSA_RIPRESA = 87;
inline constexpr uint8_t FORZIERE_CRESCIA = 88;
inline constexpr uint8_t FORZIERE_BISCOTTI = 89;
inline constexpr uint8_t GUERRIERI_VINTI = 90;
inline constexpr uint8_t GUARDIA_FORNACE_1 = 91;
inline constexpr uint8_t GUARDIA_FORNACE_2 = 92;
inline constexpr uint8_t GUARDIA_FORNACE_3 = 93;

// Le tre quest della v1 (copione/04_quest.md): dove si consegnano, da quale bandiera si prendono, entro
// quale si consegnano, la bandiera della consegna e il premio (indice di GameState::oggetti, come
// battaglia::OggettoId). Le legge storia::consegna_quest().
struct Quest
{
    const char* codice;
    int8_t consegna;             // mondo::AreaId
    Bandiera da;
    Bandiera entro;
    uint8_t consegnata;          // bandiera 64-127
    uint8_t oggetto;
    uint8_t quanti;
};

inline constexpr int QUEST = 3;
inline constexpr Quest QUEST_V1[QUEST] = {
    { "Q-SM01", int8_t(mondo::AreaId::SAN_MARTINO), Bandiera::ULTIMATUM_RICEVUTO, Bandiera::ATTO_I_COMPLETATO, Q_SM01_CONSEGNATA, 0, 3 },  // 3 Crescia di Pasqua
    { "Q-SA01", int8_t(mondo::AreaId::SANT_ANDREA), Bandiera::CITTA_IN_DIGIUNO, Bandiera::ATTO_I_COMPLETATO, Q_SA01_CONSEGNATA, 3, 3 },  // 3 Biscotti all'Anice
    { "Q-SP01", int8_t(mondo::AreaId::SAN_PIETRO), Bandiera::CITTA_IN_DIGIUNO, Bandiera::ATTO_I_COMPLETATO, Q_SP01_CONSEGNATA, 1, 1 },  // 1 Crescia sotto la Cenere
};

// --- Le quest giocabili (SV2c, copione/04_quest.md) ----------------------------------------------
// Le battute delle quest: proposta, attesa, consegna, raccolta, dopo (per fase), indizi e infiltrato.
struct Righe
{
    uint16_t prima;               // in FRASE_QUEST
    uint8_t quante;
};

inline constexpr int FRASI_QUEST = 73;
inline constexpr Battuta FRASE_QUEST[FRASI_QUEST] = {
    { testi::TestoId::QST_SM01_00, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_01, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_02, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_03, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_04, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_05, testi::TestoId::QST_SM01_05, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_06, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_07, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_08, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_09, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_10, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_11, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_12, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_13, testi::TestoId::QST_SM01_13, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_14, testi::TestoId::QST_SM01_14, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_15, testi::TestoId::QST_SM01_15, TipoBattuta::SISTEMA, Espressione::CALMO, 22, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_16, testi::TestoId::QST_SM01_16, TipoBattuta::SISTEMA, Espressione::CALMO, 23, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_17, testi::TestoId::QST_SM01_17, TipoBattuta::SISTEMA, Espressione::CALMO, 24, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_18, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 25, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_19, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_20, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SM01_21, testi::TestoId::PARLANTE_RANIERO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_00, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_01, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_02, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_03, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_05, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_06, testi::TestoId::PARLANTE_FERITO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_07, testi::TestoId::QST_SA01_07, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_08, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_09, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_10, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_11, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_12, testi::TestoId::QST_SA01_12, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_13, testi::TestoId::QST_SA01_13, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_14, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 26, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_15, testi::TestoId::QST_SA01_15, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_16, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 27, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_17, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 28, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_18, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_19, testi::TestoId::PARLANTE_FERITO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SA01_20, testi::TestoId::PARLANTE_AGNESE, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_00, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_01, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_03, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_05, testi::TestoId::QST_SP01_05, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_06, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_07, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_08, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_09, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_10, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_11, testi::TestoId::QST_SP01_11, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_12, testi::TestoId::QST_SP01_12, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_13, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_14, testi::TestoId::PARLANTE_FRA__BERNARDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_15, testi::TestoId::QST_SP01_15, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_16, testi::TestoId::QST_SP01_16, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_17, testi::TestoId::QST_SP01_17, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_18, testi::TestoId::QST_SP01_18, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_19, testi::TestoId::PARLANTE_GIORDANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_20, testi::TestoId::PARLANTE_GIORDANO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_21, testi::TestoId::QST_SP01_21, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_22, testi::TestoId::PARLANTE_INFILTRATO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_23, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_24, testi::TestoId::PARLANTE_INFILTRATO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_25, testi::TestoId::PARLANTE_INFILTRATO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_26, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_27, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_28, testi::TestoId::PARLANTE_INFILTRATO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::QST_SP01_29, testi::TestoId::QST_SP01_29, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
};

// Il datore di ogni quest (nell'ordine di QUEST_V1) e i pezzi dell'obiettivo: bandiere consecutive da
// primo_pezzo, il contatore e' quante sono accese (storia::pezzi_raccolti).
struct QuestGioco
{
    uint8_t presa;                // la bandiera della quest presa (la proposta)
    uint8_t primo_pezzo;
    uint8_t pezzi;
    int8_t area;                  // dove sta il datore (mondo::AreaId)
    uint8_t tx;
    uint8_t ty;
    uint8_t figura;               // FIGURA_NPC
    Righe proposta;
    Righe attesa;
    Righe consegna;
    Righe raccolta;      // dette a ogni pezzo raccolto, con le guardie CONTEGGIO
    Righe dopo[3];               // per fase (ULTIMATUM, DIGIUNO, NOTTE)
};

inline constexpr QuestGioco QUEST_GIOCO[QUEST] = {
    { Q_SM01_PRESA, 80, 3, int8_t(mondo::AreaId::SAN_MARTINO), 36, 33, 1, { 0, 6 }, { 6, 1 }, { 7, 8 }, { 15, 4 }, { { 19, 1 }, { 20, 1 }, { 21, 1 } } },  // Q-SM01, Mastro Raniero
    { Q_SA01_PRESA, 83, 4, int8_t(mondo::AreaId::SANT_ANDREA), 38, 26, 2, { 22, 8 }, { 30, 1 }, { 31, 6 }, { 37, 3 }, { { 40, 0 }, { 40, 1 }, { 41, 2 } } },  // Q-SA01, Monna Agnese
    { Q_SP01_PRESA, 87, 1, int8_t(mondo::AreaId::SAN_PIETRO), 31, 27, 4, { 43, 6 }, { 49, 1 }, { 50, 6 }, { 56, 0 }, { { 56, 0 }, { 56, 1 }, { 57, 1 } } },  // Q-SP01, Fra' Bernardo
};

// Gli oggetti da raccogliere sulla mappa: ci sono finche' la loro bandiera e' spenta (anche se la quest non
// e' presa); toccarli accende la bandiera e fa dire le battute di raccolta della quest.
struct Raccolta
{
    int8_t area;                  // mondo::AreaId
    uint8_t tx;
    uint8_t ty;
    uint8_t quest;
    uint8_t bandiera;
    uint8_t figura;               // FIGURA_RACCOLTA
};

inline constexpr int RACCOLTE = 7;
inline constexpr Raccolta RACCOLTA[RACCOLTE] = {
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 38, 15, 0, FERRO_1, 0 },
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 44, 35, 0, FERRO_2, 0 },
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 34, 51, 0, FERRO_3, 0 },
    { int8_t(mondo::AreaId::BOTTACCIONE), 47, 48, 1, ELLEBORO_1, 1 },
    { int8_t(mondo::AreaId::GOLA_STRISCIA), 44, 10, 1, ELLEBORO_2, 1 },
    { int8_t(mondo::AreaId::GOLA_MIASMI), 32, 14, 1, ELLEBORO_3, 1 },
    { int8_t(mondo::AreaId::GOLA_ARCO), 35, 19, 1, ELLEBORO_4, 1 },
};

// Le figure degli oggetti da raccogliere, 16x16 (4 tile), con la palette dei popolani (tools/figure_npc.py).
inline constexpr int FIGURE_RACCOLTA = 5;
inline constexpr uint32_t FIGURA_RACCOLTA[FIGURE_RACCOLTA][4 * 8] = {
    {  // ferro
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x11110000, 0xD66D1000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00001111, 0x0001DDDD,
        0xDDDDD100, 0x77777100, 0x7777D100, 0x7777D100, 0x11111000, 0xCCCC0000, 0x00000000, 0x00000000,
        0x001DDDDD, 0x001C7777, 0x001C7777, 0x001CC777, 0x0C111111, 0x0CCCCCCC, 0x00000000, 0x00000000,
    },
    {  // elleboro
        0x00000000, 0x00000000, 0x00110000, 0x01FF1000, 0x1FEF1000, 0x1FF10000, 0x1F100000, 0xF1001100,
        0x00000000, 0x00000000, 0x00001100, 0x0001FF10, 0x0001FEF1, 0x00001FF1, 0x000001F1, 0x0011001F,
        0xF101FF10, 0xF11FF100, 0xFFFF1000, 0xFFF10000, 0x99981000, 0x99998100, 0x11111000, 0x00000000,
        0x01FF101F, 0x001FF11F, 0x00011FFF, 0x00001FFF, 0x00018999, 0x00189999, 0x00011111, 0x00000000,
    },
    {  // forziere
        0x00000000, 0x00000000, 0x00000000, 0x11111000, 0xBBBBB100, 0xBBBBBB10, 0xBBBBBD10, 0xCCCCCC10,
        0x00000000, 0x00000000, 0x00000000, 0x00011111, 0x01ABBBBB, 0x1AABBBBB, 0x1DABBBBB, 0x1CCCCCCC,
        0x1AAAAB10, 0x1AAAAB10, 0xAAAAAD10, 0xAAAAAB10, 0xCCCCCD10, 0x11111100, 0xCCCCC000, 0x00000000,
        0x1CAAAA1E, 0x1CAAAA1E, 0x1CDAAAA1, 0x1CAAAAAA, 0x1CCCCCCC, 0x0C111111, 0x00CCCCCC, 0x00000000,
    },
    {  // forziere_aperto
        0x00000000, 0x11111000, 0xBBBBB100, 0xBBBBA100, 0xCCCCC100, 0x11111110, 0x11111D10, 0xCCCCCC10,
        0x00000000, 0x00011111, 0x01ABBBBB, 0x01AABBBB, 0x1CCCCCCC, 0x01111111, 0x1D111111, 0x1CCCCCCC,
        0xAAAAAB10, 0xAAAAAB10, 0xAAAAAD10, 0xAAAAAB10, 0xCCCCCD10, 0x11111100, 0xCCCCC000, 0x00000000,
        0x1CAAAAAA, 0x1CAAAAAA, 0x1CDAAAAA, 0x1CAAAAAA, 0x1CCCCCCC, 0x0C111111, 0x00CCCCCC, 0x00000000,
    },
    {  // fiamma_cero
        0x00000000, 0x10000000, 0x51000000, 0x51000000, 0xE5100000, 0xE5100000, 0xEE510000, 0x6E510000,
        0x00000000, 0x00000001, 0x00000015, 0x00000015, 0x00000015, 0x0000015E, 0x0000155E, 0x000015E6,
        0x6E510000, 0xEE510000, 0xE5100000, 0x51000000, 0x10000000, 0x00000000, 0x00000000, 0x00000000,
        0x000015E6, 0x000015EE, 0x0000015E, 0x00000015, 0x00000001, 0x00000000, 0x00000000, 0x00000000,
    },
};

// Gli indizi di Q-SP01: l'NPC (NPC_AMBIENTE) che, con la quest presa e la Rosa non ancora ripresa, dopo le
// sue battute dice le righe dell'indizio e accende la bandiera. Con tutti e tre, INDIZI_COMPLETI.
struct Indizio
{
    uint8_t npc;
    uint8_t bandiera;
    Righe righe;
};

inline constexpr int QUEST_DEGLI_INDIZI = 2;
inline constexpr int INDIZI = 3;
inline constexpr Indizio INDIZIO[INDIZI] = {
    { 9, INDIZIO_LUCIA, { 58, 2 } },  // Lucia la Tessitrice
    { 7, INDIZIO_VENDITORE, { 60, 2 } },  // Venditore delle Logge
    { 19, INDIZIO_FONTANIERE, { 62, 2 } },  // Giordano il fontaniere
};

inline constexpr Righe INDIZI_COMPLETI = { 64, 1 };

// L'infiltrato sotto le Logge: compare con i tre indizi; parlargli fa dire le righe di prima, la battaglia,
// e se si vince quelle di dopo e ROSA_RIPRESA.
struct Infiltrato
{
    int8_t area;
    uint8_t tx;
    uint8_t ty;
    uint8_t figura;
    int8_t incontro;              // battaglia::INCONTRO
    Righe prima;
    Righe dopo;
};

inline constexpr Infiltrato INFILTRATO = { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), 99, 71, 29, 6, { 65, 3 }, { 68, 5 } };

// --- La gola del Bottaccione (T2) ----------------------------------------------------------------
// Le scene che partono su una cella dell'area (non entrando): B-02 sulla prima nebbia, B-03 sotto l'arco.
struct Innesco
{
    int8_t scena;                 // indice in SCENA
    mondo::Cella cella;
};

inline constexpr int INNESCHI = 2;
inline constexpr Innesco INNESCO[INNESCHI] = {
    { 14, mondo::Cella::MIASMA },  // B-02
    { 15, mondo::Cella::ARCO },  // B-03
};

// I soldati di B-03 sulla mappa (FIGURA_NPC): ci sono finche' PIANO_DI_CORRADO e' spenta.
struct Sentinella
{
    int8_t area;                  // mondo::AreaId
    uint8_t tx;
    uint8_t ty;
    uint8_t figura;
};

inline constexpr int SENTINELLE = 2;
inline constexpr Sentinella SENTINELLA[SENTINELLE] = {
    { int8_t(mondo::AreaId::GOLA_ARCO), 43, 14, 3 },
    { int8_t(mondo::AreaId::GOLA_ARCO), 43, 20, 3 },
};

// I forzieri negli slarghi: toccarli da' 'quanti' dell'oggetto (battaglia::OggettoId, fino al massimo che se
// ne porta), accende la bandiera (64-127) e fa dire il testo; preso, non torna.
struct Forziere
{
    int8_t area;                  // mondo::AreaId
    uint8_t tx;
    uint8_t ty;
    uint8_t bandiera;
    uint8_t oggetto;
    uint8_t quanti;
    testi::TestoId testo;
};

inline constexpr int FORZIERI = 2;
inline constexpr Forziere FORZIERE[FORZIERI] = {
    { int8_t(mondo::AreaId::GOLA_STRISCIA), 40, 21, FORZIERE_CRESCIA, 0, 2, testi::TestoId::FORZIERE_CRESCIA },  // 2 CRESCIA
    { int8_t(mondo::AreaId::GOLA_ARCO), 20, 22, FORZIERE_BISCOTTI, 3, 3, testi::TestoId::FORZIERE_BISCOTTI },  // 3 BISCOTTI
};

// Le figure del forziere in FIGURA_RACCOLTA: chiuso, e aperto (preso, resta li').
inline constexpr int FIGURA_FORZIERE = 2;
inline constexpr int FIGURA_FORZIERE_APERTO = 3;
// La fiamma sopra i ceri dell'altare, con i Ceri risvegliati (CERO_ALTARE di storia_logica.h).
inline constexpr int FIGURA_FIAMMA_CERO = 4;

// --- Le guardie delle fornaci (F10, Q-SM01) -----------------------------------------------------
// Un Guerriero della Roccia davanti a ogni blocco di ferro, visibile sulla mappa: toccarlo avvia la battaglia
// (INCONTRO_FORNACE); vinta, la sua bandiera (64-127) si accende, non torna e il blocco si puo' prendere.
struct GuardiaFornace
{
    int8_t area;                  // mondo::AreaId
    uint8_t tx;
    uint8_t ty;
    uint8_t bandiera;
    uint8_t raccolta;             // il blocco che guarda (RACCOLTA)
};

inline constexpr int INCONTRO_FORNACE = 5;     // battaglia::INCONTRO
inline constexpr int GUARDIE_FORNACE = 3;
inline constexpr GuardiaFornace GUARDIA_FORNACE[GUARDIE_FORNACE] = {
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 40, 16, GUARDIA_FORNACE_1, 0 },  // davanti a FERRO_1
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 44, 37, GUARDIA_FORNACE_2, 1 },  // davanti a FERRO_2
    { int8_t(mondo::AreaId::TEATRO_ROMANO), 36, 50, GUARDIA_FORNACE_3, 2 },  // davanti a FERRO_3
};

// Le figure degli NPC, 16x32 (8 tile in mappatura 1D) con la palette dei popolani: quelle dei
// mestieri (tools/figure_npc.py) e quelle degli amici (base e accessorio, dati/amici.json).
inline constexpr int FIGURE_NPC = 30;
inline constexpr uint32_t FIGURA_NPC[FIGURE_NPC][8 * 8] = {
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x00001BBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0001BBBB, 0x0001BBBB, 0x0001EEEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDD100000, 0x33D10000, 0x13D10000, 0x36D10000, 0x66100000, 0x68810000,
        0x00000000, 0x00000011, 0x000001DD, 0x00001D33, 0x00001D33, 0x00001D63, 0x00000166, 0x00001886,
        0x88881A00, 0x88881300, 0x88881A00, 0x88881A00, 0x88810A00, 0x88810A00, 0x0A100A00, 0x01100A00,
        0x00188888, 0x00188888, 0x00188888, 0x00188888, 0x00188888, 0x00018888, 0x00001A10, 0x00001110,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x66441000, 0x66441000, 0x66441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x00014466, 0x00014466, 0x00014466, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310000, 0x33310000, 0x33100000,
        0x00D00000, 0x00D00011, 0x00B01DDD, 0x00B1DD77, 0x00B01333, 0x00B01313, 0x00B01333, 0x00B00133,
        0x44410000, 0x64441000, 0x66641000, 0x64441000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14446, 0x00B14666, 0x00B14446, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0xAA100000, 0x3AA10000, 0x33AA1000, 0x313A1000, 0x333A1000, 0x33A10000, 0xAAAA1000,
        0x00000000, 0x000001AA, 0x00001AA3, 0x0001AA33, 0x0001A313, 0x0001A333, 0x00001A33, 0x0001AAAA,
        0xAAABA100, 0xAAABA100, 0x6666A100, 0x6AAA1000, 0x6AAA1000, 0xAAAA1000, 0x00210000, 0x00110000,
        0x001ABAAA, 0x001ABAAA, 0x001A6666, 0x0001AAAA, 0x0001AAAA, 0x0001AAAA, 0x00001200, 0x00001100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x0AA00000, 0xAA070000, 0x0A070000, 0x0A070000,
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310000, 0x33310000, 0x33100000,
        0x0AD70000, 0x0AD70011, 0x0AB71DDD, 0x0AB7DD77, 0x0AB71333, 0x0AB71313, 0x0AB71333, 0x0AB70133,
        0x44410000, 0x64441000, 0x66641000, 0x64441000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x0AB71444, 0x0AB74446, 0x0AB74666, 0x0AB74446, 0x0AB71444, 0xAAB71CCC, 0x0AA01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x66441000, 0x66441000, 0x66441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x000BBBBB, 0x000BEBEB, 0x000BBBBB, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x0A001313, 0x00A01333, 0x00A00133, 0x000AAABB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x000A1ABB, 0x000AAABB, 0x000AAAEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xB4E10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x00001BBB,
        0x4EBB1000, 0xEBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0001BBBB, 0x0001BBB4, 0x0001EE4E, 0x000144EB, 0x00014EBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x0EEEE133, 0x0EE4EBBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xCBCB1000, 0xBCBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0E4EEBBB, 0x0EEEEBBB, 0x0001EEEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDD100000, 0x33D10000, 0x13D10000, 0x33D10000, 0x33100000, 0x68810000,
        0x00000000, 0x00000011, 0x000001DD, 0x00001D33, 0x00001D33, 0x00001D33, 0x00B00133, 0x00B01886,
        0x88881A00, 0x88881300, 0x88881A00, 0x88881A00, 0x88810A00, 0x88810A00, 0x0A100A00, 0x01100A00,
        0x00B88888, 0x00B88888, 0x0D1D8888, 0x0CCC8888, 0x0CCC8888, 0x0CCC8888, 0x00001A10, 0x00001110,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310000, 0x33310000, 0x33100000,
        0x00D00000, 0x00D00011, 0x00B01DDD, 0x00B1DD77, 0x00B01333, 0x00B01313, 0x00B0A333, 0x00B00A33,
        0x44410000, 0x66661000, 0x44441000, 0x44441000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14466, 0x00B14644, 0x00B14444, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310D00, 0x33310D00, 0xAAAAAAA0,
        0x00D00000, 0x00D00011, 0x00B01DDD, 0x00B1DD77, 0x00B01333, 0x00B01313, 0x00B01333, 0x00BAAAAA,
        0x44410D00, 0x64441D00, 0x66641000, 0x64441000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14446, 0x00B14666, 0x00B14446, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x0D000133, 0x0DEEEEBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x00EEEEBB, 0x00EEEEBB, 0x00EEEEEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0xAA441000, 0x6A441000, 0xAA441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x000144AA, 0x000144A6, 0x000144AA, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x66441000, 0x66441000, 0x66441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x0099D466, 0x00D99466, 0x00014466, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0xAA100000, 0x3AA10000, 0x33AA1000, 0x313A1000, 0x333A1000, 0x33A10000, 0xAAAA1000,
        0x00000000, 0x000001AA, 0x00001AA3, 0x0001AA33, 0x0001A313, 0x0001A333, 0x00001A33, 0x0001AAAA,
        0xAAABA100, 0xAAABA100, 0x6666A100, 0x6AAA1000, 0x6AAA1000, 0xAAAA1000, 0x00210000, 0x00110000,
        0x0099DAAA, 0x00D99AAA, 0x001A6666, 0x0001AAAA, 0x0001AAAA, 0x0001AAAA, 0x00001200, 0x00001100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000A00, 0x00000A00,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000A00, 0x66100A00, 0x66610A00, 0x33610A00, 0x31610A00, 0x33610A00, 0x33100A00, 0x44410A00,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x66441A00, 0x66441A00, 0x66441A00, 0x66441A00, 0x44441A00, 0x44444A00, 0x11111A00, 0x00000000,
        0x00114466, 0x00EE4466, 0x00EE4466, 0x00EE4466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0xBBBBBBBB, 0xBABBABBA, 0xAAAA1000, 0x33310000, 0x31310000, 0x33310000, 0x33100000,
        0x00D00000, 0xBBBBBBBB, 0xABBABBAB, 0x00B1AAAA, 0x00B01333, 0x00B01313, 0x00B01333, 0x00B00133,
        0x44410000, 0x64443000, 0x66643000, 0x64443000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14446, 0x00B14666, 0x00B14446, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310000, 0x33310000, 0x33444440,
        0x00D00000, 0x00D00011, 0x00B01DDD, 0x00B1DD77, 0x00B01333, 0x00B01313, 0x00B01333, 0x00B00133,
        0x44446440, 0x64466640, 0x66466640, 0x64444440, 0x44144410, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14446, 0x00B14666, 0x00B14446, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x00001BBB,
        0x666B1000, 0x666B1000, 0xEEEE1000, 0x666B1000, 0x666B1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0001B666, 0x00A1B666, 0x0FFFEEEE, 0x0FFF4E66, 0x0FFF4666, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x11100000, 0x33310000, 0x39310000, 0x31310000, 0x33310000,
        0x00000000, 0x00000000, 0x00000000, 0x00000001, 0x00000013, 0x00000013, 0x00000013, 0x00000013,
        0x33100000, 0x77710000, 0x77771000, 0x77771000, 0x77771000, 0x77D71000, 0x77771000, 0x77771000,
        0x00000001, 0x00000017, 0x00000177, 0x00000177, 0x00000177, 0x0000017D, 0x00000177, 0x00000177,
        0x77710000, 0x77710000, 0x00710000, 0x00A10000, 0x00110000, 0x00000000, 0x00000000, 0x00000000,
        0x00000017, 0x00000017, 0x00000017, 0x0001001A, 0x00010011, 0x00000000, 0x00000000, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x6B441000, 0xBB441000, 0x66441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x000144B6, 0x000144BB, 0x00014466, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x0BCBCBBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0CBCBBBB, 0x0BCBCBBB, 0x0CBCBEEE, 0x0BBBBEBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00DDD333, 0x00DDD133, 0x000D1BBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x000DBBBB, 0x000DBBBB, 0x00DDEEEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0xB6441000, 0xB6441000, 0xB6441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x00014BBB, 0x00014B11, 0x00014BBB, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x11100000, 0xAAA10000, 0x33310000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000001, 0x0000001A, 0x00000013,
        0x11310000, 0x33100000, 0x44410000, 0x44441000, 0x44410000, 0x00310000, 0x00110000, 0x00000000,
        0x00000013, 0x00000001, 0x00000014, 0x00000144, 0x00000014, 0x00000013, 0x00000011, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00CC0133, 0x0C00CBBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0xC0AABCBB, 0xC0AABCBB, 0x0C01CEEE, 0x00CC4EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x11000000, 0xDD100000, 0x33D10000, 0x13D10000, 0x33D10000, 0x33100000, 0x68810000,
        0x00000000, 0x00000011, 0x000001DD, 0x00001D33, 0x00001D33, 0x00001D33, 0x00000133, 0x00001886,
        0x88881A00, 0x88881300, 0x88881A00, 0x88881A00, 0x88810A00, 0x88810A00, 0x0A100A00, 0x01100A00,
        0x00188888, 0x00188888, 0x0AAA8888, 0x0AAA8888, 0x0AAA8888, 0x00018888, 0x00001A10, 0x00001110,
    },
    {
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000A00, 0x00000A00,
        0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x55000A00, 0x55500A00, 0x55510A00, 0x33310A00, 0x31310A00, 0x33310A00, 0x33100A00, 0xBBB10A00,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x00001BBB,
        0xBBBB1A00, 0xBBBB1A00, 0xEEEE1A00, 0xBBBB1A00, 0xBBBB1A00, 0xBBBBBA00, 0x11111A00, 0x00000000,
        0x0011BBBB, 0x00EEBBBB, 0x00EEEEEE, 0x00EE4EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
};

}

#endif
