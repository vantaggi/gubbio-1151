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
};

enum class Effetto : uint8_t
{
    NESSUNO,
    USTIONE,
    MURO_DELLA_FEDE,
    BASTIONE,
};

enum class AbilitaId : uint8_t
{
    ATTACCO,
    MURO_DELLA_FEDE,
    GIUDIZIO_DELLA_VERGA,
    FENDENTE_DEL_DRAGO,
    BASTIONE_AZZURRO,
    FUOCO_DI_SANTANTONIO,
    COLPO_NEMICO,
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
inline constexpr AbilitaId ABILITA_FIRMA[EROI] = {
    AbilitaId::GIUDIZIO_DELLA_VERGA, AbilitaId::FENDENTE_DEL_DRAGO, AbilitaId::FUOCO_DI_SANTANTONIO };

enum class NemicoId : uint8_t
{
    FANTE_DI_PERUGIA,
    BALESTRIERE_PESANTE,
    CORRADO_DI_SPOLETO,
    CONTEGGIO,
};

struct Nemico
{
    Statistiche statistiche;
    int azioni_per_turno;       // il boss due, i comuni una (decisione del piano F4)
    bool immune_al_taglio;      // Corrado: il fisico non lo scalfisce finche' non e' ustionato
};

inline constexpr Nemico NEMICI[int(NemicoId::CONTEGGIO)] = {
    { { 228, 0, 45, 40,  8, 20, 26, 2, Elemento::FIAMMA, Elemento::NESSUNO }, 1, false },  // Fante di Perugia
    { { 456, 0, 62, 55, 12, 26, 34, 3, Elemento::FEDE,   Elemento::FISICO },  1, false },  // Balestriere Pesante
    { { 1520, 0, 95, 60, 20, 30, 22, 4, Elemento::FIAMMA, Elemento::FISICO }, 2, true },   // Corrado di Spoleto
};

inline constexpr int NEMICI_MAX = 6;

struct Incontro
{
    int nemici;
    NemicoId schieramento[NEMICI_MAX];
};

inline constexpr int INCONTRI = 2;
inline constexpr Incontro INCONTRO[INCONTRI] = {
    { 3, { NemicoId::FANTE_DI_PERUGIA, NemicoId::FANTE_DI_PERUGIA, NemicoId::BALESTRIERE_PESANTE } },  // Pattuglia Perugina
    { 1, { NemicoId::CORRADO_DI_SPOLETO } },                                                          // Duello con Corrado
};

inline constexpr int ROUND_MAX = 40;            // oltre, la battaglia finisce in parita'

}

#endif
