// GENERATO da tools/genera_colonna_sonora.py da musica/colonna_sonora.txt e audio/: non modificare a mano.
#ifndef GUBBIO_COLONNA_SONORA_H
#define GUBBIO_COLONNA_SONORA_H

#include <cstdint>

namespace gubbio::colonna
{

// I brani di audio/*.xm e gli effetti di audio/*.wav, in ordine di nome (bn::music_items, bn::sound_items).
enum class Brano : uint8_t
{
    BANDIERE,
    BASILICA,
    BATTAGLIA,
    BOTTACCIONE,
    CANZONE_DI_FLAVIANO,
    CITTA,
    CORRADO,
    FAZIO,
    NOTTE,
    PASTORALE,
    PRESENTAZIONE,
    PROLOGO,
    SCONFITTA,
    STRADONI,
    TAVERNA,
    TERZA_ALBA,
    TITOLO,
    UNDICI_BANDIERE,
    VITTORIA,
};

inline constexpr int BRANI = 19;
inline constexpr int NESSUNO = -1;   // nessun brano, nessun effetto

// Torna da capo? I jingle (anello: no nella partitura) suonano una volta.
inline constexpr bool IN_ANELLO[BRANI] = {
    true,   // bandiere
    true,   // basilica
    true,   // battaglia
    true,   // bottaccione
    true,   // canzone_di_flaviano
    true,   // citta
    true,   // corrado
    false,   // fazio
    true,   // notte
    false,   // pastorale
    false,   // presentazione
    true,   // prologo
    false,   // sconfitta
    true,   // stradoni
    true,   // taverna
    true,   // terza_alba
    true,   // titolo
    true,   // undici_bandiere
    false,   // vittoria
};

enum class Effetto : uint8_t
{
    ANNULLA,
    CAMPANONE,
    COLPO,
    CONFERMA,
    CURA,
    CURSORE,
    FEDE,
    FUOCO,
    LIVELLO,
    SALVA,
    SCUDO,
    SVANISCE,
    TESTO,
};

inline constexpr int EFFETTI = 13;

// Le fasi della musica: quelle degli NPC (storia::Fase) piu' l'alba dell'epilogo.
enum class Fase : uint8_t
{
    GIORNO,
    DIGIUNO,
    NOTTE,
    ALBA,
};

inline constexpr int FASI = 4;
inline constexpr int AREE = 19;

// Il brano di ogni area (mondo::AreaId) in ogni fase.
inline constexpr Brano BRANO_AREA[AREE][FASI] = {
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::BANDIERE },   // PIAZZA_GRANDE
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // VIA_XX_SETTEMBRE
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // DUOMO_DUCALE
    { Brano::STRADONI, Brano::STRADONI, Brano::STRADONI, Brano::STRADONI },   // MONTE_INGINO
    { Brano::STRADONI, Brano::STRADONI, Brano::STRADONI, Brano::STRADONI },   // BASILICA
    { Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE },   // BOTTACCIONE
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // SAN_MARTINO
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // LARGO_BARGELLO
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // VIA_DEI_CONSOLI
    { Brano::BASILICA, Brano::BASILICA, Brano::BASILICA, Brano::BASILICA },   // BASILICA_INTERNO
    { Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE },   // CONDOTTO
    { Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE },   // GOLA_ARCO
    { Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE },   // GOLA_MIASMI
    { Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE, Brano::BOTTACCIONE },   // GOLA_STRISCIA
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // PIAZZA_QUARANTA_MARTIRI
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // SAN_PIETRO
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // SANT_AGOSTINO
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // SANT_ANDREA
    { Brano::CITTA, Brano::CITTA, Brano::NOTTE, Brano::CANZONE_DI_FLAVIANO },   // TEATRO_ROMANO
};

enum class Modo : uint8_t
{
    FONDO,      // al posto del brano dell'area, finche' si resta
    SEGNALE,    // una volta entrando, poi torna il brano dell'area
};

// Un luogo dentro un'area: le celle da (x0, y0) a (x1, y1) comprese, intorno al portone di un edificio.
struct Luogo
{
    uint8_t area;       // mondo::AreaId
    uint8_t x0;
    uint8_t y0;
    uint8_t x1;
    uint8_t y1;
    Brano brano;
    Modo modo;
    int8_t npc;         // l'amico (storia::NPC_AMBIENTE) che deve essere in bottega, o -1
};

inline constexpr int LUOGHI = 2;
inline constexpr Luogo LUOGO[2] = {
    { 15, 23, 6, 30, 12, Brano::TAVERNA, Modo::FONDO, -1 },   // taverna
    { 16, 37, 28, 41, 33, Brano::FAZIO, Modo::SEGNALE, 31 },   // fazio
};

inline constexpr int LUOGO_TAVERNA = 0;
inline constexpr int LUOGO_FAZIO = 1;

