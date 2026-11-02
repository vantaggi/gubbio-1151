#ifndef GUBBIO_BATTAGLIA_H
#define GUBBIO_BATTAGLIA_H

#include "battaglia_dati.h"

// La battaglia a eventi (fase F4, parte 1: solo logica). Il modello si risolve tutto qui e lascia
// una sequenza di eventi: la vista, quando ci sara', leggera' solo quelli. Riscritta sul modello
// del prototipo (tag prototipo-v0: src/battle_scene.cpp), con le decisioni del piano F4:
//   - il boss agisce due volte per turno, i comuni una; lo Shield Break le annulla tutte e due;
//   - Corrado e' IMMUNE al taglio finche' non e' ustionato;
//   - il Muro della Fede va, per difetto, sull'alleato piu' ferito;
//   - la Suprema (Boost massimo) richiede sempre la carica: un turno prima, poi il colpo;
//   - l'IA dei nemici e' a regole (docs/piano_ia_boss.md del prototipo): tabelle REGOLE e SCRIPT.
// Niente heap: array fissi. Deterministica: l'unico caso e' un xorshift32 con il suo seme, lo
// stesso del mirror Python (tools/battaglia_mirror.py). Tutto constexpr: l'autotest confronta a
// tempo di compilazione ogni battaglia con le firme che il mirror ha scritto in
// include/battaglia_attese.h.
namespace gubbio::battaglia
{

enum class EventKind : uint8_t
{
    HIT,              // danno agli PV: quantita = danno, pv_dopo = PV rimasti
    SHIELD_BREAK,     // scudo azzerato colpendo la debolezza
    BARRIER_ABSORB,   // il Muro della Fede ha assorbito: quantita = punti assorbiti
    GUARD_REDIRECT,   // il Bastione ha preso il colpo: bersaglio = chi era puntato, quantita = chi lo prende
    FERVOR_GAIN,      // Fervore guadagnato: quantita = guadagno, pv_dopo = Fervore dopo (non PV)
    BURN_TICK,        // ustione di fine round
    DEFEAT,           // l'unita' e' caduta
    BARRIER_UP,       // Muro della Fede alzato: quantita = punti di barriera
    GUARD_UP,         // Bastione alzato: quantita = round di guardia
    CHARGE,           // carica della Suprema
    BREAK_SKIP,       // azione annullata dallo Shield Break
    IMMUNE,           // colpo fisico su Corrado non ustionato: nessun danno
    FERVOR_SPEND,     // un eroe spende Fervore per agire: quantita = spesa, pv_dopo = Fervore rimasto
    DEF_UP,           // Scudo di Forgia: quantita = percento di Difesa in piu'
    COUNT,
};

struct Evento
{
    EventKind kind;
    uint8_t attore;
    uint8_t bersaglio;
    bool attore_nemico;
    bool bersaglio_nemico;
    int16_t quantita;
    int16_t pv_dopo;
};

// Il round peggiore, derivato: 3 eroi la cui Suprema colpisce tutti i NEMICI_MAX nemici, NEMICI_MAX
// nemici con due azioni, fino a 7 eventi per colpo (guardia, immunita', scudo, barriera, danno,
// sconfitta, Fervore), un evento di comando per azione, ustione e sconfitta a fine round per tutti.
inline constexpr int EVENTI_PER_COLPO = 7;
inline constexpr int AZIONI_MAX = EROI + NEMICI_MAX * 2;
inline constexpr int EVENTI_ROUND_MAX =
        EROI * NEMICI_MAX * EVENTI_PER_COLPO + NEMICI_MAX * 2 * EVENTI_PER_COLPO + AZIONI_MAX * 3 + (EROI + NEMICI_MAX) * 3;

enum class Esito : uint8_t
{
    IN_CORSO,
    VITTORIA,
    SCONFITTA,
    PARITA,
};

// Le fasi della macchina a stati: ogni chiamata ad avanza() ne fa una.
enum class Fase : uint8_t
{
    SCELTA_COMANDI,
    CODA,
    ESECUZIONE,
    FINE_ROUND,
    ESITO,
    FINITA,
};

enum class TipoComando : uint8_t
{
    USA_ABILITA,
    CARICA,
    SUPREMA,
};

struct Comando
{
    TipoComando tipo = TipoComando::USA_ABILITA;
    AbilitaId abilita = AbilitaId::ATTACCO;
    int bersaglio = -1;         // -1: il bersaglio predefinito
    int boost = 0;
};

struct Unita
{
    int pv = 0;
    int pv_max = 0;
    int fervore = 0;
    int fervore_max = 0;
    int attacco = 0;
    int difesa = 0;
    int mistico = 0;
    int resistenza = 0;
    int velocita = 0;
    int barriera = 0;
    int scudo = 0;
    int scudo_max = 0;
    int rotto = 0;              // round di Shield Break rimasti
    Elemento debolezza = Elemento::NESSUNO;
    Elemento resiste = Elemento::NESSUNO;
    int ustione_cariche = 0;
    int ustione_danno = 0;
    int ustione_turni = 0;
    int guardia = 0;
    bool carica = false;
    bool nemico = false;
    int azioni = 1;
    bool immune_al_taglio = false;
    int difesa_bonus = 0;       // percento in piu' (Scudo di Forgia)
    int script = 0;
    int ia_round = 0;           // i round in cui l'unita' ha agito, per le condizioni dell'IA
    uint32_t ia_battaglia = 0;  // un bit per regola: gia' usata in questa battaglia
    uint32_t ia_round_bit = 0;  // un bit per regola: gia' usata in questo round

