#ifndef GUBBIO_STORIA_SCENA_H
#define GUBBIO_STORIA_SCENA_H

#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "storia.h"

namespace gubbio
{

class Esplorazione;

// La storia a schermo (F6 parte 1): le scene del copione recitate battuta per battuta (nome di chi
// parla, testo a macchina da scrivere, A per andare avanti), il nodo segnaposto delle cutscene (per
// ora un cartello col titolo), le battaglie delle scene, gli NPC d'ambiente che parlano secondo la
// fase della storia. La gola (T2): le scene che partono su una cella (la nebbia, l'arco), i miasmi che
// feriscono chi corre, i soldati di B-03, i forzieri, l'uscita del Condotto chiusa nel duello. Le quest (SV2c): i datori (proposta, attesa, consegna, dopo), gli oggetti da
// raccogliere sulla mappa (si prendono toccandoli), gli indizi di Q-SP01 e l'infiltrato con la sua
// battaglia. Le decisioni sono di include/storia_logica.h.
class Storia
{
public:
    // La partita nuova: le scene a schermo intero (il prologo) prima di entrare in citta'.
    void prologo(const bn::sprite_palette_ptr& palette_testo, bool automatica = false);

    // Da chiamare a ogni frame dell'esplorazione: rifa' gli NPC se l'area e' cambiata, avvia la scena
    // pronta nell'area, fa parlare l'NPC davanti al giocatore se si preme A. True se ha recitato.
    bool aggiorna(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

    // Recita una scena: battute, eventuale battaglia; ritorna true se la scena e' finita (e le sue
    // bandiere accese). Con automatica=true non aspetta tasti; la battaglia la gioca il pilota (con le
    // istantanee) se battaglia_col_pilota, se no la da' per vinta (la prova GUBBIO_AVVIO=8).
    bool recita(int scena, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                bool automatica = false, bool battaglia_col_pilota = false);

    void svuota();

private:
    // false se la cutscene era gia' vista e non e' ripartita
    bool recita_regia(int regia, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                      bool automatica);
    void recita_tratto(int da, int a, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                       bool automatica);

    // gli NPC d'ambiente (indice in NPC_AMBIENTE), i datori delle quest (NPC + quest) e l'infiltrato
    // (NPC + QUEST); poi gli oggetti da raccogliere (indice in RACCOLTA)
    static constexpr int PERSONE_MAX = storia::NPC + storia::QUEST + 1;
    bn::vector<bn::sprite_ptr, PERSONE_MAX> _npc;
    bn::vector<int, PERSONE_MAX> _indici;
    bn::vector<bn::sprite_ptr, storia::RACCOLTE> _raccolte;
    // la gola (T2): i soldati di B-03 e i forzieri (chiusi o aperti); le guardie delle fornaci e le fiamme dei
    // ceri della Basilica (F10)
    bn::vector<bn::sprite_ptr, storia::SENTINELLE + storia::FORZIERI + storia::GUARDIE_FORNACE + storia::CERI_ALTARE> _gola;
    int _area = -1;
    int _respiro = 0;           // i frame di fila di corsa nella nebbia (storia::respira_i_miasmi)
    uint32_t _ultimo_urto = 0;  // il frame dell'ultimo avviso dell'uscita chiusa (uno ogni due secondi)

    void _prepara_npc(const Esplorazione& esplorazione);
    void _parla_col_datore(int quest, const bn::sprite_palette_ptr& palette_testo);
    void _affronta_l_infiltrato(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);
    void _affronta_la_guardia(int guardia, Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);
};

// GUBBIO_AVVIO=8: la storia intera senza camminare, dalla prima battuta ai titoli di coda; una riga di
// log per scena e il riepilogo ("Storia: N scene visitate su M"). Non ritorna.
[[noreturn]] void prova_storia(const bn::sprite_palette_ptr& palette_testo);

// GUBBIO_AVVIO=9: il prologo giocabile senza tasti: l'ultimatum a Piazza Grande (Giorgio nel gruppo),
// la postierla di San Martino, la Pattuglia sulla mappa del Teatro e la battaglia col pilota che
// salva Antonio; le istantanee e il riepilogo nel log ("Prologo: ...").
void prova_prologo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

// GUBBIO_AVVIO=11: le cinque figure degli NPC (FIGURA_NPC) in fila in Piazza Grande accanto al
// giocatore, per l'istantanea "figure_npc".
[[noreturn]] void prova_figure_npc(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

}

#endif
