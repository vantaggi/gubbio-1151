---
name: decisioni-aperte
description: Scioglie UNA decisione di design ancora aperta di Gubbio 1151, interrogando il committente per round finche' non resta nulla di implicitamente assunto, e chiudendola nel GDD e in HANDOVER.md. Usala quando un passo del piano e' bloccato da una scelta non presa, quando il GDD si contraddice, o quando il committente dice "decidiamo X".
---

# Sciogliere una decisione aperta

> **Nota:** copia operativa per Claude Code. La sorgente canonica e'
> `.agents/skills/decisioni-aperte/SKILL.md` (convenzione Antigravity): le due vanno tenute
> allineate a mano.

## Perche' questa skill esiste

Il collo di bottiglia di questo progetto non e' scrivere codice: e' che **il GDD si contraddice**,
e che una ventina di scelte non sono mai state prese. Il piano lo dice in modo esplicito —
*"nessuna riga di codice dei passi indicati parte prima che la decisione sia scritta nel GDD"* —
e la storia gli da' ragione: la Sessione 02b ha dovuto riconciliare la scala del Fervore dopo che
un valore sbagliato era sopravvissuto a due sessioni, e la lezione a verbale e' che **una
decisione che resta solo in chat viene disfatta dalla sessione successiva.**

Questa skill fa una cosa sola: prende **una** decisione, la porta a chiusura, e la scrive dove
nessuno potra' piu' ignorarla.

## Il metodo: round sulla frontiera

Non si spara un elenco di domande. Si procede a **round**, e ogni round contiene *tutte e sole* le
domande le cui premesse sono gia' risolte — la **frontiera**. Le domande che dipendono da una
risposta non ancora data si tengono per il round dopo, altrimenti si chiede al committente di
decidere due volte la stessa cosa con informazioni diverse.

La sessione finisce **quando la frontiera e' vuota**: ogni ramo visitato, nulla lasciato
tacitamente assunto. Normalmente sono 3-5 round, non uno.

**Regola d'oro: si arriva con le prove, non con le domande a vuoto.** Prima di aprire bocca:

1. Cerca nel GDD **tutte** le sezioni che toccano la questione e citale per numero.
2. Guarda cosa fa **il codice oggi**, e cosa gia' dipende da quel comportamento.
3. Conta le occorrenze: se una lettura compare in una sede sola e l'altra in tre, dillo. E' cosi'
   che la Sessione 02b ha sciolto il nodo del Fervore, ed e' un argomento, non un'opinione.
4. Porta una **raccomandazione motivata**. "Cosa preferisci?" scarica sul committente un lavoro
   che spetta a te; "propongo A perche' la Sez. 6 la presuppone, e B costerebbe X — confermi?" no.

Se durante l'indagine trovi che la decisione **e' gia' implicitamente presa dal GDD** — come il
carry-over del Fervore, che la Sez. 6 presuppone assegnando all'Eremo il "recupero MP/Fervore" —
allora non e' una decisione: e' una lettura. Portala come tale, con la citazione.

## Le tre classi di decisione

**(a) Riservate al committente.** Non si decidono da soli, nemmeno con una buona motivazione:
toccano l'identita' del gioco o impegnano risorse esterne. Sono elencate in fondo alla Sezione 0
di `HANDOVER.md` — oggi: chi produce la pixel art, se l'Alzata Trionfale sia la Mossa Suprema dei
Tre Ceri, se i boss agiscano una o due volte per turno, come trattare il font privo di accenti
italiani. Su queste, se il committente risponde "fai tu", **non si procede lo stesso**: si
restringe il campo a due opzioni con i loro costi e si richiede una scelta secca.

**(b) Decidibili dall'agente, motivando.** Tutto il resto dell'elenco in fondo a
`docs/piano_fase_successiva.md`. Qui la regola del progetto e' chiara: *scegli motivando la
scelta, e correggi ANCHE il GDD*. Si decide, non si accumula.

**(c) Gia' chiuse — non riaprirle.** Ogni chiusura lascia una nota di revisione datata nel GDD.
Prima di aprire un nodo, verifica che non porti gia' quella nota: riaprire una decisione chiusa e'
il modo tipico in cui questo progetto ha perso tempo.

## Il registro

Non tenerne una copia qui dentro: si sfaserebbe. Le fonti sono due e restano quelle.

* `docs/piano_fase_successiva.md`, sezione finale — l'elenco completo, con l'indicazione di cosa
  ciascuna decisione blocca.
* `HANDOVER.md`, Sezione 0 — quelle riservate al committente, e quelle maturate dopo il piano.

## Protocollo di chiusura (non negoziabile, AGENTS.md §4)

Una decisione non e' chiusa finche' non e' **scritta in tre posti**. Mancarne uno significa che la
sessione successiva la disfara':

1. **Nel GDD**, dentro la sezione che oggi la contraddice — non in fondo al file, non in un
   documento a parte. Nella forma gia' usata: `> **NOTA DI REVISIONE (data, Sessione N).**` con
   la decisione, **le prove** che l'hanno determinata e le conseguenze rimaste aperte. Se due
   sezioni si contraddicono, si annotano entrambe.
2. **In `HANDOVER.md`**: cosa e' stato deciso, perche', e cosa si sblocca adesso.
3. **Nel codice**, se la decisione ne ha uno: il valore, piu' una `static_assert` che la renda
   irreversibile per distrazione, dove possibile. E' cio' che si e' fatto per la Mossa Suprema
   irraggiungibile — un ritocco di bilanciamento che la violasse rompe la build invece di passare
   inosservato.

Se la decisione tocca la pipeline degli asset o l'architettura delle scene, aggiorna **entrambe**
le copie della skill `butano-gba-dev`.

## Anti-pattern

* **Chiedere tutto insieme.** Un muro di dieci domande riceve tre risposte e sette silenzi, e i
  sette silenzi diventano assunzioni tacite.
* **Chiedere senza aver letto il GDD.** Meta' delle "decisioni" sono contraddizioni fra due
  sezioni: portale entrambe, o il committente decidera' senza sapere cosa sta contraddicendo.
* **Accettare "decidi tu" su una decisione di classe (a).**
* **Chiudere in chat.** Vedi il protocollo qui sopra: la chat non e' uno dei tre posti.
* **Prendere l'occasione per riaprire tutto.** Una decisione per sessione. Le altre restano nel
  registro, che esiste apposta.
* **Decidere ignorando cosa costa.** Se una scelta muove VRAM, palette, slot OAM o byte del
  salvataggio, il numero va portato *prima* della domanda, non scoperto dopo.