    [[nodiscard]] constexpr bool vivo() const
    {
        return pv > 0;
    }

    [[nodiscard]] constexpr int difesa_effettiva() const
    {
        int d = (difesa * (100 + difesa_bonus)) / 100;
        return rotto > 0 ? d / 2 : d;
    }

    [[nodiscard]] constexpr int resistenza_effettiva() const
    {
        return rotto > 0 ? resistenza / 2 : resistenza;
    }
};

struct Azione
{
    bool nemico = false;
    int slot = 0;
    Comando comando;
    int velocita = 0;
};

// Lo xorshift32 del mirror: stesso seme, stessa sequenza.
class Caso
{

public:
    constexpr explicit Caso(uint32_t seme) :
        _stato(seme * 2654435761u + 0x9E3779B9u)
    {
        if(! _stato)
        {
            _stato = 1;
        }
    }

    constexpr uint32_t prossimo()
    {
        _stato ^= _stato << 13;
        _stato ^= _stato >> 17;
        _stato ^= _stato << 5;
        return _stato;
    }

    constexpr int intero(int n)
    {
        return int(prossimo() % uint32_t(n));
    }

private:
    uint32_t _stato;
};

[[nodiscard]] constexpr int moltiplicatore(const Unita& bersaglio, Elemento elemento)
{
    if(elemento == Elemento::NESSUNO)
    {
        return ELEMENTO_NEUTRO;
    }

    if(bersaglio.debolezza == elemento)
    {
        return ELEMENTO_DEBOLE;
    }

    return bersaglio.resiste == elemento ? ELEMENTO_RESISTE : ELEMENTO_NEUTRO;
}

// Formule della Sezione 13C del GDD, in interi a 32 bit.
[[nodiscard]] constexpr int calcola_danno(const Unita& attore, const Unita& bersaglio, const Abilita& abilita, int boost)
{
    int danno;

    if(abilita.elemento == Elemento::FISICO)
    {
        int difesa = (bersaglio.difesa_effettiva() * (100 - abilita.perforazione)) / 100;
        danno = ((attore.attacco * 2) - difesa) / 2;
        danno = (danno * abilita.potenza) / 100;
    }
    else
    {
        danno = abilita.danno_mistico + ((attore.mistico - bersaglio.resistenza_effettiva()) / 2);
    }

    danno = (danno * moltiplicatore(bersaglio, abilita.elemento)) / 100;
    danno = (danno * BOOST_DANNO[boost]) / 100;
    return danno < 1 ? 1 : danno;
}

[[nodiscard]] constexpr int calcola_muro(const Unita& lanciatore, int boost)
{
    int base = ((lanciatore.mistico * 18) / 10) + 12;
    return (base * BOOST_SOSTEGNO[boost]) / 100;
}

// La firma di una battaglia: quello che il mirror deve ritrovare identico.
struct Firma
{
    uint32_t hash = 2166136261u;    // FNV-1a su tutti gli eventi, nell'ordine
    int eventi = 0;
    int round = 0;
    Esito esito = Esito::IN_CORSO;
    uint32_t tipi = 0;              // un bit per EventKind emesso
    bool traboccato = false;        // un round ha superato EVENTI_ROUND_MAX
};

class Battaglia
{

public:
    constexpr Battaglia(int incontro, uint32_t seme, bool pilota_debole = false) :
        _caso(seme)
    {
        ricomincia(incontro, seme, pilota_debole);
    }

