#ifndef DIALOGUE_DATA_H
#define DIALOGUE_DATA_H

#include <stdint.h>

#include "bn_string_view.h"

#include "dialogue_box.h"

// GENERATO DA tools/dialogue_exporter.py — non modificare a mano.
//
// Il copione della Sezione 31B del GDD, gia' spezzato in righe. Il taglio e' fatto **in pixel**
// sulle larghezze reali di `font_gubbio.h`: spezzare a 28 caratteri, come dice alla lettera la
// Sez. 25, darebbe righe da 90 a 220 px, alcune fuori dal box e altre mezze vuote.
//
// PERCHE' LE TABELLE SONO PIATTE. Il codice della Sez. 31C del GDD **non e' trascrivibile**:
// usa `bn::vector<DialogueNode, 4>` dentro un array `constexpr`, e `bn::vector` non e' un tipo
// letterale in Butano — non compilerebbe. Qui le battute stanno in un unico array e ogni script
// e' un INTERVALLO su quell'array: nessun contenitore annidato, tutto in ROM, zero RAM.

namespace gubbio {

struct DialogueLine
{
    bn::string_view row[DIALOGUE_MAX_ROWS];
    Speaker speaker;
};

// Tutte le battute del gioco, in fila. `inline` obbligatorio: senza, ogni unita' di traduzione
// ne riceverebbe una copia in .rodata (regola del Passo 1 del piano).
inline constexpr DialogueLine DIALOGUE_LINES[] = {
    {{"Monsignore... undici stendardi circondano", "la conca.", ""}, Speaker::PODESTA},
    {{"Le nostre milizie sono poche, e le", "scorte di grano a Palazzo Pretorio", "basteranno per una settimana."}, Speaker::PODESTA},
    {{"Se non troviamo un miracolo, cadremo", "prima dell'estate.", ""}, Speaker::PODESTA},
    {{"Non contare le lance dei perugini,", "Guido. Conta la fede di chi abita queste", "pietre."}, Speaker::UBALDO},
    {{"Fate sprangare le porte e ordinate alla", "città tre giorni di silenzio e digiuno.", ""}, Speaker::UBALDO},
    {{"Porta Romana sta cedendo sotto i colpi", "dei mangani di Foligno!", ""}, Speaker::PODESTA},
    {{"Giorgio, guida i balestrieri sui", "camminamenti prima che aprano una", "breccia!"}, Speaker::PODESTA},
    {{"Fermati, cavaliere! Nessuno passa davanti", "al Bargello senza dimostrare la follia", "sacra"}, Speaker::CITIZEN},
    {{"di chi ama questa terra più della", "propria vita!", ""}, Speaker::CITIZEN},
    {{"Sei pronto a compiere i tre giri e a", "bagnarti la fronte?", ""}, Speaker::CITIZEN},
    {{"Che l'acqua della fonte liberi il tuo", "braccio dalla paura!", ""}, Speaker::CITIZEN},
    {{"Eccoti la patente, ceraiolo!", "", ""}, Speaker::CITIZEN},
    {{"Mio nonno ha scalpellato la pietra del", "Condotto nel Bottaccione.", ""}, Speaker::CITIZEN},
    {{"Diceva sempre: c'è una fessura dove la", "roccia diventa nera come la pece... lì la", "terra non dorme."}, Speaker::CITIZEN},
    {{"Fate attenzione se scendete laggiù.", "", ""}, Speaker::CITIZEN},
    {{"Le mie fornaci sono spente, ragazzo. Le", "truppe di Spoleto hanno bloccato i", "carichi al passo."}, Speaker::CITIZEN},
    {{"Se mi riporti il ferro sequestrato alle", "fornaci basse,", ""}, Speaker::CITIZEN},
    {{"forgerò per Giorgio un pettorale che", "nessun dardo potrà scalfire.", ""}, Speaker::CITIZEN},
    {{"Gli alchimisti di Cagli stanno", "riversando veleno nel fosso.", ""}, Speaker::CITIZEN},
    {{"I feriti alle porte hanno le labbra", "viola e le bende non bastano.", ""}, Speaker::CITIZEN},
    {{"Mi serve l'elleboro che cresce solo", "sulle rocce umide del Bottaccione, o non", "supereranno la notte."}, Speaker::CITIZEN},
};

inline constexpr int DIALOGUE_LINE_COUNT = int(sizeof(DIALOGUE_LINES) / sizeof(DIALOGUE_LINES[0]));

// Uno script e' una sequenza di battute consecutive.
struct DialogueScript
{
    uint16_t first_line;
    uint8_t line_count;
};

enum class ScriptId : uint8_t
{
    PODESTA_ATTO_I,
    PODESTA_ATTO_III,
    TANO_INGAGGIO,
    TANO_PATENTE,
    BERTO_LORE,
    RANIERO_QUEST,
    AGNESE_QUEST,
    COUNT
};

inline constexpr DialogueScript DIALOGUE_SCRIPTS[int(ScriptId::COUNT)] = {
    {0, 5},   // PODESTA_ATTO_I
    {5, 2},   // PODESTA_ATTO_III
    {7, 3},   // TANO_INGAGGIO
    {10, 2},   // TANO_PATENTE
    {12, 3},   // BERTO_LORE
    {15, 3},   // RANIERO_QUEST
    {18, 3},   // AGNESE_QUEST
};

[[nodiscard]] constexpr const DialogueScript& dialogue_script(ScriptId id)
{
    return DIALOGUE_SCRIPTS[int(id)];
}

// Ogni script deve stare dentro la tabella delle battute: un intervallo che sborda sarebbe una
// lettura fuori array, e nessun assert lo direbbe prima che accada.
static_assert([]
{
    for(const DialogueScript& s : DIALOGUE_SCRIPTS)
    {
        if(s.line_count == 0 || int(s.first_line) + int(s.line_count) > DIALOGUE_LINE_COUNT)
        {
            return false;
        }
    }

    return true;
}(), "Uno script di dialogo esce dalla tabella delle battute");

} // namespace gubbio

#endif // DIALOGUE_DATA_H
