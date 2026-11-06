# Registro delle decisioni

Tutte le scelte che hanno indirizzato Gubbio 1151, in ordine di ambito e poi di data. È la memoria che
serve al prossimo gioco: che cosa si è deciso, chi l'ha deciso, se vale per qualunque gioco della serie
(**G**) o solo per Gubbio (**S**), e se è ancora valida.

- **Chi**: «Cioti» = deciso da lui; «Claude» = deciso da Claude su delega (Cioti giudica giocando);
  «Claude, ok Cioti» = proposto da Claude e approvato.
- **Stato**: `valida`, `in corso`, `da rivedere`, oppure `superata da Dnnn`. Una decisione superata è un
  rifacimento: ha sempre una lezione in [LEZIONI.md](LEZIONI.md) che la cita (lo controlla
  `tests/test_metodo.py`).
- Le decisioni **di trama** non stanno qui, per non rovinare la storia a chi gioca: qui c'è solo il
  *metodo* con cui la storia si fa. Il contenuto sta nel copione e nei documenti della storia.
- Si aggiunge una riga a ogni decisione nuova, nella stessa fusione che la applica. Il modello è in
  [modelli/DECISIONE.md](modelli/DECISIONE.md).

## 1. Fondamenta del progetto

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D001 | 2026-11-01 | Progetto | Ripartire da zero: il prototipo resta solo come riferimento (tag `prototipo-v0`); si portano avanti idee, test e strumenti, non gli asset | Cioti | G | valida |
| D002 | 2026-11-01 | Rilascio | Rilascio = ROM gratuita su itch.io; niente vendita né cartuccia | Cioti | G | valida |
| D003 | 2026-11-04 | Rilascio | Progetto amatoriale: prima prova offline con gli amici, si pubblica (e si scrive a Comune e Basilica) solo se piace a loro | Cioti | G | valida |
| D004 | 2026-11-01 | Asset | Grafica procedurale generata da script; foto solo come riferimento (misure, ritmo, colori medi), nessun pixel fotografico nel gioco o nel repo; ogni fonte tracciata con autore e licenza | Cioti | G | valida |
| D005 | 2026-11-01 | Repo | Stesso repo, ramo orfano `ripartenza` per la nuova storia; `main` sostituito solo dopo che Cioti vede la ROM | Cioti | G | superata da D006 |
| D006 | 2026-11-06 | Repo | `main` = il gioco nuovo (ex `ripartenza`); il prototipo resta nel tag `prototipo-v0` e nel ramo `main-vecchio`. Per i giochi futuri si sviluppa su `main` dal primo giorno | Cioti | G | valida |
| D007 | 2026-11-01 | Licenze | Codice MIT; grafica, testi, storia e musica CC BY-NC 4.0; fonti solo CC0, pubblico dominio o CC BY; registro dei crediti versionato con test | Cioti | G | valida |
| D008 | 2026-11-01 | Ambito | v1 = «Atto I e Bottaccione», 2-3 ore, 14 aree, livelli 1-8; fuori dalla v1 combo, equipaggiamento, assedio a ondate, mappa regionale, post-game | Cioti | S | valida |
| D009 | 2026-11-01 | Lingua | Si lavora e si scrive in italiano (gioco, documenti, commit) | Cioti | G | valida |
| D010 | 2026-11-01 | Ruoli | Cioti non è sceneggiatore né game designer: trama e design li decide Claude dopo ricerca online con fonti; Cioti prova il gioco e giudica se è divertente | Cioti | G | valida |
| D011 | 2026-11-01 | Mondo | La città vera è una guida, non un vincolo: sono ammesse scelte di stile non fedeli quando servono al gioco | Cioti | G | valida |
| D012 | 2026-11-01 | Mondo | Ci sono tutti gli edifici, anche quelli posteriori al 1151 (anacronismi accettati) | Cioti | S | valida |

