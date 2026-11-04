#ifndef GUBBIO_ESPLORAZIONE_H
#define GUBBIO_ESPLORAZIONE_H

#include "bn_bg_palette_ptr.h"
#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_tiles_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "mondo_logica.h"
#include "vista_testo.h"
#include "aiuti.h"
#include "pannello.h"

namespace gubbio
{

// La scena di esplorazione: il fondale dell'area (dalla mappa generata), la camera che segue il
// giocatore senza uscire dall'area, i varchi con una dissolvenza e l'etichetta col nome
// dell'area. Muoversi, urtare e attraversare passa tutto da mondo_logica.h.
inline constexpr int ALTEZZA_SCHERMO_ESPLORAZIONE = 160;

class Esplorazione
{
public:
    explicit Esplorazione(const bn::sprite_palette_ptr& palette_testo);

    void entra(mondo::AreaId id, int spawn);

    // Rimette il giocatore dove l'ha lasciato un salvataggio: area e piedi in pixel.
    void riprendi(mondo::AreaId id, int x, int y);

    // Per una battaglia: lo sfondo si libera (i suoi tile servono alla scena) e il giocatore si
    // nasconde; ricompari() rimette tutto com'era.
    void sospendi();

    // I compagni che seguono Ubaldo in fila (0 nessuno, 1 Giorgio, 2 Giorgio e Antonio): lo decide la storia a ogni
    // frame (GIORGIO_NEL_GRUPPO, ANTONIO_NEL_GRUPPO). Camminano sulle orme di Ubaldo, COMPAGNO_DISTANZA px l'uno
    // dietro l'altro; entrando in un'area escono da dietro di lui.
    void imposta_compagni(int quanti);

    // I compagni si tolgono (i loro sprite servono alla pausa); tornano da se' al prossimo aggiorna().
    void togli_compagni();

    // La citta' di notte (storia::fase_npc NOTTE): i fondali con le rampe di notte, fiaccole e drappi caldi (L5).
    void imposta_notte(bool notte);
    void ricompari();

    // Uno sprite che sta sulla mappa (un nemico, un NPC, la gente): sulla camera dell'area, coi piedi in (x, y)
    // pixel, e con lo z dai piedi (z_sulla_mappa), cosi' chi sta piu' in basso sta davanti a chi sta piu' in alto.
    void colloca_sulla_mappa(bn::sprite_ptr& sprite, int x, int y, int altezza) const;

    // L'ordine di tutti gli sprite della mappa (STANDARD: chi sta piu' in basso sullo schermo sta davanti), uno
    // solo per la fila, gli NPC, la gente e i nemici: z minore = davanti. Quattro z per riga di pixel, cosi' a pari
    // y Ubaldo (-2) e i compagni (-1, 0) stanno davanti agli altri. y fino a 128 celle = 1024 px: z da -96 a 4000.
    [[nodiscard]] static constexpr int z_sulla_mappa(int y)
    {
        return 4 * (1000 - y);
    }

    // Input di un frame: dx, dy in -1..1, 'passi' pixel per asse. Ignorato durante una dissolvenza.
    void muovi(int dx, int dy, int passi);

    // Il giocatore e' stato spostato da fuori (la camminata automatica): ridisegna se serve.
    void sincronizza(mondo::Evento evento);

    void aggiorna();

    // Nasconde l'etichetta d'area e gli aiuti (promemoria, cartello): un dialogo, una battaglia o la pausa
    // stanno per prendere lo schermo. Il cartello torna da se' al prossimo aggiorna().
    void nascondi_etichetta();
    // I menu (MPA): la scena sotto si scurisce col fade dell'hardware, solo fondale e giocatore, cosi' le
    // cornici e le scritte dei menu restano coi loro colori (il fade di bg_palettes scuriva anche quelle).
    void scurisci(bool scura);

    // Il segnale d'interazione (STANDARD I2): il fumetto coi tre puntini sopra chi o cosa risponde ad A.
    // (x, y) sono i piedi in pixel, 'altezza' quanto e' alto in pixel (una persona 24): il fumetto sta 2 px
    // sopra. La storia lo chiama a ogni frame; spegni_segnale() lo toglie (anche nascondi_etichetta() e
    // sospendi(), cosi' non resta sotto un dialogo).
    void segnala(int x, int y, int altezza);

    // Il giocatore sta nella meta' bassa dello schermo? Allora il riquadro del dialogo va in alto, per non
    // coprire chi parla (STANDARD I3). Conta la testa, 16 px sopra i piedi.
    [[nodiscard]] bool giocatore_in_basso() const
    {
        return _e.y - 16 - (_cam_y - ALTEZZA_SCHERMO_ESPLORAZIONE / 2) >= ALTEZZA_SCHERMO_ESPLORAZIONE / 2;
    }
    void spegni_segnale();
    // Gli aiuti al giocatore (MAI): il cartello ai varchi e il promemoria di Select. Spenti nei modi di prova
    // (le istantanee e la camminata automatica fotografano il mondo, non gli aiuti).
    void attiva_aiuti(bool attivi)
    {
        _aiuti = attivi;
    }

