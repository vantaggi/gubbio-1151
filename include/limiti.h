#ifndef GUBBIO_LIMITI_H
#define GUBBIO_LIMITI_H

// La caccia ai crash (docs/caccia_ai_crash.md). Due pezzi:
//
// 1. Sempre, anche nel gioco vero: quando scatta un assert di Butano (BN_ASSERT, BN_ERROR: "There are no more
//    available colors", "No more sprite tiles items available"...) prima che il gioco si fermi una riga nel
//    log di mGBA, "ASSERT scattato ...", con area, posizione e frame. Senza, l'errore si vedeva solo a schermo
//    e una prova automatica poteva passare senza accorgersene. Il banco (tools/banco_mgba.c) a quella riga fa
//    la foto della schermata d'errore e si ferma.
//
// 2. Con -DGUBBIO_LIMITI (solo per le prove): a ogni frame l'uso di ogni risorsa a tetto fisso del GBA e di
//    Butano (colori, sprite, tile, fondali, mappe, matrici affini, IWRAM, EWRAM). Una riga
//    "LIMITI picco NOME USO su TOT (P%)" a ogni nuovo picco: le prove (tests/mgba/prove.json) falliscono quando
//    una risorsa si avvicina al tetto, prima che il gioco si fermi. -DGUBBIO_PALETTE da' le righe "PALETTE" di
//    sempre (le stesse misure delle palette, nel formato delle prove vecchie).
namespace gubbio::limiti
{

// Da chiamare una volta, subito dopo bn::core::init().
void installa();

// Dove si e' (per la riga dell'assert e, con GUBBIO_LIMITI, la riga "LIMITI area" a ogni cambio d'area).
// La chiama l'esplorazione quando entra in un'area; costa due scritture.
void segna_area(int area, int x, int y);

}

#endif
