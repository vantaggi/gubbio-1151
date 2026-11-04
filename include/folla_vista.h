#ifndef GUBBIO_FOLLA_VISTA_H
#define GUBBIO_FOLLA_VISTA_H

#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "folla.h"

namespace gubbio
{

class Esplorazione;

// La folla della citta' (pezzo VIVA): chi passa per le strade e gli animali dell'area, secondo la fase della
// storia (include/folla.h, da mondo/folla.json). Ognuno va avanti e indietro sul suo percorso, si ferma ai capi
// (chi arriva da un varco sparisce dietro l'angolo e torna), si ferma se il giocatore gli sta davanti; le galline
// scappano, i piccioni volano via e tornano dopo un po'. Nessuno parla e nessuno ferma il giocatore.
class Folla
{
public:
    // Rifa' la folla dell'area per la fase (0 ULTIMATUM, 1 DIGIUNO, 2 NOTTE), con la palette della gente.
    void prepara(int area, int fase, const Esplorazione& esplorazione, const bn::sprite_palette_ptr& gente);

    void svuota()
    {
        _v.clear();
    }

    // Un frame: x, y i piedi del giocatore.
    void aggiorna(const Esplorazione& esplorazione, int x, int y, int frame);

    [[nodiscard]] int quanti() const
    {
        return _v.size();
    }

private:
    struct Viandante
    {
        bn::sprite_ptr sprite;
        int lunghezza;          // pixel del percorso
        int s;                  // pixel percorsi dal primo punto
        int verso;              // +1 verso l'ultimo punto, -1 verso il primo
        int pausa;              // frame di sosta rimasti
        int volo;               // piccione: >0 in volo, <0 nascosto prima di tornare
        int vx;
        int vy;
        int x;
        int y;
        uint8_t corrente;
        uint8_t caricato;       // il fotogramma nei tile (255: nessuno)
        uint8_t passi;          // pixel fatti, per la camminata
        uint8_t indice;
    };

    bn::vector<Viandante, folla::FOLLA_MAX> _v;

    void _carica(Viandante& v, int fotogramma);
};

}

#endif
