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
// fase della storia. Le decisioni sono di include/storia_logica.h.
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
    void recita_regia(int regia, Esplorazione* esplorazione, const bn::sprite_palette_ptr& palette_testo,
                      bool automatica);

    bn::vector<bn::sprite_ptr, storia::NPC> _npc;
    bn::vector<int, storia::NPC> _indici;
    int _area = -1;

    void _prepara_npc(const Esplorazione& esplorazione);
};

// GUBBIO_AVVIO=8: la storia intera senza camminare, dalla prima battuta ai titoli di coda; una riga di
// log per scena e il riepilogo ("Storia: N scene visitate su M"). Non ritorna.
[[noreturn]] void prova_storia(const bn::sprite_palette_ptr& palette_testo);

// GUBBIO_AVVIO=9: il prologo giocabile senza tasti: l'ultimatum a Piazza Grande (Giorgio nel gruppo),
// la postierla di San Martino, la Pattuglia sulla mappa del Teatro e la battaglia col pilota che
// salva Antonio; le istantanee e il riepilogo nel log ("Prologo: ...").
void prova_prologo(Esplorazione& esplorazione, const bn::sprite_palette_ptr& palette_testo);

}

#endif
