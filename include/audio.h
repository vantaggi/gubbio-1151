#ifndef GUBBIO_AUDIO_H
#define GUBBIO_AUDIO_H

#include "colonna_sonora.h"
#include "game_state.h"

namespace gubbio::battaglia
{
struct Evento;
}

// Il suono del gioco (F7c): maxmod attraverso Butano, coi brani di audio/ scelti da
// include/colonna_sonora.h e dalle regole di include/audio_logica.h. Un brano non riparte se sta gia'
// suonando: passando da un'area all'altra dello stesso quartiere la musica continua.
namespace gubbio::audio
{

// Il gancio per l'opzione dell'audio (il menu delle opzioni verra' dopo): spento, la musica si ferma e
// gli effetti tacciono; riacceso, il brano giusto riparte al prossimo frame dell'esplorazione.
void accendi(bool acceso);
[[nodiscard]] bool acceso();

// I volumi delle opzioni (MOP), in tacche da 0 a opzioni::TACCHE: si applicano subito, anche al brano che suona.
void volumi(int musica, int effetti);

// Un brano: torna da capo se la partitura lo vuole (colonna::IN_ANELLO). Non riparte se sta gia' suonando.
void brano(colonna::Brano b);

// Ogni frame dell'esplorazione: il brano di fondo dell'area, della fase e del luogo, e il segnale di un
// luogo appena ci si entra. Un jingle (vittoria, segnale di Fazio) si lascia finire prima di cambiare.
void esplorazione(const GameState& partita, int area, int cella_x, int cella_y);

// All'inizio di una cutscene (regia::CUTSCENE_DATI): il suo brano e l'effetto del primo quadro. Alla fine,
// se aveva un brano suo, torna quello dell'area dove si era (la scena prosegue li', a dialogo).
void cutscene(int cutscene);
void fine_cutscene(int cutscene);

// Battaglia: il brano dell'incontro all'inizio, la vittoria o la sconfitta alla fine, l'effetto di ogni evento.
void battaglia(int incontro);
void fine_battaglia(bool vinta);
void evento(const battaglia::Evento& e);

void effetto(colonna::Effetto e);
void suona(colonna::Suono s);

}

#endif
