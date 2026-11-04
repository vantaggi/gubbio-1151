#ifndef GUBBIO_VISTA_BATTAGLIA_H
#define GUBBIO_VISTA_BATTAGLIA_H

#include "battaglia.h"

// La vista della battaglia, senza Butano: quel che lo schermo mostra (le barre dei PV e del Fervore,
// chi e' caduto) e come si anima ogni evento. Il modello (include/battaglia.h) risolve un round tutto
// insieme; la vista consuma gli eventi uno per volta, e una barra cambia solo nel momento in cui la
// scena consuma l'evento che la riguarda (HIT, BURN_TICK, CURA, FERVOR_GAIN, FERVOR_SPEND): mai leggendo
// i PV gia' risolti del modello. src/autotest_vista.cpp lo prova a tempo di compilazione.
namespace gubbio::battaglia
{

inline constexpr int SLOT_VISTA = EROI + NEMICI_MAX;   // eroi 0..2, nemici dopo

[[nodiscard]] constexpr int slot_vista(bool nemico, int slot)
{
    return nemico ? EROI + slot : slot;
}

// Come la scena anima un evento: chi si muove (uno solo per volta), chi lampeggia, che numero o
// che scritta compare sopra chi.
enum class Gesto : uint8_t
{
    NESSUNO,        // l'evento cambia solo le barre (Fervore)
    COLPO,          // l'attore scatta verso il bersaglio, il bersaglio lampeggia, il danno sale
    IMMUNE,         // l'attore scatta, sul bersaglio la scritta IMMUNE e l'indizio del fuoco
    SCUDO_ROTTO,    // il bersaglio trema
    PARATA,         // assorbito da una barriera o preso dal Bastione: il bersaglio si illumina
    POTERE,         // l'attore si raccoglie: barriera, guardia, carica, difesa su, azione persa
    USTIONE,        // il bersaglio lampeggia di fuoco, il danno sale
    CADUTA,         // il bersaglio sparisce
    CURA,           // un consumabile: chi lo usa si raccoglie, il bersaglio si illumina, i PV salgono
};

struct Mossa
{
    Gesto gesto = Gesto::NESSUNO;
    int attore = -1;        // slot della vista che si muove, -1 nessuno
    int bersaglio = -1;     // slot della vista che reagisce
    int numero = 0;         // il danno da mostrare (0: nessun numero)
};

class VistaBattaglia
{

public:
    // All'inizio della battaglia vista e modello coincidono: e' l'unica volta che la vista legge
    // i PV e il Fervore dal modello.
    constexpr void inizia(const Battaglia& b, int nemici)
    {
        _nemici = nemici;

        for(int e = 0; e < EROI; ++e)
        {
            _pv[e] = b.eroe(e).pv;
            _pv_max[e] = b.eroe(e).pv_max;
            _fervore[e] = b.eroe(e).fervore;
            _fervore_max[e] = b.eroe(e).fervore_max;
            _caduto[e] = false;
        }

        for(int n = 0; n < NEMICI_MAX; ++n)
        {
            _pv[EROI + n] = b.nemico(n).pv;
            _pv_max[EROI + n] = b.nemico(n).pv_max;
            _caduto[EROI + n] = n >= nemici;
        }
    }

    // Consuma un evento: aggiorna le barre che quell'evento tocca e dice come animarlo.
    constexpr Mossa consuma(const Evento& e)
    {
        int attore = slot_vista(e.attore_nemico, e.attore);
        int bersaglio = slot_vista(e.bersaglio_nemico, e.bersaglio);
        Mossa m;

        switch(e.kind)
        {

        case EventKind::HIT:
            _pv[bersaglio] = e.pv_dopo;
            m = { Gesto::COLPO, attore, bersaglio, e.quantita };
            break;

        case EventKind::BURN_TICK:
            _pv[bersaglio] = e.pv_dopo;
            m = { Gesto::USTIONE, -1, bersaglio, e.quantita };
            break;

        case EventKind::CURA:
            _pv[bersaglio] = e.pv_dopo;
            m = { Gesto::CURA, attore, bersaglio, e.quantita };
            break;

        case EventKind::PURIFICA:
            m = { Gesto::CURA, attore, bersaglio, 0 };
            break;

        case EventKind::FERVOR_GAIN:
        case EventKind::FERVOR_SPEND:
            if(! e.bersaglio_nemico)
            {
                _fervore[e.bersaglio] = e.pv_dopo;
            }

            break;

        case EventKind::DEFEAT:
            _caduto[bersaglio] = true;
            m = { Gesto::CADUTA, -1, bersaglio, 0 };
            break;

        case EventKind::IMMUNE:
            m = { Gesto::IMMUNE, attore, bersaglio, 0 };
            break;

        case EventKind::SHIELD_BREAK:
            m = { Gesto::SCUDO_ROTTO, -1, bersaglio, 0 };
            break;

        case EventKind::BARRIER_ABSORB:
        case EventKind::GUARD_REDIRECT:
            m = { Gesto::PARATA, -1, bersaglio, 0 };
            break;

        case EventKind::BARRIER_UP:
        case EventKind::GUARD_UP:
        case EventKind::CHARGE:
        case EventKind::DEF_UP:
        case EventKind::BREAK_SKIP:
            m = { Gesto::POTERE, attore, bersaglio, 0 };
            break;

        default:
            break;
        }

        return m;
    }

