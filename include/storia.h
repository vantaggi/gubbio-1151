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

inline constexpr int BATTUTE = 223;
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
    { testi::TestoId::C_A1_05_11, testi::TestoId::C_A1_05_11, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_A1_05_12, testi::TestoId::C_A1_05_12, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
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
    { testi::TestoId::C_A1_07_02, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
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
    { testi::TestoId::C_B_01_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
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
    { testi::TestoId::C_B_04_05, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_06, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_07, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_08, testi::TestoId::PARLANTE_CORRADO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_09, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_10, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_11, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_12, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_13, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_14, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_15, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_16, testi::TestoId::C_B_04_16, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_04_17, testi::TestoId::C_B_04_17, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_00, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_01, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_02, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_03, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_04, testi::TestoId::PARLANTE_NELLO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_05, testi::TestoId::C_B_05_05, TipoBattuta::AREA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_06, testi::TestoId::PARLANTE_FOLLA, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 7, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_07, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 7, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_08, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 7, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_10, testi::TestoId::C_B_05_10, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_11, testi::TestoId::C_B_05_11, TipoBattuta::OBIETTIVO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_B_05_12, testi::TestoId::C_B_05_12, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_00, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_01_A, testi::TestoId::C_E_01_01_B, TipoBattuta::SCELTA, Espressione::CALMO, 0, { 26, 255 }, -1 },
    { testi::TestoId::C_E_01_02, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_03, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_04, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_05, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_06, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_07, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_08, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 2, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_09, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_10, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::DECISO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_11, testi::TestoId::PARLANTE_ARALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_12, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_13, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_14, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 8, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_15, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 9, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_16, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_17, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_01_18, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_00, testi::TestoId::C_E_02_00, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_01, testi::TestoId::C_E_02_01, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::C_E_02_02, testi::TestoId::C_E_02_02, TipoBattuta::NARRATORE, Espressione::CALMO, 0, { 255, 255 }, -1 },
};

inline constexpr Scena SCENA[SCENE] = {
    { "P-00", testi::TestoId::SCENA_P_00, false, -1, NESSUNA_AREA, 0x0u, 0x0u, 0x0u, -1, -1, 0, 0 },
    { "P-01", testi::TestoId::SCENA_P_01, true, 1, NESSUNA_AREA, 0x0u, 0x0u, 0x0u, 0, -1, 0, 3 },
    { "P-02", testi::TestoId::SCENA_P_02, true, -2, NESSUNA_AREA, 0x0u, 0x0u, 0x1u, 1, -1, 3, 7 },
    { "A1-01", testi::TestoId::SCENA_A1_01, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x1u, 0x0u, 0x6u, -1, -1, 10, 24 },
    { "A1-02", testi::TestoId::SCENA_A1_02, false, -1, int8_t(mondo::AreaId::VIA_DEI_CONSOLI), 0x2u, 0x8u, 0x8u, -1, -1, 34, 2 },
    { "A1-03", testi::TestoId::SCENA_A1_03, false, -1, int8_t(mondo::AreaId::SAN_MARTINO), 0x2u, 0x10u, 0x10u, -1, -1, 36, 8 },
    { "A1-04", testi::TestoId::SCENA_A1_04, false, -1, int8_t(mondo::AreaId::TEATRO_ROMANO), 0x10u, 0x20u, 0x20u, -1, 0, 44, 19 },
    { "A1-05", testi::TestoId::SCENA_A1_05, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x20u, 0x40u, 0x40u, -1, -1, 63, 13 },
    { "A1-05b", testi::TestoId::SCENA_A1_05B, false, -1, int8_t(mondo::AreaId::SANT_ANDREA), 0x40u, 0xC00000u, 0x0u, -1, -1, 76, 12 },
    { "A1-06", testi::TestoId::SCENA_A1_06, false, -1, int8_t(mondo::AreaId::DUOMO_DUCALE), 0x40u, 0x80u, 0x80u, -1, -1, 88, 4 },
    { "A1-07", testi::TestoId::SCENA_A1_07, false, -1, int8_t(mondo::AreaId::MONTE_INGINO), 0x80u, 0x0u, 0x300u, -1, 1, 92, 16 },
    { "A1-08", testi::TestoId::SCENA_A1_08, false, -1, int8_t(mondo::AreaId::BASILICA_INTERNO), 0x200u, 0x0u, 0xC00u, -1, 3, 108, 25 },
    { "A1-09", testi::TestoId::SCENA_A1_09, false, -1, int8_t(mondo::AreaId::BASILICA_INTERNO), 0x800u, 0x0u, 0x1000u, -1, -1, 133, 12 },
    { "B-01", testi::TestoId::SCENA_B_01, false, -1, int8_t(mondo::AreaId::GOLA_STRISCIA), 0x1000u, 0x2000u, 0x2000u, -1, -1, 145, 5 },
    { "B-02", testi::TestoId::SCENA_B_02, false, -1, int8_t(mondo::AreaId::GOLA_MIASMI), 0x0u, 0x0u, 0x4000u, 13, -1, 150, 3 },
    { "B-03", testi::TestoId::SCENA_B_03, false, -1, int8_t(mondo::AreaId::GOLA_ARCO), 0x0u, 0x0u, 0x8000u, 14, -1, 153, 17 },
    { "B-04", testi::TestoId::SCENA_B_04, false, -1, int8_t(mondo::AreaId::CONDOTTO), 0x0u, 0x0u, 0x230000u, 15, 2, 170, 18 },
    { "B-05", testi::TestoId::SCENA_B_05, false, -1, int8_t(mondo::AreaId::SAN_MARTINO), 0x20000u, 0x0u, 0x40000u, -1, -1, 188, 13 },
    { "E-01", testi::TestoId::SCENA_E_01, false, -1, int8_t(mondo::AreaId::PIAZZA_GRANDE), 0x40000u, 0x0u, 0x80000u, -1, -1, 201, 19 },
    { "E-02", testi::TestoId::SCENA_E_02, true, 8, int8_t(mondo::AreaId::BASILICA_INTERNO), 0x80000u, 0x0u, 0x100000u, -1, -1, 220, 3 },
};

// Le cutscene dentro le scene: prima della battuta (indice in BATTUTA), la cutscene.
struct Inserto
{
    uint16_t battuta;
    int8_t regia;
};

inline constexpr int INSERTI = 6;
inline constexpr Inserto INSERTO[INSERTI > 0 ? INSERTI : 1] = {
    { 11, 7 },  // A1-01 prima della battuta 1: C3U
    { 12, 6 },  // A1-01 prima della battuta 2: C3G
    { 14, 2 },  // A1-01 prima della battuta 4: C2
    { 18, 3 },  // A1-01 prima della battuta 8: C2P
    { 45, 4 },  // A1-04 prima della battuta 1: C3A
    { 170, 5 },  // B-04 prima della battuta 0: C3C
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
};

inline constexpr int FRASI_NPC = 48;
inline constexpr Battuta FRASE_NPC[FRASI_NPC] = {
    { testi::TestoId::NPC_00_02, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_00, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 10, { 255, 255 }, -1 },
    { testi::TestoId::NPC_00_01, testi::TestoId::PARLANTE_GUIDO, TipoBattuta::PERSONAGGIO, Espressione::PREOCCUPATO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_04, testi::TestoId::NPC_01_04, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_01, testi::TestoId::NPC_01_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_02, testi::TestoId::NPC_01_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_03, testi::TestoId::NPC_01_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_01_00, testi::TestoId::NPC_01_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_08, testi::TestoId::NPC_02_08, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_02, testi::TestoId::NPC_02_02, TipoBattuta::SISTEMA, Espressione::CALMO, 11, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_03, testi::TestoId::NPC_02_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_04_A, testi::TestoId::NPC_02_04_B, TipoBattuta::SCELTA, Espressione::CALMO, 12, { 69, 255 }, 0 },
    { testi::TestoId::NPC_02_05, testi::TestoId::PARLANTE_GIORGIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_06, testi::TestoId::NPC_02_06, TipoBattuta::SISTEMA, Espressione::CALMO, 1, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_07, testi::TestoId::PARLANTE_ANTONIO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 2, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_00, testi::TestoId::NPC_02_00, TipoBattuta::SISTEMA, Espressione::CALMO, 11, { 255, 255 }, -1 },
    { testi::TestoId::NPC_02_01, testi::TestoId::NPC_02_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_03_00, testi::TestoId::NPC_03_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_02, testi::TestoId::NPC_04_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_01, testi::TestoId::NPC_04_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_04_00, testi::TestoId::NPC_04_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_01, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 13, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_02, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_05_00, testi::TestoId::PARLANTE_CECCO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_02, testi::TestoId::NPC_06_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_01, testi::TestoId::NPC_06_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_06_00, testi::TestoId::NPC_06_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_03, testi::TestoId::NPC_07_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_01, testi::TestoId::NPC_07_01, TipoBattuta::SISTEMA, Espressione::CALMO, 10, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_02, testi::TestoId::NPC_07_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_07_00, testi::TestoId::NPC_07_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_08_02, testi::TestoId::NPC_08_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_08_01, testi::TestoId::NPC_08_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_08_00, testi::TestoId::NPC_08_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_03, testi::TestoId::NPC_09_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_04, testi::TestoId::PARLANTE_UBALDO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_01, testi::TestoId::NPC_09_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_02, testi::TestoId::NPC_09_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_09_00, testi::TestoId::NPC_09_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_03, testi::TestoId::NPC_10_03, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_02, testi::TestoId::NPC_10_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_00, testi::TestoId::NPC_10_00, TipoBattuta::SISTEMA, Espressione::CALMO, 14, { 255, 255 }, -1 },
    { testi::TestoId::NPC_10_01, testi::TestoId::NPC_10_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_02, testi::TestoId::NPC_11_02, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_01, testi::TestoId::NPC_11_01, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_11_00, testi::TestoId::NPC_11_00, TipoBattuta::SISTEMA, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_01, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
    { testi::TestoId::NPC_12_00, testi::TestoId::PARLANTE_CANONICO, TipoBattuta::PERSONAGGIO, Espressione::CALMO, 0, { 255, 255 }, -1 },
};

inline constexpr int NPC = 13;
inline constexpr Npc NPC_AMBIENTE[NPC] = {
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 18, 30, { 0xFFFF, 0, 1 }, { 0, 1, 2 }, 3, 255, 0 },  // Il console Guido
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 26, 30, { 3, 4, 7 }, { 1, 3, 1 }, 4, 255, 0 },  // Berto il Tagliapietre
    { int8_t(mondo::AreaId::PIAZZA_GRANDE), 18, 34, { 8, 9, 15 }, { 1, 6, 2 }, 0, 255, 0 },  // Popolana
    { int8_t(mondo::AreaId::VIA_DEI_CONSOLI), 10, 28, { 17, 0xFFFF, 0xFFFF }, { 1, 0, 0 }, 3, 255, 0 },  // Merciaio
    { int8_t(mondo::AreaId::LARGO_BARGELLO), 16, 14, { 18, 19, 20 }, { 1, 1, 1 }, 4, 255, 0 },  // Mastro Tano
    { int8_t(mondo::AreaId::SAN_MARTINO), 35, 28, { 0xFFFF, 21, 23 }, { 0, 2, 1 }, 2, 255, 0 },  // Cecco il Balestriere
    { int8_t(mondo::AreaId::SAN_MARTINO), 39, 28, { 24, 25, 26 }, { 1, 1, 1 }, 0, 255, 0 },  // Lavandaia
    { int8_t(mondo::AreaId::PIAZZA_QUARANTA_MARTIRI), 64, 50, { 27, 28, 30 }, { 1, 2, 1 }, 3, 255, 0 },  // Venditore delle Logge dei Tiratori
    { int8_t(mondo::AreaId::SAN_PIETRO), 22, 18, { 31, 32, 33 }, { 1, 1, 1 }, 0, 255, 0 },  // Lucia la Tessitrice
    { int8_t(mondo::AreaId::VIA_XX_SETTEMBRE), 10, 28, { 34, 36, 38 }, { 2, 2, 1 }, 4, 255, 0 },  // Vecchio sulla scalinata
    { int8_t(mondo::AreaId::SANT_AGOSTINO), 29, 24, { 39, 40, 41 }, { 1, 1, 2 }, 1, 255, 0 },  // Frate agostiniano
    { int8_t(mondo::AreaId::SANT_ANDREA), 42, 22, { 43, 44, 45 }, { 1, 1, 1 }, 2, 255, 0 },  // Sentinella di Porta Romana
    { int8_t(mondo::AreaId::DUOMO_DUCALE), 27, 28, { 46, 0xFFFF, 47 }, { 1, 0, 1 }, 1, 255, 0 },  // Canonico
};

inline constexpr int GUARDIE = 15;
inline constexpr Guardia GUARDIA[GUARDIE] = {
    { TipoGuardia::SEMPRE, 0, 0, 0 },
    { TipoGuardia::SCELTA, 0, 0, 0 },
    { TipoGuardia::SCELTA, 1, 0, 0 },
    { TipoGuardia::ALMENO_DUE, 64, 65, 66 },
    { TipoGuardia::NON_BANDIERA, 66, 0, 0 },
    { TipoGuardia::BANDIERA, 66, 0, 0 },
    { TipoGuardia::BANDIERA, 67, 0, 0 },
    { TipoGuardia::BANDIERA, 24, 0, 0 },
    { TipoGuardia::BANDIERA, 26, 0, 0 },
    { TipoGuardia::NON_BANDIERA, 26, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 22, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 69, 0, 0 },
    { TipoGuardia::OGGETTO_E_NON_BANDIERA, 0, 69, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 66, 0, 0 },
    { TipoGuardia::VARIANTE_BANDIERA, 23, 0, 0 },
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

// Le figure degli NPC, 16x16 (4 tile in mappatura 1D) con la palette dei popolani: popolana, frate, soldato, mercante, anziano.
inline constexpr int FIGURE_NPC = 5;
inline constexpr uint32_t FIGURA_NPC[FIGURE_NPC][4 * 8] = {
    {  // popolana
        0x11000000, 0x66100000, 0x66610000, 0x33610000, 0x31610000, 0x33610000, 0x33100000, 0x44410000,
        0x00000011, 0x00000166, 0x00001666, 0x00001633, 0x00001631, 0x00001633, 0x00000133, 0x00001444,
        0x66441000, 0x66441000, 0x66441000, 0x66441000, 0x44441000, 0x44444100, 0x11111000, 0x00000000,
        0x00014466, 0x00014466, 0x00014466, 0x00014466, 0x00014444, 0x00144444, 0x00011111, 0x00000000,
    },
    {  // frate
        0x00000000, 0xAA100000, 0x3AA10000, 0x33AA1000, 0x313A1000, 0x333A1000, 0x33A10000, 0xAAAA1000,
        0x00000000, 0x000001AA, 0x00001AA3, 0x0001AA33, 0x0001A313, 0x0001A333, 0x00001A33, 0x0001AAAA,
        0xAAABA100, 0xAAABA100, 0x6666A100, 0x6AAA1000, 0x6AAA1000, 0xAAAA1000, 0x00210000, 0x00110000,
        0x001ABAAA, 0x001ABAAA, 0x001A6666, 0x0001AAAA, 0x0001AAAA, 0x0001AAAA, 0x00001200, 0x00001100,
    },
    {  // soldato
        0x00000000, 0x11000000, 0xDDD10000, 0x77DD1000, 0x33310000, 0x31310000, 0x33310000, 0x33100000,
        0x00D00000, 0x00D00011, 0x00B01DDD, 0x00B1DD77, 0x00B01333, 0x00B01313, 0x00B01333, 0x00B00133,
        0x44410000, 0x64441000, 0x66641000, 0x64441000, 0x44410000, 0xCCC10000, 0x01C10000, 0x00110000,
        0x00B01444, 0x00B14446, 0x00B14666, 0x00B14446, 0x00B01444, 0x00B01CCC, 0x00B01C10, 0x00B01100,
    },
    {  // mercante
        0x55000000, 0x55500000, 0x55510000, 0x33310000, 0x31310000, 0x33310000, 0x33100000, 0xBBB10000,
        0x00000055, 0x00000555, 0x00001555, 0x00001333, 0x00001313, 0x00001333, 0x00000133, 0x00001BBB,
        0xBBBB1000, 0xBBBB1000, 0xEEEE1000, 0xBBBB1000, 0xBBBB1000, 0xBBBBB100, 0x11111100, 0x00000000,
        0x0001BBBB, 0x0001BBBB, 0x0001EEEE, 0x00014EBB, 0x00014BBB, 0x001BBBBB, 0x00111111, 0x00000000,
    },
    {  // anziano
        0x00000000, 0x11000000, 0xDD100000, 0x33D10000, 0x13D10000, 0x36D10000, 0x66100000, 0x68810000,
        0x00000000, 0x00000011, 0x000001DD, 0x00001D33, 0x00001D33, 0x00001D63, 0x00000166, 0x00001886,
        0x88881A00, 0x88881300, 0x88881A00, 0x88881A00, 0x88810A00, 0x88810A00, 0x0A100A00, 0x01100A00,
        0x00188888, 0x00188888, 0x00188888, 0x00188888, 0x00188888, 0x00018888, 0x00001A10, 0x00001110,
    },
};

}

#endif