## 2. Toolchain, build e prove

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D020 | 2026-11-01 | Toolchain | Butano 21.9.0 come submodule; devkitARM nell'immagine Docker bloccata per digest in `toolchain.lock`; `build.sh` si ferma se le versioni non coincidono | Claude, ok Cioti | G | valida |
| D021 | 2026-11-01 | Toolchain | La ROM ufficiale è quella della CI (stesso SHA run dopo run); la build sul PC Windows serve solo per provare | Claude, ok Cioti | G | valida |
| D022 | 2026-11-01 | Toolchain | Il cloud legge e pianifica, compilare e provare si fa solo sul PC di Cioti con Remote Control | Claude | G | superata da D023 |
| D023 | 2026-11-04 | Toolchain | La ROM si compila anche in cloud (Docker con `mirror.gcr.io/devkitpro/devkitarm`, stesso digest) e si provano scene e battaglie con libmgba senza schermo (`tools/banco.sh`); il PC serve solo alla prova di Cioti | Claude | G | valida |
| D024 | 2026-11-02 | Prove | Sul PC di Cioti mai tasti simulati verso le finestre: le prove automatiche usano flag di compilazione (`GUBBIO_AVVIO`) | Claude | G | valida |
| D025 | 2026-11-01 | Prove | Ogni test ha la sua prova negativa (si rimette il difetto e il test deve fallire); mai `skip`: `tools/check_no_skip.py` | Cioti | G | valida |
| D026 | 2026-11-01 | Prove | Regola 0: log e anteprime non sostituiscono il giocare; le prove leggono le tabelle in modo esaustivo invece di campionare | Cioti | G | valida |
| D027 | 2026-11-04 | Prove | Giro corto `tools/prove.py` (solo i test toccati, in parallelo) e `--tutte` prima di fondere (55 s invece di 7 min); prove in mGBA con `tools/prove_mgba.py` | Cioti | G | valida |
| D028 | 2026-11-05 | Codice | `-Werror` (zero avvisi), gate EWRAM 16 KB, grafo dei moduli generato e controllato (`docs/architettura/`) | Claude | G | valida |
| D029 | 2026-11-05 | Codice | Regole di sviluppo GBA (`docs/regole_sviluppo_gba.md`): niente float, niente `std::` e heap, tabelle `constexpr`, niente divisioni nel ciclo di ogni frame; controlli automatici in test, build e CI; pannello di debug L+Select | Cioti | G | valida |
| D030 | 2026-11-05 | Codice | Budget hardware dichiarati e misurati: 128 strati di ordinamento degli sprite, palette degli sprite liberate prima di battaglie e cutscene, picchi nelle prove mGBA | Claude | G | valida |
| D031 | 2026-11-05 | Prove | Nella cartella `rom/` resta solo la ROM dell'ultima fusione; le vecchie si cancellano | Cioti | G | valida |
| D032 | 2026-11-06 | Prove | Caccia ai crash soprattutto con prove automatiche in cloud: ogni assert finisce nel log con la foto della schermata, `-DGUBBIO_LIMITI` misura ogni risorsa a tetto fisso e la prova fallisce sopra il 90%, il giocatore scimmia (tasti a caso con seme) gioca gioco vero, titolo con slot e salti per tutti i varchi con battaglie; una prova della rete con un assert voluto (`docs/caccia_ai_crash.md`); a Cioti una sessione breve e mirata | Claude, ok Cioti | G | valida |

