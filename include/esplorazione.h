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

    // La citta' di notte (storia::fase_npc NOTTE): i fondali con le rampe di notte, fiaccole e drappi caldi (L5).
    void imposta_notte(bool notte);
    void ricompari();

    // Uno sprite che sta sulla mappa (un nemico): sulla camera dell'area, coi piedi in (x, y) pixel.
    void colloca_sulla_mappa(bn::sprite_ptr& sprite, int x, int y, int altezza) const;

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
    int _varco_cartello = -1;       // il varco del cartello a schermo, -1 nessuno
    bool _aiuti = false;
    mondo::Esploratore _e;
    mondo::AreaId _area_caricata = mondo::AreaId(0);
    int _mezza_larghezza_mappa = 0;
    int _mezza_altezza_mappa = 0;
    int _dissolvenza = 0;           // >0 in uscita, <0 in entrata
    int _riflessi = 0;              // i frame dei riflessi dell'acqua nelle stanze della gola
    int _varco_chiuso = -1;         // il varco che si urta come un muro (chiudi_varco)
    bool _urto_al_varco = false;
    bool _notte = false;
    int _attesa_etichetta = 0;
    // la figura del giocatore (tools/sagome_mappa.py): direzione, passo, respiro
    enum Direzione { GIU, SU, DESTRA, SINISTRA };
    int _direzione = GIU;
    int _passo = 0;
    int _fermo = 0;
    int _mostrato = -1;
    bool _mosso = false;
    bool _corre = false;
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
