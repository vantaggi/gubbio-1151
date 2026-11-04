#ifndef GUBBIO_ANIMAZIONE_BATTAGLIA_H
#define GUBBIO_ANIMAZIONE_BATTAGLIA_H

#include "vista_battaglia.h"

// Le animazioni della battaglia (pezzo SAG), senza Butano: per ogni gesto della vista
// (include/vista_battaglia.h) e ogni fotogramma, che posa ha chi agisce e chi subisce, dove stanno,
// chi lampeggia, quanto trema lo schermo, che effetto si vede e dove sta il numero del danno.
//
// Il ritmo viene dalle battaglie del GBA che funzionano (Fire Emblem, Golden Sun): un passo verso il
// nemico, l'anticipazione tenuta (10 vblank), il colpo veloce (3), il fermo sull'impatto (8: tutto si
// ferma, il bersaglio diventa bianco, lo schermo trema), il bersaglio che arretra e torna, il numero
// che salta e ricade, il ritorno al proprio posto. Le pose sono quelle di tools/sagome_battaglia.py.
// src/autotest_animazione.cpp lo prova a tempo di compilazione.
namespace gubbio::battaglia::animazione
{

// Nell'ordine di POSE in tools/sagome_battaglia.py: e' l'indice della posa nello sprite.
enum class Posa : uint8_t
{
    RIPOSO,
    RESPIRO,
    ANTICIPA,
    COLPO,
    COLPITO,
    POTERE,
    CADUTO,
    LIBERA,     // nessuna posa imposta: la figura respira da sola (respiro())
};

inline constexpr int POSE_DISEGNATE = int(Posa::LIBERA);

// Gli effetti, nell'ordine di EFFETTI in tools/sagome_battaglia.py; ognuno ha FOTOGRAMMI_EFFETTO pose.
enum class Effetto : uint8_t
{
    NESSUNO,
    SCIA,           // il fendente: un arco d'acciaio (Giorgio, i soldati)
    SCINTILLA,      // l'impatto: una stella che si apre
    RAGGIO,         // il Giudizio della Verga: una colonna di luce dall'alto (Ubaldo)
    FIAMMA,         // il fuoco di Antonio e l'ustione
    AURA,           // il Fervore che si raccoglie: anelli d'oro che salgono
    SCUDO,          // il Muro della Fede, il Bastione: un alone azzurro
    SCHEGGE,        // lo scudo che si rompe
    POLVERE,        // la polvere del passo
    CONTEGGIO,
};

inline constexpr int FOTOGRAMMI_EFFETTO = 4;

// Il colore che un lampo sostituisce a tutta la figura (una palette intera, il contorno resta).
enum class Lampo : uint8_t
{
    NESSUNO,
    BIANCO,     // colpito
    FUOCO,      // ustionato
    LUCE,       // curato, protetto, il Fervore che sale
};

struct Quadro
{
    Posa posa_attore = Posa::LIBERA;
    int avanti_attore = 0;          // pixel verso il nemico
    Lampo lampo_attore = Lampo::NESSUNO;
    Effetto effetto_attore = Effetto::NESSUNO;
    int fotogramma_attore = 0;
    Posa posa_bersaglio = Posa::LIBERA;
    int indietro_bersaglio = 0;     // pixel di rinculo, lontano da chi colpisce
    Lampo lampo_bersaglio = Lampo::NESSUNO;
    Effetto effetto_bersaglio = Effetto::NESSUNO;
    int fotogramma_bersaglio = 0;
    bool bersaglio_visibile = true;
    int scossa = 0;                 // pixel di tremito verticale dello schermo
    bool numero = false;
    int su_numero = 0;              // pixel sopra la posizione di riposo del numero
};

// Come si colpisce: l'effetto proprio di chi colpisce, e se il colpo e' forte (un'abilita' col
// Fervore, la Suprema, Corrado): il fermo piu' lungo, il lampo doppio, lo schermo che trema di piu'.
struct Stile
{
    Effetto colpo = Effetto::SCINTILLA;
    bool forte = false;
    bool resta_a_terra = false;     // CADUTA: un eroe resta in ginocchio, un nemico svanisce
};

// --- i tempi, in vblank (1/60 s) ---------------------------------------------------------------
inline constexpr int CORSA = 10;            // il passo verso il nemico
inline constexpr int ANTICIPA = 10;         // la posa caricata, tenuta
inline constexpr int SCATTO = 3;            // il colpo
inline constexpr int FERMO = 8;             // il fermo sull'impatto
inline constexpr int FERMO_FORTE = 12;
inline constexpr int RINCULO = 14;          // il bersaglio arretra e torna
inline constexpr int RITORNO = 10;          // chi ha colpito torna al suo posto
inline constexpr int AVANZATA = 20;         // pixel del passo
inline constexpr int AFFONDO = 4;           // pixel in piu' nel colpo
inline constexpr int RINCULO_PIXEL = 3;

// Il numero del danno: sale, ricade, rimbalza una volta, poi resta fermo.
inline constexpr int SALTO_NUMERO[] = { 0, 4, 7, 9, 10, 10, 9, 7, 4, 0, 2, 3, 3, 2, 0 };
inline constexpr int SALTO_FOTOGRAMMI = int(sizeof(SALTO_NUMERO) / sizeof(SALTO_NUMERO[0]));

[[nodiscard]] constexpr int salto(int f)
{
    return f < 0 ? 0 : (f < SALTO_FOTOGRAMMI ? SALTO_NUMERO[f] : 0);
}

[[nodiscard]] constexpr int fermo(const Stile& s)
{
    return s.forte ? FERMO_FORTE : FERMO;
}

// Gli istanti del colpo: quando arriva il colpo, quando scatta l'impatto, quando si torna.
[[nodiscard]] constexpr int inizio_scatto()
{
    return CORSA + ANTICIPA;
}

[[nodiscard]] constexpr int impatto()
{
    return CORSA + ANTICIPA + SCATTO;
}

[[nodiscard]] constexpr int inizio_ritorno(const Stile& s)
{
    return impatto() + fermo(s) + RINCULO;
}

[[nodiscard]] constexpr int durata(Gesto g, const Stile& s = {})
{
    switch(g)
    {

    case Gesto::COLPO:
    case Gesto::IMMUNE:
        return inizio_ritorno(s) + RITORNO;

    case Gesto::USTIONE:
    case Gesto::CURA:
        return 36;

    case Gesto::POTERE:
        return 32;

    case Gesto::PARATA:
        return 20;

    case Gesto::SCUDO_ROTTO:
        return 28;

    case Gesto::CADUTA:
        return 40;

    default:
        return 6;
    }
}

// L'uscita lenta (il passo che frena) e l'entrata lenta (il ritorno che parte piano), in pixel.
[[nodiscard]] constexpr int frena(int pixel, int f, int n)
{
    int resto = n - f;
    return pixel - pixel * resto * resto / (n * n);
}

[[nodiscard]] constexpr int parte(int pixel, int f, int n)
{
    return pixel - pixel * f * f / (n * n);
}

// Il tremito: alterna su e giu', e si spegne in 'n' fotogrammi.
[[nodiscard]] constexpr int tremito(int ampiezza, int f, int n)
{
    if(f < 0 || f >= n)
    {
        return 0;
    }

    int a = (ampiezza * (n - f) + n - 1) / n;
    return f % 2 ? -a : a;
}

[[nodiscard]] constexpr Quadro quadro_colpo(int f, const Stile& s, bool immune)
{
    Quadro q;
    int t_scatto = inizio_scatto();
    int t_impatto = impatto();
    int t_ritorno = inizio_ritorno(s);
    int fe = fermo(s);

    // chi colpisce: il passo, l'anticipazione, il colpo, il ritorno
    if(f < CORSA)
    {
        q.posa_attore = (f / 4) % 2 ? Posa::RESPIRO : Posa::RIPOSO;
        q.avanti_attore = frena(AVANZATA, f + 1, CORSA);
        q.effetto_attore = f < 2 * FOTOGRAMMI_EFFETTO ? Effetto::POLVERE : Effetto::NESSUNO;
        q.fotogramma_attore = f < 2 * FOTOGRAMMI_EFFETTO ? f / 2 : 0;
    }
    else if(f < t_scatto)
    {
        q.posa_attore = Posa::ANTICIPA;
        q.avanti_attore = AVANZATA - 2;
    }
    else if(f < t_ritorno)
    {
        int dopo = f - t_impatto;
        q.posa_attore = f < t_impatto + fe + 4 ? Posa::COLPO : Posa::RIPOSO;
        q.avanti_attore = AVANZATA + AFFONDO;

        if(immune && dopo >= 0)
        {
            // il ferro rimbalza: chi colpisce viene ricacciato indietro
            q.avanti_attore = AVANZATA + AFFONDO - (dopo < 8 ? dopo + 2 : 10);
            q.posa_attore = dopo < 10 ? Posa::COLPITO : Posa::RIPOSO;
        }
        else if(dopo >= fe)
        {
            q.avanti_attore = AVANZATA + AFFONDO - (dopo - fe < AFFONDO ? dopo - fe : AFFONDO);
        }
    }
    else
    {
        int da = immune ? AVANZATA + AFFONDO - 10 : AVANZATA;
        q.posa_attore = (f / 4) % 2 ? Posa::RESPIRO : Posa::RIPOSO;
        q.avanti_attore = parte(da, f - t_ritorno + 1, RITORNO);
    }

    // l'effetto del colpo: parte con lo scatto, due vblank per fotogramma
    int fx = f - t_scatto;

    if(fx >= 0 && fx < 2 * FOTOGRAMMI_EFFETTO)
    {
        q.effetto_bersaglio = immune ? Effetto::SCINTILLA : s.colpo;
        q.fotogramma_bersaglio = fx / 2;
    }

    int d = f - t_impatto;

    if(d < 0)
    {
        return q;
    }

    if(immune)
    {
        q.scossa = tremito(1, d, 6);
        return q;
    }

    // chi subisce: bianco nell'impatto (due volte se forte), arretra e torna, il numero salta
    q.posa_bersaglio = d < fe + RINCULO - 4 ? Posa::COLPITO : Posa::LIBERA;
    q.lampo_bersaglio = d < 3 || (s.forte && d >= 5 && d < 7) ? Lampo::BIANCO : Lampo::NESSUNO;
    q.indietro_bersaglio = d < fe ? RINCULO_PIXEL : (d < fe + RINCULO ? RINCULO_PIXEL - RINCULO_PIXEL * (d - fe) / RINCULO : 0);
    q.scossa = tremito(s.forte ? 3 : 1, d, fe);
    q.numero = true;
    q.su_numero = salto(d);
    return q;
}

// Il quadro 'f' del gesto 'g' (0 <= f < durata(g, s)).
[[nodiscard]] constexpr Quadro quadro(Gesto g, int f, const Stile& s = {})
{
    Quadro q;

    switch(g)
    {

    case Gesto::COLPO:
        return quadro_colpo(f, s, false);

    case Gesto::IMMUNE:
        return quadro_colpo(f, s, true);

    case Gesto::USTIONE:
        q.effetto_bersaglio = f < 24 ? Effetto::FIAMMA : Effetto::NESSUNO;
        q.fotogramma_bersaglio = (f / 3) % FOTOGRAMMI_EFFETTO;
        q.lampo_bersaglio = f < 16 && (f / 4) % 2 == 0 ? Lampo::FUOCO : Lampo::NESSUNO;
        q.posa_bersaglio = f >= 4 && f < 22 ? Posa::COLPITO : Posa::LIBERA;
        q.numero = f >= 6;
        q.su_numero = salto(f - 6);
        break;

    case Gesto::CURA:
        q.posa_attore = f < 22 ? Posa::POTERE : Posa::LIBERA;
        q.effetto_bersaglio = f >= 6 && f < 6 + 4 * FOTOGRAMMI_EFFETTO ? Effetto::AURA : Effetto::NESSUNO;
        q.fotogramma_bersaglio = (f - 6) / 4;
        q.lampo_bersaglio = f >= 10 && f < 14 ? Lampo::LUCE : Lampo::NESSUNO;
        q.numero = f >= 12;
        q.su_numero = salto(f - 12);
        break;

    case Gesto::POTERE:
        q.posa_attore = f < 26 ? Posa::POTERE : Posa::LIBERA;
        q.effetto_attore = f < 6 * FOTOGRAMMI_EFFETTO ? Effetto::AURA : Effetto::NESSUNO;
        q.fotogramma_attore = (f / 6) % FOTOGRAMMI_EFFETTO;
        q.lampo_attore = f >= 8 && f < 11 ? Lampo::LUCE : Lampo::NESSUNO;
        // il Muro e il Bastione su un altro: l'alone compare anche su di lui
        q.effetto_bersaglio = f >= 12 && f < 12 + 4 * FOTOGRAMMI_EFFETTO ? Effetto::SCUDO : Effetto::NESSUNO;
        q.fotogramma_bersaglio = (f - 12) / 4;
        break;

    case Gesto::PARATA:
        q.effetto_bersaglio = f < 4 * FOTOGRAMMI_EFFETTO ? Effetto::SCUDO : Effetto::NESSUNO;
        q.fotogramma_bersaglio = f / 4;
        q.lampo_bersaglio = f < 3 ? Lampo::LUCE : Lampo::NESSUNO;
        q.scossa = tremito(1, f, 6);
        break;

    case Gesto::SCUDO_ROTTO:
        q.posa_bersaglio = f < 20 ? Posa::COLPITO : Posa::LIBERA;
        q.effetto_bersaglio = f < 4 * FOTOGRAMMI_EFFETTO ? Effetto::SCHEGGE : Effetto::NESSUNO;
        q.fotogramma_bersaglio = f / 4;
        q.lampo_bersaglio = f < 4 ? Lampo::BIANCO : Lampo::NESSUNO;
        q.scossa = tremito(2, f, 10);
        q.indietro_bersaglio = f < 10 ? 2 : 0;
        break;

    case Gesto::CADUTA:
        q.posa_bersaglio = Posa::CADUTO;
        q.bersaglio_visibile = s.resta_a_terra || f < 16 || (f < 36 && (f / 2) % 2 == 0);
        q.effetto_bersaglio = f >= 4 && f < 4 + 3 * FOTOGRAMMI_EFFETTO ? Effetto::POLVERE : Effetto::NESSUNO;
        q.fotogramma_bersaglio = (f - 4) / 3;
        break;

    default:
        break;
    }

    if(q.fotogramma_attore < 0 || q.fotogramma_attore >= FOTOGRAMMI_EFFETTO)
    {
        q.fotogramma_attore = 0;
    }

    if(q.fotogramma_bersaglio < 0 || q.fotogramma_bersaglio >= FOTOGRAMMI_EFFETTO)
    {
        q.fotogramma_bersaglio = 0;
    }

    return q;
}

// Il respiro di chi aspetta: riposo e respiro, 30 vblank l'uno (Guida, scelta 11), sfasati per
// figura cosi' non respirano tutti insieme.
[[nodiscard]] constexpr Posa respiro(int tick, int slot)
{
    return ((tick + slot * 17) / 30) % 2 ? Posa::RESPIRO : Posa::RIPOSO;
}

}

#endif
