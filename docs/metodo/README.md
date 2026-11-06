# Il metodo di lavoro della serie

Gubbio 1151 è il primo di una serie di giochi su storie di Gubbio e delle città intorno. Questa cartella
è il **metodo**: ciò che abbiamo deciso, ciò che abbiamo imparato rifacendo le cose, e il percorso per
fare il prossimo gioco più in fretta e con la stessa qualità. È un documento vivo: cresce con il gioco.

| File | A cosa serve |
| :-- | :-- |
| [PERCORSO_DA_ZERO.md](PERCORSO_DA_ZERO.md) | Le fasi di un gioco nuovo, in ordine, con i cancelli e le prime dieci decisioni. **Si parte da qui.** |
| [DECISIONI.md](DECISIONI.md) | Il registro di tutte le scelte: chi, quando, generica o di Gubbio, ancora valida o superata |
| [LEZIONI.md](LEZIONI.md) | Le lezioni imparate: cosa si è rifatto, quanto è costato, cosa si doveva decidere prima |
| [GENERICO_E_SPECIFICO.md](GENERICO_E_SPECIFICO.md) | Cosa del repo si porta nel prossimo gioco (motore, pipeline, test, toolchain) e cosa resta a Gubbio |
| [modelli/](modelli/) | Modelli da copiare: scheda di avvio, voce di decisione, voce di lezione, brief di un thread |

## La regola di aggiornamento

Vale per ogni thread e per ogni fusione, da oggi alla fine del gioco.

1. **Ogni decisione** (di Cioti o presa da Claude su delega) diventa una riga in `DECISIONI.md`, nella
   stessa fusione che la applica. Se ne cambia una vecchia, la vecchia diventa `superata da Dnnn`.
2. **Ogni rifacimento** (qualcosa fatto e poi rifatto, o scoperto tardi) diventa una voce in
   `LEZIONI.md` con i sei campi del modello, e la sua regola entra nella fase giusta di
   `PERCORSO_DA_ZERO.md`.
3. Se cambia cosa si porta nel gioco successivo, si aggiorna `GENERICO_E_SPECIFICO.md`.
4. `python3 tools/controlla_metodo.py` (e `tests/test_metodo.py`, che gira con le altre prove) fallisce
   se una decisione superata non ha la sua lezione, se una lezione non è nel percorso, o se il registro
   è scritto male.
5. Niente trama: qui si scrive il *come*, mai il contenuto della storia, perché Cioti deve potersi godere
   il gioco senza spoiler (D077). Le decisioni di trama stanno nei documenti della storia.

Chi non sa se una scelta «conta»: se cambiarla dopo costringerebbe a rifare lavoro, conta.

## Come si usa per un gioco nuovo

1. Nuovo repo; si copia questa cartella, `tools/controlla_metodo.py` e `tests/test_metodo.py`.
2. In `DECISIONI.md` si tengono come punto di partenza le righe con Tipo `G` e `G+S` (marcate «ereditata
   da Gubbio 1151»), si tolgono le `S`.
3. `LEZIONI.md` si tiene tutta: è il valore accumulato. Le lezioni nuove continuano la numerazione.
4. Si compila [modelli/SCHEDA_AVVIO.md](modelli/SCHEDA_AVVIO.md) e si segue
   [PERCORSO_DA_ZERO.md](PERCORSO_DA_ZERO.md) dalla fase 0.
