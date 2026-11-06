# Modello: una lezione

Si aggiunge in fondo a `LEZIONI.md`, con il primo numero libero. Il titolo usa il punto in mezzo «·».
Tutti e sei i campi sono obbligatori (li controlla `tools/controlla_metodo.py`).

```
## L20 · Titolo breve che dice cosa è andato storto

**Cosa è successo.** I fatti, con le date. Niente trama.

**Quanto è costato.** Misurato quando si può (file e righe del commit del rifacimento, ore, thread
fermi); se è una stima, scriverlo.

**Perché.** La causa vera, non il sintomo.

**Cosa si doveva decidere prima.** La decisione (Dnnn) che, presa prima, avrebbe evitato il rifacimento,
e in quale momento andava presa.

**Regola nuova.** Cosa si fa d'ora in poi, in modo che si possa controllare.

**Dove vive ora.** La fase del percorso, il test o lo strumento che la fa rispettare.
```

Poi si cita `L20` nella fase giusta di `PERCORSO_DA_ZERO.md`: una lezione che non cambia il percorso non
serve al gioco successivo.
