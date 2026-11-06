# Scheda di avvio di un gioco nuovo

Si compila il primo giorno, prima di qualunque codice o asset (fase 0 del percorso). Ogni risposta
diventa una riga di `DECISIONI.md`. Fra parentesi la scelta fatta per Gubbio 1151, come opzione di
partenza: si porta al committente come consigliata, salvo motivo.

## 1. Il gioco

- Titolo di lavoro: ____
- Città e periodo: ____
- Storia di partenza e fonti principali: ____
- Genere e modello di riferimento (RPG a turni alla Golden Sun e Pokémon, esplorazione della città): ____
- Durata della v1 in ore e numero di aree (2-3 ore, 14 aree, D008): ____
- Cosa è dentro la v1 e cosa resta fuori, in due liste: ____

## 2. Fondazioni (si cambiano solo a caro prezzo)

- Rilascio: gratis o a pagamento, dove, prova privata prima? (ROM gratuita su itch.io dopo la prova con
  gli amici, D002, D003): ____
- Origine degli asset (procedurali da script, foto solo come riferimento, D004): ____
- Licenze (MIT codice, CC BY-NC 4.0 contenuti, D007): ____
- Repo (nuovo, sviluppo su `main`, tag ai punti fermi, D006): ____
- Lingua (italiano, D009): ____
- Persone vere nel gioco? Nomi di gioco e regola di rispetto (D074): ____

## 3. Ruoli e modo di lavorare

- Chi decide trama e design, chi gioca e giudica (Claude decide dopo ricerca, il committente gioca, D010): ____
- Autonomia di Claude e merge (D100, D101, D103): ____
- Spoiler al committente (nessuno, D077): ____
- Custode visivo e custode di trama e nomi (D107): ____
- Cadenza delle prove giocate (a ogni fase, una ROM sola in `rom/`, D031): ____

## 4. Cosa serve a chi gioca (si chiude in fase 2)

Segnare per ognuna: serve? com'è? mockup approvato?

- [ ] Titolo, nuova partita, continua
- [ ] Dove sono (nome dell'area, mappa)
- [ ] Dove vado (obiettivo corrente, promemoria, freccia o segnalini)
- [ ] Cosa ho (bisaccia, denaro, compagni)
- [ ] Come salvo (slot, anteprima)
- [ ] Dove si entra (porte leggibili, interni)
- [ ] Chi parla (nome nel cartiglio, ritratto)
- [ ] Come scelgo in battaglia (effetto, danno, costo, anteprima sul bersaglio)
- [ ] Negozio, cartelli, aiuti, opzioni
- [ ] Cosa succede se perdo

## 5. Stile e mondo (si chiude in fase 4)

- Orientamento della mappa (nord in alto, D061), provato con un greybox: ____
- Vista (tetti dall'alto e facciata bassa, D042): ____
- Proporzioni del personaggio e scala del mondo nella stessa tavola (16x32, 1 cella = 1,5 m, D046, D063): ____
- Le 12 scelte di stile (D040): riprendere quelle della serie o cambiarle? ____
- Standard grafico e pezzi campione per tipo (D054): ____

## 6. Tecnica (si chiude in fase 0 e 5)

- [ ] Toolchain bloccata e build in cloud, in CI e sul PC con lo stesso digest (D020, D023)
- [ ] Prova mGBA senza schermo in cloud
- [ ] Regole del codice e controlli attivi (D029)
- [ ] Tabella dei budget della console con contatori (D030)
- [ ] Giro corto delle prove (D027)
- [ ] `docs/metodo/` copiato e registro azzerato (D108)