    // Select: per 3 secondi l'obiettivo della cronaca in alto e una freccia verso il varco della strada piu'
    // breve per la meta (include/aiuti.h). Senza obiettivo, una riga che lo dice.
    void promemoria();

    // Il fumetto sopra il cartello del varco (STANDARD I2: vale anche per i cartelli): se gli aiuti sono attivi,
    // il cartello e' a schermo e la sua cella sta a portata (aiuti::cartello_a_portata, 14 px come il tasto A),
    // chiama segnala() e dice true. Niente lettera «A». La storia lo chiama quando nessuna persona e' a portata,
    // e spegne il fumetto se dice false.
    bool segnala_cartello();

    // Da pixel dell'area a pixel dello schermo (0, 0 in alto a sinistra), con la camera di adesso.
    [[nodiscard]] int schermo_x(int x) const;
    [[nodiscard]] int schermo_y(int y) const;

    // Il varco 'indice' dell'area si urta come un muro (-1: tutti aperti). Lo decide la storia a ogni frame
    // (storia::varco_chiuso(): il duello del Condotto).
    void chiudi_varco(int indice)
    {
        _varco_chiuso = indice;
    }

    // Il giocatore ha urtato il varco chiuso dall'ultima chiamata? (una volta: poi torna false)
    [[nodiscard]] bool urto_al_varco_chiuso()
    {
        bool urto = _urto_al_varco;
        _urto_al_varco = false;
        return urto;
    }

    [[nodiscard]] const mondo::Esploratore& esploratore() const
    {
        return _e;
    }

    [[nodiscard]] mondo::Esploratore& esploratore()
    {
        return _e;
    }

    // La variante di fase della stanza (mondo::VARIANTE, -1 nessuna): se cambia, il fondale si ricarica.
    void imposta_variante(int variante);

    // L'area del fondale caricato: durante la dissolvenza resta quella vecchia (la nuova si carica a meta').
    [[nodiscard]] mondo::AreaId area_caricata() const
    {
        return _area_caricata;
    }

    [[nodiscard]] bool in_dissolvenza() const
    {
        return _dissolvenza != 0;
    }

private:
    static constexpr int COMPAGNI_MAX = 2;
    // la distanza fra uno e il seguente, in orme: 18 px in orizzontale, 21 in verticale (le figure sono alte 32:
    // in colonna con 18 le teste coprivano il busto di chi sta davanti). Un passo di lato costa 7, uno in su o in
    // giu' 6: COMPAGNO_DISTANZA e' il costo fra due della fila.
    static constexpr int COSTO_LATO = 7;
    static constexpr int COSTO_SU = 6;
    static constexpr int COMPAGNO_DISTANZA = 18 * COSTO_LATO;
    static constexpr int ORME = COMPAGNI_MAX * (COMPAGNO_DISTANZA / COSTO_SU + 1) + 2;

    struct Orma
    {
        int16_t x;
        int16_t y;
    };

    struct Compagno
    {
        bn::sprite_ptr sprite;
        int x = 0;
        int y = 0;
        int direzione = 0;
        mondo::Camminata camminata;
        int fermo = 0;
        int mostrato = -1;
    };