## 3. Stile grafico

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D040 | 2026-11-01 | Stile | Lo stile si blocca PRIMA di produrre qualunque asset: fase FS con 12 scelte, una alla volta, ciascuna preceduta da ricerca con fonti e mostrata con tavole 240x160 generate | Cioti | G | valida |
| D041 | 2026-11-01 | Stile | Direzione artistica: naturalistico luminoso di giorno, cupo per la notte e il Bottaccione (cambio di palette); carattere «vetrata» solo in interfaccia e titolo | Cioti | S | valida |
| D042 | 2026-11-01 | Stile | Vista ibrida alla Pokémon: tetto visto dall'alto + facciata bassa sotto | Cioti | G | valida |
| D043 | 2026-11-01 | Stile | Palette propria di circa 42 colori in 9 rampe con spostamento di tinta, generata da parametri; la notte è la stessa palette trasformata | Cioti | G+S | valida |
| D044 | 2026-11-01 | Stile | Luce fissa dall'alto a sinistra, ombre in basso a destra, niente «pillow shading» | Cioti | G | valida |
| D045 | 2026-11-01 | Stile | Contorni alla LPC: quasi nero su figure e oggetti, tono scuro del materiale su edifici e alberi | Cioti | G | valida |
| D046 | 2026-11-01 | Stile | Personaggio 16x24 in sprite 16x32 (circa 2,5 teste); «regola del piano terra» per le altezze degli edifici | Cioti | G | valida |
| D047 | 2026-11-01 | Stile | Font proprio proporzionale 5x7 in file dati, con test dei glifi contro tutti i testi | Cioti | G | valida |
| D048 | 2026-11-01 | Stile | Interfaccia a vetrata (piombi, tessere, cornici 9-slice), dialogo in basso di 3 righe col cartiglio del nome | Cioti | S | valida |
| D049 | 2026-11-01 | Stile | Ritratti 32x32 a strati da parametri, 3 espressioni, solo per i personaggi della storia | Cioti | G | valida |
| D050 | 2026-11-01 | Stile | Animazione: camminata a 6 fotogrammi, attacco a 5 pose, sinistra = specchio hardware della destra | Cioti | G | valida |
| D051 | 2026-11-01 | Stile | Titolo in capitali lombarde oro col sottotitolo nel cartiglio | Cioti | S | valida |
| D052 | 2026-11-01 | Stile | La Guida di stile diventa dati (`stile/dati/*.json` → `include/stile/*.h` constexpr) con test di conformità; nessuno aggiunge colori | Claude | G | valida |
| D053 | 2026-11-01 | Stile | La Guida dice quali colori, luce e misure usare, ma non come si dipinge pezzo per pezzo: ogni thread dipinge col suo metodo | Claude | G | superata da D054 |
| D054 | 2026-11-04 | Stile | Standard grafico con regole siglate (C, L, P, M, F, A, I, O, W), quelle misurabili con test; un custode visivo approva ogni grafica nuova prima della fusione | Cioti | G | valida |
| D055 | 2026-11-04 | Stile | Ogni ambito grafico passa da un loop di almeno 10 giri di controllo e miglioramento, con tavole prima/dopo (sagome, edifici, interni, cutscene, menù, titolo, mappa) | Cioti | G | valida |
| D056 | 2026-11-04 | Stile | Porte leggibili: il nero aperto è riservato alle porte vere; ogni ingresso ha luce, soglia e insegna | Claude | G | valida |
| D057 | 2026-11-05 | Stile | Fedeltà col metodo dei professionisti: comprimere le distanze e non i segni, 3 segni per edificio, prima la silhouette, direzioni vere fra i luoghi | Cioti | G | valida |
| D058 | 2026-11-04 | Stile | Sagome e animazioni di battaglia rifatte con un generatore a parti; protagonisti presenti nelle cutscene | Cioti | G | valida |
| D059 | 2026-11-05 | Stile | Una figura, una forma: il controluce di una presentazione si ricava dalla figura a colori che segue, e ogni oggetto in primo piano si controlla perché non somigli a un simbolo d'interfaccia (bersagli, frecce, cursori) | Claude | G | valida |

