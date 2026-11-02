#ifndef GUBBIO_REGIA_LOGICA_H
#define GUBBIO_REGIA_LOGICA_H

#include "game_state.h"
#include "regia.h"

// Il lettore delle cutscene senza Butano: a che inquadratura si e', quale battuta del narratore si
// legge, quanto scorre ogni piano, quanto e' scura la dissolvenza. Start salta tutto, A avanza il
// testo; gli stacchi fra inquadrature sono netti, la dissolvenza c'e' solo all'inizio e alla fine.
// src/autotest_regia.cpp lo prova a tempo di compilazione; src/regia.cpp lo mette a schermo.
namespace gubbio::regia
{

inline constexpr int FRAME_DISSOLVENZA = 30;
inline constexpr int FRAME_COLPO = 30;          // quando cade il colpo in un'inquadratura "colpo"
inline constexpr int FRAME_LAMPO = 12;          // quanto dura il lampo bianco
inline constexpr int FRAME_SCOSSA = 20;         // quanto trema il quadro
inline constexpr int FRAME_PASSO = 15;          // ogni quanto i fanti cambiano posa

class Lettore
{

public:
    constexpr void inizia(int cutscene)
    {
        _c = &CUTSCENE_DATI[cutscene];
        _inquadratura = 0;
        _frame = 0;
        _frame_totale = 0;
        _avanzate = 0;
        _finita = false;
        _stacco = true;
    }

    // Un frame. Ritorna false a cutscene finita.
    constexpr bool passo(bool a, bool start)
    {
        if(_finita)
        {
            return false;
        }

        _stacco = false;

        if(start)
        {
            _finita = true;
            return false;
        }

        const Inquadratura& q = inquadratura();

        // A: la battuta dopo; dopo l'ultima dell'inquadratura, l'inquadratura dopo
        if(a && q.battute > 0)
        {
            if(battuta_nell_inquadratura() + 1 < q.battute)
            {
                ++_avanzate;
            }
            else
            {
                _frame = q.frame;
            }
        }

        ++_frame;
        ++_frame_totale;

        if(_frame >= q.frame)
        {
            ++_inquadratura;
            _frame = 0;
            _avanzate = 0;
            _stacco = true;

            if(_inquadratura >= _c->inquadrature)
            {
                _finita = true;
                return false;
            }
        }

        return true;
    }

    [[nodiscard]] constexpr const Inquadratura& inquadratura() const
    {
        return INQUADRATURA[_c->prima_inquadratura + _inquadratura];
    }

    [[nodiscard]] constexpr int indice_inquadratura() const
    {
        return _inquadratura;
    }

    // La battuta dell'inquadratura che si legge: il tempo dell'inquadratura si divide fra le sue
    // battute, A porta avanti prima.
    [[nodiscard]] constexpr int battuta_nell_inquadratura() const
    {
        const Inquadratura& q = inquadratura();

        if(q.battute == 0)
        {
            return -1;
        }

        int per_tempo = _frame * q.battute / q.frame;
        int b = per_tempo + _avanzate;
        return b >= q.battute ? q.battute - 1 : b;
    }

    // L'indice in BATTUTA della battuta a schermo, -1 se nessuna.
    [[nodiscard]] constexpr int battuta() const
    {
        int b = battuta_nell_inquadratura();
        return b < 0 ? -1 : inquadratura().prima_battuta + b;
    }

    // Di quanti pixel e' scorso il piano 'k' (0 il piu' lontano) dei 'piani' dell'inquadratura: il
    // primo piano alla velocita' data, gli altri a 3/4, 1/2 e 1/4.
    [[nodiscard]] constexpr int scorrimento(int k, int piani) const
    {
        int quarti = k + 1 + (PIANI_PER_INQUADRATURA - piani);
        return _frame * inquadratura().velocita * quarti / (4 * FRAME_PER_SECONDO);
    }

    // Quanto e' buio (0 niente, FRAME_DISSOLVENZA tutto): solo nei primi frame della prima
    // inquadratura e negli ultimi dell'ultima.
    [[nodiscard]] constexpr int buio() const
    {
        const Inquadratura& q = inquadratura();
        int b = 0;

        if(_inquadratura == 0 && _frame < FRAME_DISSOLVENZA)
        {
            b = FRAME_DISSOLVENZA - _frame;
        }

        if(_inquadratura == _c->inquadrature - 1 && q.frame - _frame < FRAME_DISSOLVENZA)
        {
            int fine = FRAME_DISSOLVENZA - (q.frame - _frame);
            b = fine > b ? fine : b;
        }

        return b;
    }

    // Il lampo del colpo (0 niente, FRAME_LAMPO tutto bianco): parte pieno e si spegne.
    [[nodiscard]] constexpr int lampo() const
    {
        int f = _frame - FRAME_COLPO;
        return inquadratura().colpo && f >= 0 && f < FRAME_LAMPO ? FRAME_LAMPO - f : 0;
    }

    // La scossa del colpo: di quanti pixel si spostano i piani, a destra e a sinistra, sempre meno.
    [[nodiscard]] constexpr int scossa() const
    {
        int f = _frame - FRAME_COLPO;

        if(! inquadratura().colpo || f < 0 || f >= FRAME_SCOSSA)
        {
            return 0;
        }

        int ampiezza = 3 - f * 3 / FRAME_SCOSSA;
        return (f / 2) % 2 ? -ampiezza : ampiezza;
    }

    // La posa dei fanti (0 o 1) nei piani che hanno il passo.
    [[nodiscard]] constexpr int posa() const
    {
        return (_frame_totale / FRAME_PASSO) % 2;
    }

    [[nodiscard]] constexpr bool finita() const
    {
        return _finita;
    }

    [[nodiscard]] constexpr bool stacco() const
    {
        return _stacco;
    }

    [[nodiscard]] constexpr int frame_totale() const
    {
        return _frame_totale;
    }

private:
    const Cutscene* _c = &CUTSCENE_DATI[0];
    int _inquadratura = 0;
    int _frame = 0;
    int _frame_totale = 0;
    int _avanzate = 0;
    bool _finita = false;
    bool _stacco = true;
};

// Le cutscene viste: un bit per cutscene in GameState. Una cutscene gia' vista non riparte da sola.
[[nodiscard]] constexpr bool vista(const GameState& p, int cutscene)
{
    return (p.cutscene_viste[cutscene / 8] >> (cutscene % 8)) & 1;
}

constexpr void segna_vista(GameState& p, int cutscene)
{
    p.cutscene_viste[cutscene / 8] = uint8_t(p.cutscene_viste[cutscene / 8] | (1 << (cutscene % 8)));
}

static_assert(CUTSCENE <= 16, "le cutscene viste stanno in due byte di GameState");

}

#endif