    [[nodiscard]] constexpr int pv(int slot) const
    {
        return _pv[slot];
    }

    [[nodiscard]] constexpr int pv_max(int slot) const
    {
        return _pv_max[slot];
    }

    [[nodiscard]] constexpr int fervore(int eroe) const
    {
        return _fervore[eroe];
    }

    [[nodiscard]] constexpr int fervore_max(int eroe) const
    {
        return _fervore_max[eroe];
    }

    [[nodiscard]] constexpr bool caduto(int slot) const
    {
        return _caduto[slot];
    }

    [[nodiscard]] constexpr int nemici() const
    {
        return _nemici;
    }

private:
    int _pv[SLOT_VISTA] = {};
    int _pv_max[SLOT_VISTA] = {};
    int _fervore[EROI] = {};
    int _fervore_max[EROI] = {};
    bool _caduto[SLOT_VISTA] = {};
    int _nemici = 0;
};

// La scelta del bersaglio nel menu: su chi punta un comando, chi si puo' scegliere, da chi si parte.
enum class Puntamento : uint8_t
{
    NESSUNO,        // il comando non sceglie (Bastione su se stesso, Carica, la Suprema su tutti)
    NEMICO,
    ALLEATO,        // il Muro della Fede
    CHI_MANGIA,     // un consumabile: un alleato che non e' a digiuno (Ubaldo nel DIGIUNO non mangia)
};

[[nodiscard]] constexpr Puntamento mira_del_comando(const Comando& c)
{
    if(c.tipo == TipoComando::OGGETTO)
    {
        return Puntamento::CHI_MANGIA;
    }

    if(c.tipo != TipoComando::USA_ABILITA)
    {
        return Puntamento::NESSUNO;
    }

    const Abilita& a = ABILITA[int(c.abilita)];

    if(a.bersaglio == Bersaglio::NEMICO)
    {
        return Puntamento::NEMICO;
    }

    return a.effetto == Effetto::MURO_DELLA_FEDE ? Puntamento::ALLEATO : Puntamento::NESSUNO;
}

[[nodiscard]] constexpr bool sceglibile(const Battaglia& b, Puntamento m, int i)
{
    return m == Puntamento::NEMICO ? i >= 0 && i < NEMICI_MAX && b.nemico(i).vivo() :
                               i >= 0 && i < EROI && b.eroe(i).vivo() &&
                               ! (m == Puntamento::CHI_MANGIA && b.eroe(i).a_digiuno);
}

// Il bersaglio da cui parte il cursore: lo stesso che il modello sceglierebbe da solo con -1 (il primo
// nemico vivo; per il Muro l'alleato piu' ferito, per un consumabile il piu' ferito fra chi mangia), cosi'
// chi preme subito A ha il comportamento di prima. -1 se nessuno si puo' scegliere.
[[nodiscard]] constexpr int bersaglio_predefinito(const Battaglia& b, Puntamento m)
{
    int scelto = -1;

    if(m == Puntamento::NEMICO)
    {
        for(int i = 0; i < NEMICI_MAX && scelto < 0; ++i)
        {
            scelto = sceglibile(b, m, i) ? i : -1;
        }
    }
    else if(m == Puntamento::ALLEATO || m == Puntamento::CHI_MANGIA)
    {
        for(int e = 0; e < EROI; ++e)
        {
            const Unita& u = b.eroe(e);

            if(sceglibile(b, m, e) && (scelto < 0 || u.pv * 100 / u.pv_max < b.eroe(scelto).pv * 100 / b.eroe(scelto).pv_max))
            {
                scelto = e;
            }
        }
    }

    return scelto;
}

// Il bersaglio dopo 'da' nel verso 'passo' (+1 o -1), saltando chi e' caduto; da' 'da' se non c'e' altri.
[[nodiscard]] constexpr int prossimo_bersaglio(const Battaglia& b, Puntamento m, int da, int passo)
{
    int quanti = m == Puntamento::NEMICO ? NEMICI_MAX : EROI;

    for(int k = 1; k <= quanti; ++k)
    {
        int i = ((da + passo * k) % quanti + quanti) % quanti;

        if(sceglibile(b, m, i))
        {
            return i;
        }
    }

    return da;
}

// Quanti pixel di una barra larga 'larghezza' sono pieni: arrotondato in su, cosi' chi ha ancora
// un PV ha almeno un pixel acceso.
[[nodiscard]] constexpr int pieno(int valore, int massimo, int larghezza)
{
    if(valore <= 0 || massimo <= 0)
    {
        return 0;
    }

    int p = (valore * larghezza + massimo - 1) / massimo;
    return p > larghezza ? larghezza : p;
}

}

#endif
