#ifndef PIAZZA_GRANDE_COLLISION_H
#define PIAZZA_GRANDE_COLLISION_H

#include <stdint.h>

namespace gubbio::maps {

// I DUE ASSI ERANO SCAMBIATI, e il committente lo ha reso visibile con una fotografia aerea.
//
// L'asse x corre da SUD a NORD, l'asse y da OVEST a EST (vedi l'orientamento piu' sotto). Fino
// alla Sessione 20 la mappa era 64 tile su x e 40 su y: cioe' 96 metri in senso nord-sud e 60
// in senso ovest-est, con l'asse LUNGO che andava da nord a sud.
//
// La piazza vera e' il contrario, e non serve la fotografia per saperlo — bastava la tabella
// LANDMARKS di questo stesso progetto. Li' Piazza Grande e' dichiarata 130 m x 40 m, il fronte
// dei Consoli 33 m e quello del Pretorio 25 m. I due palazzi SI FRONTEGGIANO, quindi i loro
// fronti stanno sul lato da 40 m, e la distanza fra loro e' il lato lungo. Il lato lungo e'
// dunque quello OVEST-EST, non quello nord-sud. Il fronte dei Consoli, largo 22 tile, stava
// disteso sull'asse da 64: era il palazzo messo per il verso sbagliato dentro la piazza.
//
// Quindi 32 su x (48 m nord-sud, contro i 40 reali piu' i due margini) e 64 su y (96 m ovest-est,
// che e' la distanza fra i palazzi compressa secondo la regola dell'illusione). La piazza aperta
// che ne risulta e' 25 tile per 39, cioe' un rettangolo largo una volta e mezza piu' che alto —
// che e' quello che si vede nella fotografia aerea.
//
// Effetto collaterale gradito: 32 x 64 tile sono 256 x 512 px, ed e' esattamente un BG regolare
// legale. La mappa riempie il proprio sfondo senza righe sprecate, cosa che con 64 x 40 dentro
// un 512 x 512 non accadeva.
constexpr int PIAZZA_WIDTH = 32;
constexpr int PIAZZA_HEIGHT = 64;

// Misure in PIXEL. Servono alla camera e al clamping del giocatore, che lavorano in pixel
// mentre la collisione lavora in tile: tenerle derivate invece che riscritte a mano e' cio'
// che impedisce alle due unita' di divergere.
constexpr int TILE_SIZE_PX = 8;
constexpr int PIAZZA_WIDTH_PX = PIAZZA_WIDTH * TILE_SIZE_PX;    // 256
constexpr int PIAZZA_HEIGHT_PX = PIAZZA_HEIGHT * TILE_SIZE_PX;  // 512

// Legenda Collisioni (Sez. 21B GDD). I valori numerici sono quelli originali: la griglia e'
// nata come numeri nudi e i numeri restano la rappresentazione in memoria.
enum class TileType : uint8_t
{
    GROUND            = 0,   // suolo libero
    WALL              = 1,   // Palazzo dei Consoli / Pretorio / ostacoli
    RAILING           = 2,   // parapetto panoramico sud: blocca il passo, non la vista
    DOOR_CONSOLI      = 3,   // trigger: ingresso del Palazzo dei Consoli
    EXIT_SAN_MARTINO  = 4,   // trigger: Quartiere San Martino (Bargello)
    EXIT_PORTA_ROMANA = 5,   // trigger: Porta Romana
    FOUNTAIN          = 6,   // Fontana dei Matti: sta in Largo del Bargello, NON in piazza