## 4. Mondo e mappa

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D060 | 2026-11-01 | Mondo | Orientamento ruotato: in alto l'ovest, così le facciate principali (che guardano a est) si vedono di fronte | Cioti | S | superata da D061 |
| D061 | 2026-11-04 | Mondo | Nord in alto per città e mappa del menù, così si capisce il giro della città; tutte le facciate si disegnano verso il basso, il lato vero resta nei dati | Cioti | G | valida |
| D062 | 2026-11-01 | Mondo | Il contratto del mondo del prototipo (14 aree ad anello) vale così com'è | Cioti | S | superata da D063 |
| D063 | 2026-11-02 | Mondo | Il grafo delle aree si ricava dalla rete stradale vera (OpenStreetMap), con misure in pianta da OSM, 1 cella = 1,5 m e quote esagerate di 1,6 volte | Cioti | G | valida |
| D064 | 2026-11-02 | Mondo | Punto fermo della città approvata nel tag `citta-v1`; le correzioni arrivano come dati e passano dai generatori e dai test, mai griglie a mano | Cioti | G | valida |
| D065 | 2026-11-02 | Mondo | Aree grandi fino a 128 tile con le big map di Butano; nessuna piazza compressa | Claude | G | valida |
| D066 | 2026-11-04 | Mondo | Edifici esplorabili: 6 interni nella v1, le chiese di città restano chiuse | Claude, ok Cioti | S | valida |
| D067 | 2026-11-01 | Simboli | Simboli: si usano stemmi e colori storici; esclusi Ceri e divise moderne dei ceraioli (eccezione: i ceri dentro la Basilica); stemma del 1151 senza aggiunte successive | Cioti | S | valida |

