#ifndef GUBBIO_MENU_PAGINE_H
#define GUBBIO_MENU_PAGINE_H

#include "bn_optional.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"

#include "aiuti.h"
#include "battaglia_dati.h"
#include "game_state.h"
#include "testo.h"
#include "vista_menu.h"
#include "vista_testo.h"

// Lo schema comune delle pagine del menu di pausa (MPA; mockup menu/mockup_menu.py, pagina() e piede()) e le
// pagine, una per file: src/menu_pausa.cpp (la pausa e il Salva), src/menu_diario.cpp (MDI), ...
namespace gubbio
{
class Esplorazione;
}

namespace gubbio::menu
{

inline constexpr int PAGINE = 6;
inline constexpr int PAGINA_DIARIO = 0;
inline constexpr int PAGINA_MAPPA = 1;
inline constexpr int PAGINA_BISACCIA = 2;
inline constexpr int PAGINA_COMPAGNI = 3;
inline constexpr int PAGINA_SALVA = 4;
inline constexpr int PAGINA_OPZIONI = 5;

inline constexpr testo::TestoId VOCI[PAGINE] = {
    testo::TestoId::MENU_DIARIO, testo::TestoId::MENU_MAPPA, testo::TestoId::MENU_BISACCIA,
    testo::TestoId::MENU_COMPAGNI, testo::TestoId::MENU_SALVA, testo::TestoId::MENU_OPZIONI };

// L'interno delle pagine: le scritte da x 12 a 227 (4 px di respiro dal piombo), il piede a y 141.
inline constexpr int MARGINE_X = 12;
inline constexpr int DESTRA_X = 227;
inline constexpr int PIEDE_Y = 141;
// il cartiglio sta sulla griglia dei tile (Riquadri): sopra il bordo alto, il nome a 4 px dall'alto
inline constexpr int CARTIGLIO_Y = 0;
inline constexpr int FRAME_MESSAGGIO = 60;

void attendi(int frame);

enum class Esito : uint8_t
{
    INDIETRO,       // B: alla pausa
    CHIUDI,         // Start: al gioco
    SINISTRA,       // L: alla pagina prima
    DESTRA,         // R: alla pagina dopo
};

// Start, B, L o R premuti in questo frame? Allora 'esito' dice quale.
[[nodiscard]] bool navigazione(Esito& esito);

[[nodiscard]] testo::TestoId testo_della_fase(aiuti::FaseCronaca f);
[[nodiscard]] testo::TestoId testo_dell_area(const GameState& p);

// I compagni nell'ordine di sempre (Ubaldo, Giorgio, Antonio): il nome, il ritratto 32x32 con l'angolo in (x, y), e
// le forze come le avranno alla prossima battaglia (i PV tolti dai miasmi della gola, il Fervore iniziale, piu' alto
// coi Ceri).
inline constexpr testo::TestoId NOMI_COMPAGNI[battaglia::EROI] = {
    testo::TestoId::PARLANTE_UBALDO, testo::TestoId::PARLANTE_GIORGIO, testo::TestoId::PARLANTE_ANTONIO };

// Il posto di ogni compagno in una fila da sinistra (regola O1 di Cioti): Antonio a sinistra, Ubaldo al centro,
// Giorgio a destra. Lo prova tests/test_menu_pausa.py.
inline constexpr int POSTO_IN_FILA[battaglia::EROI] = { 1, 2, 0 };

static_assert(POSTO_IN_FILA[battaglia::UBALDO] == 1 && POSTO_IN_FILA[battaglia::GIORGIO] == 2 &&
              POSTO_IN_FILA[battaglia::ANTONIO] == 0, "O1: Antonio a sinistra, Ubaldo al centro, Giorgio a destra");

[[nodiscard]] bn::sprite_ptr crea_ritratto(int e, int x, int y);

struct Forze
{
    int livello;
    battaglia::Statistiche al_livello;
    int pv;
    int fervore;
};

[[nodiscard]] Forze forze(const GameState& p, int e);

// Una scritta col contesto del suo testo (cosi' non si sbaglia: VistaTesto lo controlla con un assert).
class Scritta
{
public:
    Scritta(testo::TestoId id, int x, int y, int inchiostro, const bn::sprite_palette_ptr& palette);

private:
    VistaTesto _vista;
};

// Gli aiuti dei tasti, «A: apri» e «B: indietro», a 12 px uno dall'altro (il font non tiene gli spazi doppi).
class AiutoTasti
{
public:
    AiutoTasti(testo::TestoId a, testo::TestoId b, int x, int y, const bn::sprite_palette_ptr& palette);
    AiutoTasti(testo::TestoId solo, int x, int y, const bn::sprite_palette_ptr& palette);

private:
    VistaTesto _a;
    bn::optional<VistaTesto> _b;
};

// Riquadro pieno, cartiglio col nome in alto a sinistra, in fondo il filo, gli aiuti dei tasti a sinistra e le
// sei tessere delle pagine a destra fra L e R.
class Pagina
{
public:
    Pagina(int indice, testo::TestoId aiuto_a, testo::TestoId aiuto_b, const bn::sprite_palette_ptr& palette);
    Pagina(int indice, testo::TestoId aiuto, const bn::sprite_palette_ptr& palette);

private:
    Riquadri _riquadri;
    VistaTesto _titolo;
    AiutoTasti _aiuto;
    VistaTesto _l;
    VistaTesto _r;
    Striscia _filo;
    Striscia _tessere;

    void _componi(int indice);
};

// Le pagine. Ognuna ritorna come se ne esce; con istantanea=true si mostra, scrive "Istantanea pausa_<nome>" e
// ritorna subito.
[[nodiscard]] Esito pagina_salva(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette, bool istantanea);
[[nodiscard]] Esito pagina_diario(const bn::sprite_palette_ptr& palette, bool istantanea);
[[nodiscard]] Esito pagina_bisaccia(const bn::sprite_palette_ptr& palette, bool istantanea);
[[nodiscard]] Esito pagina_compagni(const bn::sprite_palette_ptr& palette, bool istantanea);
[[nodiscard]] Esito pagina_opzioni(const bn::sprite_palette_ptr& palette, bool istantanea);

}

#endif
