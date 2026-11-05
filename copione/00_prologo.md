# Prologo: L'ombra delle undici corone

Fonte: GDD Sez. 7 (Prologo), Sez. 33A (avvio), Sez. 37B (vetrata). Formato delle battute nel [README](README.md).

Idea di regia: il gioco si apre e si chiude sulla **vetrata della Basilica** che racconta la battaglia delle Undici Città e Sant'Ubaldo che la ferma. All'inizio i vetri sono chiari, senza storia; alla fine della v1 se ne accende uno solo, quello del Bottaccione. Le altre vetrate restano chiare: sono gli aggiornamenti futuri.

---

## P-00 · Avvio

| | |
| :-- | :-- |
| Luogo | schermo nero, poi titolo |
| Condizione | accensione |
| Imposta | nulla |

Regia: un rintocco isolato del Campanone sul nero. Compare il titolo (scelta di stile 12). Menu: `NUOVA CRONACA`, `CONTINUA`, `IMPOSTAZIONI`. «Nuova cronaca» porta a P-01.

---

## P-01 · La vetrata chiara

| | |
| :-- | :-- |
| Luogo | interno della Basilica, inquadratura fissa sulla vetrata grande |
| Condizione | NUOVA CRONACA |
| Imposta | nulla |

Regia: piombi neri, vetri chiari senza figure. La luce entra di sbieco. La camera sale lentamente.

- NARRATORE: Sul Monte Ingino c'è una vetrata che racconta una guerra.
- NARRATORE: Chi la guarda oggi vede soldati in rotta, stendardi spezzati e un vescovo con le braccia aperte.
- NARRATORE: Ora torniamo a quei giorni, quando nessuno sapeva ancora come sarebbe finita.

Regia: un vetro si oscura, la camera ci entra dentro e la scena diventa la mappa di P-02.

---

## P-02 · La mappa che annerisce

| | |
| :-- | :-- |
| Luogo | mappa dell'Umbria medievale, pergamena |
| Condizione | segue P-01 |
| Imposta | `PROLOGO_VISTO` alla fine |

Regia: l'inchiostro nero si allarga sulla pergamena. A ogni battuta del narratore si piantano alcuni stendardi sui valichi, con il nome della città sotto. L'ultimo, più grande, è quello di Perugia: rosso scuro, con il grifo bianco coronato d'oro. Gubbio resta al centro: un piccolo drappo rosso con il monte bianco a cinque cime. Grifo bianco contro monte bianco, entrambi su rosso: è il confronto visivo di tutto il gioco (vedi `simboli/CENSIMENTO_SIMBOLI.md`).

- NARRATORE: Anno 1151. Gubbio ha molti nemici, e alcuni hanno anche delle buone ragioni.
- NARRATORE: Contro di lei si alleano Spoleto e Foligno, Assisi, Spello e Bettona, Todi e Cagli.
- NARRATORE: E poi Nocera, Gualdo Tadino e Fossato. A guidarle tutte c'è Perugia.
- NARRATORE: Undici città in tutto. I loro eserciti si accampano nella valle, sotto le mura di Gubbio.
- NARRATORE: La città è circondata: nessuno può uscire, e il grano basta per pochi giorni.
- NARRATORE: Gubbio è sola. Ma non vuole arrendersi.
- NARRATORE: Il vescovo Ubaldo sceglie di combatterli con un'arma diversa: la fede.

Regia: dissolvenza sul loggiato di Palazzo dei Consoli. Si passa ad A1-01.

> Nota v2 (3 nov 2026). La prima riga non dice più «l'invidia e la sete di dominio»: la coalizione ha delle ragioni, e una è un torto di Gubbio (Bibbia della storia v2, `storia/BIBBIA_STORIA.md`). Via anche «maggio»: la data è solo tradizionale. La riga vive nella cutscene C1.

> Nota. L'elenco delle undici città è quello della Sez. 3 del GDD (Perugia, Spoleto, Cagli, Foligno, Todi, Nocera, Gualdo Tadino, Fossato, Assisi, Bettona, Spello). Le fonti storiche non concordano tutte sull'elenco: va bene per il gioco, ma è da segnare nel registro delle fonti come scelta.
