#ifndef DIALOGUE_BOX_H
#define DIALOGUE_BOX_H

#include <stdint.h>

#include "bn_assert.h"
#include "bn_keypad.h"
#include "bn_string.h"
#include "bn_string_view.h"
#include "bn_utf8_character.h"

namespace gubbio {

// Motore della finestra di dialogo (Sez. 25 GDD): tiene il TESTO e il suo avanzamento.
// Il disegno e' di `dialogue_view.h`: qui non si tocca un solo sprite.
//
// STORIA DI QUESTO FILE. Esisteva dalla Sessione 01 e non e' MAI stato compilato ne' eseguito:
// nessuna unita' di traduzione lo includeva. Non andava dato per funzionante, e infatti la
// ricognizione della Sessione 13 vi ha trovato difetti reali — piu' uno che il piano gli
// attribuiva a torto.
//
// --- I DIFETTI CHIUSI QUI, e cosa si e' scoperto verificandoli ---
//
// 1. AVANZAMENTO IN BYTE INVECE CHE IN CARATTERI. `_visible_chars` cresceva di 1 e si
//    confrontava con `size()`, che e' in byte. Con il font italiano della Sessione 12 ogni
//    lettera accentata occupa 2 byte, quindi il taglio cadeva regolarmente a meta' di una
//    sequenza UTF-8.
//    LA CONSEGUENZA NON E' QUELLA CHE IL PIANO PREVEDEVA. Verificato sui sorgenti di Butano:
//    tagliare una `bn::string_view` a meta' di una sequenza NON fa scattare alcun assert —
//    `bn::utf8_character` legge il byte successivo, che e' ancora nel buffer originale, lo trova
//    valido e disegna il glifo accentato INTERO (bn_utf8_character.h:83). Il typewriter mostra
//    un carattere che non aveva ancora rivelato, e se la view finisce esattamente a fine buffer
//    si legge memoria non posseduta: un difetto che passa i test e sbaglia in produzione.
//    L'assert scatta invece se il prefisso viene COPIATO in una `bn::string`, perche' li' il
//    terminatore non e' un byte di continuazione — cioe' proprio nella forma "prudente" che
//    verrebbe naturale adottare.
//    Qui il cursore avanza di `bn::utf8_character::size()`, quindi cade SEMPRE su un confine di
//    carattere e nessuno dei due casi puo' presentarsi.
//
// 2. LA VIEW NON POSSEDEVA LA MEMORIA. `bn::string_view` ha costruttori impliciti: passare una
//    stringa locale compilava senza una diagnostica e lasciava la view appesa a stack riusato.
//    Contratto scritto: `show_message` accetta SOLO view su memoria a durata statica —
//    letterali e tabelle in ROM. Per le battute costruite a runtime c'e' `show_composed()`, che
//    copia nel buffer membro.
//
// 3. IL TERZO DIFETTO DELL'ELENCO NON ESISTE. Il piano prescriveva di "normalizzare i confronti
//    signed/unsigned": `bn::string_view::size_type` e' `int` (bn_string_view.h:38), quindi non
//    c'era nulla da normalizzare. Chi "correggesse" mettendo cast a `unsigned` introdurrebbe il
//    difetto che crede di togliere, perche' `npos` vale -1 e ogni sottrazione sotto zero
//    diventerebbe un valore enorme. Annotato per iscritto perche' nessuno lo "ripari" domani.
//
// Difetti in piu', trovati dalla ricognizione e chiusi qui: nessuna guardia su `show_message`
// chiamata a dialogo gia' aperto, e nessun modo di chiudere il box se non premendo A.

enum class Speaker
{
    UBALDO,
    GIORGIO,
    ANTONIO,
    MONALDO,
    PODESTA,
    CITIZEN
};

// Righe per battuta. La Sez. 25 GDD dice "massimo 3 righe per box"; la struttura `DialogueNode`
// della Sez. 31C ne prevede due (`text_line_1`, `text_line_2`). Si adotta il 3 della Sez. 25,
// che e' la sezione che descrive il motore di testo, e le righe eccedenti restano vuote.
inline constexpr int DIALOGUE_MAX_ROWS = 3;

// Larghezza massima di una riga, in caratteri (Sez. 25 GDD). Il word-wrap NON e' compito di
// questa classe: le battute arrivano gia' spezzate in righe (Passo 17 del piano, `DialogueLine`
// con `row[3]`). Qui la costante serve a chi generera' quelle tabelle.
inline constexpr int DIALOGUE_MAX_CHARS_PER_ROW = 28;

// Capacita' del buffer per le battute interpolate. 64 byte decisi ora contro un bug non
// riproducibile fra dieci sessioni: e' il costo di una riga con qualche nome sostituito dentro.
inline constexpr int DIALOGUE_COMPOSED_CAPACITY = 64;

// Frame fra un carattere e il successivo: 1 ogni 2 frame = 30 caratteri al secondo (Sez. 25).
inline constexpr int DIALOGUE_FRAMES_PER_CHAR = 2;

class DialogueManager
{
public:
    DialogueManager() = default;

