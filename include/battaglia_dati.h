#ifndef GUBBIO_BATTAGLIA_DATI_H
#define GUBBIO_BATTAGLIA_DATI_H

#include <cstdint>

// Le tabelle della battaglia, riprese dal prototipo (tag prototipo-v0: include/battle_engine.h,
// hero_data.h, enemy_data.h) e adattate al codice nuovo. Il mirror Python e' tools/battaglia_mirror.py:
// ogni numero qui ha il suo gemello la', e tests/test_battaglia.py controlla che coincidano.
// Aritmetica intera con troncamento verso zero, come su ARM7TDMI: niente virgola mobile.
namespace gubbio::battaglia
{

enum class Elemento : uint8_t
{
    FISICO,
    FEDE,
    FIAMMA,
    OMBRA,
    NESSUNO,
};

inline constexpr int ELEMENTO_DEBOLE = 150;     // percentuali
inline constexpr int ELEMENTO_NEUTRO = 100;
inline constexpr int ELEMENTO_RESISTE = 50;

// Fervor Boost: 0 normale, 1 x1, 2 doppio colpo, 3 la Suprema (tutto lo schieramento).
inline constexpr int LIVELLI_BOOST = 4;
inline constexpr int BOOST_SUPREMA = 3;
inline constexpr int BOOST_COSTO[LIVELLI_BOOST] = { 0, 25, 50, 100 };
inline constexpr int BOOST_COLPI[LIVELLI_BOOST] = { 1, 1, 2, 1 };
inline constexpr int BOOST_DANNO[LIVELLI_BOOST] = { 100, 150, 100, 350 };
inline constexpr int BOOST_SCUDO_PER_COLPO[LIVELLI_BOOST] = { 1, 1, 1, 3 };
inline constexpr int BOOST_SOSTEGNO[LIVELLI_BOOST] = { 100, 200, 200, 350 };

inline constexpr int DURATA_BREAK = 2;          // il nemico salta questo round e il prossimo
inline constexpr int USTIONE_CARICHE_MAX = 3;
inline constexpr int DURATA_USTIONE = 3;
inline constexpr int USTIONE_PERCENTO_MISTICO = 25;
inline constexpr int DURATA_GUARDIA = 1;

inline constexpr int FERVORE_GIORGIO_COLPITO = 15;
inline constexpr int FERVORE_UBALDO_SOSTEGNO = 20;
inline constexpr int FERVORE_ANTONIO_USTIONE = 10;

inline constexpr int VARIANZA_MINIMA = 90;      // danno x 90..110 %
inline constexpr int VARIANZA_PASSI = 21;

enum class Bersaglio : uint8_t
{
    NEMICO,
    ALLEATO,
    SE_STESSO,
};

enum class Effetto : uint8_t
{
    NESSUNO,
    USTIONE,
    MURO_DELLA_FEDE,
    BASTIONE,
    DIFESA_SU,
};

inline constexpr int DIFESA_SU_PERCENTO = 50;   // Scudo di Forgia: +50% di Difesa, per tutta la battaglia

enum class AbilitaId : uint8_t
{
    ATTACCO,
    MURO_DELLA_FEDE,
    GIUDIZIO_DELLA_VERGA,
    FENDENTE_DEL_DRAGO,
    BASTIONE_AZZURRO,
    FUOCO_DI_SANTANTONIO,
    COLPO_NEMICO,
    SCUDO_DI_FORGIA,
    MARTELLO_DASSEDIO,
    CONTEGGIO,
};

struct Abilita
{
    Elemento elemento;
    Bersaglio bersaglio;
    Effetto effetto;
    int costo;
    int potenza;            // percentuale per le abilita' fisiche
    int danno_mistico;      // danno base per quelle mistiche
    int perforazione;       // percentuale di armatura ignorata
    int priorita;           // si somma alla velocita' nella coda
};

inline constexpr Abilita ABILITA[int(AbilitaId::CONTEGGIO)] = {
    { Elemento::FISICO,  Bersaglio::NEMICO,  Effetto::NESSUNO,         0, 100,  0,  0, 0 },  // Attacco
    { Elemento::FEDE,    Bersaglio::ALLEATO, Effetto::MURO_DELLA_FEDE, 25,  0,  0,  0, 4 },  // Muro della Fede
    { Elemento::FEDE,    Bersaglio::NEMICO,  Effetto::NESSUNO,        20,   0, 35,  0, 0 },  // Giudizio della Verga
    { Elemento::FISICO,  Bersaglio::NEMICO,  Effetto::NESSUNO,        20, 160,  0, 50, 0 },  // Fendente del Drago
    { Elemento::NESSUNO, Bersaglio::ALLEATO, Effetto::BASTIONE,       15,   0,  0,  0, 8 },  // Bastione Azzurro
    { Elemento::FIAMMA,  Bersaglio::NEMICO,  Effetto::USTIONE,        15,   0, 40,  0, 0 },  // Fuoco di Sant'Antonio
    { Elemento::FISICO,  Bersaglio::NEMICO,  Effetto::NESSUNO,         0, 100,  0,  0, 0 },  // Colpo (nemici)
    // Le due abilita' di Corrado, da docs/piano_ia_boss.md del prototipo (Sezione 26A del GDD).
    { Elemento::NESSUNO, Bersaglio::SE_STESSO, Effetto::DIFESA_SU,     0,   0,  0,  0, 6 },  // Scudo di Forgia
    { Elemento::FISICO,  Bersaglio::NEMICO,  Effetto::NESSUNO,         0, 220,  0, 25, -4 }, // Martello d'Assedio
};

// I tre Santi (Sezione 5 del GDD). Fervore d'ingresso in percentuale del pool.
inline constexpr int EROI = 3;
inline constexpr int UBALDO = 0;
inline constexpr int GIORGIO = 1;
inline constexpr int ANTONIO = 2;

struct Statistiche
{
    int pv;
    int fervore;
    int attacco;
    int difesa;
    int mistico;
    int resistenza;
    int velocita;
    int scudo;
    Elemento debolezza;
    Elemento resiste;
};

inline constexpr Statistiche STATISTICHE_EROI[EROI] = {
    { 240, 180, 25, 45, 95, 72, 30, 0, Elemento::NESSUNO, Elemento::NESSUNO },   // Sant'Ubaldo
    { 380, 120, 90, 80, 25, 40, 42, 0, Elemento::NESSUNO, Elemento::NESSUNO },   // San Giorgio
    { 210, 210, 18, 28, 95, 56, 38, 0, Elemento::NESSUNO, Elemento::NESSUNO },   // Sant'Antonio
};
inline constexpr int FERVORE_INIZIALE[EROI] = { 80, 45, 20 };
// Con i Ceri risvegliati (CERI_RISVEGLIATI, A1-08: «il Fervore che parte piu' alto in battaglia») ogni Santo
// parte con questi punti percentuali in piu' del suo Fervore massimo, mai oltre il massimo: 95, 60, 35.
// Il mirror Python ha lo stesso numero (FERVORE_CERI di tools/battaglia_mirror.py).
inline constexpr int FERVORE_CERI = 15;
inline constexpr AbilitaId ABILITA_FIRMA[EROI] = {
    AbilitaId::GIUDIZIO_DELLA_VERGA, AbilitaId::FENDENTE_DEL_DRAGO, AbilitaId::FUOCO_DI_SANTANTONIO };

enum class NemicoId : uint8_t
{
    FANTE_DI_PERUGIA,
    BALESTRIERE_PESANTE,
    CORRADO_DI_SPOLETO,
    SPIA_UMBRA,
    SPETTRO_DEL_DUBBIO,
    GUERRIERO_DELLA_ROCCIA,
    INFILTRATO,
    CONTEGGIO,
};

// L'IA a regole (docs/piano_ia_boss.md del prototipo): le regole di uno script si valutano in
// ordine, vince la prima che regge; UNA_PER_ROUND e UNA_PER_BATTAGLIA usano un bit per regola.
enum class Condizione : uint8_t
{
    SEMPRE,
    ROUND_UGUALE,       // il round dell'unita' e' uguale a param
    ROUND_PARI,
    ROUND_DISPARI,
};

enum class Limite : uint8_t
{
    RIPETIBILE,
    UNA_PER_ROUND,
    UNA_PER_BATTAGLIA,
};

enum class Mira : uint8_t
{
    MENO_DIFESA,
    MENO_PV,
    EROE,               // l'eroe param, se vivo; se no, chi ha meno Difesa
    SE_STESSO,
};

struct Regola
{
    Condizione condizione;
    int param;
    Limite limite;
    AbilitaId abilita;
    Mira mira;
    int param_mira;
};

inline constexpr int REGOLE_MAX_PER_SCRIPT = 8;

struct Script
{
    int prima;
    int quante;
};

inline constexpr Regola REGOLE[] = {
    // 0. il mob comune: colpisce chi ha meno Difesa (Sezione 13D del GDD)
    { Condizione::SEMPRE, 0, Limite::RIPETIBILE, AbilitaId::COLPO_NEMICO, Mira::MENO_DIFESA, 0 },
    // 1. la spia umbra: colpisce chi ha meno PV
    { Condizione::SEMPRE, 0, Limite::RIPETIBILE, AbilitaId::COLPO_NEMICO, Mira::MENO_PV, 0 },
    // 2-4. Corrado di Spoleto: al primo round lo Scudo di Forgia su se stesso (una volta per
    // battaglia), nei round pari il Martello d'Assedio su San Giorgio (una volta per round), sempre
    // il Colpo su chi ha meno Difesa
    { Condizione::ROUND_UGUALE, 1, Limite::UNA_PER_BATTAGLIA, AbilitaId::SCUDO_DI_FORGIA, Mira::SE_STESSO, 0 },
    { Condizione::ROUND_PARI, 0, Limite::UNA_PER_ROUND, AbilitaId::MARTELLO_DASSEDIO, Mira::EROE, GIORGIO },
    { Condizione::SEMPRE, 0, Limite::RIPETIBILE, AbilitaId::COLPO_NEMICO, Mira::MENO_DIFESA, 0 },
};

inline constexpr int SCRIPT_MOB = 0;
inline constexpr int SCRIPT_SPIA = 1;
inline constexpr int SCRIPT_CORRADO = 2;
inline constexpr Script SCRIPT[] = { { 0, 1 }, { 1, 1 }, { 2, 3 } };

struct Nemico
{
    Statistiche statistiche;
    int azioni_per_turno;       // il boss due, i comuni una (decisione del piano F4)
    bool immune_al_taglio;      // Corrado: il fisico non lo scalfisce finche' non e' ustionato
    int script;
};

inline constexpr Nemico NEMICI[int(NemicoId::CONTEGGIO)] = {
    { { 228, 0, 45, 40,  8, 20, 26, 2, Elemento::FIAMMA, Elemento::NESSUNO }, 1, false, SCRIPT_MOB },     // Fante di Perugia
    { { 456, 0, 62, 55, 12, 26, 34, 3, Elemento::FEDE,   Elemento::FISICO },  1, false, SCRIPT_MOB },     // Balestriere Pesante
    { { 1520, 0, 95, 60, 20, 30, 22, 4, Elemento::FIAMMA, Elemento::FISICO }, 2, true, SCRIPT_CORRADO },  // Corrado di Spoleto
    // La spia umbra dell'imboscata agli Stradoni (copione v1, A1-07): nel GDD non ha numeri.
    // Provvisoria, da tarare: rapida e fragile, debole alla Fede.
    { { 180, 0, 50, 30, 10, 22, 44, 2, Elemento::FEDE,   Elemento::NESSUNO }, 1, false, SCRIPT_SPIA },    // Spia umbra
    // Gli Spettri del Dubbio del rito nella Basilica (copione v1, A1-08): il boss tutorial, deboli
    // alla Fede, il ferro li attraversa. Provvisori come la spia: nel GDD non hanno numeri.
    { { 300, 0, 40, 30, 30, 40, 30, 2, Elemento::FEDE,   Elemento::FISICO },  1, false, SCRIPT_SPIA },    // Spettro del Dubbio
    // I Guerrieri della Roccia di Spoleto (copione: B-03 sotto l'arco, Q-SM01 davanti alle fornaci; Sez. 8D
    // del GDD, senza numeri): il ferro battuto a freddo, a strati, regge la lama e si apre col fuoco (Raniero,
    // 04_quest.md). Lenti e duri: resistono al fisico, deboli alla Fiamma. Tarati con tools/bilanciamento.py.
    { { 520, 0, 60, 62, 10, 22, 24, 3, Elemento::FIAMMA, Elemento::FISICO },  1, false, SCRIPT_MOB },     // Guerriero della Roccia
    // L'infiltrato delle Logge (Q-SP01): l'esule dei Valmarcola col mantello da pellegrino, la mano sotto il
    // mantello. Il capo delle spie umbre: piu' robusto di loro, rapido, colpisce chi ha meno PV come loro.
    { { 300, 0, 56, 36, 16, 28, 46, 3, Elemento::FEDE,   Elemento::NESSUNO }, 1, false, SCRIPT_SPIA },    // Infiltrato
};

inline constexpr int NEMICI_MAX = 6;

struct Incontro
{
    int nemici;
    NemicoId schieramento[NEMICI_MAX];
};

inline constexpr int INCONTRI = 7;
inline constexpr Incontro INCONTRO[INCONTRI] = {
    { 3, { NemicoId::FANTE_DI_PERUGIA, NemicoId::FANTE_DI_PERUGIA, NemicoId::BALESTRIERE_PESANTE } },  // Pattuglia Perugina
    { 3, { NemicoId::SPIA_UMBRA, NemicoId::SPIA_UMBRA, NemicoId::SPIA_UMBRA } },                      // Imboscata agli Stradoni
    { 1, { NemicoId::CORRADO_DI_SPOLETO } },                                                          // Duello con Corrado
    { 2, { NemicoId::SPETTRO_DEL_DUBBIO, NemicoId::SPETTRO_DEL_DUBBIO } },                             // Il rito della Basilica
    { 2, { NemicoId::GUERRIERO_DELLA_ROCCIA, NemicoId::GUERRIERO_DELLA_ROCCIA } },                     // Guerrieri della Roccia (B-03)
    { 1, { NemicoId::GUERRIERO_DELLA_ROCCIA } },                                                      // Guardia della fornace (Q-SM01)
    { 3, { NemicoId::INFILTRATO, NemicoId::SPIA_UMBRA, NemicoId::SPIA_UMBRA } },                       // L'infiltrato delle Logge (Q-SP01)
};

// Gli incontri per nome, dove il codice li chiama (le scene, le quest, le prove).
inline constexpr int INCONTRO_GUERRIERI = 4;
inline constexpr int INCONTRO_FORNACE = 5;
inline constexpr int INCONTRO_INFILTRATO = 6;

// I consumabili (dal prototipo, include/item_data.h, Sezione 8E del GDD), nell'ordine dei posti
// di GameState::oggetti. In battaglia per ora si usano la Crescia (cura) e i Biscotti (purificano
// dall'ustione); gli altri sono nell'inventario ma non ancora usabili.
enum class OggettoId : uint8_t
{
    CRESCIA,        // Crescia di Pasqua al Formaggio
    CENERE,         // Crescia sotto la Cenere
    BACCALA,        // Baccala' alla Ceraiola
    BISCOTTI,       // Biscotti all'Anice di Sant'Ubaldo
    VINO,           // Vino Rosso delle Colline Eugubine
    CONTEGGIO,
};

struct Oggetto
{
    bool usabile;       // si puo' scegliere in battaglia
    int cura_pv;        // PV restituiti a un alleato vivo
    bool purifica;      // toglie l'ustione
    int priorita;       // si somma alla velocita' nella coda, come per le abilita'
    int massimo;        // quanti se ne portano
};

inline constexpr Oggetto OGGETTI[int(OggettoId::CONTEGGIO)] = {
    { true, 100, false, 6, 5 },     // Crescia
    { false, 0, false, 6, 2 },      // Cenere (la rianimazione: piu' avanti)
    { false, 0, false, 6, 1 },      // Baccala' (tutto il Fervore: piu' avanti)
    { true, 0, true, 10, 5 },       // Biscotti: consumabile rapido, priorita' sopra il Bastione
    { false, 0, false, 6, 3 },      // Vino (il potenziamento: piu' avanti)
};

inline constexpr int ROUND_MAX = 40;            // oltre, la battaglia finisce in parita'

}

#endif
