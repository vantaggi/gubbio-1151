#ifndef DIALOGUE_BOX_H
#define DIALOGUE_BOX_H

#include "bn_core.h"
#include "bn_string_view.h"
#include "bn_keypad.h"

namespace gubbio {

enum class Speaker { 
    UBALDO, 
    GIORGIO, 
    ANTONIO, 
    MONALDO, 
    PODESTA, 
    CITIZEN 
};

class DialogueManager {
private:
    bn::string_view _current_text;
    int _visible_chars;
    int _frame_counter;
    bool _is_active;

public:
    DialogueManager() : _current_text(""), _visible_chars(0), _frame_counter(0), _is_active(false) {}

    void show_message(Speaker speaker, bn::string_view text) {
        (void)speaker; // In futuro usato per selezionare avatar e pitch del bip audio
        _current_text = text;
        _visible_chars = 0;
        _frame_counter = 0;
        _is_active = true;
    }

    void update() {
        if(!_is_active) return;

        // Skip rapido testo con tasto B
        if(bn::keypad::b_pressed()) {
            _visible_chars = _current_text.size();
        }

        // Avanzamento tipo macchina da scrivere: 1 char ogni 2 frame
        if(_visible_chars < _current_text.size()) {
            _frame_counter++;
            if(_frame_counter % 2 == 0) {
                _visible_chars++;
            }
        }

        // Chiusura con tasto A quando il testo è completato
        if(_visible_chars >= _current_text.size() && bn::keypad::a_pressed()) {
            _is_active = false;
        }
    }

    [[nodiscard]] bool is_active() const { return _is_active; }
    [[nodiscard]] int visible_characters() const { return _visible_chars; }
    [[nodiscard]] bn::string_view text() const { return _current_text; }
};

} // namespace gubbio

#endif // DIALOGUE_BOX_H