    // Una battaglia nuova sul posto: la ROM tiene una sola Battaglia in EWRAM e la riusa.
    // Il pilota debole sceglie male apposta (solo l'Attacco): serve a mostrare che si puo' perdere.
    constexpr void ricomincia(int incontro, uint32_t seme, bool pilota_debole = false)
    {
        _caso = Caso(seme);
        _pilota_debole = pilota_debole;
        _n_azioni = 0;
        _n_eventi_round = 0;
        _fase = Fase::SCELTA_COMANDI;
        _firma = Firma();

        for(int e = 0; e < EROI; ++e)
        {
            _eroi[e] = da_statistiche(STATISTICHE_EROI[e], false);
            _eroi[e].fervore = (_eroi[e].fervore_max * FERVORE_INIZIALE[e]) / 100;
        }

        const Incontro& i = INCONTRO[incontro];
        _n_nemici = i.nemici;

        for(int n = 0; n < NEMICI_MAX; ++n)
        {
            _nemici[n] = Unita();
        }

        for(int n = 0; n < _n_nemici; ++n)
        {
            const Nemico& dati = NEMICI[int(i.schieramento[n])];
            _nemici[n] = da_statistiche(dati.statistiche, true);
            _nemici[n].azioni = dati.azioni_per_turno;
            _nemici[n].immune_al_taglio = dati.immune_al_taglio;
            _nemici[n].script = dati.script;
        }
    }

    // I comandi degli eroi per il round che sta per cominciare, scelti da fuori (la scena, il
    // giocatore): sostituiscono quelli del pilota. Va chiamata dopo la fase SCELTA_COMANDI.
    constexpr void imposta_comando(int eroe, const Comando& comando)
    {
        _comandi[eroe] = comando;
    }

    // Una fase della macchina a stati. Ritorna false a battaglia finita.
    constexpr bool avanza()
    {
        switch(_fase)
        {

        case Fase::SCELTA_COMANDI:
            ++_firma.round;
            _n_eventi_round = 0;
            pilota();
            _fase = Fase::CODA;
            return true;

        case Fase::CODA:
            prepara_coda();
            _fase = Fase::ESECUZIONE;
            return true;

        case Fase::ESECUZIONE:
            for(int i = 0; i < _n_azioni; ++i)
            {
                if(tutti_morti(true) || tutti_morti(false))
                {
                    break;
                }

                esegui(_azioni[i]);
            }

            _fase = Fase::FINE_ROUND;
            return true;

        case Fase::FINE_ROUND:
            for(int n = 0; n < _n_nemici; ++n)
            {
                fine_round(_nemici[n], true, n);
            }

            for(int e = 0; e < EROI; ++e)
            {
                fine_round(_eroi[e], false, e);
            }

            _fase = Fase::ESITO;
            return true;

        case Fase::ESITO:
            if(tutti_morti(true))
            {
                _firma.esito = Esito::VITTORIA;
            }
            else if(tutti_morti(false))
            {
                _firma.esito = Esito::SCONFITTA;
            }
            else if(_firma.round >= ROUND_MAX)
            {
                _firma.esito = Esito::PARITA;
            }

            _fase = _firma.esito == Esito::IN_CORSO ? Fase::SCELTA_COMANDI : Fase::FINITA;
            return _fase != Fase::FINITA;

        default:
            return false;
        }
    }

    constexpr Firma gioca()
    {
        while(avanza())
        {
        }

        return _firma;
    }

    [[nodiscard]] constexpr const Firma& firma() const
    {
        return _firma;
    }

    [[nodiscard]] constexpr Fase fase() const
    {
        return _fase;
    }

    // Gli eventi del round in corso, per la vista.
    [[nodiscard]] constexpr int eventi_round() const
    {
        return _n_eventi_round;
    }

