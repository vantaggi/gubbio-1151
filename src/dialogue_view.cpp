#include "dialogue_view.h"

#include <stdint.h>

#include "bn_assert.h"
#include "bn_display.h"

#include "bn_regular_bg_items_dialogue_frame.h"

#include "bn_log.h"
#include "bn_utf8_character.h"

#include "font_gubbio.h"

namespace gubbio {

namespace {

// Coordinate della finestra, nel sistema a origine in alto a sinistra (0-239 / 0-159), poi
// convertite a quello centrato di Butano. Il GDD non le fissa: la Sez. 25 descrive il motore di
// testo ma non quota la finestra, e l'unica geometria quotata in tutto il documento e' quella
// dell'HUD di BATTAGLIA (y 112-160, Sez. 14B.1). Si adotta la stessa fascia bassa, alzata di
// quattro pixel per far posto al bordo con le formelle.
constexpr int TEXT_X = 14;
constexpr int FIRST_ROW_Y = 118;
constexpr int ROW_HEIGHT = 13;      // 8 px di glifo piu' 5 di interlinea: tre righe in 47 px

// Larghezza di uno sprite di testo di Butano: e' li' che il generatore chiude lo sprite e ne
// apre un altro.
constexpr int SPRITE_TEXT_WIDTH = 32;

// Arretra un offset fino al piu' vicino inizio di carattere. I byte di continuazione UTF-8
// hanno i due bit alti a `10`: cominciare una sottostringa su uno di essi significa passare al
// generatore di testo una sequenza monca, e `sprite_text_generator::_paint` la respinge con
// "Invalid character" — fermando il gioco davanti al giocatore.
//
// PERCHE' SERVE QUI, se il motore avanza gia' per codepoint. Perche' questa vista NON taglia
// dove taglia il motore: spezza la riga anche ai confini di sprite, per rigenerare solo la coda
// in crescita, e quei confini sono decisi dalla larghezza in pixel — che non sa nulla di UTF-8.
[[nodiscard]] int allinea_a_carattere(bn::string_view riga, int offset)
{
    while(offset > 0 && offset < riga.size() &&
          (uint8_t(riga.data()[offset]) & 0xC0) == 0x80)
    {
        --offset;
    }

    return offset;
}

[[nodiscard]] constexpr int sx(int screen_x) { return screen_x - 120; }
[[nodiscard]] constexpr int sy(int screen_y) { return screen_y - 80; }

} // namespace

DialogueView::DialogueView() :
    _frame(bn::regular_bg_items::dialogue_frame.create_bg(0, 0)),
    _generator(FONT_GUBBIO)
{
    _generator.set_left_alignment();

    // Priorita' 0: la cornice sta davanti a suolo (2), foreground (1) e cielo (3), come vuole la
    // Sez. 14A. Gli sprite del testo, a parita' di priorita', stanno davanti ai background.
    _frame.set_priority(0);

    // Stessa ragione del suolo: l'origine di un BG e' il suo centro. La cornice e' dipinta nelle
    // righe 108-159 di un'immagine 256x256, e senza questo spostamento compariva 48 px piu' in
    // alto — con il testo, che e' fatto di sprite e usa coordinate di schermo, che le finiva
    // sotto invece che dentro.
    _frame.set_position(0, 128 - bn::display::height() / 2);
    _generator.set_bg_priority(0);

    // Il BG e' allocato ALL'INGRESSO della scena e non a richiesta (Passo 9 del piano): tre BG
    // residenti piu' uno intermittente e' il caso in cui l'allocatore best-fit fallisce per
    // frammentazione anche con blocchi liberi a sufficienza. Resta invisibile finche' non serve.
    _frame.set_visible(false);
}

int DialogueView::_row_y(int row) const
{
    return sy(FIRST_ROW_Y + row * ROW_HEIGHT);
}

void DialogueView::_reset()
{
    _stable.clear();
    _tail.clear();
    _row = -1;
    _stable_bytes = 0;
    _tail_bytes = 0;
    _tail_x = sx(TEXT_X);
}

void DialogueView::_close_tail(bn::string_view riga)
{
    if(! riga.data() || _tail_bytes <= 0)
    {
        _tail.clear();
        _tail_bytes = 0;
        return;
    }

    // Il pezzo appena chiuso diventa definitivo: i suoi sprite passano fra gli stabili e non
    // verranno piu' rigenerati. La coda riparte da qui, spostata a destra della sua larghezza.
    const int inizio = allinea_a_carattere(riga, _stable_bytes);
    const int quanti = allinea_a_carattere(riga, inizio + _tail_bytes) - inizio;
    const bn::string_view chiuso(riga.data() + inizio, quanti > 0 ? quanti : 0);

    for(const bn::sprite_ptr& sprite : _tail)
    {
        if(! _stable.full())
        {
            _stable.push_back(sprite);
        }
    }

    _tail.clear();
    _tail_x += _generator.width(chiuso);
    // Si avanza della lunghezza ALLINEATA appena disegnata, non dei byte grezzi della coda.
    // I due valori coincidono sempre — `coda` e' per costruzione la differenza fra due
    // offset gia' allineati — e una simulazione dell'algoritmo su tutte le battute lo ha
    // confermato: la vecchia forma NON produceva mai un taglio storto. Resta questa perche'
    // dice cosa intende fare invece di appoggiarsi a una coincidenza, ma va messo a verbale
    // che NON e' la causa dell'errore "Invalid character" visto dal committente: quella e'
    // ancora aperta.
    _stable_bytes = inizio + (quanti > 0 ? quanti : 0);
    _tail_bytes = 0;
}

void DialogueView::update(const DialogueManager& dialogue)
{
    if(! dialogue.is_active())
    {
        if(_visible)
        {
            _reset();
            _frame.set_visible(false);
            _visible = false;
        }

        return;
    }

    if(! _visible)
    {
        _reset();
        _frame.set_visible(true);
        _visible = true;
    }

    const int riga_attiva = dialogue.active_row();
    const bn::string_view visibile = dialogue.visible_row(riga_attiva);

    // Cambio di riga: quella precedente e' conclusa, e cio' che ne resta nella coda diventa
    // stabile. Da qui in poi non verra' piu' toccata.
    if(riga_attiva != _row)
    {
        if(_row >= 0)
        {
            _close_tail(dialogue.visible_row(_row));
        }

        _row = riga_attiva;
        _stable_bytes = 0;
        _tail_bytes = 0;
        _tail_x = sx(TEXT_X);
        _tail.clear();
    }

    if(! visibile.data())
    {
        return;                     // riga non ancora cominciata: niente da disegnare
    }

    const int byte_visibili = visibile.size();

    if(byte_visibili == _stable_bytes + _tail_bytes)
    {
        return;                     // nulla di nuovo da rivelare: nessun tocco all'allocatore
    }

    // Il pezzo che la coda dovrebbe contenere adesso, allineato ai confini di carattere.
    _stable_bytes = allinea_a_carattere(visibile, _stable_bytes);
    const bn::string_view coda(visibile.data() + _stable_bytes, byte_visibili - _stable_bytes);

    // Se la coda supererebbe la larghezza di uno sprite, si chiude PRIMA di aggiungere il nuovo
    // carattere: e' la stessa regola con cui `sprite_text_generator` decide di aprire un nuovo
    // sprite, quindi i pezzi cadono esattamente dove cadrebbero disegnando la riga intera.
    if(_generator.width(coda) > SPRITE_TEXT_WIDTH)
    {
        _close_tail(visibile);

        // RIALLINEARE ANCHE DOPO. L'allineamento di poche righe sopra vale per il
        // `_stable_bytes` con cui si e' MISURATA la coda; `_close_tail` lo sposta in
        // avanti, e quel nuovo valore non era controllato da nessuno. Due chiamate a una
        // funzione che costa una manciata di confronti sono il prezzo per non dover
        // dimostrare, ogni volta che si tocca questo file, che il secondo punto non ne ha
        // bisogno.
        _stable_bytes = allinea_a_carattere(visibile, _stable_bytes);
    }

    _tail_bytes = byte_visibili - _stable_bytes;
    _tail.clear();

    if(_tail_bytes > 0)
    {
        const bn::string_view nuova_coda(visibile.data() + _stable_bytes, _tail_bytes);
        // NON SI ASSERISCE, SI RINUNCIA AL FOTOGRAMMA. Passare al generatore una coda che non
        // sia un numero intero di caratteri lo fa terminare con BN_ERROR("Invalid character"),
        // cioe' FERMA IL GIOCO davanti a chi sta giocando; saltare il disegno per un frame
        // costa invece un carattere che compare un sessantesimo di secondo dopo, e nessuno se
        // ne accorge — al fotogramma successivo la coda e' cresciuta e torna valida.
        //
        // Fra un difetto che interrompe la partita e uno che ritarda un glifo, la scelta non e'
        // discutibile. Il BN_LOG resta perche' l'occasione di sapere QUALE testo lo provoca non
        // vada persa: e' l'informazione che finora e' mancata per correggerlo alla radice.
        bool coda_intera = nuova_coda.data() != nullptr;
        int passo = 0;

        while(coda_intera && passo < _tail_bytes)
        {
            const int larghezza_carattere = bn::utf8_character(nuova_coda.data()[passo]).size();

            if(larghezza_carattere <= 0 || passo + larghezza_carattere > _tail_bytes)
            {
                coda_intera = false;
                break;
            }

            passo += larghezza_carattere;
        }

        if(! coda_intera)
        {
            BN_LOG("DIALOGO: coda scartata, ", _tail_bytes, " byte da ", _stable_bytes,
                   " sulla riga ", _row, " (primo byte ",
                   nuova_coda.data() ? int(uint8_t(nuova_coda.data()[0])) : -1, ")");
            return;
        }

        _generator.generate(_tail_x, _row_y(_row), nuova_coda, _tail);
    }
}

} // namespace gubbio
