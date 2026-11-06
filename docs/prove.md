# Le prove: il giro corto e il giro lungo

Il 4 novembre 2026 la suite Python (883 test) girava in 7 min 18 s, in serie. Il tempo andava quasi
tutto in tre moduli: `test_mondo` (190 s), `test_grafo_trama` (73 s), `test_regia` (25 s). Il resto della
suite stava sotto i 30 s.

## Cosa e' cambiato

- **Memoria dei fondali** (`tools/genera_mondo.py`, `disegna_area`). I test negativi del mondo cambiano un
  solo file `.area` e chiamano `genera()`, che ridipingeva tutte le 25 aree (14 s ogni volta). Ora il
  disegno di un'area si ricorda, con la chiave fatta dall'impronta di tutto cio' da cui dipende: l'area,
  monumenti e censimento, i dati dei moduli di `tools/` e `stile/` e l'identita' delle loro funzioni (un
  test che sostituisce un pittore non riceve un disegno vecchio). Rimette anche i registri che il disegno
  scrive (`COMPROMESSI`, `PORTALI_APERTI`, `SOSTITUZIONI`). Rigenerare il mondo nei test: da 14 s a 0,6 s.
  Lo script vero dipinge una volta e l'header esce identico.
- **Grafo della trama** (`tools/grafo_trama.py`). `recita()` e `frasi_npc()` leggono solo le bandiere
  delle loro guardie: l'esito si ricorda su quelle sole bandiere e si rimette sopra le bandiere vere; nel
  modello con la mappa scene e NPC si cercano per area. Risultati identici (confrontati per intero sul
  copione vero), `analizza()` da 5 s a 2,9 s.
- **`tests/test_icone_menu.py` non girava**: erano funzioni nello stile di pytest, che unittest non
  raccoglie. Ora e' una classe, e `tools/check_no_skip.py` rifiuta una `def test_` fuori da una classe.

In serie la suite ora gira in circa 3 min; con `tools/prove.py --tutte` su 4 core in circa 54 s.

## `tools/prove.py`

    python3 tools/prove.py              # giro corto: solo i moduli che leggono un file cambiato
    python3 tools/prove.py --da HEAD    # ... rispetto all'ultimo commit invece che a origin/main
    python3 tools/prove.py --veloci     # tutti tranne i lenti (oltre 15 s l'ultima volta)
    python3 tools/prove.py --tutte      # tutto: prima di fondere (la CI fa lo stesso)
    python3 tools/prove.py test_mondo.Mondo     # quelli nominati
    opzioni: -j N, --elenco (dice cosa farebbe), --senza-mgba

Come sceglie: ogni volta che un modulo gira, un gancio di audit (`tools/prove/sitecustomize.py`, anche
nei processi figli che il test lancia) annota i file che apre e le cartelle che elenca o in cui cerca con
glob. Le tracce stanno in `build_prove/tracce.json`, fuori dal repo. Un file modificato tocca un modulo se
il modulo l'ha letto; un file nuovo o tolto anche se il modulo ha guardato nella sua cartella. Un modulo
senza traccia gira sempre. La prima volta (nessuna traccia) gira tutto.

I moduli lunghi si dividono per classe in al piu' 3 pezzi su core diversi, partendo dai piu' lunghi.
Nessun test si salta: un modulo o gira intero o non gira.

Il giro corto e' per lavorare. **Prima di una fusione** si lancia `--tutte` (o la CI).

## `tools/prove_mgba.py`: le prove nel gioco vero

Le prove di `tests/mgba/prove.json` compilano la ROM col modo `GUBBIO_AVVIO` voluto (e altri flag), la
fanno girare in libmgba senza finestra col loro copione di tasti e controllano il log: righe attese,
righe vietate (assert), limiti numerici, e le registrazioni in `tests/dati/*_mgba.txt` rifatte uguali.

| prova | modo | cosa controlla |
|---|---|---|
| camminata | 1 | movimento e collisione vera su ogni arco del grafo, ingressi e uscite da ogni area, nessun frame oltre il budget, CPU, sprite, stack |
| storia | 8 | la storia intera nei due giri di scelte, uguale a `tests/dati/storia_mgba.txt` |
| prologo | 9 | il prologo col pilota, uguale a `tests/dati/prologo_mgba.txt` |
| battaglie | 3 | i 700 scontri uguali al mirror Python e a `tests/dati/battaglia_mgba.txt` |
| salvataggio | 6 | scrittura, ricarica, banche, CRC |
| varchi, folla, fila | 14, 12 | prestazioni (riga PREST con `-DGUBBIO_PRESTAZIONI`): picchi limitati e al piu' 3 finestre sopra il 100% vicino ai varchi; la fila senza assert |
| palette_* | 2, 5, 9, 10, 11 | i picchi dei colori di sprite e fondali (`-DGUBBIO_PALETTE`) |
| caccia_* (lunghe) | 0, 15, 13 | la caccia ai crash: il giocatore scimmia per 100 000 frame a seme, con `-DGUBBIO_LIMITI` ([caccia_ai_crash.md](caccia_ai_crash.md)) |
| rete | 13 | un assert voluto: la rete che prende i crash deve vederlo e fotografarlo |

Ogni assert di Butano finisce nel log ("ASSERT scattato") e il banco fotografa la schermata d'errore in
`build_banco/crash/<prova>.png`; il log intero di ogni prova resta in `build_banco/log/<prova>.txt`. Con
`-DGUBBIO_LIMITI` nessuna risorsa puo' passare il 90% del suo tetto. Le prove "lunghe" (la caccia) non girano nel
giro corto di `tools/prove.py`, solo con `--tutte` (o `tools/prove_mgba.py` senza `--corte`).

Perche' e' veloce: ogni combinazione di modo e flag ha la sua cartella di oggetti (`banco_obj<...>/`),
quindi make ricompila solo i file cambiati (un `.cpp` toccato: 2 s), e accanto alla ROM c'e' l'impronta dei
sorgenti (`src/`, `include/`, `graphics/`, `audio/`, `Makefile`, commit di Butano, flag, immagine): se non e'
cambiato niente docker non parte. Le cinque prove con le ROM in cache: circa 6 s. La prima volta ogni ROM
costa circa un minuto.

`tools/prove.py` le lancia da solo quando cambia un file della ROM. Servono docker e libmgba: in cloud
`nohup dockerd &` e `apt-get install -y libmgba-dev`. Dove mancano (il PC Windows) lo dice e non fallisce.
Con `--aggiorna` riscrive le registrazioni quando il cambio e' voluto.

Per aggiungere una prova: una voce in `tests/mgba/prove.json` (il formato e' spiegato in cima al file),
con un copione che finisce con `finche`, cosi' la prova si ferma appena il gioco ha detto quello che serve.