    [[nodiscard]] constexpr const Evento& evento(int i) const
    {
        return _eventi[i];
    }

    [[nodiscard]] constexpr const Unita& eroe(int i) const
    {
        return _eroi[i];
    }

    [[nodiscard]] constexpr const Unita& nemico(int i) const
    {
        return _nemici[i];
    }

private:
    Caso _caso;
    Unita _eroi[EROI];
    Unita _nemici[NEMICI_MAX];
    int _n_nemici = 0;
    Comando _comandi[EROI];
    Azione _azioni[AZIONI_MAX];
    int _n_azioni = 0;
    Evento _eventi[EVENTI_ROUND_MAX] = {};
    int _n_eventi_round = 0;
    Fase _fase = Fase::SCELTA_COMANDI;
    Firma _firma;
    bool _pilota_debole = false;

    static constexpr Unita da_statistiche(const Statistiche& s, bool nemico)
    {
        Unita u;
        u.pv = u.pv_max = s.pv;
        u.fervore_max = s.fervore;
        u.attacco = s.attacco;
        u.difesa = s.difesa;
        u.mistico = s.mistico;
        u.resistenza = s.resistenza;
        u.velocita = s.velocita;
        u.scudo = u.scudo_max = s.scudo;
        u.debolezza = s.debolezza;
        u.resiste = s.resiste;
        u.nemico = nemico;
        return u;
    }

    constexpr Unita& unita(bool nemico, int slot)
    {
        return nemico ? _nemici[slot] : _eroi[slot];
    }

    [[nodiscard]] constexpr int quanti(bool nemico) const
    {
        return nemico ? _n_nemici : EROI;
    }

    [[nodiscard]] constexpr bool tutti_morti(bool nemici) const
    {
        for(int i = 0; i < quanti(nemici); ++i)
        {
            if((nemici ? _nemici[i] : _eroi[i]).vivo())
            {
                return false;
            }
        }

        return true;
    }

    [[nodiscard]] constexpr int primo_vivo(bool nemici) const
    {
        for(int i = 0; i < quanti(nemici); ++i)
        {
            if((nemici ? _nemici[i] : _eroi[i]).vivo())
            {
                return i;
            }
        }

        return -1;
    }

    // L'alleato piu' ferito: la percentuale di PV piu' bassa; a parita', lo slot piu' basso.
    [[nodiscard]] constexpr int piu_ferito() const
    {
        int scelto = -1;

        for(int e = 0; e < EROI; ++e)
        {
            if(_eroi[e].vivo() && (scelto < 0 ||
               _eroi[e].pv * 100 / _eroi[e].pv_max < _eroi[scelto].pv * 100 / _eroi[scelto].pv_max))
            {
                scelto = e;
            }
        }

        return scelto;
    }

    constexpr void emetti(EventKind kind, bool attore_nemico, int attore, bool bersaglio_nemico, int bersaglio,
                          int quantita, int pv_dopo)
    {
        Evento e{ kind, uint8_t(attore), uint8_t(bersaglio), attore_nemico, bersaglio_nemico, int16_t(quantita),
                  int16_t(pv_dopo) };
        const uint8_t byte[9] = { uint8_t(e.kind), e.attore, e.bersaglio, uint8_t(e.attore_nemico),
                                  uint8_t(e.bersaglio_nemico), uint8_t(uint16_t(e.quantita) & 0xFF),
                                  uint8_t(uint16_t(e.quantita) >> 8), uint8_t(uint16_t(e.pv_dopo) & 0xFF),
                                  uint8_t(uint16_t(e.pv_dopo) >> 8) };

        for(uint8_t b : byte)
        {
            _firma.hash = (_firma.hash ^ b) * 16777619u;
        }

        ++_firma.eventi;
        _firma.tipi |= 1u << int(kind);

        if(_n_eventi_round < EVENTI_ROUND_MAX)
        {
            _eventi[_n_eventi_round++] = e;
        }
        else
        {
            _firma.traboccato = true;
        }
    }