## 5. Storia, testi e nomi (solo il metodo)

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D070 | 2026-11-01 | Storia | Copione scritto direttamente in scene, dalla scaletta del GDD, e messo subito nel motore | Claude | G | superata da D071 |
| D071 | 2026-11-03 | Storia | Prima un prompt strutturato (tema, fronti, archi, segreti, dilemmi, prove di qualità), poi una Bibbia della storia approvata da Cioti, solo dopo il copione | Cioti | G | valida |
| D072 | 2026-11-03 | Storia | Ogni copione, scaletta o cutscene passa da un grafo che cerca buchi e vicoli ciechi (`tools/grafo_trama.py`, 0 errori per fondere) | Cioti | G | valida |
| D073 | 2026-11-01 | Testi | Il copione in Markdown è l'unica sorgente dei testi: `genera_storia.py` → `genera_testi.py` → include, con a capo misurato in pixel | Claude | G | valida |
| D074 | 2026-11-03 | Persone | Amici di Cioti come NPC con nomi di gioco riconoscibili solo a chi sa; regola di rispetto (nessuno traditore, vigliacco o zimbello, nessuno muore in scena) | Cioti | G | valida |
| D075 | 2026-11-04 | Nomi | Luoghi con «San/Sant'»; i protagonisti santi senza «San» durante la storia; controllo automatico | Cioti | S | valida |
| D076 | 2026-11-04 | Nomi | Una sola fonte dei nomi (copione e `dati/` del repo); ogni copia fuori dal repo si rigenera; test dei nomi coerenti anche su docs e dati | Claude | G | valida |
| D077 | 2026-11-04 | Persone | Niente spoiler di trama a Cioti: a lui solo l'esito tecnico; la trama la validano i thread col grafo | Cioti | G | valida |
| D078 | 2026-11-04 | NPC | Molti NPC di contorno, anche con una sola battuta, per i mestieri della città | Cioti | G | valida |
| D079 | 2026-11-04 | NPC | NPC di contorno senza nome a schermo e con battute evocative | Claude | G | superata da D080 |
| D080 | 2026-11-05 | NPC | Ogni NPC ha il nome nel cartiglio; battute concrete (cosa fa, vede, teme), niente aforismi né riferimenti che il giocatore non può conoscere | Cioti | G | valida |
| D081 | 2026-11-04 | Testi | Revisione dei testi con test di redazione (tipografia, anacronismi lessicali, nomi all'italiana, convenzioni sugli oggetti) | Cioti | G | valida |
| D082 | 2026-11-04 | Scene | Disposizione fissa del trio in ogni scena: Ubaldo al centro, Giorgio a destra, Antonio a sinistra | Cioti | S | valida |
| D083 | 2026-11-05 | Tono | Il siparietto comico fra i tre protagonisti è un punto di forza da mantenere | Cioti | S | valida |

## 6. Cutscene, musica, sistemi di gioco

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D090 | 2026-11-02 | Cutscene | Cutscene cinematografiche a dati (copioni di regia): bande nere = si guarda, senza bande = si gioca; carrellata lenta; Start salta; al massimo 90 s | Cioti | G | valida |
| D091 | 2026-11-03 | Musica | Musica e effetti generati da script (`musica/*.brano` → XM e WAV), strumenti sintetizzati d'epoca, brani della tradizione cittadina; niente brani d'autore non verificato | Claude, ok Cioti | G+S | valida |
| D092 | 2026-11-02 | Battaglia | Battaglia come macchina a stati a eventi con un gemello in Python (mirror) che deve dare gli stessi risultati; bilanciamento col pilota automatico | Claude | G | valida |
| D093 | 2026-11-05 | Battaglia | Nessun altro nemico visibile nella v1, livelli tarati senza grind | Claude | S | valida |
| D094 | 2026-11-02 | Battaglia | Schermata di scelta delle mosse ridotta a un elenco di nomi | Claude | G | superata da D095 |
| D095 | 2026-11-05 | Battaglia | Schermata delle mosse con scheda (effetto, danno, costo) e anteprima sul bersaglio, sul modello dei giochi del genere | Claude | G | valida |
| D096 | 2026-11-04 | Menù | Pausa a 6 voci (Diario, Mappa, Bisaccia, Compagni, Salva, Opzioni), mappa con segnalini, promemoria dell'obiettivo, negozio, «libro» della città com'è oggi | Claude, ok Cioti | G | valida |
| D097 | 2026-11-01 | Salvataggio | Due slot con CRC e versione del formato; una versione vecchia si rifiuta pulita | Claude | G | valida |

## 7. Modo di lavorare

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D100 | 2026-11-01 | Processo | Claude può fondere da solo: finché non c'è una fase stabile i rami sono di sviluppo | Cioti | G | valida |
| D101 | 2026-11-02 | Processo | Niente attesa della CI a ogni fusione: si fonde dopo le prove locali, la CI si guarda ogni 3-4 fusioni | Cioti | G | valida |
| D102 | 2026-11-01 | Processo | Ogni scelta di Cioti si prepara con un'opzione consigliata e il perché, una alla volta | Cioti | G | valida |
| D103 | 2026-11-03 | Processo | Le scelte ragionevoli o in linea con le decisioni già prese le prende Claude da solo; si chiede solo per scelte nuove o di gusto | Cioti | G | valida |
| D104 | 2026-11-03 | Processo | Gli spunti di Cioti sono suggerimenti: se il lavoro fatto è buono si tiene | Cioti | G | valida |
| D105 | 2026-11-03 | Processo | Il coordinatore tiene allineati i thread: ogni decisione o prodotto rilevante va girato ai thread interessati | Cioti | G | valida |
| D106 | 2026-11-03 | Piano | Piano come grafo dei pezzi con dipendenze e risorse esclusive (`produzione.yaml` + `piano.py`) per sapere cosa si può fare in parallelo | Cioti | G | valida |
| D107 | 2026-11-04 | Processo | I thread lavorano insieme: custode visivo (standard grafico) e custode di trama e nomi (grafo a 0 errori) approvano prima di ogni fusione | Cioti | G | valida |
| D108 | 2026-11-06 | Metodo | Metodo di lavoro per la serie (`docs/metodo/`): registro delle decisioni, lezioni imparate e percorso da zero, aggiornati a ogni decisione o rifacimento e controllati da un test | Cioti | G | valida |

## 8. Rilascio

| ID | Data | Ambito | Decisione | Chi | Tipo | Stato |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| D110 | 2026-11-04 | Rilascio | Materiale pronto ma rilascio in pausa: checklist con persone vere, beni culturali (artt. 107-108), dichiarazione IA, «No payments», crediti | Cioti | G | valida |
| D111 | 2026-11-01 | Rilascio | Prima del rilascio verificare la norma sui beni culturali per l'uso non commerciale delle immagini dei monumenti | Claude | G | da rivedere |