    // Apre una battuta. Le view devono puntare a memoria a DURATA STATICA: letterali, o tabelle
    // `constexpr` in ROM. Per tutto il resto esiste `show_composed`.
    void show_message(Speaker speaker, bn::string_view row0,
                      bn::string_view row1 = bn::string_view(),
                      bn::string_view row2 = bn::string_view())
    {
        // Aprire una battuta mentre un'altra e' in corso perdeva la prima senza che nulla lo
        // segnalasse. Ora e' un errore dichiarato: chi vuole incatenare due battute chiude la
        // precedente con `close()`.
        BN_ASSERT(! _active, "Dialogo gia' aperto: chiamare close() prima di mostrarne un altro");

        _speaker = speaker;
        _rows[0] = row0;
        _rows[1] = row1;
        _rows[2] = row2;
        _row_count = ! row2.empty() ? 3 : (! row1.empty() ? 2 : (! row0.empty() ? 1 : 0));
        _row_index = 0;
        _visible_bytes = 0;
        _frame_counter = 0;
        _active = _row_count > 0;
    }

    // Battuta costruita a runtime: il testo viene COPIATO nel buffer membro, e la view punta al
    // buffer. E' l'unica forma sicura per un nome di quartiere, un conteggio di oggetti
    // raccolti, o il nome dell'oggetto di un GIVE_ITEM (Passo 18).
    void show_composed(Speaker speaker, bn::string_view testo)
    {
        BN_ASSERT(testo.size() <= DIALOGUE_COMPOSED_CAPACITY,
                  "Battuta interpolata piu' lunga del buffer: ", testo.size());

        _composed.clear();

        for(char c : testo)
        {
            _composed.push_back(c);
        }

        show_message(speaker, bn::string_view(_composed.data(), _composed.size()));
    }

    void update()
    {
        if(! _active)
        {
            return;
        }

        if(bn::keypad::b_pressed())
        {
            _reveal_all();
        }
        else if(! is_complete())
        {
            ++_frame_counter;

            if(_frame_counter >= DIALOGUE_FRAMES_PER_CHAR)
            {
                _frame_counter = 0;
                _advance_one_character();
            }
        }

        if(is_complete() && bn::keypad::a_pressed())
        {
            close();
        }
    }

    void close()
    {
        _active = false;
        _row_count = 0;
        _row_index = 0;
        _visible_bytes = 0;
    }

    [[nodiscard]] bool is_active() const { return _active; }
    [[nodiscard]] Speaker speaker() const { return _speaker; }
    [[nodiscard]] int row_count() const { return _row_count; }

    [[nodiscard]] bool is_complete() const
    {
        return _row_count == 0 ||
               (_row_index >= _row_count - 1 && _visible_bytes >= _rows[_row_index].size());
    }

    // La porzione VISIBILE di una riga, gia' tagliata su un confine di carattere.
    //
    // La classe espone la sottostringa e non un contatore da interpretare: con un contatore,
    // ogni chiamante reimplementerebbe il taglio, e ogni chiamante potrebbe sbagliarlo — che e'
    // esattamente il modo in cui il difetto n.1 tornerebbe da un'altra porta.
    [[nodiscard]] bn::string_view visible_row(int row) const
    {
        if(row < 0 || row >= _row_count)
        {
            return bn::string_view();
        }

        if(row < _row_index)
        {
            return _rows[row];                                   // riga gia' completata
        }

        if(row > _row_index)
        {
            return bn::string_view();                            // non ancora cominciata
        }

        return bn::string_view(_rows[row].data(), _visible_bytes);
    }

    // Riga su cui la macchina da scrivere sta lavorando: l'unica che il disegno deve rifare.
    [[nodiscard]] int active_row() const { return _row_index; }

private:
    bn::string_view _rows[DIALOGUE_MAX_ROWS];
    bn::string<DIALOGUE_COMPOSED_CAPACITY> _composed;
    Speaker _speaker = Speaker::CITIZEN;
    int _row_count = 0;
    int _row_index = 0;
    int _visible_bytes = 0;      // offset IN BYTE dentro la riga corrente, su confine di carattere
    int _frame_counter = 0;
    bool _active = false;

    void _advance_one_character()
    {
        const bn::string_view& riga = _rows[_row_index];

        if(_visible_bytes >= riga.size())
        {
            if(_row_index < _row_count - 1)
            {
                ++_row_index;
                _visible_bytes = 0;
            }

            return;
        }

        // L'UNICA API di Butano che sa quanti byte occupa un carattere. Sommando questo valore
        // il cursore cade sempre su un confine, e il taglio non puo' spezzare una sequenza.
        const bn::utf8_character carattere(riga.data()[_visible_bytes]);
        _visible_bytes += carattere.size();

        // INVARIANTE: il cursore cade sempre su un confine di carattere. Un byte di
        // continuazione UTF-8 ha i due bit alti a 10; trovarcisi sopra significa che il taglio
        // spezzerebbe una sequenza, cioe' che qualcuno ha rimesso l'avanzamento in byte.
        // E' l'unico modo di far fallire subito un difetto che altrimenti non fallisce affatto:
        // tagliare una view a meta' sequenza non produce alcun assert di Butano, disegna solo
        // un carattere in anticipo.
        BN_ASSERT(_visible_bytes >= riga.size() ||
                      (uint8_t(riga.data()[_visible_bytes]) & 0xC0) != 0x80,
                  "Cursore del dialogo a meta' di una sequenza UTF-8: byte ", _visible_bytes);

        if(_visible_bytes > riga.size())
        {
            // Una sequenza troncata dai dati stessi: ci si ferma al limite della riga invece di
            // leggere oltre. Non accade con tabelle ben formate, e se accade e' un difetto del
            // copione, non del motore.
            _visible_bytes = riga.size();
        }
    }

    void _reveal_all()
    {
        _row_index = _row_count - 1;
        _visible_bytes = _rows[_row_index].size();
    }
};

} // namespace gubbio

#endif // DIALOGUE_BOX_H