    // Il pilota automatico: i comandi degli eroi senza tastiera, deterministici, uguali nel mirror.
    constexpr void pilota()
    {
        for(int e = 0; e < EROI; ++e)
        {
            Unita& eroe = _eroi[e];
            Comando c;

            if(! eroe.vivo())
            {
                _comandi[e] = c;
                continue;
            }

            if(_pilota_debole)
            {
                _comandi[e] = { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, primo_vivo(true), 0 };
                continue;
            }

            AbilitaId firma = ABILITA_FIRMA[e];
            int costo_suprema = ABILITA[int(firma)].costo + BOOST_COSTO[BOOST_SUPREMA];

            int ferito = piu_ferito();
            // Il Muro sull'alleato piu' ferito che non ne ha gia' uno: sotto il 40% dei PV, e comunque al secondo round, quando
            // il primo giro di colpi ha gia' deciso chi e' il piu' ferito.
            bool serve_il_muro = e == UBALDO && ferito >= 0 && _eroi[ferito].barriera == 0 &&
                    (_eroi[ferito].pv * 100 / _eroi[ferito].pv_max < 40 || _firma.round == 2) &&
                    eroe.fervore >= ABILITA[int(AbilitaId::MURO_DELLA_FEDE)].costo;

            if(eroe.carica)
            {
                c = { TipoComando::SUPREMA, firma, primo_vivo(true), BOOST_SUPREMA };
            }
            else if(serve_il_muro)
            {
                c = { TipoComando::USA_ABILITA, AbilitaId::MURO_DELLA_FEDE, -1, 0 };
            }
            else if(_firma.round >= 2 && eroe.fervore >= costo_suprema)
            {
                c = { TipoComando::CARICA, firma, -1, 0 };
            }
            else if(e == UBALDO)
            {
                int debole = -1;

                for(int n = 0; n < _n_nemici && debole < 0; ++n)
                {
                    if(_nemici[n].vivo() && _nemici[n].debolezza == Elemento::FEDE)
                    {
                        debole = n;
                    }
                }

                if(debole >= 0 && eroe.fervore >= 20)
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::GIUDIZIO_DELLA_VERGA, debole, 0 };
                }
                else
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, primo_vivo(true), 0 };
                }
            }
            else if(e == GIORGIO)
            {
                if(_firma.round % 2 == 1 && eroe.fervore >= 15)
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::BASTIONE_AZZURRO, -1, 0 };
                }
                else if(eroe.fervore >= 20)
                {
                    int scelto = -1;

                    for(int n = 0; n < _n_nemici; ++n)
                    {
                        if(_nemici[n].vivo() && (scelto < 0 || _nemici[n].pv < _nemici[scelto].pv))
                        {
                            scelto = n;
                        }
                    }

                    c = { TipoComando::USA_ABILITA, AbilitaId::FENDENTE_DEL_DRAGO, scelto, 0 };
                }
                else
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, primo_vivo(true), 0 };
                }
            }
            else
            {
                int bersaglio = -1;

                for(int n = 0; n < _n_nemici && bersaglio < 0; ++n)
                {
                    if(_nemici[n].vivo() && _nemici[n].debolezza == Elemento::FIAMMA)
                    {
                        bersaglio = n;
                    }
                }

                bersaglio = bersaglio < 0 ? primo_vivo(true) : bersaglio;

                // Al primo round Antonio saggia il nemico con un colpo di taglio, poi lo incendia.
                if(_firma.round == 1)
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, primo_vivo(true), 0 };
                }
                else if(eroe.fervore >= 15 + BOOST_COSTO[2])
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::FUOCO_DI_SANTANTONIO, bersaglio, 2 };
                }
                else if(eroe.fervore >= 15)
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::FUOCO_DI_SANTANTONIO, bersaglio, 0 };
                }
                else
                {
                    c = { TipoComando::USA_ABILITA, AbilitaId::ATTACCO, primo_vivo(true), 0 };
                }
            }

            _comandi[e] = c;
        }
    }

    // Il bersaglio di una regola dell'IA fra gli eroi vivi; -1 se non ce n'e'.
    [[nodiscard]] constexpr int mira(Mira m, int param) const
    {
        if(m == Mira::EROE && param >= 0 && param < EROI && _eroi[param].vivo())
        {
            return param;
        }

        int scelto = -1;

        for(int e = 0; e < EROI; ++e)
        {
            if(! _eroi[e].vivo())
            {
                continue;
            }

            if(scelto < 0 || (m == Mira::MENO_PV ? _eroi[e].pv < _eroi[scelto].pv
                                                 : _eroi[e].difesa_effettiva() < _eroi[scelto].difesa_effettiva()))
            {
                scelto = e;
            }
        }

        return scelto;
    }

    // La coda del round: eroi e nemici, ordinata per velocita' (piu' priorita') decrescente, stabile.
    constexpr void prepara_coda()
    {
        _n_azioni = 0;

        for(int e = 0; e < EROI; ++e)
        {
            if(_eroi[e].vivo())
            {
                const Comando& c = _comandi[e];
                int priorita = c.tipo == TipoComando::CARICA ? 0 : ABILITA[int(c.abilita)].priorita;
                _azioni[_n_azioni++] = { false, e, c, _eroi[e].velocita + priorita };
            }
        }

        bool senza_bersagli = false;

        for(int n = 0; n < _n_nemici && ! senza_bersagli; ++n)
        {
            Unita& nemico = _nemici[n];

            if(! nemico.vivo())
            {
                continue;
            }

            // In BREAK le sue azioni si annullano tutte: restano in coda per lasciare l'evento.
            if(nemico.rotto > 0)
            {
                for(int k = 0; k < nemico.azioni; ++k)
                {
                    Comando c{ TipoComando::USA_ABILITA, AbilitaId::COLPO_NEMICO, -1, 0 };
                    _azioni[_n_azioni++] = { true, n, c, nemico.velocita };
                }

                continue;
            }

            ++nemico.ia_round;

            for(int k = 0; k < nemico.azioni && ! senza_bersagli; ++k)
            {
                const Script& script = SCRIPT[nemico.script];

                for(int r = 0; r < script.quante; ++r)
                {
                    const Regola& regola = REGOLE[script.prima + r];
                    bool regge = regola.condizione == Condizione::SEMPRE ||
                            (regola.condizione == Condizione::ROUND_UGUALE && nemico.ia_round == regola.param) ||
                            (regola.condizione == Condizione::ROUND_PARI && nemico.ia_round % 2 == 0) ||
                            (regola.condizione == Condizione::ROUND_DISPARI && nemico.ia_round % 2 == 1);

                    if(! regge)
                    {
                        continue;
                    }

                    uint32_t bit = 1u << r;
                    uint32_t& maschera = regola.limite == Limite::UNA_PER_BATTAGLIA ? nemico.ia_battaglia : nemico.ia_round_bit;

                    if(regola.limite != Limite::RIPETIBILE)
                    {
                        if(maschera & bit)
                        {
                            continue;
                        }

                        maschera |= bit;
                    }

                    int bersaglio = regola.mira == Mira::SE_STESSO ? n : mira(regola.mira, regola.param_mira);

                    if(bersaglio < 0)
                    {
                        senza_bersagli = true;
                        break;
                    }

                    Comando c{ TipoComando::USA_ABILITA, regola.abilita, bersaglio, 0 };
                    _azioni[_n_azioni++] = { true, n, c, nemico.velocita + ABILITA[int(regola.abilita)].priorita };
                    break;
                }
            }
        }

        for(int i = 1; i < _n_azioni; ++i)
        {
            Azione chiave = _azioni[i];
            int j = i - 1;

            while(j >= 0 && _azioni[j].velocita < chiave.velocita)
            {
                _azioni[j + 1] = _azioni[j];
                --j;
            }

            _azioni[j + 1] = chiave;
        }
    }

    constexpr void esegui(const Azione& azione)
    {
        Unita& attore = unita(azione.nemico, azione.slot);

        if(! attore.vivo())
        {
            return;
        }

        if(attore.rotto > 0)
        {
            emetti(EventKind::BREAK_SKIP, azione.nemico, azione.slot, azione.nemico, azione.slot, attore.rotto, attore.pv);
            return;
        }

        Comando c = azione.comando;

        // La Suprema senza carica non parte: l'eroe carica, e la scarica al turno dopo.
        if(c.tipo == TipoComando::CARICA || (c.tipo == TipoComando::SUPREMA && ! attore.carica))
        {
            attore.carica = true;
            emetti(EventKind::CHARGE, azione.nemico, azione.slot, azione.nemico, azione.slot, 0, attore.pv);
            return;
        }

        const Abilita& abilita = ABILITA[int(c.abilita)];

        if(attore.fervore < abilita.costo + BOOST_COSTO[c.boost])
        {
            return;
        }

        int spesa = abilita.costo + BOOST_COSTO[c.boost];
        attore.fervore -= spesa;

        if(spesa > 0)
        {
            emetti(EventKind::FERVOR_SPEND, azione.nemico, azione.slot, azione.nemico, azione.slot, spesa, attore.fervore);
        }

        if(c.tipo == TipoComando::SUPREMA)
        {
            attore.carica = false;
        }

        if(abilita.effetto == Effetto::MURO_DELLA_FEDE)
        {
            int bersaglio = c.bersaglio >= 0 && _eroi[c.bersaglio].vivo() ? c.bersaglio : piu_ferito();

            if(bersaglio < 0)
            {
                return;
            }

            int punti = calcola_muro(attore, c.boost);
            _eroi[bersaglio].barriera += punti;
            attore.fervore = attore.fervore + FERVORE_UBALDO_SOSTEGNO > attore.fervore_max ?
                    attore.fervore_max : attore.fervore + FERVORE_UBALDO_SOSTEGNO;
            emetti(EventKind::BARRIER_UP, false, azione.slot, false, bersaglio, punti, _eroi[bersaglio].pv);
            emetti(EventKind::FERVOR_GAIN, false, azione.slot, false, azione.slot, FERVORE_UBALDO_SOSTEGNO, attore.fervore);
            return;
        }

        if(abilita.effetto == Effetto::DIFESA_SU)
        {
            attore.difesa_bonus = DIFESA_SU_PERCENTO;
            emetti(EventKind::DEF_UP, azione.nemico, azione.slot, azione.nemico, azione.slot, DIFESA_SU_PERCENTO, attore.pv);
            return;
        }

        if(abilita.effetto == Effetto::BASTIONE)
        {
            attore.guardia = DURATA_GUARDIA + c.boost;
            emetti(EventKind::GUARD_UP, false, azione.slot, false, azione.slot, attore.guardia, attore.pv);
            return;
        }

        bool lato_nemico = ! azione.nemico;

        if(c.boost == BOOST_SUPREMA)
        {
            for(int i = 0; i < quanti(lato_nemico); ++i)
            {
                if(unita(lato_nemico, i).vivo())
                {
                    colpo(azione, abilita, c.boost, i);
                }
            }

            return;
        }

        int bersaglio = c.bersaglio;

        if(bersaglio < 0 || ! unita(lato_nemico, bersaglio).vivo())
        {
            bersaglio = primo_vivo(lato_nemico);

            if(bersaglio < 0)
            {
                return;
            }
        }

        for(int k = 0; k < BOOST_COLPI[c.boost]; ++k)
        {
            if(! unita(lato_nemico, bersaglio).vivo())
            {
                break;
            }

            colpo(azione, abilita, c.boost, bersaglio);
        }
    }

    constexpr void colpo(const Azione& azione, const Abilita& abilita, int boost, int slot)
    {
        Unita& attore = unita(azione.nemico, azione.slot);
        bool lato_nemico = ! azione.nemico;

        // Il Bastione: San Giorgio prende i colpi diretti a Ubaldo e Antonio.
        if(! lato_nemico && slot != GIORGIO && _eroi[GIORGIO].vivo() && _eroi[GIORGIO].guardia > 0)
        {
            emetti(EventKind::GUARD_REDIRECT, azione.nemico, azione.slot, false, slot, GIORGIO, _eroi[GIORGIO].pv);
            slot = GIORGIO;
        }

        Unita& bersaglio = unita(lato_nemico, slot);

        if(! bersaglio.vivo())
        {
            return;
        }

        if(bersaglio.immune_al_taglio && abilita.elemento == Elemento::FISICO && bersaglio.ustione_cariche == 0)
        {
            emetti(EventKind::IMMUNE, azione.nemico, azione.slot, lato_nemico, slot, 0, bersaglio.pv);
            return;
        }

        // Shield Break prima del danno: la difesa dimezzata vale gia' per il colpo che rompe.
        if(abilita.elemento == bersaglio.debolezza && bersaglio.scudo > 0)
        {
            bersaglio.scudo -= BOOST_SCUDO_PER_COLPO[boost];

            if(bersaglio.scudo <= 0)
            {
                bersaglio.scudo = 0;
                bersaglio.rotto = DURATA_BREAK;
                emetti(EventKind::SHIELD_BREAK, azione.nemico, azione.slot, lato_nemico, slot,
                       BOOST_SCUDO_PER_COLPO[boost], bersaglio.pv);
            }
        }

        int danno = calcola_danno(attore, bersaglio, abilita, boost);
        danno = (danno * (VARIANZA_MINIMA + _caso.intero(VARIANZA_PASSI))) / 100;
        danno = danno < 1 ? 1 : danno;

        if(bersaglio.barriera > 0)
        {
            int assorbito = danno < bersaglio.barriera ? danno : bersaglio.barriera;
            bersaglio.barriera -= assorbito;
            danno -= assorbito;
            emetti(EventKind::BARRIER_ABSORB, azione.nemico, azione.slot, lato_nemico, slot, assorbito, bersaglio.pv);
        }

        bool era_vivo = bersaglio.vivo();
        bersaglio.pv = bersaglio.pv > danno ? bersaglio.pv - danno : 0;
        emetti(EventKind::HIT, azione.nemico, azione.slot, lato_nemico, slot, danno, bersaglio.pv);

        if(era_vivo && ! bersaglio.vivo())
        {
            emetti(EventKind::DEFEAT, azione.nemico, azione.slot, lato_nemico, slot, 0, 0);
        }

        if(! lato_nemico && slot == GIORGIO && abilita.elemento == Elemento::FISICO && bersaglio.vivo())
        {
            bersaglio.fervore = bersaglio.fervore + FERVORE_GIORGIO_COLPITO > bersaglio.fervore_max ?
                    bersaglio.fervore_max : bersaglio.fervore + FERVORE_GIORGIO_COLPITO;
            emetti(EventKind::FERVOR_GAIN, azione.nemico, azione.slot, false, slot, FERVORE_GIORGIO_COLPITO, bersaglio.fervore);
        }

        if(abilita.effetto == Effetto::USTIONE && bersaglio.vivo())
        {
            if(bersaglio.ustione_cariche < USTIONE_CARICHE_MAX)
            {
                ++bersaglio.ustione_cariche;
            }

            int per_carica = (attore.mistico * USTIONE_PERCENTO_MISTICO) / 100;
            bersaglio.ustione_danno = per_carica < 1 ? 1 : per_carica;
            bersaglio.ustione_turni = DURATA_USTIONE;
        }
    }

    constexpr void fine_round(Unita& u, bool nemico, int slot)
    {
        if(u.ustione_cariche > 0 && u.vivo())
        {
            int danno = u.ustione_danno * u.ustione_cariche;
            u.pv = u.pv > danno ? u.pv - danno : 0;
            emetti(EventKind::BURN_TICK, nemico, slot, nemico, slot, danno, u.pv);

            if(! u.vivo())
            {
                emetti(EventKind::DEFEAT, nemico, slot, nemico, slot, 0, 0);
            }

            if(nemico && _eroi[ANTONIO].vivo())
            {
                Unita& antonio = _eroi[ANTONIO];
                antonio.fervore = antonio.fervore + FERVORE_ANTONIO_USTIONE > antonio.fervore_max ?
                        antonio.fervore_max : antonio.fervore + FERVORE_ANTONIO_USTIONE;
                emetti(EventKind::FERVOR_GAIN, nemico, slot, false, ANTONIO, FERVORE_ANTONIO_USTIONE, antonio.fervore);
            }

            if(--u.ustione_turni <= 0)
            {
                u.ustione_cariche = 0;
                u.ustione_turni = 0;
            }
        }

        if(u.guardia > 0)
        {
            --u.guardia;
        }

        u.ia_round_bit = 0;

        if(u.rotto > 0 && --u.rotto == 0)
        {
            u.scudo = u.scudo_max;
        }
    }
};

[[nodiscard]] constexpr Firma gioca(int incontro, uint32_t seme, bool pilota_debole = false)
{
    Battaglia b(incontro, seme, pilota_debole);
    return b.gioca();
}

}

#endif