inline constexpr int CUTSCENE = 14;
// Per cutscene (regia::CUTSCENE_DATI): il codice (ricontrollato), il brano (Brano, o NESSUNO: resta
// quello che suonava) e l'effetto del primo quadro (Effetto, o NESSUNO).
inline constexpr const char* CODICE_CUTSCENE[CUTSCENE] = { "C0", "C1", "C2", "C2P", "C3A", "C3C", "C3G", "C3U", "C4", "C5", "C6", "C7B", "C7S", "C9" };
inline constexpr int8_t BRANO_CUTSCENE[CUTSCENE] = {
    NESSUNO,   // C0
    int8_t(Brano::PROLOGO),   // C1
    int8_t(Brano::UNDICI_BANDIERE),   // C2
    int8_t(Brano::PASTORALE),   // C2P
    int8_t(Brano::PRESENTAZIONE),   // C3A
    int8_t(Brano::PRESENTAZIONE),   // C3C
    int8_t(Brano::PRESENTAZIONE),   // C3G
    int8_t(Brano::PRESENTAZIONE),   // C3U
    int8_t(Brano::TERZA_ALBA),   // C4
    int8_t(Brano::BASILICA),   // C5
    int8_t(Brano::BOTTACCIONE),   // C6
    int8_t(Brano::BOTTACCIONE),   // C7B
    int8_t(Brano::STRADONI),   // C7S
    NESSUNO,   // C9
};
inline constexpr int8_t EFFETTO_CUTSCENE[CUTSCENE] = {
    NESSUNO,   // C0
    NESSUNO,   // C1
    NESSUNO,   // C2
    NESSUNO,   // C2P
    NESSUNO,   // C3A
    NESSUNO,   // C3C
    NESSUNO,   // C3G
    NESSUNO,   // C3U
    int8_t(Effetto::CAMPANONE),   // C4
    NESSUNO,   // C5
    NESSUNO,   // C6
    NESSUNO,   // C7B
    NESSUNO,   // C7S
    NESSUNO,   // C9
};

inline constexpr Brano BRANO_TITOLO = Brano::TITOLO;
inline constexpr Brano BRANO_VITTORIA = Brano::VITTORIA;
inline constexpr Brano BRANO_SCONFITTA = Brano::SCONFITTA;

inline constexpr int INCONTRI = 7;
// Il brano di ogni incontro (battaglia::INCONTRO): la battaglia, o il duello.
inline constexpr Brano BRANO_INCONTRO[INCONTRI] = { Brano::BATTAGLIA, Brano::BATTAGLIA, Brano::CORRADO, Brano::BATTAGLIA, Brano::BATTAGLIA, Brano::BATTAGLIA, Brano::BATTAGLIA };

inline constexpr int EVENTI = 16;
// L'effetto di ogni evento della battaglia (battaglia::EventKind), o NESSUNO.
inline constexpr int8_t EFFETTO_EVENTO[EVENTI] = {
    int8_t(Effetto::COLPO),   // HIT
    int8_t(Effetto::SCUDO),   // SHIELD_BREAK
    int8_t(Effetto::FEDE),   // BARRIER_ABSORB
    int8_t(Effetto::SCUDO),   // GUARD_REDIRECT
    NESSUNO,   // FERVOR_GAIN
    int8_t(Effetto::FUOCO),   // BURN_TICK
    int8_t(Effetto::SVANISCE),   // DEFEAT
    int8_t(Effetto::FEDE),   // BARRIER_UP
    int8_t(Effetto::SCUDO),   // GUARD_UP
    int8_t(Effetto::FEDE),   // CHARGE
    NESSUNO,   // BREAK_SKIP
    int8_t(Effetto::SCUDO),   // IMMUNE
    NESSUNO,   // FERVOR_SPEND
    int8_t(Effetto::SCUDO),   // DEF_UP
    int8_t(Effetto::CURA),   // CURA
    int8_t(Effetto::CURA),   // PURIFICA
};

// Il colpo di questo eroe non e' 'colpo': e' il suo fuoco.
inline constexpr int EROE_DEL_FUOCO = 2;
inline constexpr Effetto EFFETTO_DEL_FUOCO = Effetto::FUOCO;

// Gli effetti dell'interfaccia, per uso (audio::suona).
enum class Suono : uint8_t
{
    CURSORE,
    CONFERMA,
    ANNULLA,
    TESTO,
    SALVA,
    LIVELLO,
    RACCOLTA,
};

inline constexpr int SUONI = 7;
inline constexpr Effetto EFFETTO_SUONO[SUONI] = {
    Effetto::CURSORE,   // CURSORE
    Effetto::CONFERMA,   // CONFERMA
    Effetto::ANNULLA,   // ANNULLA
    Effetto::TESTO,   // TESTO
    Effetto::SALVA,   // SALVA
    Effetto::LIVELLO,   // LIVELLO
    Effetto::CURA,   // RACCOLTA
};

}

// Gli item di Butano, nello stesso ordine: solo nella build della ROM, dove mmutil genera gli header.
#if __has_include("bn_music_items.h") && __has_include("bn_sound_items.h")
    #include "bn_music_items.h"
    #include "bn_sound_items.h"

namespace gubbio::colonna
{

inline constexpr bn::music_item MUSICA[BRANI] = {
    bn::music_items::bandiere,
    bn::music_items::basilica,
    bn::music_items::battaglia,
    bn::music_items::bottaccione,
    bn::music_items::canzone_di_flaviano,
    bn::music_items::citta,
    bn::music_items::corrado,
    bn::music_items::fazio,
    bn::music_items::notte,
    bn::music_items::pastorale,
    bn::music_items::presentazione,
    bn::music_items::prologo,
    bn::music_items::sconfitta,
    bn::music_items::stradoni,
    bn::music_items::taverna,
    bn::music_items::terza_alba,
    bn::music_items::titolo,
    bn::music_items::undici_bandiere,
    bn::music_items::vittoria,
};

inline constexpr bn::sound_item SUONO[EFFETTI] = {
    bn::sound_items::annulla,
    bn::sound_items::campanone,
    bn::sound_items::colpo,
    bn::sound_items::conferma,
    bn::sound_items::cura,
    bn::sound_items::cursore,
    bn::sound_items::fede,
    bn::sound_items::fuoco,
    bn::sound_items::livello,
    bn::sound_items::salva,
    bn::sound_items::scudo,
    bn::sound_items::svanisce,
    bn::sound_items::testo,
};

}

#endif

#endif
