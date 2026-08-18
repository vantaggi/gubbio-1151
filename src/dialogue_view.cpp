#include "dialogue_view.h"

#include "bn_regular_bg_items_dialogue_frame.h"

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
    // Il pezzo appena chiuso diventa definitivo: i suoi sprite passano fra gli stabili e non
    // verranno piu' rigenerati. La coda riparte da qui, spostata a destra della sua larghezza.
    const bn::string_view chiuso(riga.data() + _stable_bytes, _tail_bytes);

    for(const bn::sprite_ptr& sprite : _tail)
    {
        if(! _stable.full())
        {
            _stable.push_back(sprite);
        }
    }

    _tail.clear();
    _tail_x += _generator.width(chiuso);
    _stable_bytes += _tail_bytes;
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

    const int byte_visibili = visibile.size();

    if(byte_visibili == _stable_bytes + _tail_bytes)
    {
        return;                     // nulla di nuovo da rivelare: nessun tocco all'allocatore
    }

    // Il pezzo che la coda dovrebbe contenere adesso.
    const bn::string_view coda(visibile.data() + _stable_bytes, byte_visibili - _stable_bytes);

    // Se la coda supererebbe la larghezza di uno sprite, si chiude PRIMA di aggiungere il nuovo
    // carattere: e' la stessa regola con cui `sprite_text_generator` decide di aprire un nuovo
    // sprite, quindi i pezzi cadono esattamente dove cadrebbero disegnando la riga intera.
    if(_generator.width(coda) > SPRITE_TEXT_WIDTH)
    {
        _close_tail(visibile);
    }

    _tail_bytes = byte_visibili - _stable_bytes;
    _tail.clear();

    if(_tail_bytes > 0)
    {
        const bn::string_view nuova_coda(visibile.data() + _stable_bytes, _tail_bytes);
        _generator.generate(_tail_x, _row_y(_row), nuova_coda, _tail);
    }
}

} // namespace gubbio