    bn::optional<bn::regular_bg_tiles_ptr> _tiles;
    bn::bg_palette_ptr _palette;
    bn::camera_ptr _camera;
    bn::optional<bn::regular_bg_ptr> _fondale;
    bn::sprite_ptr _giocatore;
    bn::sprite_ptr _fumetto;            // il segnale d'interazione (STANDARD I2), con la palette del giocatore
    bool _fumetto_acceso = false;
    int _fumetto_x = 0;
    int _fumetto_y = 0;
    int _oscilla = 0;
    bn::vector<bn::sprite_ptr, 6> _cartiglio;  // creato per primo: sta sotto il testo
    VistaTesto _ombra;              // creata prima: i suoi sprite stanno sotto quelli dell'etichetta
    VistaTesto _etichetta;
    // MAI: il promemoria (mockup 09, A3: riquadro scuro, stella, targa con la freccia) e il cartello del varco
    // vicino (mockup 12, A2: legno, freccia, due righe). Si creano solo mentre si vedono: con i loro sprite sempre
    // allocati «Dove eravamo» e i dialoghi finivano gli elementi di tile degli sprite di Butano.
    bn::sprite_palette_ptr _palette_testo;
    bn::sprite_palette_ptr _palette_aiuti;
    bn::optional<pannello::Pannello> _promemoria_fondo;
    bn::optional<VistaTesto> _promemoria;
    bn::optional<pannello::Pannello> _targa;
    bn::optional<VistaTesto> _targa_nome;
    aiuti::Verso _targa_verso = aiuti::Verso::GIU;
    int _targa_x = 0;
    int _targa_y = 0;
    int _promemoria_t = -1;         // i frame da Select, -1 spento
    int _promemoria_alto = 0;
    bn::optional<pannello::Pannello> _cartello_fondo;
    bn::optional<VistaTesto> _cartello;
    bn::optional<VistaTesto> _oltre;
    int _cartello_x = 0;
    int _cartello_y = 0;
    int _cartello_k = -1;           // il passo dell'entrata o dell'uscita (A2), -1 nessun cartello
    bool _cartello_esce = false;
    int _cartello_scrivi = 0;       // le righe del cartello ancora da scrivere (una per frame)
    testi::TestoId _cartello_dove = testi::TestoId(0);
    int _cartello_oltre = -1;
    int _varco_cartello = -1;       // il varco del cartello a schermo, -1 nessuno
    int _compagni = 0;
    bool _scura = false;
    bn::vector<Compagno, COMPAGNI_MAX> _fila;
    Orma _orme[ORME];               // le orme di Ubaldo, un pixel l'una: _orme[_orma] e' la piu' recente
    int _orma = 0;
    int _orme_n = 0;
    // il centro di ogni varco dell'area caricata (aiuti::centro_del_varco scorre tutta la griglia: si fa una
    // volta al caricamento, a schermo nero, e non a ogni frame vicino al varco)
    aiuti::Punto _centri[mondo::VARCHI_MAX];
    int _varchi_sx[mondo::VARCHI_MAX] = {};
    int _varchi_sy[mondo::VARCHI_MAX] = {};
    int _varchi_n[mondo::VARCHI_MAX] = {};
    int _varchi_cella = 0;              // fin dove la griglia e' stata letta
    bool _varchi_pronti = false;
    bool _aiuti = false;
    mondo::Esploratore _e;
    mondo::AreaId _area_caricata = mondo::AreaId(0);
    int _variante = -1;             // mondo::VARIANTE da usare se vale per l'area (la sceglie la storia)
    int _variante_caricata = -1;    // quella del fondale caricato, -1 se e' il fondale dell'area
    int _mezza_larghezza_mappa = 0;
    int _mezza_altezza_mappa = 0;
    int _dissolvenza = 0;           // >0 in uscita, <0 in entrata
    int _riflessi = 0;              // i frame dei riflessi dell'acqua nelle stanze della gola
    int _varco_chiuso = -1;         // il varco che si urta come un muro (chiudi_varco)
    bool _urto_al_varco = false;
    bool _notte = false;
    int _attesa_etichetta = 0;
    int _etichetta_passo = 0;       // 2, 1: l'ombra e la scritta da preparare (una per frame)
    testi::TestoId _testo_etichetta = testi::TestoId(0);
    // la figura del giocatore (tools/sagome_mappa.py): direzione, passo, respiro
    enum Direzione { GIU, SU, DESTRA, SINISTRA };
    int _direzione = GIU;
    mondo::Camminata _camminata;    // il ciclo della camminata (mondo_logica.h)
    int _fermo = 0;
    int _mostrato = -1;
    bool _mosso = false;
    bool _corre = false;
    // la velocita' in diagonale uguale a quella dritta (muovi): il resto dei passi in 256esimi di pixel
    int _resto_diagonale = 0;
    // la camera morbida (giro 6): il punto inquadrato insegue il giocatore con un anticipo nella direzione
    // in cui guarda; _camera_ferma = la prossima inquadratura salta subito al bersaglio (cambio d'area)
    int _cam_x = 0;
    int _cam_y = 0;
    bool _camera_ferma = true;

    void _carica_fondale(bool etichetta = true);
    void _mostra_etichetta(testi::TestoId id);
    void _mostra_cartiglio(bool visibile);
    void _dopo_evento(mondo::Evento evento);
    void _anima_giocatore();
    void _azzera_orme();
    void _segna_orme();
    void _anima_compagni();
    void _cerca_i_varchi(bool tutto);
    void _aggiorna_aiuti();
    // Crea la vista se non c'e' e ci scrive il testo tutto rivelato; _nascondi_aiuti() le distrugge.
    void _mostra_aiuto(bn::optional<VistaTesto>& vista, testo::Contesto contesto, int x, int y, int inchiostro,
                       testo::TestoId testo);
    void _nascondi_aiuti();
    [[nodiscard]] aiuti::Rettangolo _rettangolo_del_giocatore() const;
    void _disegna_freccia_della_targa(bool spenta);
    void _anima_promemoria();
    void _crea_cartello(int varco);
    void _anima_cartello();
};

}

#endif
