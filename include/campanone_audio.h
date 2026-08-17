#ifndef CAMPANONE_AUDIO_H
#define CAMPANONE_AUDIO_H

// `bn_sound_items.h` e' GENERATO da Butano a partire dai file in audio/: finche' la cartella
// e' vuota l'header non esiste e l'include spezza la build. Va riattivato insieme alle
// chiamate commentate qui sotto, nel momento in cui i campioni del Campanone entrano in
// audio/ (pipeline descritta nella Sezione 18B GDD).
// #include "bn_sound_items.h"
#include "bn_sound.h"

namespace gubbio {

class CampanoneAudio {
public:
    // Riproduce il singolo tocco maestoso del Campanone di Palazzo dei Consoli
    static void play_strike() {
        // bn::sound_items::campanone_hit.play(1.0);
    }

    // Riproduce la sequenza d'allarme / assedio a doppi
    static void play_siege_double() {
        // bn::sound_items::campanone_doppio.play(1.0);
    }
};

} // namespace gubbio

#endif // CAMPANONE_AUDIO_H