    // Aggiunti nella Sessione 16, applicando la regola dell'illusione (city_reference.h): gli
    // EDIFICI stanno in scala anche quando le distanze sono compresse. Prima la fascia nord era
    // muro indistinto, e il palazzo simbolo della citta' non si distingueva da un magazzino.
    CONSOLI_FACADE    = 7,   // fronte del Palazzo dei Consoli: 33 m = 22 tile, in scala
    PRETORIO_FACADE   = 8,   // Palazzo Pretorio, che gli sta di fronte: 25 m = 16 tile
    STAIRS            = 9,   // scalinata a ventaglio davanti al portone: si calpesta
    DOOR_PRETORIO     = 10,  // ingresso del Pretorio: oggi solo VISIVO, non porta altrove
    ROAD              = 11   // ciottolato: via dei Consoli / via XX Settembre, a nord
};

// --- LA DISPOSIZIONE DELLA PIAZZA, E IL SUO ORIENTAMENTO ------------------------------------
//
// Disposizione reale (correzione del committente, Sessione 19): **Palazzo dei Consoli a OVEST**,
// **Pretorio a EST**, i due che si fronteggiano; a **nord** la strada in ciottolato dove via dei
// Consoli si unisce a via XX Settembre, e oltre la strada il **Palazzo Ducale, i giardini
// pensili e il Duomo** — non la Basilica di Sant'Ubaldo, che sta molto piu' in alto sul Monte
// Ingino e non affaccia sulla piazza; a **sud** il muretto sul vuoto, perche' la piazza e'
// PENSILE, sospesa sopra gli Arconi.
//
// **LA MAPPA NON E' ORIENTATA A NORD: e' orientata a OVEST**, per scelta del committente.
// Ruotando di novanta gradi, in gioco si vede cosi':
//
//        ALTO SCHERMO = OVEST reale        -> PALAZZO DEI CONSOLI
//        BASSO SCHERMO = EST reale         -> PALAZZO PRETORIO
//        SINISTRA SCHERMO = NORD reale     -> ciottolato, via dei Consoli e via XX Settembre
//        DESTRA SCHERMO = SUD reale        -> muretto sul vuoto, e sotto gli Arconi
//
// Non e' un compromesso di comodo: mette i due palazzi che si fronteggiano sui lati LUNGHI della
// mappa, dove ci stanno alla loro scala — 22 tile i Consoli, 16 il Pretorio — e lascia le facciate
// fotografate orizzontali, come sono state riprese. Con l'orientamento a nord avrebbero dovuto
// essere ruotate, perdendo la ragione per cui le si e' fotografate frontali.
//
// La regola delle adiacenze di `city_reference.h` resta rispettata: cambia l'orientamento della
// vista, non l'ordine in cui le cose si incontrano.
constexpr int CONSOLI_LAST_Y = 18;       // fascia alta: il palazzo, cioe' OVEST
constexpr int PRETORIO_FIRST_Y = 58;     // fascia bassa: il Pretorio, cioe' EST
// A DESTRA il nord, a SINISTRA il sud. Non e' arbitrario: ruotando di 90 gradi una mappa con il
// nord in alto — cioe' portando l'ovest in cima — il nord finisce a destra e il sud a sinistra.
// La prima stesura li aveva scambiati, e quello non era una rotazione ma un RIBALTAMENTO: la
// pianta risultante era l'immagine allo specchio di Gubbio, con via dei Consoli dalla parte
// sbagliata rispetto al muretto. Chi tocca questi due numeri li tocca in coppia.
constexpr int RAILING_LAST_X = 1;        // fascia sinistra: il muretto, cioe' SUD
constexpr int ROAD_FIRST_X = 27;         // fascia destra: il ciottolato, cioe' NORD
// Il fronte edificato sul lato esterno della strada. Senza, la carreggiata finiva contro il
// bordo invisibile della mappa: si camminava fino al nulla. Dietro questi muri stanno il
// Palazzo Ducale, i giardini pensili e il Duomo, che sono a nord e sopra la piazza.
constexpr int NORTH_FRONT_X = 31;

// Fronti in scala (city_reference.h): 33 m = 22 tile per i Consoli, 25 m = 16 per il Pretorio.
constexpr int CONSOLI_FIRST_X = 3;
constexpr int CONSOLI_LAST_X = 24;
// Specchiate insieme al resto: x -> PIAZZA_WIDTH - 1 - x porta 26..41 in 22..37. Il fronte dei
// Consoli, 21..42, e' simmetrico rispetto al centro e quindi non cambia.
constexpr int PRETORIO_FIRST_X = 6;
constexpr int PRETORIO_LAST_X = 21;


inline constexpr uint8_t get_tile_type(int x, int y) {
    if (x < 0 || x >= PIAZZA_WIDTH || y < 0 || y >= PIAZZA_HEIGHT) return 1; // Fuori mappa = muro

    // SINISTRA = SUD: il muretto sul vuoto, con gli Arconi sotto.
    if (x <= RAILING_LAST_X) return 2;

    // DESTRA = NORD: la strada in ciottolato, che sale da EST a OVEST cioe' dal basso verso
    // l'alto. Via dei Consoli entra dall'angolo verso i Consoli, via XX Settembre da quello
    // verso il Pretorio: sono gli imbocchi nord-ovest e nord-est della piazza vera, e si
    // congiungono proprio lungo questa fascia.
    if (x >= NORTH_FRONT_X) return 1;    // fronti sul lato nord della strada

    if (x >= ROAD_FIRST_X) {
        if (y <= 8) return 4;                        // via dei Consoli (nord-ovest)
        if (y >= PIAZZA_HEIGHT - 9) return 5;        // via XX Settembre (nord-est)
        return 11;                                   // ciottolato percorribile
    }

    // ALTO = OVEST: Palazzo dei Consoli, col portone al centro del fronte.
    if (y <= CONSOLI_LAST_Y) {
        if (y == CONSOLI_LAST_Y && (x == 13 || x == 14)) return 3;
        if (x >= CONSOLI_FIRST_X && x <= CONSOLI_LAST_X) return 7;
        return 1;                                    // edificato minore ai lati
    }

    // La scalinata a ventaglio, sul selciato davanti al portone.
    if (y == CONSOLI_LAST_Y + 1 && x >= 11 && x <= 16) return 9;

    // BASSO = EST: Palazzo Pretorio, che fronteggia i Consoli.
    if (y >= PRETORIO_FIRST_Y) {
        if (x >= PRETORIO_FIRST_X && x <= PRETORIO_LAST_X) {
            // 15 e 16: il portale ad arco della fotografia cade a nove tile dall'angolo della
            // fascia (la foto e' specchiata, vedi photo_to_tiles.py). Finche' questo numero e il
            // disegno non coincidono, il giocatore preme A davanti a un muro dipinto.
            if (y == PRETORIO_FIRST_Y && (x == 15 || x == 16)) return 10;
            return 8;
        }

        return 1;
    }

    return 0; // selciato in cotto a lisca di pesce
}

// Variante in PIXEL, e la ragione per cui esiste.
//
// La Sez. 21D del GDD stampa `get_tile_type(const uint8_t* grid, int pixel_x, int pixel_y)` —
// puntatore e pixel — mentre il codice implementa `get_tile_type(int x, int y)` in TILE.
// Omettendo il puntatore le due firme hanno lo STESSO NUMERO DI ARGOMENTI dello stesso tipo:
// un chiamante che segue il documento sbaglia di un fattore 8 senza il minimo errore di
// compilazione, e il difetto si manifesta come un giocatore che attraversa i muri. Da qui in
// avanti l'unita' e' nel NOME della funzione.
//
// Lo `>> 3` si applica a un `int`. Su un `bn::fixed` opererebbe sul valore grezzo a 12 bit di
// frazione, cioe' un errore di fattore 4096; da un `bn::fixed` si passa per `.floor_integer()`
// e mai per `.integer()`, che tronca verso zero e sbaglia in negativo.
// Lo shift e' preferito alla divisione anche per una ragione di CORRETTEZZA, non solo di costo:
// `-1 / 8` vale 0 (troncamento verso zero), quindi un pixel appena fuori dal bordo sinistro
// verrebbe letto come tile 0 — suolo libero — e il giocatore uscirebbe dalla mappa. `-1 >> 3`
// vale -1, che `get_tile_type` riconosce come fuori mappa e quindi come muro.
[[nodiscard]] inline constexpr uint8_t get_tile_type_px(int pixel_x, int pixel_y)
{
    return get_tile_type(pixel_x >> 3, pixel_y >> 3);
}

// Blocca il passo? I trigger NON sono solidi: bisogna poterci salire sopra perche' scattino.
// La Fontana e' oggi calpestabile (l'eroe cammina dentro il bacino): la sua solidita' e le sue
// misure — 2x2 nel codice contro 3x3 della Sez. 15B — sono una decisione di design aperta.
[[nodiscard]] inline constexpr bool is_solid(uint8_t tile)
{
    return tile == uint8_t(TileType::WALL) || tile == uint8_t(TileType::RAILING) ||
           tile == uint8_t(TileType::CONSOLI_FACADE) || tile == uint8_t(TileType::PRETORIO_FACADE);
    // ROAD e STAIRS non sono solidi: si cammina sul ciottolato e si sale la scalinata.
}

// Porta verso un'altra area: il giocatore che vi sale cambia scena.
[[nodiscard]] inline constexpr bool is_transition(uint8_t tile)
{
    return tile == uint8_t(TileType::DOOR_CONSOLI) ||
           tile == uint8_t(TileType::EXIT_SAN_MARTINO) ||
           tile == uint8_t(TileType::EXIT_PORTA_ROMANA);
}

// --- La griglia come DATO, derivata dalla funzione -------------------------------------------
//
// `MapDescriptor` (map_data.h) vuole un `const uint8_t*`: le mappe 2..9 della Sez. 38 lo
// riceveranno da Tiled via `tools/map_exporter.py`, Piazza Grande — che e' la mappa zero e il
// riferimento con cui il generatore d'arte va tenuto coerente — resta autorata in codice.
//
// La forma conta: `consteval` calcola l'array A COMPILE TIME dalla stessa `get_tile_type` di
// sopra, quindi non esistono due descrizioni della piazza da tenere allineate a mano. E
// `inline constexpr` fa esistere i 2560 byte UNA SOLA VOLTA in ROM: senza `inline`, a namespace
// scope, ogni unita' di traduzione che include l'header ne riceve una copia propria e i
// puntatori memorizzati in `MapDescriptor` differirebbero da una unita' all'altra.
struct CollisionGrid
{
    uint8_t data[PIAZZA_WIDTH * PIAZZA_HEIGHT];
};

[[nodiscard]] consteval CollisionGrid make_piazza_grid()
{
    CollisionGrid grid{};

    for(int y = 0; y < PIAZZA_HEIGHT; ++y)
    {
        for(int x = 0; x < PIAZZA_WIDTH; ++x)
        {
            grid.data[x + y * PIAZZA_WIDTH] = get_tile_type(x, y);
        }
    }

    return grid;
}

inline constexpr CollisionGrid PIAZZA_GRID = make_piazza_grid();

// Punti notevoli della disposizione, verificati dal compilatore. Sono anche la documentazione
// eseguibile dell'orientamento: se qualcuno ruotasse di nuovo la mappa, si fermerebbe qui.
static_assert(PIAZZA_GRID.data[13 + CONSOLI_LAST_Y * PIAZZA_WIDTH] == uint8_t(TileType::DOOR_CONSOLI),
              "Il portone dei Consoli non e' al centro del fronte");
static_assert(PIAZZA_GRID.data[0 + 30 * PIAZZA_WIDTH] == uint8_t(TileType::RAILING),
              "Il muretto sul vuoto deve stare a SINISTRA (sud reale)");
static_assert(PIAZZA_GRID.data[28 + 30 * PIAZZA_WIDTH] == uint8_t(TileType::ROAD),
              "Il ciottolato deve stare a DESTRA (nord reale)");
static_assert(PIAZZA_GRID.data[28 + 2 * PIAZZA_WIDTH] == uint8_t(TileType::EXIT_SAN_MARTINO),
              "Via dei Consoli sbocca verso il Palazzo dei Consoli");
static_assert(PIAZZA_GRID.data[28 + 60 * PIAZZA_WIDTH] == uint8_t(TileType::EXIT_PORTA_ROMANA),
              "Via XX Settembre sbocca verso il Pretorio");

// La coppia che distingue una ROTAZIONE da un ribaltamento: strada e muretto stanno su lati
// OPPOSTI, e su quale dei due non e' indifferente. Se qualcuno li riscambiasse otterrebbe di
// nuovo l'immagine allo specchio di Gubbio, che compila e si gioca senza dare segno di se'.
static_assert(ROAD_FIRST_X > RAILING_LAST_X,
              "Strada e muretto si sovrappongono");
static_assert(PIAZZA_GRID.data[0 + 30 * PIAZZA_WIDTH] != PIAZZA_GRID.data[28 + 30 * PIAZZA_WIDTH],
              "I due lati corti non possono essere la stessa cosa");
static_assert(PIAZZA_GRID.data[NORTH_FRONT_X + 30 * PIAZZA_WIDTH] == uint8_t(TileType::WALL),
              "La strada deve essere chiusa anche sul lato nord");
static_assert(PIAZZA_GRID.data[14 + 10 * PIAZZA_WIDTH] == uint8_t(TileType::CONSOLI_FACADE),
              "Il Palazzo dei Consoli sta in ALTO (ovest reale)");
static_assert(PIAZZA_GRID.data[14 + 60 * PIAZZA_WIDTH] == uint8_t(TileType::PRETORIO_FACADE),
              "Il Palazzo Pretorio sta in BASSO (est reale), di fronte ai Consoli");
static_assert(PIAZZA_GRID.data[14 + 38 * PIAZZA_WIDTH] == uint8_t(TileType::GROUND),
              "Il centro della piazza non e' calpestabile");
static_assert(sizeof(CollisionGrid) == PIAZZA_WIDTH * PIAZZA_HEIGHT,
              "La griglia deve restare un blocco contiguo di byte");

// La conversione pixel -> tile deve concordare con la griglia, altrimenti il giocatore
// collide contro qualcosa che non e' dove crede.
static_assert(get_tile_type_px(13 * TILE_SIZE_PX + 7, 18 * TILE_SIZE_PX + 7) ==
                  uint8_t(TileType::DOOR_CONSOLI),
              "get_tile_type_px non concorda con get_tile_type sull'ultimo pixel del tile");
static_assert(get_tile_type_px(-1, 30 * TILE_SIZE_PX) == uint8_t(TileType::WALL),
              "Un pixel fuori dal bordo sinistro deve essere muro, non suolo libero");

} // namespace gubbio::maps

#endif // PIAZZA_GRANDE_COLLISION_H
